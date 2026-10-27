# Same child tasks: Windows fixture V2 continuation, no elevation

dispatch_id: BLACKBOX_UPDATE_PREREQUISITES_20261027
execution_host: ZHANGWEI
notebook_evidence_host: SAM
status: READY_RESUME_AFTER_REVIEWED_FIXTURE_UPDATE
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

The desktop V1 test attempt is FAILED (15 passed, 2 setup errors, actual exit 1); its collector did NOT run. Preserve its ACK, stdout/stderr, command ledger and probe. Do not overwrite V1 or represent it as passed.

1. Before doing anything, inspect the existing child ACK/PID/results. If that host has already completed a collector under a passing package, reuse its result; this fixture update does not request another capture. Do not stop or duplicate a running process.
2. Stage the complete package from:
agents/chatgpt/reviews/BLACKBOX_UPDATE_PREREQUISITES_20261027/windows_fixture_v2/
to a NEW directory:
C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\package_windows_fixture_v2\
Verify PACKAGE.json and all nine payload hashes/lengths. Collector SHA remains 3e20395ef19dec1a81b4d81c5112f4f5dcc00de09c146d7076c6267f7dc96858.
3. The two fixtures now create real temporary C: directory junctions using mklink /J. Do not elevate, enable Developer Mode, alter system policy, skip tests or change code. Junctions are removed before temporary-root cleanup. If fixture creation still fails, preserve that failure and stop; no bypass.
4. Run seventeen controls once using the same ordinary interpreter:
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 -m unittest discover -s "C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\package_windows_fixture_v2" -p test_collect_prerequisites.py -v
Save new literal outputs as FIXTURE_CONTROLS_ATTEMPT2_STDOUT.txt and FIXTURE_CONTROLS_ATTEMPT2_STDERR.txt. Append actual process times/argv/exit to COMMAND_LEDGER; retain the original exit-1 row.
5. Only if all seventeen local controls pass and no same-host collector is running/completed, execute once:
& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 "C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\package_windows_fixture_v2\collect_prerequisites.py" --role ZHANGWEI --out "C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027\ZHANGWEI\capture_002"
For SAM, use --role SAM and the SAM\capture_002 output instead. Never pre-create or delete capture_002. An existing directory means stop and report, not overwrite.
6. All prior collector exit meanings and read-only/business/source/credential boundaries remain unchanged. Upload the existing child return folder with attempt-2 names and the actual new capture; do not replace historical failure evidence. Read back every uploaded file and finish Cursor chat with exactly END.

Reuse notes for both hosts:
- The six deployed source/metadata bodies have been independently reconciled in deployed_source; V2 known-body metadata includes them. Do not upload another byte-identical copy.
- The fourteen-member corrected provenance index is reconciled. Use the existing D:-archive producer findings in RELEASE_PRODUCER_MAP and evidence notes. Do not launch any additional manual/global producer search. The collector's original bounded E:-only lookup does not establish absence in D:.
- The reported live candidate_commit.py is 53,208 B / e4772dda..., different from the uploaded reviewed v3 body. The existing exact-path collector will capture changed bytes; do not substitute the old body, edit the live module, rerun a pipeline or add a duplicate export task.
- A current source hash is not historical process attestation. Preserve UNKNOWN where exact historical binding or request/page evidence was not retained.
- No acquisition, release publication, CURRENT switch, strategy run or order is authorized.
