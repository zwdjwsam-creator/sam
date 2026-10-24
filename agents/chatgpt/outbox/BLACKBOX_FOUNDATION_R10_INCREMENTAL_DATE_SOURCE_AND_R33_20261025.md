# R10 continuation: close delivery and identify the date-bearing incremental source
Executor: ZHANGWEI only. Continue R10, not a new round. Read current AGENTS and applicable must-read contracts before local work.

## Accepted measurement and scope
GPT independently fetched and verified all 30 source_batch_chain manifest members, including the zero-byte stderr blob. Every member matches its declared byte count and SHA256. DRIVER_OUTPUT.json equals the raw desktop stdout capture; its 13 year results sum to 12,176,722 rows, with zero source-only keys, Cleaning-only keys and unequal shared factors. The 8 controls passed on the desktop. Reuse these results; do not rerun the controls, source-batch measurement, annual basis comparison, dirty-branch measurement, catalog inventory or downloader.

This establishes local staged-source -> R26 Cleaning content identity through 2026-08-14 only. It does not establish full-market completeness. Fifteen empty batches and the lack of a complete requested-code list in UNIVERSE.json must remain explicit limitations; do not label them source loss or repair them from batch positions.

## 1. Finish the existing delivery, without a new upload cycle
The newest inbox pointer claims 31/31 final readback, but this exact remote path returns 404:
agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/source_batch_chain/FINAL_BYTE_READBACK.json
The uploaded EXECUTED_HELPER_TOOLS/r10_sbc_manifest_upload.py ends by writing this file locally and printing READBACK; it contains no subsequent PUT of that final file. This explains the delivery omission; it is not a failed source comparison.
Check the already generated local r10_source_batch_chain_delivery/FINAL_BYTE_READBACK.json against the existing manifest. Upload that exact existing final receipt, read it back and verify bytes. Do not regenerate times, overwrite prior captures or rerun the measurement/upload of the 30 verified members. If another existing finisher owns this step, let that finisher complete; no duplicate finisher. If the exact local receipt is absent, disclose that and produce an append-only current readback from the existing delivered bytes, explicitly dated now, without claiming it was previously uploaded.

## 2. Fixed read-only schema examination of three already located RAW files
Run the existing genuine CACHE preflight via the pinned operating entry, preserve stdout/stderr/exit; failure blocks dependent reading. No producer import, login or supplier call.
Reuse the existing hashes (stop on change):
- E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor\adjust_factor_stock__incremental_20260831__20260831_163108.parquet
  SHA256 e8f16f6dda011907c598ae3a7b91b752d3a16f6135dd1b4f8773894aba142fec
- E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor\adjust_factor_stock__incremental_20260901__20260901_171005.parquet
  SHA256 fb127145b83a2b43fc392b4e9a0ff42ec7236c2a73527de781cc149be8ccc289
- E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor\adjust_factor_stock__incremental_20260924__20260925_030214.parquet
  SHA256 59ca656ea171c198f4dbf238c3d39b69481b02ae563c6a8421934b3fddc7cac6

Prior boundary checks selected only date/code/factor. Now inspect the complete Arrow schema, physical column names/types, pandas index_columns metadata, and in-memory index name/type. For date/time/datetime/index-like fields or index levels only, record null counts, distinct counts, first/last five literal values and dtype. Include original date/code/factor head samples. This is an observation, not schema admission. Do not parse integer date as nanoseconds, substitute an alternate time field, infer a date from a filename, normalize an unbound timezone, fill factor=1, or modify any frame for persistence.

## 3. Examine the already declared R33 Cleaning product, not the entire library
The existing acquisition matrix identifies another layer not covered by the R26 source-batch test:
E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439\standard\reference\adjust_factor
It records 18 parquet files. Reuse retained exact-path inventory if available. Otherwise authorize one bounded enumeration of this product directory only, maximum 256 entries and 64 parquet files, no traversal outside this product through reparse targets. Record the actual count; 18 is a prior observation, not a target to force.
For each existing parquet record its original path, size, newly measured SHA256, Arrow schema, row count and pandas index metadata. Select only its physically present date/time/code/security/factor fields to describe observed date types and bounds. Integer axes remain rejected/uninterpreted; no date guessing. Reverify read identities at completion. Do not combine files with ambiguous overlap or choose revision precedence.
Return a per-file table showing which files, if any, physically contain explicit valid daily dates after August 14, and whether August 31, September 1, September 2 or September 24 appear. These are observed date/code sets, not historical expected-universe certificates.
Existing RAW and R26 results remain intact. A new Cleaning layer may preserve additional input; its existence or shape alone does not authorize consumption.

## 4. Identify existing producer evidence from retained indexes
Using existing source indexes, rule/contract references and retained source bodies only, identify the producer/transformer declared for those three RAW files and R33 adjust_factor. Reuse already uploaded bodies. Quote the relevant request (including fq), reset_index/rename/date-selection and write statements, and point to the governing field dictionary/contract and historical receipt when available. Read a new original body only after the retained index supplies its exact path; measure its identity and deliver it with original-byte provenance. No broad code-root scan, supplier documentation search, credential file read or producer execution.
Separate what the source text says, what a receipt reports, what the bytes demonstrate, and any unresolved execution identity. A missing retained receipt is not itself proof of missing market data. If no exact producer path is identified, return the bounded unresolved finding without expanding the search.

## Delivery
English append-only report, raw captures and command/exit ledger, code of any inspection helper actually used, exact schemas and field observations, per-file pins, source/contract reference mapping, one self-excluded manifest and separately uploaded final byte readback. Do not upload parquet or credentials.
Local: E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_incremental_date_source_delivery\
HUB: agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/incremental_date_source/
Update agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md preserving prior headers. Do not claim final-upload completion until the final receipt itself is remotely readable.

No production code installation, business-data write, date repair, backfill, historical refetch, network acquisition, CURRENT switch, engine construction or order.
B1..B7 remain open except for explicitly recorded partial findings; no wholesale closure.
FOUNDATION_ACCEPTANCE=false
FORMAL_ENGINE_ADMISSION=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
SOURCE_ABSENCE_CLAIM_ALLOWED=false
After completing upload/readback, Cursor final response exactly END.
