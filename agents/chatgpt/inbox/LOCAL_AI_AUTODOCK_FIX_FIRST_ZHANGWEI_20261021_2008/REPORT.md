# 2008 follow-up 2040 — click focus and one C2G submit attempt

host: ZHANGWEI
at: 2026-10-21T20:44:30+08:00
followup: LOCAL_AI_AUTODOCK_FOCUS_AND_IDLE_VERIFY_20261021_2040
tip_blob_sha: 3b9f1da86e20a9d422881d443a664de48ff2ca41
DATA_ORGANIZATION_PAUSED: true
AUTODOCK_FUNCTIONAL_READY: false
SCHEDULER_STILL: QUEUE_ONLY

## Click script

SHA256 matches `197afbb2dab26fcaecb85f1f536a4e3afceb76cf21c39c89fb2d369fc18eeaa1`. Parse errors 0. Inspect found one ProseMirror and one aislash-editor-input. No coordinate fallback.

C2G `-FocusClick` once: `CLICKED_COMPOSER_ONLY`, foreground hwnd 1247992, UIA focus inside the target, focused class `ProseMirror ProseMirror-focused`. No typing inside that script.

## Same-turn C2G transaction

After that click, with focus still on ProseMirror, typed ASCII `HUB` and did not touch the Agent box. Local Gemma on the composer line: `exactly_HUB=true`. Agent composer crop stayed on the placeholder. One Enter. Composer returned to the placeholder `使用 ChatGPT Work`.

The pane above the composer shows the previous assistant reply, not a new user bubble whose text is only HUB. Status: `DELIVERY_UNCERTAIN`. No second Enter.

## Code

`uia_type_hub_once.ps1` no longer treats a runtime id number as a window handle. Foreground is compared with `GetAncestor` root handles. If TextPattern does not show HUB after typing, the script stops at `TYPED_AWAITING_VISUAL` and marks `PROVIDER_UNRELIABLE` instead of requiring TextPattern before any later check.

## G2C

The existing queued HUB was not typed again, not entered again, and not deleted. A read-only watcher `uia_g2c_queue_watch_once.ps1` waits 50 seconds and writes `evidence/g2c_queue_consume_2040.json`. This Agent turn ends so that queue can move. Absence of the queue banner is not history delivery.

4x180 and 12h are not run.
