# CLOSED — P1 native fixture conformance accepted; do not rerun

GPT independently reviewed the 18 returned files, exact 20 native fixture tests, three process exits and all 17 date rows at snapshot 89152d8b42839cebf7a9bd9763faef0d277de787. Verdict: ACCEPTED_NATIVE_FIXTURE_CONFORMANCE_ONLY. Owner-approved policy remains a presumption; no real-data backtest admission or P3 cleaning is conferred. See agents/chatgpt/reviews/BLACKBOX_P1_NATIVE_TEST_ACCEPTANCE_20261101/REVIEW.md. The command below is historical and closed, not a replay instruction.

---

# Approved P1 policy — one ZHANGWEI fixture-conformance run

task_id=BLACKBOX_P1_NATIVE_TEST_20261101
execution_host=ZHANGWEI
policy_status=OWNER_APPROVED_POLICY_ONLY
ORDER_ALLOWED=false

The owner explicitly approved the corrected stock-only P1 policy and requested HUB task dispatch. POLICY_BODY.txt and APPROVAL.json record that approval. Do not request a handwritten signature. This command authorizes native C: fixture tests and a date-only eligibility plan, not price processing or backtest admission. P2 is closed and MUST NOT be rerun.

## Scope
P1 presumes next frozen-calendar session at 09:00 Asia/Shanghai; it does not establish actual historical publication or revision vintage. Stock RAW_NONE/XSHG/XSHE only, factor excluded from the policy view, raw factor retained unchanged outside this view. ETF/index/other domains are not admitted. The final 2026-10-27 data day remains UNRESOLVED. Use only the bound calendar; no supplier calls or extrapolation. The 13 projected fields remain subject to semantic binding before any real-data admission.

The pure Python p1_layer is an availability view, not an execution/fill engine. It preserves paused/zero-volume observations and does not certify tradability or produce orders. Its fixture tests do not certify E: price-source completeness, native candidate cleaning, execution constraints or the seven open RCID publication defects. Those remain GPT work.

## Stage and ACK
Check this task's ACK/results/control folder and current processes before starting. If RUN_ONCE.json, result_001, an execution receipt or a matching running instance exists: no duplicate, interruption, cleanup, directory substitution or replay. An absent new report is not restart permission.

Stage the ten files from agents/chatgpt/reviews/BLACKBOX_P1_NATIVE_TEST_20261101/ unchanged to:
C:\LAN_SHARE_REPORT\BLACKBOX_P1_NATIVE_TEST_20261101\package
Verify PACKAGE.json raw SHA and all nine payload lengths/SHA. Read every staged file back. No newline conversion, installation, interpreter substitution, source patch or test skipping.

Read POLICY_BODY.txt, APPROVAL.json and this task. Write ACK.json and PACKAGE_VERIFY.json at the C: control root and upload/read both back at the return path BEFORE execution. ACK binds task/host, package and policy-body SHA, all payload identities, exact executable, permitted new C: writes, no price reads/cleaning/supplier/CURRENT/orders, and the fact that ACK is not execution.

Use the measured E:\BLACKBOX\.venv\Scripts\python.exe only. If it cannot launch, preserve the literal failure and stop. No repair or fallback Python. Parent C: directories may be created only if ordinary/non-reparse.

## One attached command
& "E:\BLACKBOX\.venv\Scripts\python.exe" -B -X utf8 "C:\LAN_SHARE_REPORT\BLACKBOX_P1_NATIVE_TEST_20261101\package\run_native_tests.py"

Capture separate outer streams at control\OUTER.stdout.txt and OUTER.stderr.txt, and immediately record actual waited-for OS exit/argv/start/end at OUTER_RUN.json. No automatic retry. The script exclusively creates control\RUN_ONCE.json outside result_001, then creates result_001 once.

The script may read only the staged package and three exact E: source bodies: original R1 CALENDAR.json, original preflight and _base.py at their embedded pins. The unchanged preflight may read its own fixed rule/kernel/manifest metadata, DATA class, no --acceptance/--write-manifest/repair. It runs before the 20 fixture tests. Each process's original streams and actual exit are distinct. A preflight failure or timeout stops, retains output and authorizes no business entry. HAND_READ annotation is preserved verbatim, not used to override actual results.

The bound calendar is compared against the E: original and the three E: sources are re-read before success. No raw price files, credentials, supplier modules, paid entitlement checks, environment dumps, directory inventories or CURRENT reads/writes are authorized by this task. Metadata/calendar mismatch blocks rather than selecting a similar source.

## Outputs and exits
Within result_001: preflight.json/stdout.txt/stderr.txt; tests.json/stdout.txt/stderr.txt; DATE_PLAN.json; RESULT.json; LOCAL_READBACK.json; FAILED.json only on failure. No output overwrite, original hardlink, secret hashing or user-data deletion. Exit 0 means fixture conformance plus the date-only plan; exit 2/other/timeout means retained failure, no retry. Success is NOT real-data backtest admission.

At control root: ACK.json, PACKAGE_VERIFY.json, RUN_ONCE.json, OUTER.stdout.txt, OUTER.stderr.txt, OUTER_RUN.json, REPORT.md, DELIVERY_MANIFEST.json and UPLOAD_READBACK.json. REPORT distinguishes approved policy, publication, ACK, actual native execution, test result, unresolved dates, and still-pending GPT review/native cleaning.

Return root:
agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/p1_native_test_20261101/

Upload every generated result, including failures, using the existing authenticated GitHub connector's Contents/Git Data operations only, repository zwdjwsam-creator/sam branch main. Do not overwrite prior results. No new credentials, random diagnostic blobs, curl/urllib/gh fallback, permission probes or transport experiments. If blocked, preserve output and report the exact blocker.

Every local and uploaded file must be read back as bytes and checked for length/SHA with immutable commit/blob identity. encoding=none is not an empty body. Manifests exclude themselves and later readback files; finally read back UPLOAD_READBACK itself and report that observation in chat, without a self-hashing loop. After complete upload/readback, the final Cursor chat message must be exactly END. If a readback is blocked, report it rather than claiming completion.

Hold after return. No P3 cleaning, acquisition, live/paper execution, signals, scheduling, HAND, CURRENT/Cache switch or release. GPT independently reviews results and supplies the next exact repaired implementation; local AI must not invent policies, fields, gates, aliases or bypasses.
