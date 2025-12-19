# Jamie's Claude Plugins

Personal plugin marketplace for Claude Code.

## Installation

Add this marketplace to Claude Code:

```bash
claude plugin marketplace add jamiewilson1977/claude
```

Then install plugins:

```bash
claude plugin install jira
```

## Available Plugins

### jira

Manages Atlassian products (JIRA and Confluence) via REST API. Parameterized to work with any Atlassian instance.

**Features:**
- Create, update, and transition JIRA tickets
- Link tickets to epics
- Search issues with JQL
- Read and search Confluence pages

**Setup Required:**

1. Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens

2. Add authentication to keychain:
```bash
security add-generic-password -s 'atlassian-auth' -a 'jwilson' -w 'your-email@company.com:your-api-token'
```

3. Add configuration to keychain:
```bash
security add-generic-password -s 'atlassian-config' -a 'jwilson' -w '{"domain":"yourcompany.atlassian.net","project":"PROJ","issueTypeId":"10002"}'
```

See the full SKILL.md for all configuration options.
