---
name: calendar
description: Manage Apple Calendar events with natural language
allowed-tools: Bash
---

# /calendar — Apple Calendar Management

You manage calendar events via `${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py`. Parse the user's natural language request and execute the appropriate subcommand.

## Script

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
| Generic queries ("what's on my schedule?", "this week") | All calendars (omit --calendar) |

Use `--calendar "Name"` to target a specific calendar. Run `calendars` first if unsure which calendars are available.

## Date & Time Formats

| User Says | --start | --end | Type |
|-----------|---------|-------|------|
| "March 5" | `2026-03-05` | `2026-03-06` | All-day |
| "March 5-7" | `2026-03-05` | `2026-03-08` | Multi-day (end exclusive) |
| "March 5 at 2pm" | `2026-03-05T14:00:00` | `2026-03-05T15:00:00` | Timed (1hr default) |
| "March 5 2-4pm" | `2026-03-05T14:00:00` | `2026-03-05T16:00:00` | Timed |
| "tomorrow at 9am for 30min" | Calculate date, `T09:00:00` | `T09:30:00` | Timed |

Rules:
- **All-day events**: Use date-only format (no T). End date is exclusive (June 11-14 → start: 06-11, end: 06-15)
- **Timed events**: Use datetime with T. Default duration is 1 hour if end not specified
- **Use the current date** as reference: today is the date shown in system context
- **Timezone**: The script uses the system local timezone automatically

## Emoji Selection

Prepend a contextually appropriate emoji to the event title:

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

## Subcommands Reference

### List calendars
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py calendars
```

### List events
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py list [--start-date YYYY-MM-DD] [--days N] [--calendar "Name"]
```

### Search events
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py search --query "text" [--days N] [--calendar "Name"]
```

### Add event
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/calendar.py add \
  --title "🏀 Event Title" \
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
  [--title "New Title"] \
  [--start "2026-03-06T14:00:00"] \
  [--end "2026-03-06T15:00:00"] \
  [--calendar "Name"] \
  [--location "New Place"] \
  [--notes "New notes"]
```

### Delete event
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
7. **For updates**: First search/list to find the event, then confirm changes
8. **Execute** the script command
9. **Confirm** the result with a brief summary

## Recurrence

For recurring events, add:
- `--recurrence daily|weekly|monthly|yearly`
- `--recurrence-interval N` (every N periods, default 1)
- `--recurrence-days MO,TU,WE,TH,FR,SA,SU` (for weekly)
- `--recurrence-end YYYY-MM-DD` or `--recurrence-count N`

Examples: "every weekday" → `--recurrence weekly --recurrence-days MO,TU,WE,TH,FR`
