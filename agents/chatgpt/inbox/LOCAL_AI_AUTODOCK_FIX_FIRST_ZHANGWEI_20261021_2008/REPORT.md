# 2008 follow-up 2018 — bound control checkpoint

host: ZHANGWEI
at: 2026-10-21T20:23:10+08:00
followup: LOCAL_AI_AUTODOCK_BOUND_CONTROL_FIX_20261021_2018
tip_blob_sha: a9cf4e668d2e058e4f0b9f50bf42e87aa58183b1
DATA_ORGANIZATION_PAUSED: true
AUTODOCK_FUNCTIONAL_READY: false
SCHEDULER_STILL: QUEUE_ONLY

## Probe

GPT script SHA256 matches `be36e7ab5284d1db589dba45bd9d6c4c2420f1fecb30d5e911b17debc96ffb17`.
Parse errors: 0. Ran on this machine. Result: `evidence/uia_bound_controls_probe.json`.

- Window pid 43324 hwnd 1247992 (snapshot only, not hardcoded).
- Agent candidates: 1, class `aislash-editor-input`, ValuePattern, no Invoke on nearby buttons (nearest button is the model picker).
- GPT candidates: 1, class `ProseMirror`, name `使用 ChatGPT Work`, ValuePattern. Nearby buttons: 添加文件等内容, 选择 ChatGPT 模型, 听写, 开始语音. None named 发送 and none expose InvokePattern.
- Terminal `xterm-helper-textarea` excluded.

## Code

- `uia_send_hub_once.ps1` SHA256 `e3654ed6e18ddaa373fbe20cfd4288898adf91dd91c02418887b516d05437ba4`
  - Fresh class match, count must be 1. No last-edit fallback. No filename needle.
  - Send and Verify are separate modes. Verify does not write or press Enter.
  - SetValue `HUB` only when the composer value is empty. Readback must be exactly `HUB` before any submit.
  - Invoke only a button named 发送/Send. Otherwise one Enter only if FocusedElement runtime id is the target. Focus failure clears the HUB draft and stops.
  - Success requires the target pane (ancestor that does not contain the other composer) to gain a non-Edit name `HUB`, and the composer to be empty. Otherwise `NOT_SUBMITTED` or `DELIVERY_UNCERTAIN`. No automatic retry.
- Operator now calls that script for both C2G and G2C. `agent_composer_unique` uses the verify mode class count, not cached names.
- Queue writes the queue file before seen, and keeps a baseline copy of the old seen file. Inbox notifier reports stay ignored. Outbox `LOCAL_AI_*` repair tips are no longer dropped.

## Single-shot tests (armed only inside that process)

| Direction | Result |
|---|---|
| C2G | `BLOCKED` `DRAFT_PRESENT` draft_len=16. Did not overwrite. |
| G2C | `BLOCKED` `VALUE_READBACK_NOT_HUB` readback_len=1. No Enter. `aislash-editor-input` ValuePattern did not hold `HUB`. |

Scheduler was not switched to auto-send. 4x180 functional seal and 12h stay open.
