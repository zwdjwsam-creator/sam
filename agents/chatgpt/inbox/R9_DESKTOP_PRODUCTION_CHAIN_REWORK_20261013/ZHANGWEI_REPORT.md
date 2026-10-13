# ZHANGWEI_REPORT — R9_DESKTOP_PRODUCTION_CHAIN_REWORK_20261013_1842

host: ZHANGWEI
SAM: HOLD
status: PARTIAL
IMPLEMENTATION_READY=false
COPY_IMPLEMENTATION_READY=false
ACCEPTANCE_IMPLEMENTATION_READY=false
WINDOWS_IO_EXECUTED=false
WRITE_TESTS_NOT_RUN=true
FORMAT_DONE=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
SOURCE_LIVE_PREFLIGHT_PENDING=true

What this round fixed:
- copy_entity now takes only the entity. The scheduler no longer passes payload and identity.
- Default backend is Win32Syscalls, not the string REAL_NOT_RUN.
- A non-empty fixture plan goes through read_executable, production_run, and WindowsBackend(VirtualSyscalls). One entity is copied, the alias hardlink uses the destination file id, not the source id. A 999-byte plan size against a shorter source fails.
- Preparation entry does not call Win32 write. write_calls stayed 0.
- Empty acceptance is not a full pass. A wrong destination file id fails. A zero-byte write fails.

Still not done, so this is not ready:
- Directory batch, real CreateHardLinkW, and real junction creation are not on the production path.
- Three interrupt resume cases are not implemented.
- Full-plan acceptance driver is not bound to the 6GB plan.
- Real Win32 copy was not executed.

No format, no E: write, no real hardlink or junction test.
