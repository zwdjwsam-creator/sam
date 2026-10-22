# 2008 follow-up 1145 — finish-now install checkpoint

host: ZHANGWEI  
at: 2026-10-22T11:56:30+08:00  
followup: LOCAL_AI_AUTODOCK_FINISH_NOW_ZHANGWEI_20261022_1145  
tip_blob_sha: 6c21674cabb64167bff43f154e751b53d4ffd463  
DATA_ORGANIZATION_PAUSED: true  
AUTODOCK_FUNCTIONAL_READY: false  

## Package install

Copied GPT package into `D:\LOCAL_AI\Watchdog\hub_two_window_notifier_1913`.  
SHA256 `run_autodock_once.py` / `test_runtime.py` matched VALIDATION.json on install.  
Local edits after that: tokenized fetch via `GITHUB_TOKEN` in `run_autodock_once.py` (desktop auth), wrapper `run_autodock_tick.py`, adapter `ui_delivery_adapter.py`, ProseMirror class prefix in click script, SetFocus fallback for Agent.

12/12 `test_runtime.py` OK on this machine.

HUB checkout for `--repo`: `D:\LOCAL_AI\HUB_sam` (not under E:\BLACKBOX). Remote URL scrubbed; fetch uses process token only.

Baseline: `state/autodock_remote.json` initialized once, objects=1563, no GUI on init. Old queue-only state kept.

## One-shot tests (explicit --test-event, not in schtask)

| Direction | Event | Result |
|---|---|---|
| C2G | `.../TEST_HUB_1145_20261022_115328_C2G.md` | click → type HUB → Gemma exactly_HUB → Enter once → composer cleared. No proven user bubble reader → **UNCERTAIN** |
| G2C | `outbox/TEST_HUB_1145_20261022_115328_G2C.md` | click hit-test failed (NO_CLICKABLE_POINT); SetFocus fallback → type → Enter → **QUEUED** (frontend queue / until history proof). Not DELIVERED |

Old overnight receipts stay INCONCLUSIVE / not resent.

## Scheduler

Task `LOCAL_AI_HUB_TwoWindowNotifier_1913` Action now:
`python -u ...\run_autodock_tick.py --adapter ...\ui_delivery_adapter.py --send`  
Logon: Interactive only. No `--test-event`. Old queue-only Action replaced (same task, not a second service).

Independent 4×180s seal started under `logs/autodock_4x180.out.log` (span ≥540s). Not finished at report time.

## Not claimed

- AUTODOCK_FUNCTIONAL_READY = false (need DELIVERED both ways + sealed 4×180)
- LONG_RUN_12H = PENDING
- Data organization still paused
