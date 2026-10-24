# R10 continuation — offline response gate for factor replies, and the reviewer corrections

Executor: ZHANGWEI. Round: `BLACKBOX_FOUNDATION_R10_RESPONSE_GATE_AND_PINNED_REGRESSIONS_20261025` (R10 continuation).
Instruction: `outbox/BLACKBOX_FOUNDATION_R10_RESPONSE_GATE_AND_PINNED_REGRESSIONS_20261025.md` (6,755 B).
Window: 2026-10-25 02:21:57 – 02:25 +08:00. Host ZHANGWEI, cwd `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024`,
`PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`, interpreter `runtime/.venv/Scripts/python.exe`.

Append-only. Nothing from the accepted `producer_fq_contract` delivery was rerun or re-uploaded; no source search,
no parquet inspection, no original receipt export.

FOUNDATION_ACCEPTANCE=false · FORMAL_ENGINE_ADMISSION=false · NEW_DATA_ACQUISITION_AUTHORIZED=false ·
CURRENT_SWITCH_ALLOWED=false · ORDER_ALLOWED=false · SOURCE_ABSENCE_CLAIM_ALLOWED=false · B1..B7 OPEN.

---

## 1. Reviewer corrections carried forward (append-only)

| id | carried forward |
| --- | --- |
| RC1 | The three CSVs impose no physical `fq` column; missing `fq` bytes are not by themselves a contract violation; explicit fq semantics belong to the consumer contract / request binding; `None` is never relabelled `pre` from a numerical `factor=1`. |
| RC2 | `domain_schema.price_fq_factor` targets `stock_daily`; its full OHLCV list must not be imposed on a standalone adjust-factor source. Shared date meaning applies; full product-specific schema and authority still need that product's own contract. |
| RC3 | A midnight timestamp is an observed explicit daily value. The dtype difference from the CSV `date` category is recorded as a representation difference; `timestamp[ns]` is not declared invalid merely for being `timestamp[ns]`. |
| RC4 | The measured mounted CACHE plane, the historical backward-refresh writer and the new candidate merge/response gate are three separate objects. |
| RC5 | The pinned backward-refresh engine fetches replies directly via `fetch_factor(jq,...)` and the retained receipt reports `raw_fallback_used=false`; no requirement is invented to identify P1 files it "consumed". That direct-response lineage is kept separate from the current CACHE `tip_source`, a different declared RAW input. No new source search or execution is authorized here. |

Applied this round: no search, no parquet read, no re-upload; `factor=1` kept as a valid observation; no `fq` column
fabricated; the gate described strictly as a candidate component in front of concat/write — not the CACHE plane,
not the historical writer, not a merge engine; the legacy reproductions described as mechanism only, not as the
historical cause of the two integer-axis files.

## 2. Staged before execution

Manifest staged first, then every pinned member, bytes and sha256 checked against `RESPONSE_GATE_PACKAGE.json`:

| member | bytes | sha256 | declared match | notes |
| --- | --- | --- | --- | --- |
| `RESPONSE_GATE_PACKAGE.json` | 1,094 | `7dbc184c238c488a…` | manifest itself | staged before any execution |
| `r10_factor_response_gate.py` | 3,878 | `bfe4b45f9d1d056a…` | yes | the candidate gate |
| `test_r10_factor_response_gate.py` | 6,743 | `67d88af984c4b24e…` | yes | the 20 controls |
| `r10_factor_input_contract.py` | 4,046 | `e30acaddecf03e0a…` | yes | pure input contract |
| `OFFLINE_TEST_RECEIPT.json` | 490 | `bab65232874b62ee…` | yes | GPT's own offline receipt |
| `CANDIDATE_BODIES/aux_billboard_adjust_index_minute_r15.py` | 10,815 | `767c73c7a5c17e01…` | yes | fixture, no BOM, 295 CRLF |
| `CANDIDATE_BODIES/full_data_update_r14_run.py` | 23,720 | `a1ca66995ccecc15…` | yes | fixture, **UTF-8 BOM**, 1 CRLF |

Fixtures were taken from the exact local prior-delivery bytes, not from the remote copies; no line-ending
conversion and no re-pin. The BOM and CRLF counts are recorded because the test decodes with `utf-8-sig`, so the
BOM does not alter the parsed AST. `all_pins_match=true` for all six members.

## 3. Genuine pinned preflight

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\operating_entry\blackbox_operate_r10.py describe --product ADJUST_FACTOR_PIT_R1
    exit 0   02:21:57.6625779 -> 02:21:58.6862836 +08:00   stdout 6,632 B   stderr 0 B

    real_preflight.ok                    = true
    real_preflight.MUST_READ_PRECHECK    = PASS
    real_preflight.task_class            = [CACHE]
    real_preflight.required              = [BOOTSTRAP, DATA_ACCESS]
    real_preflight.problems              = []
    KERNEL_SHA256                        = b05a69958e29f7c90cf1ea794a4c437d36120bb960515ce9e26d3f4d5bdf197a
    BOOTSTRAP / DATA_ACCESS              = VERIFIED (expected == actual for both)
    TASK_EXECUTION                       = ALLOWED     TASK_EXECUTION_FORBIDDEN = FALSE

Captured literally to `captures/PREFLIGHT.stdout.bin` / `.stderr.bin`. This is a read-only describe: no
acquisition, no CURRENT switch.

## 4. The one authorized execution

    .\runtime\.venv\Scripts\python.exe -X utf8 reviews\R10\factor_response_gate\test_r10_factor_response_gate.py
    exit 0   02:22:02.2272741 -> 02:22:03.2416254 +08:00   stdout 156 B   stderr 549 B

stdout, verbatim:

    {"tests_run": 20, "passed": true, "scope": "SYNTHETIC_RESPONSES_AND_PINNED_ISOLATED_LEGACY_AST_ONLY", "supplier_calls": 0, "FOUNDATION_ACCEPTANCE": false}

stderr, verbatim (progress dots elided only where marked):

    ........<one DeprecationWarning from the test body at line 62>
    ............
    ----------------------------------------------------------------------
    Ran 20 tests in 0.066s

    OK

    DeprecationWarning: The 'generic' unit for NumPy timedelta is deprecated, and will raise an error in the
    future. This includes implicit conversion of bare integers (e.g. `+ 1`). Please use a specific unit instead.
      f=frame();f['date']+=pd.Timedelta(hours=1);self.reject(f,'INTRADAY_AXIS_IN_DAILY_PRODUCT')

Expected 20 / passed / exit 0; observed 20 / true / exit 0 — expectation met, executed exactly once, not rerun for
capture. The warning is raised by the test body, not by the gate or the contract module; no source, test or
fixture was edited to remove it.

## 5. What the gate actually enforces, read from the supplied source

`request_plan` requires canonical `\d{6}\.(XSHE|XSHG)` codes, uniqueness, an explicit `YYYY-MM-DD` request day
validated through `daily_axis`, an explicit `fq_arg` of `None`/`pre`/`post`, and a real positive `batch_size`.

`assemble_responses` then, **before any concat or write**: revalidates the untrusted plan through `request_plan`;
requires `plan['fq_arg'] == required_fq` (`FQ_ARGUMENT_CONSUMER_CONFLICT`); requires `frequency='daily'` and
`fields=['factor']`; requires one reply per planned batch, each `status='OK'` with matching `batch_index` and
`requested_codes`; requires a non-empty frame; flattens through the contract; requires every response date to equal
the request day (`RESPONSE_DATE_OUTSIDE_REQUEST`); requires exact security coverage per batch
(`BATCH_SECURITY_COVERAGE_CONFLICT`); and finally requires the flattened row count to equal the planned count.

`flatten_factor` (contract) resets a named `time`/`date` index so a real date in the index is not silently lost;
`daily_axis` rejects a numeric or numeric-string axis (`NUMERIC_DATE_AXIS_FORBIDDEN`), requires an explicit ISO date
shape, rejects timezone-carrying axes, and rejects intraday values in a daily product; `flatten_factor` rejects
conflicting `date`/`time` or `code`/`security` aliases, non-canonical codes, non-finite or non-positive factors, and
duplicate `(date, code)` keys pending a revision contract. It preserves `factor=1` as a valid observation and adds
no `fq` column.

The three legacy controls assert the opposite direction on the pinned AST only: both bodies lose a genuine date
held in a named `time` index and still return `PASS` writing no date; both write 200 of 201 requested securities
after one batch fails and still return `PASS`; R14 additionally renames an integer column `index` to `date` and
returns `PASS`. These are reproduced mechanisms, not proof of the historical malformed-file cause.

## 6. Exact scope

Component, not system. This round proves that a supplied candidate can reject numeric/absent/conflicting/intraday
dates, bind replies to an explicitly planned day without filling that day, require complete batch coverage, and
enforce the consumer's explicit fq argument — on synthetic replies only.

Not proven, and deliberately not attempted: any supplier execution, the expected historical market universe,
formal admission, publication freshness, real-file merge, date repair or factor fill.

**The candidate source is integrated into neither the production writer nor the formal engine.** The live updater
was not patched; the gate sits outside it. An offline gate is a component, not whole-system readiness.

## 7. Delivery contents

    SUPPLIED_SOURCES/   the five supplied members at original bytes (incl. the package manifest)
    FIXTURES/           the two pinned legacy fixtures at original bytes (BOM/CRLF preserved)
    captures/           PREFLIGHT.stdout.bin, PREFLIGHT.stderr.bin, TEST.stdout.bin, TEST.stderr.bin
    STAGE_AND_PIN_CHECK.json      manifest-first staging and per-member pin verification
    EXECUTION_RECORD.json         both commands, windows, capture hashes, preflight block, verbatim stdout/stderr
    BODY_PROVENANCE.json          original path / bytes / sha256 / byte-identity for every delivered body
    CORRECTIONS_APPEND_ONLY.json  RC1..RC5 and how each was applied
    MEASURED_NOTES_APPEND_ONLY.json  M1..M5 from this round's own observations
    COMMAND_LEDGER.json           every step, exit and outcome
    DELIVERY_MANIFEST.json        every member except itself and the readback
    FINAL_BYTE_READBACK.json      separate readback written after the upload, then itself uploaded

No parquet, no original historical receipt, no credential value was uploaded.
