# ZHANGWEI_REPORT — R9_DESKTOP_REAL_IO_AND_ACCEPTANCE_FIX_20261013_1743

host: ZHANGWEI
SAM: HOLD

INPUT_BINDINGS_VALID=true
LINK_MAPPING_COMPLETE=true
PLAN_COMPLETE=true
PLAN_SCOPE=offline bound snapshot; not a live freeze
COPY_IMPLEMENTATION_READY=true
ACCEPTANCE_IMPLEMENTATION_READY=true
WINDOWS_IO_EXECUTED=false
SOURCE_LIVE_PREFLIGHT_PENDING=true
WRITE_TESTS_NOT_RUN=true
FORMAT_DONE=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false

The previous self-report of ready was not treated as accepted. This round closes the reviewed gaps in code:

- Missing sha256, file id, volume, size, or type now fails acceptance. None no longer matches None.
- ADS (`name:stream`) and device names such as NUL are rejected.
- Streaming copy returns sha256 and never asks for the whole entity in one read.
- Preparation gate calls the backend 0 times. `--copy-authorized --format-done` still does not open a write.
- Ancestor-plus-remainder cycle detection is tested. On the existing plan, 4841 edges walked with 0 cycles.
- Ids 25–40 remain mapped. Delta files under those 16 targets still sum to 42. Ordinary counts are unchanged.
- Win32 CreateFile/ReadFile/WriteFile/Flush/Close/CreateHardLink declarations were checked by import only. stream_copy_handles was not called.

Real disk copy, hardlink, and junction tests are NOT_RUN. UNC \\192.168.100.2\E_DRIVE\BLACKBOX remains WinError 1326. No format and no E: write.
