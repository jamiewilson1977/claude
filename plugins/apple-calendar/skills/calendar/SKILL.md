---
name: apple-calendar
description: Use when the user asks about their schedule, events, meetings, appointments, availability, or wants to add/update/delete calendar events. Handles questions like "what's on my calendar", "am I free Friday", "add a meeting tomorrow", "what do I have this week". Manages Apple Calendar via EventKit across all accounts (iCloud, Google, Exchange).
---

# Apple Calendar Skill

Manage calendar events across all macOS Calendar accounts using EventKit. No credentials needed — uses macOS system permissions. Events sync automatically to all devices.

## How It Works

This plugin provides an MCP server (`apple-calendar`) that runs locally and has full access to macOS EventKit. Use the MCP tools for all calendar operations. If MCP tools are unavailable, fall back to the CLI script.

## Calendars

All calendars visible in Calendar.app are accessible. Use `mcp__apple-calendar__list_calendars` to see available calendars.

### Calendar Routing

| Keywords | Calendar |
|----------|----------|
| "work", "standup", "sprint", "meeting", "1:1", "Zylo" | Work calendar |
| "family", "kids", "Sam", "Lucas", "softball", "school" | Family |
| Default for new events | System default calendar |
| Generic queries | All calendars |

## MCP Tools

### List calendars
`mcp__apple-calendar__list_calendars` — no arguments.

### List events
`mcp__apple-calendar__list_events`:
- `start_date`: ISO datetime (e.g. `2026-03-05T00:00:00`)
- `end_date`: ISO datetime (e.g. `2026-03-05T23:59:59`)
- `calendar_name`: Optional filter

### Create event
`mcp__apple-calendar__create_event` with `create_event_request`:
- `title`, `start_time`, `end_time` (required)
- `calendar_name`, `location`, `notes`, `all_day`, `alarms_minutes_offsets`, `recurrence_rule` (optional)

### Update event
`mcp__apple-calendar__update_event`:
- `event_id` (required)
- `update_event_request` with optional fields to change

### Delete event (CLI only)
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py delete --event-id "ID"
```

## CLI Fallback

If MCP tools are not available, use:
```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py <command> [args]
```
Commands: `calendars`, `list`, `search`, `add`, `update`, `delete`

## Date & Time

- All dates use ISO format: `2026-03-05T14:00:00`
- For day ranges: start at `T00:00:00`, end at `T23:59:59`
- Default event duration: 1 hour
- System local timezone is used automatically

## Emoji Selection

Prepend a contextually appropriate emoji to event titles:

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

First run triggers a macOS permission dialog. If denied: **System Settings > Privacy & Security > Calendars** and enable access.
