# R10 dirty-branch review and declared source-batch chain

Independently verified: 26 dirty_branch manifest members match exact bytes and SHA256, zero mismatch. Manifest SHA256 575cc6cac741ae7d5d754b72ca6bba192d9ae8461b7e43b15d01405bb735be84. All six raw command captures match their ledger declarations. The 20-control run passes; first desktop attempt stopped before preflight/data reads because PACKAGE.json was omitted. After restoring the identical supplied manifest, one actual content measurement completed with genuine CACHE preflight PASS. This staging-only retry is disclosed; no original writer, supplier or business writer ran.

The measured 2026-09-02 code set equals all seven dirty codes in the byte-pinned historical receipt, with no extra or missing code relative to that receipt. This supports consistency between the observed content and the independently reproduced dirty-branch omission. It does not prove the exact historical program identity, sole causation, complete market coverage, or every sparse date. The tested candidate assembly is not installed into production.

The original download_source_fq_pre_r1.py carrier was decoded and independently verified at 7,131 bytes, SHA256 8a49616147748b46d168542973020aed86cb1e70d09a09a45960cb641201bcea.

Its declared output is NOT the legacy P1 directory:
TASK/staging/source_batches/year=YYYY/batch_NNN.parquet
and a same-name .sidecar.json, plus TASK/staging/UNIVERSE.json and DOWNLOAD_STATE.json.
The configured request is explicit fq=pre, year-by-year, batches of 400, through 2026-08-14 only. P1 is deliberately retained as legacy. Therefore inspecting P1 alone cannot account for this separately declared staged source. Existence and contents of the declared batch directory still need actual measurement, not inference from code.

The source also exposes limitations: resume skips on parquet+sidecar existence without validating their identity; the sidecar has counts, bounds and fq but no output hash or complete requested-code list; flatten_factor guesses a date column and silently drops invalid/1970 rows. These are static implementation properties, not proof that the staged files have those defects. Do not run or patch the downloader.

The supplied reader measures exactly the declared staged source directory and two metadata files, then compares each year's validated date/code/factor tuples with the already measured, hash-pinned R26 Cleaning partitions. It uses the declared UNIVERSE n/batch only to bind the expected local file layout, never as proof of expected historical daily universe. Empty source batches can be measured when sidecars agree; they are not completeness certificates. Numeric date axes, duplicate keys, wrong fq, sidecar mismatches and out-of-scope dates are rejected rather than repaired.

Only the 13 year directories and their declared batch files are enumerated. No drive scan, other root, supplier call or source-absence conclusion is authorized. Older R26 pins are carried forward from the accepted basis measurement; staged source hashes are newly measured identities, not supplier certificates. Stop on a path/layout/pin problem without choosing an alternative.

Eight new offline controls pass. This is a different comparison (staged source -> Cleaning), not a repeat of Cleaning -> CACHE basis work. It is required to test an actual newly identified source link. No source parser, production merge, factor, historical seal or CURRENT is modified. Prior UTC correction is accepted as reporting-only; first verification execution ordering remains unproved and needs no further work.

The program's cutoff is 2026-08-14. Even an exact staged-source/Cleaning match cannot certify the later August/September records or the 83,503 physical-minus-declared discrepancy. B1..B7 remain OPEN; all acquisition, formal engine, CURRENT and order permissions remain false.
