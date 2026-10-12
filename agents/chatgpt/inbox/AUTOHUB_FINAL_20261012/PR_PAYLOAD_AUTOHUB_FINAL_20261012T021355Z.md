# AUTOHUB FINAL COMMUNICATION_TEST

test_id: AUTOHUB_FINAL_20261012T021355Z
scope: COMMUNICATION_TEST
target: WORK_REVIEW
host_expected: ZHANGWEI
action_request: REVIEW_THEN_REPLY
r9_hold: true
copy_authorized: false

## Allowed reply actions only
- WRITE_TEST_MARKER
- VERIFY_TEST_MARKER
- REVIEW_COMPLETE

Reply path if writable:
agents/chatgpt/outbox/AUTOHUB_FINAL/REPLY_AUTOHUB_FINAL_20261012T021355Z.json

Example JSON:
{
  "schema": "AUTOHUB_FINAL_REPLY_V1",
  "scope": "COMMUNICATION_TEST",
  "from": "CHATGPT_WORK",
  "test_id": "AUTOHUB_FINAL_20261012T021355Z",
  "action": "WRITE_TEST_MARKER",
  "sandbox": "C:\\LAN_SHARE_REPORT\\AUTOHUB_FINAL\\sandbox",
  "r9_hold_unchanged": true
}

Do not command BLACKBOX / E / F / migration / delete / format.