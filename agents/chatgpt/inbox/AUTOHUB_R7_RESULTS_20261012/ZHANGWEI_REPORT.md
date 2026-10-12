# AUTOHUB R7 — ZHANGWEI Cursor Agent CLI D-only Install Gate

task_id: AUTOHUB_R7_INSTALL_CURSOR_AGENT_CLI_D_ONLY_20261012
host: ZHANGWEI
reported_utc: 20261012T014827Z
status: BLOCKED_INSTALL_PATH_UNSUPPORTED

## Required fields

| Field | Value |
|------|--------|
| USER_APPROVED_INSTALL | true (with strict D: path condition) |
| INSTALL_DRIVE_REQUIRED | D: |
| OFFICIAL_CUSTOM_INSTALL_METHOD_CONFIRMED | FALSE |
| INSTALL_ATTEMPTED | false |
| INSTALL_COMPLETED | false |
| ACTUAL_AGENT_BINARY_PATH | N/A (not installed) |
| UPDATE_DESTINATION | N/A — stock installer targets `%LOCALAPPDATA%\cursor-agent` (C:) |
| CLI_VERSION_CHECK | NOT_RUN |
| HEADLESS_AGENT_ONE_SHOT | NOT_RUN |
| CURSOR_CLI_TO_GUI_BROWSER_STATUS | UNVERIFIED |
| EXTRA_BILLING_ENABLED | UNKNOWN (not opened billing UI; no CLI run) |
| C_DRIVE_PERSISTENT_CLI_FILES | NONE |
| EXISTING_D_PROGRAMS_UNTOUCHED | true (only new staging under D:\Tools\CursorAgentCLI_staging) |
| R9_HOLD_UNCHANGED | true |
| COPY_AUTHORIZED | false |
| D_ONLY_SUPPORTED | false |
| EXACT_BLOCKER_AND_SAFEST_NEXT_ACTION | see below |

## Gate 1 — D: identity (PASS)

- D: local fixed NTFS volume label `Toolchain`, DriveType=3 (Local Disk), NVMe GPT, ~1262 GB total / ~1106 GB free, Healthy
- SystemDrive=C: (D is not OS volume)
- Proposed `D:\Tools\CursorAgentCLI\` did not previously exist (no conflict)
- E:/F: present; neither used this round; BLACKBOX untouched

## Gate 1 — Official installer analysis (BLOCKER)

Downloaded **script text only** (no `iex`) from `https://cursor.com/install?win32=true` to D staging:

- path: `D:\Tools\CursorAgentCLI_staging\cursor_install_win32_20261012T014604Z.ps1`
- sha256: `E07BE53AA3BC34B5904FBB1192289239B0BBF8A61AE28263E12AB18733237318`
- bytes: 3142

Critical code (hardcoded C-user LocalAppData):

```
function Initialize-CursorAgent {
  $agentPath = "$env:LOCALAPPDATA\cursor-agent"
  ...
}
Initialize-CursorAgent
Download-InstallPackage -UrlPrefix $downloadUrl -TargetPath "$env:LOCALAPPDATA\cursor-agent\versions" -Version $version
```

- Version referenced: `2026.10.01-e373342`
- Package URL pattern: `https://downloads.cursor.com/lab/2026.10.01-e373342/windows/x64/agent-cli-package.zip`
- **No install-directory parameter / PREFIX / custom drive option** in the official Windows script
- Docs do not promise alternate install drive

Official package downloaded to D for inspection only (not executed as installer to C):

- path: `D:\Tools\CursorAgentCLI_staging\agent-cli-package_x64.zip`
- sha256: `31896CE9A43F63C8AE7FF3C4BEE868213D6D02D60FB49908BEF6DC91D582F6EE`
- bytes: 77156248
- `cursor-agent.ps1` resolves versions relative to script directory (could run from D if placed there), but also defaults `NODE_COMPILE_CACHE` to `%LOCALAPPDATA%\cursor-compile-cache` (C)
- Auto-update path permanence on a non-LOCALAPPDATA layout: **not proven**; R7 forbids proceeding without that guarantee

Forbidden workarounds **not used**: C→D junction/symlink, install-on-C-then-move, global LOCALAPPDATA/USERPROFILE rewrite, third-party builds, WSL.

## Gate 2 — Install / test

SKIPPED per R7 rule: if official mechanism cannot place durable CLI binaries on D:, abort with `BLOCKED_INSTALL_PATH_UNSUPPORTED` and do not install on C.

Checks after abort:
- `C:\Users\Admin\AppData\Local\cursor-agent` exists: False
- `agent` on PATH: 
- `cursor-agent` on PATH: 

## EXACT_BLOCKER

Official Windows installer always installs to `%LOCALAPPDATA%\cursor-agent` (on ZHANGWEI this is under C:\Users\...\AppData\Local). Owner approval requires durable program/version binaries on D:. These constraints conflict; no official custom-path method confirmed.

## SAFEST_NEXT_ACTION (single choice for owner/ChatGPT)

Publish a new authorized task_id choosing **one**:

1. **Relax D-only** — allow official C:`%LOCALAPPDATA%\cursor-agent` install + one harmless `agent -p` test; or  
2. **Authorize explicit manual D layout** — extract the **same official zip** into `D:\Tools\CursorAgentCLI\` using the script’s `Download-InstallPackage` logic with TargetPath under D, add **User PATH** only to that D root (no global LOCALAPPDATA rewrite), then require a follow-up proof that `agent update` keeps versions on D; or  
3. **Wait for Cursor official custom install-dir support** — no install until docs/installer expose a supported drive flag.

This round stops at evidence + HUB report. No CLI auth, no billing changes, no scheduled automation created.

## Safety

- No `irm | iex`
- No persistent CLI on C
- Existing D programs untouched beyond new `D:\Tools\CursorAgentCLI_staging`
- R9 HOLD; no BLACKBOX / E/F writes