# Windows fixture V3: command boundary and lossless failure diagnostics

dispatch_id: BLACKBOX_UPDATE_PREREQUISITES_20261027
execution_host: ZHANGWEI
notebook_evidence_host: SAM
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false

V1 and V2 failures remain failed. Both hosts' attempt-2 diagnostics at main 1819a16db710da732873807abd901d1ce1a6581c support a fixture quoting defect, distinct from V1's symlink privilege condition. SAM additionally retained the decoding-thread failure and None concatenation that masked the original diagnostic. GPT owns both fixture defects.

The collector and five input/metadata payloads are reused unchanged from V2. Collector SHA256 is 3e20395ef19dec1a81b4d81c5112f4f5dcc00de09c146d7076c6267f7dc96858. No business source, data policy, quota, acquisition, cleaning, candidate commit or publication logic is changed.

The fixture now calls a small stdlib-only helper with separate cmd.exe /d /c mklink /J arguments. The call remains interpreted by cmd.exe; shell metacharacters are rejected, while spaces and Unicode are retained as path content. No shell=True, undocumented Windows interface, elevation, system policy or code-page change is introduced.

subprocess captures raw bytes: no text=True and no implicit decoding. A failed process reports its actual exit and lossless stdout/stderr hex, including explicit presence flags for None. Timeout/launch errors propagate as test failures. This avoids assuming that English output identifies a code page, or that one OEM/ANSI/UTF-8 decoder always matches the child. The original test process streams must still be captured as raw bytes by the host's existing execution tool, not decoded implicitly and re-encoded.

All seventeen original test function bodies are AST-identical to V2. Their shared temporary-root prefix is now BLACKBOX followed by a space, Chinese characters, and another space. Thus the actual external-boundary and cycle controls exercise spaces/Unicode, including the existing Chinese task-directory component, when run on Windows. The helper checks reparse status and os.path.isjunction after success. Junction cleanup is registered before assertions, and remains LIFO ahead of temporary-root cleanup.

Six supplementary regression controls mock only the subprocess boundary. They check separate Unicode/space arguments, GBK bytes, invalid UTF-8 bytes, absent streams, metacharacter blocking before process creation, and timeout propagation. They do not replace the two real reparse controls or simulate native Windows acceptance.

Reviewer result: twenty-three Linux controls passed (original seventeen plus six); actual process exit 0. Original seventeen AST bodies unchanged and collector byte equality were also checked. The Windows branch and native cmd.exe/mklink have NOT executed in the reviewer environment. Both hosts must execute the exact package once and retain native outcomes. No claim of 23 Windows passes is made before those receipts arrive.

No automatic fourth attempt or unreviewed local repair. Failure receipts and bounded diagnostic output are authorized even if the fixture fails again. Any active/completed matching capture is reused instead of stopped or repeated. Only a passing native suite permits the unchanged collector; its output remains bounded evidence, not foundation or acquisition acceptance.
