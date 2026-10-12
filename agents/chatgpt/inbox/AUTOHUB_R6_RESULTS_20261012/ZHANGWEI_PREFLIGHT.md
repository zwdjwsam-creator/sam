# AUTOHUB R6 — ZHANGWEI CLI Approval Gate Preflight

task_id: AUTOHUB_R6_CLI_APPROVAL_GATE_20261012
host: ZHANGWEI
scope: PREPARE_ONLY_UNTIL_OWNER_APPROVES
reported_utc: 20261012T012145Z
status: PENDING_OWNER_APPROVAL_FOR_INSTALL

## Core fields

| Field | Value |
|------|--------|
| OFFICIAL_WINDOWS_AGENT_CLI_DOC_CONFIRMED | PASS |
| INSTALL_AUTHORIZATION_STATUS | PENDING_OWNER |
| ACCOUNT_CLI_ELIGIBILITY | UNVERIFIED (no account credential/settings scrape; not claimed) |
| USAGE_CHARGES_KNOWN | PARTIAL — CLI uses Cursor Agent models; exact quota/billing UI not inspected this round |
| HEADLESS_CLI_BROWSER_TAB_BRIDGE_STATUS | UNVERIFIED / likely SEPARATE — official CLI is terminal `agent`; prior R4 Browser PASS was GUI Agent session + cursor-ide-browser, not headless CLI |
| ANY_RUNNING_AUTOMATION_CREATED | false |
| R9_HOLD_UNCHANGED | true |
| COPY_AUTHORIZED | false |
| INSTALL_EXECUTED | false |

## Official docs (read-only)

- Overview: https://cursor.com/docs/cli/overview
  - Windows PowerShell install candidate: `irm 'https://cursor.com/install?win32=true' | iex`
  - Entry command: `agent`
  - Non-interactive: `agent -p "..."` (print mode for scripts/CI)
- Installation: https://cursor.com/docs/cli/installation
  - Verify: `agent --version`
  - Notes PATH may need `~/.local/bin` (Unix docs); Windows native install path not fully enumerated in fetched page
- Doc authenticity: served from cursor.com official docs host; install URL is the documented official channel. This run did **not** download or execute the installer.

## Local read-only recheck (no install)

- Cursor GUI: 3.24.12 at `C:\cursor\Cursor.exe` / `cursor.cmd` (editor launcher only)
- `agent` / `cursor-agent` on PATH: absent
- `agent.exe` shallow search: none
- Prior one-shot tasks remain Disabled: AUTOHUB_R4B_GPT_REPLY_CONSUME_ONCE, AUTOHUB_R5_MARKER_ONCE
- No new permanent scheduled task created this round
- R4/R5 not re-run

## BACKGROUND_CLI_TO_GUI_BROWSER_TAB

| Claim | Evidence status |
|------|-----------------|
| GUI Agent + Browser Tab can drive logged-in ChatGPT | PASS (R4 prior evidence) |
| Headless `agent -p` can attach to existing Cursor GUI Browser Tab | UNVERIFIED — no official doc statement found in overview/install pages that CLI inherits IDE Browser MCP/tab |
| PowerShell MARKER via Task Scheduler equals Agent wake | false (R5 already recorded) |

Do not treat CLI install success as ChatGPT web-bridge PASS.

## ONE_TIME_PERMISSION_REQUEST (for owner)

Please reply with an explicit approval if you want the next authorized task to:

1. Run the **official** Windows install only: `irm 'https://cursor.com/install?win32=true' | iex`
2. Authenticate CLI with the **existing** Cursor account already used on ZHANGWEI (interactive login if required; no credential upload to HUB)
3. Run **one** C-only harmless `agent -p` that writes/verifies `C:\LAN_SHARE_REPORT\AUTOHUB_R5_AUTOWAKE\MARKER.txt` (or R6-specific C path), capture exit code / model / any quota notice
4. Separately probe whether CLI can use the already-open Cursor Browser Tab (expect FAIL or limited); report honestly
5. Leave all one-shot tasks disabled; no infinite loops; R9 remains HOLD

Until that approval and a new ChatGPT outbox task_id citing it: **stop**. No install, no `irm|iex`, no billing automation enablement.

## Safety

- No BLACKBOX / E/F / 1GiB sample access
- No install/download/iex this round
- No credential capture/upload
- Notebook SAM: no new task executed