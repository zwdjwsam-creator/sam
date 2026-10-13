# ZHANGWEI_REPORT — R9_DESKTOP_END_TO_END_PACKAGE_20261013_1834

host: ZHANGWEI
SAM: HOLD
FORMAT_DONE=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
WINDOWS_IO_EXECUTED=false
SOURCE_LIVE_PREFLIGHT_PENDING=true

The previous ready flags were not treated as accepted. This package connects CLI gate, plan reader, scheduler, and WindowsBackend.

- Empty acceptance is not a full pass. A wrong destination file id or volume fails.
- A write that reports 0 bytes is a failure. Success requires the destination hash.
- ADS and NUL stay rejected.
- Preparation gate still stops before any backend call. Two bools do not authorize a write.
- Plan reader samples the existing entity table with LIMIT and EXPLAIN. It does not rebuild the 6GB plan. D source share is an explicit blocker, not a guessed D_DRIVE.
- Link check on the current plan: 16 overlays mapped, delta files sum 42, 0 cycles, ordinary counts unchanged.
- Real CreateFile/ReadFile/WriteFile path was not executed.

Remaining: live UNC WinError 1326, no formatted destination binding, no on-disk copy or junction test.