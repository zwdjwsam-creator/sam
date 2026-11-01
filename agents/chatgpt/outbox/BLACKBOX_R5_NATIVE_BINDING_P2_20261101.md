# P2: exact native runtime and read-only source binding handoff

task_id=BLACKBOX_R5_NATIVE_BINDING_P2_20261101
execution_host=ZHANGWEI
ORDER_ALLOWED=false
status=ISSUED_AWAITING_ACK_NOT_EXECUTION_EVIDENCE

The owner requested review and conditional HUB dispatch. Review found six native-cleaning gaps and policy ambiguities. This task authorizes ONLY the following bounded read-only handoff. It does not activate P1, execute candidate cleaning, acquire data, authorize backtests, switch CURRENT or establish continuous updates. SAM stays historical/read-only.

## Before any run
Read REVIEW.md and this task. Check this exact task's existing ACK/result and C: control directory. A capture directory, RUN_ONCE.json, an earlier execution receipt or a still-running instance blocks a duplicate. Do not stop processes, delete files or choose a different directory. No new report does not authorize a rerun.

Stage all seven package files from agents/chatgpt/reviews/BLACKBOX_R5_NATIVE_BINDING_P2_20261101/ unchanged under:
C:\LAN_SHARE_REPORT\BLACKBOX_R5_NATIVE_BINDING_P2_20261101\package
The parent C: control folder may be created; it must be ordinary/non-reparse. Verify PACKAGE.json raw SHA and every listed payload's length/SHA, then locally read back every staged file. Do not normalize newlines. Test source and GPT test logs are review evidence; DO NOT execute the unit suite on Windows. The Linux-only host-negative test is not a native gate.

Use only the existing E:\BLACKBOX\.venv\Scripts\python.exe, the actual R5 executable. If absent/broken, report the literal launch failure; do not install, repair or select another Python. Never read credentials or environment-variable dumps.

Create ACK.json and PACKAGE_VERIFY.json in the C: control folder, then upload/read them back to the return folder below before execution. ACK must bind task_id, host, package SHA, every payload verification, allowed writes/reads, actual selected executable, and P1/cleaning/acquisition/CURRENT/orders all NOT_AUTHORIZED. Do not claim execution in ACK.

## One exact command
After staged bytes/host/ordinary paths and ACK readback match, execute ONCE, attached:

& "E:\BLACKBOX\.venv\Scripts\python.exe" -X utf8 "C:\LAN_SHARE_REPORT\BLACKBOX_R5_NATIVE_BINDING_P2_20261101\package\capture_environment.py"

Capture separate outer stdout/stderr at control\OUTER.stdout.txt and OUTER.stderr.txt. Immediately after the attached process returns, write its actual waited-for OS exit to control\OUTER_RUN.json, with exact argv/start/end and no substituted Boolean. Preserve literal launch/timeout/nonzero output. Do not fabricate a success exit if the process did not start or did not return. No retries or local patch.

The supplied code exclusively creates control\RUN_ONCE.json before control\capture_001. The once marker is OUTSIDE capture_001. Never delete either. The collector measures Python/executable/platform and installed distribution metadata for pandas/pyarrow/numpy without importing supplier libraries. It captures raw bytes only for the fixed INPUTS list: four CURRENT JSON, exact rule/kernel/manifest/preflight/_base bodies, original R1 CALENDAR.json and two original normative CSVs. No directory scan, RAW price read, price/data copy, links, calendar query or dataset processing is allowed.

The original preflight may execute only if its raw SHA and _base SHA match embedded pins. Its exact internal argv is the approved Python -X utf8 E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class DATA. The unchanged normal preflight may read its fixed FILE_KEYS rule metadata. No --write-manifest, --acceptance or repair flag. Its streams/actual exit are separate from the collector's outer exit. Missing sources/version metadata, pin mismatch, reparse paths or failures are reported, not repaired. All captured E: sources are re-read and compared before collector completion. No CURRENT writes or source-directory creation.

Allowed output files: control\ACK.json, PACKAGE_VERIFY.json, OUTER.stdout.txt, OUTER.stderr.txt, OUTER_RUN.json, RUN_ONCE.json; capture_001\ENVIRONMENT_AND_BODIES.json, PREFLIGHT_RUN.json, optional real preflight.stdout.txt/preflight.stderr.txt, LOCAL_READBACK.json; and REPORT.md, DELIVERY_MANIFEST.json, UPLOAD_READBACK.json at control. No probe writes. Source per-file bound is 2 MiB; unknown/oversized/missing inputs remain explicit failures, not substituted paths. Preserve zero-byte streams as zero bytes.

Exit 0 = complete bounded handoff only. Exit 2 = retained partial/source/gate problems. Any exception/other exit = failed, retain all output and upload diagnostics. An old broken-runtime report is not permission to replace the current interpreter. DATA selects existing must-read rules; this task separately authorizes ONLY the listed new C: writes, not general DATA write permissions.

## Return and readback
Return root:
agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/native_binding_p2_20261101/

Use the existing authenticated GitHub connector, GitHub Contents/Git Data operations only, repository zwdjwsam-creator/sam branch main. Create only the exact ACK/package/outer/capture/report/manifest/readback files listed above. Do not replace an existing task result. No new credential handling, curl/urllib/gh experiments, random diagnostic blobs, permission probes or transport fallback. If the approved connector cannot transfer a result, retain it and report the exact blocker; do not invent another method.

Upload every generated result, including partial failures. Read every local file and each uploaded file back as actual bytes, record length/SHA and immutable commit/blob identity. For API encoding=none, obtain the exact blob body; never interpret it as zero-byte content. The delivery manifest excludes itself and later readback files; UPLOAD_READBACK lists earlier files, then read back UPLOAD_READBACK itself and record that final observation in the final chat. Do not create a self-hashing receipt loop. REPORT distinguishes publication, ACK, attempted execution, actual exit, handoff completion and still-pending GPT review.

After all generated results are uploaded and each file read back, end the Cursor chat with exactly END. If transport/readback is blocked, report the blocker instead of claiming completion or END satisfaction. Do not start any subsequent phase. GPT reviews returned evidence and owns exact native-cleaning repairs and a separately reviewed availability policy.
