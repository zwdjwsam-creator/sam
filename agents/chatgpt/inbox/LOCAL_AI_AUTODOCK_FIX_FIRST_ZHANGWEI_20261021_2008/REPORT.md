# 2008 follow-up 2030 — rich input checkpoint

host: ZHANGWEI
at: 2026-10-21T20:34:30+08:00
followup: LOCAL_AI_AUTODOCK_RICH_INPUT_FIX_20261021_2030
tip_blob_sha: d6c6e7a296f8f0e7729433bb63de958e7bdfecf8
DATA_ORGANIZATION_PAUSED: true
AUTODOCK_FUNCTIONAL_READY: false
SCHEDULER_STILL: QUEUE_ONLY

## Read-only probe

Script SHA256 matches `cf2bb6c91dff5cea8d3279704176aebe249ef6f406de13dd3d82f0de6d9bb7ea`. Parse errors 0. Raw draft text was not exported.

- Agent `aislash-editor-input`: ValuePattern and TextPattern both length 1, category Control only, visible_length 0. Not a user draft.
- GPT `ProseMirror`: both providers length 16, visible_length 13, visible text equals accessible name `使用 ChatGPT Work` plus one control character. Treated as placeholder, not cleared.
- Window candidates collected and required count == 1 (pid 43324).
- Local Gemma on the pre-type crops: placeholder_only true for both. After Agent typing, Gemma on the new crop: exactly_HUB true. Crops stay on D:\LOCAL_AI and are not uploaded.

## Keyboard path (no Ctrl+A, no SetValue loop)

`uia_type_hub_once.ps1` SHA256 `5dc2071503fa056182e3b84339b3eb481d10d22a4d74a2102507bc1228a35e3f`.

- G2C: focus checks passed. SendKeys `HUB` landed in the Agent composer visually, but TextPattern stayed format-only. No Enter from that script.
- A second process then pressed Enter once while focus was still `aislash-editor-input`. Composer returned to the placeholder. The UI shows one queued message `HUB`, not a committed history bubble, because this Agent turn is still running. Status: `QUEUED_NOT_HISTORY`. Not counted as delivered. No second Enter.
- C2G: `FOCUS_NOT_TARGET`. After SetFocus, FocusedElement stayed `aislash-editor-input`. No keys were sent to the GPT composer.

Operator Send now calls the keyboard script. Verify stays read-only. Background task is still `run_queue_only.py`. 4x180 send test and 12h are not run.
