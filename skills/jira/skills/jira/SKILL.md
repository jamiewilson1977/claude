---
name: jira
description: Manages Atlassian products (JIRA and Confluence) via REST API. Handles JIRA ticket creation, updates, epic linking, status changes. Also fetches and reads Confluence pages. Use when the user asks to "create a ticket", "update a ticket", "link to epic", "read this confluence page", or any JIRA/Confluence task.
---

# Atlassian Skill (JIRA + Confluence)

This skill handles JIRA and Confluence operations via the Atlassian REST APIs. It's parameterized to work with any Atlassian instance.

## Setup

The wrapper script is located at `${CLAUDE_PLUGIN_ROOT}/scripts/${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh`.

### Configure keychain entries

**Authentication (required):**
```bash
security add-generic-password -s 'atlassian-auth' -a 'jwilson' -w 'your-email@company.com:your-api-token'
```

**Configuration (required):**
```bash
security add-generic-password -s 'atlassian-config' -a 'jwilson' -w '{"domain":"yourcompany.atlassian.net","project":"PROJ","issueTypeId":"10002","focusFieldId":"customfield_10695","focusValueId":"10452"}'
```

### Config Fields

| Field | Description | Example |
|-------|-------------|---------|
| domain | Atlassian instance domain | `mycompany.atlassian.net` |
| project | Default project key | `PROJ` |
| issueTypeId | Default issue type ID | `10002` (Task) |
| focusFieldId | Custom field ID for focus/team | `customfield_10695` |
| focusValueId | Default focus value ID | `10452` |

---

## Reading Current Config

Run the wrapper with no endpoint to see current config:
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh
```

---

## Wrapper Script Usage

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh <METHOD> <endpoint> [json-body]
```

**Examples:**
```bash
# GET request
${CLAUDE_PLUGIN_ROOT}/scripts/${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh GET /rest/api/3/myself

# POST with JSON body
${CLAUDE_PLUGIN_ROOT}/scripts/${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh POST /rest/api/3/issue '{"fields":{...}}'

# PUT with JSON body
${CLAUDE_PLUGIN_ROOT}/scripts/${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh PUT /rest/api/3/issue/PROJ-123 '{"fields":{...}}'
```

---

# JIRA Operations

## 1. Create Ticket (Task by default)

**When:** User asks to create a new ticket, task, story, or issue

**Available Issue Types:**
| Type | ID | Use Case |
|------|-----|----------|
| Task | 10002 | Default for general work items |
| Bug | 10004 | Problems/defects |
| Spike | 10231 | Research/investigation work |
| Epic | 10000 | Large initiatives |
| Initiative | 10344 | Strategic work spanning multiple epics |

**Note:** Issue type IDs may vary by instance. Query available types with:
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh GET /rest/api/3/issuetype
```

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh POST /rest/api/3/issue '{
  "fields": {
    "project": {"key": "{PROJECT}"},
    "summary": "{title}",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [{"type": "paragraph", "content": [{"type": "text", "text": "{description}"}]}]
    },
    "issuetype": {"id": "{issueTypeId}"},
    "customfield_XXXXX": {"id": "{focusValueId}"}
  }
}'
```

**After creation:** Return the ticket key and link: `https://{domain}/browse/{key}`

---

## 2. Create Epic

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh POST /rest/api/3/issue '{
  "fields": {
    "project": {"key": "{PROJECT}"},
    "summary": "{epic title}",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [{"type": "paragraph", "content": [{"type": "text", "text": "{description}"}]}]
    },
    "issuetype": {"id": "10000"}
  }
}'
```

---

## 3. Link Ticket to Epic

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh PUT /rest/api/3/issue/{TICKET_KEY} '{"fields":{"parent":{"key":"{EPIC_KEY}"}}}'
```

---

## 4. Update Ticket

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh PUT /rest/api/3/issue/{TICKET_KEY} '{
  "fields": {
    "summary": "{new title}",
    "description": {
      "type": "doc",
      "version": 1,
      "content": [{"type": "paragraph", "content": [{"type": "text", "text": "{new description}"}]}]
    }
  }
}'
```

---

## 5. Add Comment

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh POST /rest/api/3/issue/{TICKET_KEY}/comment '{
  "body": {
    "type": "doc",
    "version": 1,
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "{comment text}"}]}]
  }
}'
```

---

## 6. Transition Status

**First, get available transitions:**
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh GET /rest/api/3/issue/{TICKET_KEY}/transitions
```

**Then apply transition:**
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh POST /rest/api/3/issue/{TICKET_KEY}/transitions '{"transition":{"id":"{transition_id}"}}'
```

---

## 7. Get Ticket Details

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh GET /rest/api/3/issue/{TICKET_KEY}
```

**Useful fields:** `fields.summary`, `fields.status.name`, `fields.assignee.displayName`, `fields.parent.key`

---

## 8. Search for Issues (JQL)

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh POST /rest/api/3/search/jql '{"jql": "project={PROJECT} AND assignee=currentUser()", "maxResults": 10}'
```

---

## 9. Search for Users

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh GET '/rest/api/3/user/search?query={name}'
```

---

# Confluence Operations

## 1. Get Page by ID

**Extract page ID from URL:** `https://.../wiki/spaces/{space}/pages/{pageId}/{title}` → `{pageId}`

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh GET '/wiki/api/v2/pages/{pageId}?body-format=storage'
```

**Response fields:** `title`, `body.storage.value` (HTML content)

---

## 2. Search Confluence

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh GET '/wiki/rest/api/content/search?cql=text~"{searchTerm}"'
```

---

## 3. List Pages in Space

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/atlassian-curl.sh GET /wiki/api/v2/spaces/{spaceId}/pages
```

---

## Parsing Confluence Content

The `body.storage.value` contains Atlassian Storage Format (XML/HTML). Common elements:
- `<h1>`, `<h2>`, `<h3>` - Headings
- `<p>` - Paragraphs
- `<table>`, `<tr>`, `<td>` - Tables
- `<ul>`, `<li>` - Lists
- `<ac:structured-macro>` - Macros

---

# Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Bad/expired credentials | Check keychain entry or regenerate API token |
| 404 Not Found | Issue/page doesn't exist | Verify ticket key or page ID |
| 400 Bad Request | Invalid field data | Check field names and formats |

---

# Switching Instances

To switch between Atlassian instances (e.g., Zylo vs IGG), update the config keychain entry:

```bash
# Delete existing
security delete-generic-password -s 'atlassian-config' -a 'jwilson'

# Add new config
security add-generic-password -s 'atlassian-config' -a 'jwilson' -w '{"domain":"igg.atlassian.net","project":"IGG",...}'
```

You may also need to update the auth entry if credentials differ between instances.

---

# Workflow Examples

### Create ticket and link to epic:
1. Create the ticket → returns key
2. Link to epic
3. Return ticket URL

### Read Confluence page:
1. Extract page ID from URL
2. Fetch with `body-format=storage`
3. Parse HTML content

---

# Notes

- Always return clickable links: `https://{domain}/browse/{KEY}`
- Use issue type IDs, not names
- Description uses Atlassian Document Format (ADF)
- Confluence content uses Atlassian Storage Format
- Pipe output through `jq` for parsing
