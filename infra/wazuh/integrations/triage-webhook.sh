#!/bin/sh
# Wazuh integration script — forwards alert JSON to the triage agent.
#
# Wazuh calls this with two args:
#   $1 = path to a temp file containing the alert JSON
#   $2 = the API key / hook URL (set in ossec.conf)
#
# Wire it up in ossec.conf:
#
#   <integration>
#     <name>triage-webhook</name>
#     <hook_url>http://triage-agent:8001/webhook/wazuh</hook_url>
#     <level>5</level>
#     <alert_format>json</alert_format>
#     <api_key>${TRIAGE_WEBHOOK_TOKEN}</api_key>
#   </integration>

set -eu

ALERT_FILE="$1"
HOOK_URL="${3:-http://triage-agent:8001/webhook/wazuh}"
TOKEN="${4:-}"

curl -sS -X POST "$HOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: $TOKEN" \
  --data-binary "@$ALERT_FILE" \
  --max-time 30 \
  > /var/ossec/logs/triage-webhook.log 2>&1

exit 0
