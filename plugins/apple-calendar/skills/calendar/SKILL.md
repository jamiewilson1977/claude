---
name: apple-calendar
description: Use when the user asks about their schedule, events, meetings, appointments, availability, or wants to add/update/delete calendar events. Handles questions like "what's on my calendar", "am I free Friday", "add a meeting tomorrow", "what do I have this week". Manages Apple Calendar via EventKit across all accounts (iCloud, Google, Exchange).
---

# Apple Calendar Skill

Manage calendar events across all macOS Calendar accounts using a single EventKit-based script. No credentials needed — uses macOS system permissions. Events sync automatically to all devices.

## Calendars

All calendars visible in Calendar.app are accessible. Run `calendars` to see what's available:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py calendars
```

### Calendar Routing

| Keywords | Calendar |
|----------|----------|
| "work", "standup", "sprint", "meeting", "1:1", "Zylo" | Work calendar |
| "family", "kids", "Sam", "Lucas", "softball", "school" | Family |
| Default for new events | System default calendar |
| Generic queries | All calendars |

## Script

All operations go through a single CLI:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py <command> [args]
```

All output is JSON: `{"success": true, ...}` or `{"success": false, "error": "..."}`.

## Commands

### List calendars
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py calendars
```

### List events
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py list [--start-date YYYY-MM-DD] [--days 7] [--calendar "Name"]
```

### Search events
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py search --query "text" [--days 90] [--calendar "Name"]
```
Searches title, notes, and location fields.

### Add event
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py add \
  --title "🏀 Event" \
  --start "2026-03-05T14:00:00" \
  --end "2026-03-05T15:00:00" \
  [--calendar "Name"] \
  [--location "Place"] \
  [--notes "Details"] \
  [--reminder 15] \
  [--all-day] \
  [--recurrence weekly --recurrence-days MO,WE,FR]
```

### Update event
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py update \
  --event-id "ID" \
  [--title "New Title"] [--start DT] [--end DT] \
  [--calendar "Name"] [--location "Place"] [--notes "Notes"]
```

### Delete event
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py delete --event-id "ID"
```

## Date & Time Formats

| Format | Example | Type |
|--------|---------|------|
| Date only | `2026-03-05` | All-day event |
| Date range | start: `2026-03-05`, end: `2026-03-08` | Multi-day (end exclusive) |
| With time | `2026-03-05T14:00:00` | Timed event |

- Date-only = all-day event
- End date for all-day events is **exclusive** (June 11-14 → end: June 15)
- Default duration for timed events: 1 hour
- All times use the system local timezone

## Recurrence

| Pattern | Flags |
|---------|-------|
| Every day | `--recurrence daily` |
| Every 2 weeks | `--recurrence weekly --recurrence-interval 2` |
| Weekdays | `--recurrence weekly --recurrence-days MO,TU,WE,TH,FR` |
| Monthly, 10 times | `--recurrence monthly --recurrence-count 10` |
| Yearly until date | `--recurrence yearly --recurrence-end 2028-01-01` |

## Emoji Selection

Auto-select contextually appropriate emojis for event titles:

| Category | Emojis |
|----------|--------|
| Sports | 🥎 ⚾ 🏀 ⚽ 🏈 🎾 🏊 🏃 💪 |
| Medical | 🦷 👨‍⚕️ 💊 🏥 |
| Work | 💼 📊 🤝 📞 |
| Travel | ✈️ 🚗 🏨 |
| Family | 👨‍👩‍👧 🎂 🎉 |
| School | 📚 🎓 🏫 |
| Food/Drink | 🍽️ ☕ 🍕 🍺 |
| Entertainment | 🎬 🎵 🎭 🎮 |
| Pets | 🐕 🐾 |
| Personal care | ✂️ 💇 💅 |
| Default | 📅 |

## Permissions

The script uses macOS EventKit, which requires calendar access:
- First run will trigger a macOS permission dialog
- If denied, go to **System Settings > Privacy & Security > Calendars** and enable access for Terminal / your IDE
