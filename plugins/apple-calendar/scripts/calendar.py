#!/usr/bin/env python3
"""
Apple Calendar CLI — manages events via EventKit/PyObjC.
All output is JSON to stdout. Errors go to stderr.

Usage:
    python3 calendar.py calendars
    python3 calendar.py list [--start-date DATE] [--days N] [--calendar NAME]
    python3 calendar.py search --query TEXT [--days N] [--calendar NAME]
    python3 calendar.py add --title TEXT --start DT --end DT [options]
    python3 calendar.py update --event-id ID [--title TEXT] [--start DT] [--end DT] [options]
    python3 calendar.py delete --event-id ID
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from threading import Semaphore

try:
    from EventKit import (
        EKAlarm,
        EKEntityTypeEvent,
        EKEvent,
        EKEventStore,
        EKRecurrenceDayOfWeek,
        EKRecurrenceEnd,
        EKRecurrenceRule,
        EKSpanFutureEvents,
        EKSpanThisEvent,
    )
    from Foundation import NSDate
except ImportError:
    print("Installing pyobjc-framework-EventKit...", file=sys.stderr)
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "pyobjc-framework-EventKit"],
        stdout=sys.stderr, stderr=sys.stderr,
    )
    from EventKit import (
        EKAlarm,
        EKEntityTypeEvent,
        EKEvent,
        EKEventStore,
        EKRecurrenceDayOfWeek,
        EKRecurrenceEnd,
        EKRecurrenceRule,
        EKSpanFutureEvents,
        EKSpanThisEvent,
    )
    from Foundation import NSDate

# ---------------------------------------------------------------------------
# Timezone helper
# ---------------------------------------------------------------------------

def _local_tz():
    """Return the system local timezone."""
    return datetime.now(timezone.utc).astimezone().tzinfo


def _parse_datetime(s):
    """Parse an ISO-format string into a timezone-aware datetime.

    - Date-only strings (e.g. '2026-03-01') are treated as midnight local time.
    - Datetime strings without tz info get local timezone attached.
    - Datetime strings with tz info are used as-is.
    """
    if "T" in s:
        dt = datetime.fromisoformat(s)
    else:
        dt = datetime.strptime(s, "%Y-%m-%d")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_local_tz())
    return dt


def _dt_to_nsdate(dt):
    """Convert a datetime to NSDate."""
    return NSDate.dateWithTimeIntervalSince1970_(dt.timestamp())


def _nsdate_to_dt(nsdate):
    """Convert an NSDate to a timezone-aware local datetime."""
    ts = nsdate.timeIntervalSince1970()
    return datetime.fromtimestamp(ts, tz=_local_tz())

# ---------------------------------------------------------------------------
# EventKit helpers
# ---------------------------------------------------------------------------

def _request_access(store):
    """Request calendar access using semaphore pattern."""
    semaphore = Semaphore(0)
    access_granted = False

    def completion(granted, error):
        nonlocal access_granted
        access_granted = granted
        semaphore.release()

    store.requestAccessToEntityType_completion_(EKEntityTypeEvent, completion)
    semaphore.acquire()
    return access_granted


def _get_store():
    """Create an EKEventStore and request access. Exits on failure."""
    store = EKEventStore.alloc().init()
    if not _request_access(store):
        _error_exit("Calendar access not granted. Check System Settings > Privacy & Security > Calendars.")
    return store


def _find_calendar(store, name):
    """Find a calendar by name (case-sensitive). Returns None if not found."""
    for cal in store.calendarsForEntityType_(EKEntityTypeEvent):
        if cal.title() == name:
            return cal
    return None


def _event_to_dict(ekevent):
    """Convert an EKEvent to a JSON-serializable dict."""
    start_dt = _nsdate_to_dt(ekevent.startDate())
    end_dt = _nsdate_to_dt(ekevent.endDate())

    d = {
        "id": ekevent.eventIdentifier(),
        "title": ekevent.title(),
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
        "all_day": bool(ekevent.isAllDay()),
        "calendar": ekevent.calendar().title(),
    }

    if ekevent.location():
        d["location"] = ekevent.location()
    if ekevent.notes():
        d["notes"] = ekevent.notes()
    if ekevent.URL():
        d["url"] = str(ekevent.URL())

    # Alarms
    if ekevent.alarms():
        d["reminders_minutes"] = []
        for alarm in ekevent.alarms():
            minutes = int(-alarm.relativeOffset() / 60)
            d["reminders_minutes"].append(minutes)

    # Attendees
    if ekevent.attendees():
        d["attendees"] = [str(a.name()) for a in ekevent.attendees() if a.name()]

    # Organizer
    if ekevent.organizer() and ekevent.organizer().name():
        d["organizer"] = str(ekevent.organizer().name())

    # Recurrence
    if ekevent.recurrenceRule():
        rule = ekevent.recurrenceRule()
        freq_map = {0: "daily", 1: "weekly", 2: "monthly", 3: "yearly"}
        rec = {
            "frequency": freq_map.get(rule.frequency(), "unknown"),
            "interval": rule.interval(),
        }
        if rule.recurrenceEnd():
            if rule.recurrenceEnd().endDate():
                rec["end_date"] = _nsdate_to_dt(rule.recurrenceEnd().endDate()).isoformat()
            elif rule.recurrenceEnd().occurrenceCount():
                rec["occurrence_count"] = rule.recurrenceEnd().occurrenceCount()
        if rule.daysOfTheWeek():
            day_names = {1: "SU", 2: "MO", 3: "TU", 4: "WE", 5: "TH", 6: "FR", 7: "SA"}
            rec["days_of_week"] = [day_names.get(d.dayOfTheWeek(), "?") for d in rule.daysOfTheWeek()]
        d["recurrence"] = rec

    return d

# ---------------------------------------------------------------------------
# Recurrence builder
# ---------------------------------------------------------------------------

FREQ_MAP = {"daily": 0, "weekly": 1, "monthly": 2, "yearly": 3}
DAY_MAP = {"SU": 1, "MO": 2, "TU": 3, "WE": 4, "TH": 5, "FR": 6, "SA": 7}


def _build_recurrence_rule(freq_str, interval=1, end_date=None, count=None, days=None):
    """Build an EKRecurrenceRule from simple parameters."""
    freq = FREQ_MAP.get(freq_str.lower())
    if freq is None:
        return None

    end = None
    if end_date:
        end = EKRecurrenceEnd.recurrenceEndWithEndDate_(_dt_to_nsdate(_parse_datetime(end_date)))
    elif count:
        end = EKRecurrenceEnd.recurrenceEndWithOccurrenceCount_(count)

    ek_days = None
    if days:
        ek_days = []
        for d in days:
            day_num = DAY_MAP.get(d.upper())
            if day_num:
                ek_days.append(
                    EKRecurrenceDayOfWeek.alloc().initWithDayOfTheWeek_weekNumber_(day_num, 0)
                )

    return EKRecurrenceRule.alloc().initRecurrenceWithFrequency_interval_daysOfTheWeek_daysOfTheMonth_monthsOfTheYear_weeksOfTheYear_daysOfTheYear_setPositions_end_(
        freq, interval, ek_days, None, None, None, None, None, end,
    )

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def _success(data):
    """Print a success JSON response and exit."""
    print(json.dumps({"success": True, **data}, ensure_ascii=False))
    sys.exit(0)


def _error_exit(msg):
    """Print an error JSON response and exit with code 1."""
    print(json.dumps({"success": False, "error": str(msg)}, ensure_ascii=False))
    sys.exit(1)

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

MAX_TITLE_LEN = 500
MAX_NOTES_LEN = 5000
MAX_DAYS = 365


def _validate_string(value, name, max_len):
    if value and len(value) > max_len:
        _error_exit(f"{name} exceeds maximum length of {max_len} characters")


def _validate_days(days):
    if days < 1 or days > MAX_DAYS:
        _error_exit(f"Days must be between 1 and {MAX_DAYS}")

# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_calendars(args):
    """List all visible calendars."""
    store = _get_store()
    calendars = []
    for cal in store.calendarsForEntityType_(EKEntityTypeEvent):
        source = cal.source()
        calendars.append({
            "name": cal.title(),
            "type": {0: "local", 1: "exchange", 2: "caldav", 3: "mobileme",
                     4: "subscribed", 5: "birthdays"}.get(cal.type(), "unknown"),
            "source": source.title() if source else None,
            "color": str(cal.color()) if cal.color() else None,
            "immutable": bool(cal.isImmutable()),
        })
    _success({"calendars": calendars})


def cmd_list(args):
    """List events in a date range."""
    _validate_days(args.days)
    store = _get_store()

    if args.start_date:
        start = _parse_datetime(args.start_date)
    else:
        start = datetime.now(tz=_local_tz()).replace(hour=0, minute=0, second=0, microsecond=0)

    end = start + timedelta(days=args.days)

    # Calendar filter
    cals = None
    if args.calendar:
        cal = _find_calendar(store, args.calendar)
        if not cal:
            _error_exit(f"Calendar '{args.calendar}' not found")
        cals = [cal]

    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
        _dt_to_nsdate(start), _dt_to_nsdate(end), cals
    )
    events = store.eventsMatchingPredicate_(predicate)
    results = sorted([_event_to_dict(e) for e in events], key=lambda x: x["start"])
    _success({"events": results, "count": len(results)})


def cmd_search(args):
    """Search events by title."""
    _validate_days(args.days)
    store = _get_store()

    now = datetime.now(tz=_local_tz())
    start = now - timedelta(days=30)
    end = now + timedelta(days=args.days)

    cals = None
    if args.calendar:
        cal = _find_calendar(store, args.calendar)
        if not cal:
            _error_exit(f"Calendar '{args.calendar}' not found")
        cals = [cal]

    predicate = store.predicateForEventsWithStartDate_endDate_calendars_(
        _dt_to_nsdate(start), _dt_to_nsdate(end), cals
    )
    events = store.eventsMatchingPredicate_(predicate)

    query_lower = args.query.lower()
    matches = []
    for e in events:
        title = e.title() or ""
        notes = e.notes() or ""
        location = e.location() or ""
        if query_lower in title.lower() or query_lower in notes.lower() or query_lower in location.lower():
            matches.append(_event_to_dict(e))

    matches.sort(key=lambda x: x["start"])
    _success({"events": matches, "count": len(matches)})


def cmd_add(args):
    """Create a new event."""
    _validate_string(args.title, "Title", MAX_TITLE_LEN)
    _validate_string(args.notes, "Notes", MAX_NOTES_LEN)
    _validate_string(args.location, "Location", MAX_TITLE_LEN)

    store = _get_store()
    event = EKEvent.eventWithEventStore_(store)
    event.setTitle_(args.title)

    # All-day detection
    is_all_day = "T" not in args.start
    start_dt = _parse_datetime(args.start)
    end_dt = _parse_datetime(args.end)

    if end_dt <= start_dt:
        _error_exit("End time must be after start time")

    event.setStartDate_(_dt_to_nsdate(start_dt))
    event.setEndDate_(_dt_to_nsdate(end_dt))

    if is_all_day or args.all_day:
        event.setAllDay_(True)

    if args.location:
        event.setLocation_(args.location)
    if args.notes:
        event.setNotes_(args.notes)

    # Reminder
    if args.reminder is not None:
        alarm = EKAlarm.alarmWithRelativeOffset_(-60 * args.reminder)
        event.addAlarm_(alarm)

    # Recurrence
    if args.recurrence:
        rule = _build_recurrence_rule(
            args.recurrence,
            interval=args.recurrence_interval or 1,
            end_date=args.recurrence_end,
            count=args.recurrence_count,
            days=args.recurrence_days.split(",") if args.recurrence_days else None,
        )
        if rule:
            event.setRecurrenceRule_(rule)

    # Calendar
    if args.calendar:
        cal = _find_calendar(store, args.calendar)
        if not cal:
            _error_exit(f"Calendar '{args.calendar}' not found")
        event.setCalendar_(cal)
    else:
        default_cal = store.defaultCalendarForNewEvents()
        if default_cal:
            event.setCalendar_(default_cal)

    success, error = store.saveEvent_span_error_(event, EKSpanThisEvent, None)
    if not success:
        _error_exit(f"Failed to create event: {error}")

    _success({"event": _event_to_dict(event)})


def cmd_update(args):
    """Update an existing event."""
    _validate_string(args.title, "Title", MAX_TITLE_LEN)
    _validate_string(args.notes, "Notes", MAX_NOTES_LEN)
    _validate_string(args.location, "Location", MAX_TITLE_LEN)

    store = _get_store()
    event = store.eventWithIdentifier_(args.event_id)
    if not event:
        _error_exit(f"Event not found: {args.event_id}")

    if args.title:
        event.setTitle_(args.title)
    if args.start:
        event.setStartDate_(_dt_to_nsdate(_parse_datetime(args.start)))
    if args.end:
        event.setEndDate_(_dt_to_nsdate(_parse_datetime(args.end)))
    if args.location:
        event.setLocation_(args.location)
    if args.notes:
        event.setNotes_(args.notes)
    if args.calendar:
        cal = _find_calendar(store, args.calendar)
        if not cal:
            _error_exit(f"Calendar '{args.calendar}' not found")
        event.setCalendar_(cal)

    success, error = store.saveEvent_span_error_(event, EKSpanFutureEvents, None)
    if not success:
        _error_exit(f"Failed to update event: {error}")

    _success({"event": _event_to_dict(event)})


def cmd_delete(args):
    """Delete an event."""
    store = _get_store()
    event = store.eventWithIdentifier_(args.event_id)
    if not event:
        _error_exit(f"Event not found: {args.event_id}")

    title = event.title()
    success, error = store.removeEvent_span_error_(event, EKSpanFutureEvents, None)
    if not success:
        _error_exit(f"Failed to delete event: {error}")

    _success({"deleted": args.event_id, "title": title})

# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Apple Calendar CLI via EventKit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- calendars ---
    subparsers.add_parser("calendars", help="List all visible calendars")

    # --- list ---
    p_list = subparsers.add_parser("list", help="List events in a date range")
    p_list.add_argument("--start-date", help="Start date (YYYY-MM-DD), default today")
    p_list.add_argument("--days", type=int, default=7, help="Number of days (default 7)")
    p_list.add_argument("--calendar", help="Filter by calendar name")

    # --- search ---
    p_search = subparsers.add_parser("search", help="Search events by title/notes/location")
    p_search.add_argument("--query", "-q", required=True, help="Search text")
    p_search.add_argument("--days", type=int, default=90, help="Days ahead to search (default 90)")
    p_search.add_argument("--calendar", help="Filter by calendar name")

    # --- add ---
    p_add = subparsers.add_parser("add", help="Create a new event")
    p_add.add_argument("--title", "-t", required=True, help="Event title")
    p_add.add_argument("--start", "-s", required=True, help="Start date or datetime (ISO format)")
    p_add.add_argument("--end", "-e", required=True, help="End date or datetime (ISO format)")
    p_add.add_argument("--calendar", help="Calendar name (default: system default)")
    p_add.add_argument("--location", "-l", help="Event location")
    p_add.add_argument("--notes", "-n", help="Event notes")
    p_add.add_argument("--reminder", type=int, help="Reminder minutes before event")
    p_add.add_argument("--all-day", action="store_true", help="Force all-day event")
    p_add.add_argument("--recurrence", choices=["daily", "weekly", "monthly", "yearly"],
                        help="Recurrence frequency")
    p_add.add_argument("--recurrence-interval", type=int, help="Recurrence interval (default 1)")
    p_add.add_argument("--recurrence-end", help="Recurrence end date (ISO format)")
    p_add.add_argument("--recurrence-count", type=int, help="Number of occurrences")
    p_add.add_argument("--recurrence-days", help="Days of week for weekly recurrence (e.g. MO,WE,FR)")

    # --- update ---
    p_update = subparsers.add_parser("update", help="Update an existing event")
    p_update.add_argument("--event-id", required=True, help="Event identifier")
    p_update.add_argument("--title", "-t", help="New title")
    p_update.add_argument("--start", "-s", help="New start date/datetime")
    p_update.add_argument("--end", "-e", help="New end date/datetime")
    p_update.add_argument("--calendar", help="Move to calendar name")
    p_update.add_argument("--location", "-l", help="New location")
    p_update.add_argument("--notes", "-n", help="New notes")

    # --- delete ---
    p_delete = subparsers.add_parser("delete", help="Delete an event")
    p_delete.add_argument("--event-id", required=True, help="Event identifier")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        {
            "calendars": cmd_calendars,
            "list": cmd_list,
            "search": cmd_search,
            "add": cmd_add,
            "update": cmd_update,
            "delete": cmd_delete,
        }[args.command](args)
    except SystemExit:
        raise
    except Exception as e:
        _error_exit(str(e))


if __name__ == "__main__":
    main()
