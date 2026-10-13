# ZHANGWEI_REPORT — R9_DESKTOP_EXECUTOR_DEV_DRYRUN_20261013_1507

CODE_READY=true
INPUT_BINDINGS_VALID=PARTIAL
PLAN_COMPLETE=false
WRITE_TESTS_NOT_RUN=true
COPY_AUTHORIZED=false
FULL_MIGRATION=false

E base on this PC matches the SAM snapshot SHA a5590154… and size 9376645120. Scan end remains 2026-10-08.
E delta SHA matches. 42 delta paths are not in the base index (overlay hits=0).
Readonly plan: files 8680280, dirs 227832, reparse rows 4809. Path logical-size sum is 5076576566879 and is not a unique-entity total. Historical 356843718412 was not reused.
D repaired DB is not on ZHANGWEI. \\192.168.100.2\E_DRIVE is not readable, so the 42 files were not live-identified. Notebook was not changed and no share was created.
Contract verify_shas third value 787b14… is the original unrepaired D DB. The validator rejects using it for the repaired DB.
Delta volume text differs from base file rows. Low-32 of the wide serial equals Win32 2387166462, but entities were not merged across those forms.
Current E: is still serial 806508DF / MarketData. That serial is not post-format copy authorization.
Executor: C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013\r9_formal_executor.py
Modes: validate-input, plan, preflight-readonly. copy exits refused while COPY_AUTHORIZED=false.
Unit tests: 7 passed. No business copy, hardlink, or junction write.

remaining_blockers: D repaired sqlite absent; live identity of 42 delta files NOT_RUN; plan not copy-ready; user format of desktop E: still pending and not requested now.