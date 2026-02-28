---
name: calendar
description: Manage Apple Calendar events with natural language
allowed-tools: mcp__apple-calendar__list_calendars, mcp__apple-calendar__list_events, mcp__apple-calendar__create_event, mcp__apple-calendar__update_event, Bash
---

# /calendar — Apple Calendar Management

You manage calendar events using the `apple-calendar` MCP tools. Parse the user's natural language request and call the appropriate tool.

If MCP tools are not available (tool not found errors), fall back to the CLI script:
```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py <subcommand> [args]
```

## Calendar Routing

Determine the target calendar from context:

| Keywords | Calendar |
|----------|----------|
| "work", "standup", "sprint", "meeting", "1:1", "Zylo" | Work calendar |
| "family", "kids", "Sam", "Lucas", "softball", "school" | Family |
| "birthday" | Family |
| Default for new events | System default (personal) |
| Generic queries ("what's on my schedule?", "this week") | All calendars (omit calendar_name) |

## Date & Time Formats

| User Says | start_date | end_date | Type |
|-----------|------------|----------|------|
| "March 5" | `2026-03-05T00:00:00` | `2026-03-05T23:59:59` | All-day |
| "March 5-7" | `2026-03-05T00:00:00` | `2026-03-07T23:59:59` | Multi-day |
| "March 5 at 2pm" | `2026-03-05T14:00:00` | `2026-03-05T15:00:00` | Timed (1hr default) |
| "March 5 2-4pm" | `2026-03-05T14:00:00` | `2026-03-05T16:00:00` | Timed |
| "this week" | Monday `T00:00:00` | Sunday `T23:59:59` | Range |

Rules:
- **All-day queries**: Start at `T00:00:00`, end at `T23:59:59`
- **Timed events**: Use ISO datetime format. Default duration is 1 hour if end not specified
- **Use the current date** as reference: today is the date shown in system context

## Emoji Selection

Prepend a contextually appropriate emoji to the event title when creating:

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

## MCP Tools Reference

### List calendars
Use `mcp__apple-calendar__list_calendars` — no arguments needed.

### List events
Use `mcp__apple-calendar__list_events`:
- `start_date`: ISO datetime (e.g. `2026-03-05T00:00:00`)
- `end_date`: ISO datetime (e.g. `2026-03-05T23:59:59`)
- `calendar_name`: Optional — filter by calendar name

### Create event
Use `mcp__apple-calendar__create_event` with a `create_event_request` object:
- `title`: Event title (with emoji prefix)
- `start_time`: ISO datetime
- `end_time`: ISO datetime
- `calendar_name`: Optional calendar name
- `location`: Optional location
- `notes`: Optional notes
- `all_day`: Boolean, default false
- `alarms_minutes_offsets`: Optional list of minutes before event for reminders (e.g. `[15]`)
- `recurrence_rule`: Optional object with `frequency` (0=daily, 1=weekly, 2=monthly, 3=yearly), `interval`, `days_of_week`, `end_date`, `occurrence_count`

### Update event
Use `mcp__apple-calendar__update_event`:
- `event_id`: The event identifier (from list_events output)
- `update_event_request`: Object with optional fields: `title`, `start_time`, `end_time`, `calendar_name`, `location`, `notes`, `all_day`, `alarms_minutes_offsets`, `recurrence_rule`

### Delete event (CLI fallback)
MCP server does not have delete. Use the CLI:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py delete --event-id "ID"
```

## Conversation Flow

1. **Parse** the natural language request
2. **Determine target calendar(s)** using the routing table above
3. **Fill in missing details** — ask the user if critical info is missing (e.g., date for an event)
4. **Select emoji** based on event content
5. **For creates**: Show the planned event details and ask for confirmation before executing
6. **For deletes**: Show the event to be deleted and confirm before executing
7. **For updates**: First list to find the event, then confirm changes
8. **Execute** the MCP tool call
9. **Confirm** the result with a brief summary

## Recurrence

For recurring events, include a `recurrence_rule` in the create request:
- `frequency`: 0=daily, 1=weekly, 2=monthly, 3=yearly
- `interval`: Every N periods (default 1)
- `days_of_week`: List of day numbers (1=Sunday, 2=Monday, ... 7=Saturday)
- `end_date`: ISO datetime to stop recurring
- `occurrence_count`: Number of times to recur

Example — "every weekday": `{"frequency": 1, "interval": 1, "days_of_week": [2, 3, 4, 5, 6]}`
