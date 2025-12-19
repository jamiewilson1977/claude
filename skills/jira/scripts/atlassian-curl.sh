#!/bin/bash
# Parameterized wrapper for curl with Atlassian auth from keychain
# Usage: atlassian-curl.sh <method> <endpoint> [json-body]
#
# Keychain entries required:
#   - atlassian-auth: email:api-token (for authentication)
#   - atlassian-config: JSON with domain, project, focusFieldId, etc.
#
# Example atlassian-config value:
#   {"domain":"mycompany.atlassian.net","project":"PROJ","issueTypeId":"10002","focusFieldId":"customfield_10695","focusValueId":"10452"}
#
# Examples:
#   atlassian-curl.sh GET /rest/api/3/myself
#   atlassian-curl.sh GET /wiki/api/v2/pages/12345?body-format=storage
#   atlassian-curl.sh POST /rest/api/3/issue '{"fields":{...}}'
#   atlassian-curl.sh PUT /rest/api/3/issue/GREEN-123 '{"fields":{...}}'

METHOD="${1:-GET}"
ENDPOINT="$2"
BODY="$3"

# Read config from keychain
CONFIG=$(security find-generic-password -s 'atlassian-config' -a 'jwilson' -w 2>/dev/null)
if [ -z "$CONFIG" ]; then
  echo "Error: atlassian-config not found in keychain" >&2
  echo "Set it with: security add-generic-password -s 'atlassian-config' -a 'jwilson' -w '<json-config>'" >&2
  exit 1
fi

# Parse config JSON
DOMAIN=$(echo "$CONFIG" | jq -r '.domain // empty')
if [ -z "$DOMAIN" ]; then
  echo "Error: 'domain' not found in atlassian-config" >&2
  exit 1
fi

# Read auth from keychain
AUTH_RAW=$(security find-generic-password -s 'atlassian-auth' -a 'jwilson' -w 2>/dev/null)
if [ -z "$AUTH_RAW" ]; then
  echo "Error: atlassian-auth not found in keychain" >&2
  echo "Set it with: security add-generic-password -s 'atlassian-auth' -a 'jwilson' -w 'email:api-token'" >&2
  exit 1
fi
AUTH=$(echo -n "$AUTH_RAW" | base64)

if [ -z "$ENDPOINT" ]; then
  echo "Usage: atlassian-curl.sh <method> <endpoint> [json-body]"
  echo ""
  echo "Current config:"
  echo "  Domain: $DOMAIN"
  echo "  Project: $(echo "$CONFIG" | jq -r '.project // "not set"')"
  exit 1
fi

# Build URL (add domain if endpoint starts with /)
if [[ "$ENDPOINT" == /* ]]; then
  URL="https://${DOMAIN}${ENDPOINT}"
else
  URL="$ENDPOINT"
fi

if [ -n "$BODY" ]; then
  curl -s -X "$METHOD" \
    -H "Authorization: Basic $AUTH" \
    -H "Content-Type: application/json" \
    -d "$BODY" \
    "$URL"
else
  curl -s -X "$METHOD" \
    -H "Authorization: Basic $AUTH" \
    -H "Content-Type: application/json" \
    "$URL"
fi
