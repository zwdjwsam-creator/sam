# Existing notifier runtime completion package
Target: ZHANGWEI. Install into existing D:\LOCAL_AI\Watchdog\hub_two_window_notifier_1913.
This replaces the existing queue-only task entry after UI testing; do not add another scheduler.

## What is implemented
run_autodock_once.py uses the existing authenticated HUB Git checkout:
- git fetch origin main, then immutable FETCH_HEAD metadata, without checkout/reset/pull of dirty files.
- atomic combined queue+seen state, OS file lock, historical baseline initialization.
- one pending HUB batch per direction, coalescing new files.
- marks SENDING before invoking UI; after crash/uncertain result only VERIFY, never automatic re-submit.
- ignores ACK/pilot/heartbeat and inbox notifier self-reports; legitimate outbox repair tasks stay eligible.
- no event means no adapter call/model inference. It does not call remote Cursor models.

## Still required on the desktop
Create a local sibling ui_delivery_adapter.py with:
    def handle(event: dict, mode: str) -> dict:
        ...
event has id (Windows filename safe), direction CURSOR_TO_GPT or GPT_TO_CURSOR, body exactly HUB, items [{path,blob_sha}], and status.
mode SUBMIT runs the complete already-authorized local UI transaction ONCE.
mode VERIFY is read-only, using baseline/context saved by event id. It must NEVER type or press Enter.

Return one of:
- DELIVERED: new submitted user HUB verified in the correct original conversation.
- QUEUED: frontend accepted exactly one pending HUB; save context, wait for consumption.
- UNCERTAIN: typing/submission may have happened; only verify later.
- DEFERRED: only if NO text or submit action occurred, e.g. busy/user draft/locked screen.
Never translate a placeholder/old HUB/text echo/model assertion alone into DELIVERED.
Save event-specific GUI baseline/evidence under existing local state/evidence directories, not BLACKBOX data.
Wire existing local Gemma vision + successful focus-click + actual keyboard input/submission scripts into this adapter. Do not merely call a type-only helper and stop.

## Minimal installation
1. Preserve existing legacy state/logs and old ambiguous test receipts. Do not reset them or replay them.
2. Use the real existing HUB git worktree for --repo. The mailbox mirror may not itself be a checkout; determine the checkout used by existing upload scripts. Do not git-init the business tree or expose its remote URL/credentials.
3. Run test_runtime.py on the existing desktop Python. No package installation required.
4. Initialize NEW runtime state once:
    python run_autodock_once.py --repo <existing_HUB_checkout> --init
   --init refuses existing state, baselines current remote files, performs no GUI action.
5. Test the local adapter one fresh event per direction. Publish and read back each event on main first. A one-off invocation can explicitly allow a pilot/self-report:
    python run_autodock_once.py --repo <checkout> --adapter <local_ui_delivery_adapter.py> --send --test-event <actual_remote_path>
   This flag is for a one-off test only; do NOT persist --test-event in the scheduled task.
   Same test path/blob is admitted once only; changing the report produces a new blob.
6. Replace the existing task Action with:
    python run_autodock_once.py --repo <checkout> --adapter <local_ui_delivery_adapter.py> --send
   Keep the existing 180s schedule and ignore-new-instance policy. Do not run the old queue-only or pilot executor in parallel.
7. Test at least four real ticks, spanning 540s or more, with quiet/deduplication behavior and actual remote commits in logs. 12h stability remains separate.

## Validation limits
12 isolated Python tests pass, including local bare Git fetch integration.
No Windows GUI, Windows file lock, GitHub authentication, local Gemma invocation or end-to-end delivery has been executed by GPT.
Desktop must finish and test the adapter and actual existing scheduled task. Passing these tests alone is NOT auto-dock acceptance.
Data organization stays paused until functional technical acceptance.
