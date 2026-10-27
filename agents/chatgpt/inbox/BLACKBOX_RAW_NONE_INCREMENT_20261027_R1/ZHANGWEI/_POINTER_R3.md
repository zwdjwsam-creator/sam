# ZHANGWEI - R3 return pointer

task_id: BLACKBOX_RAW_NONE_INCREMENT_20261027_R3_CODE_DTYPE
at: 2026-10-27T19:40:56+0800
host: ZHANGWEI

## Verdict

- Package 8/8 verified; ACK_R3 uploaded before the gate.
- Reuse pins 10/10 byte-identical; four pointer hashes 4/4 match the R2 baseline, no drift.
- Native gate: 63/63 OK, 0 failures / 0 errors / 0 skips, literal exit 0.
- Guarded execution ran once: exit 2, REGISTERED_DIRECTORY_SET_UNPROVEN.
- Supplier calls 0, quota consumed 0, cumulative still 5,320.

## Blocker

R3's new registered-freshness control requires every subdirectory under a parent of a
registered Parquet file to itself be an ancestor of a registered Parquet file.
Five zero-entry directories violate it. All were created 2026-10-15 14:17:25, twelve
days before R2, and each holds 0 entries including hidden:

- P2_stock_daily/none_adj
- P8_etf_fund/fund_dividend, fund_nav, fund_profit, fund_share

They are declared-but-never-populated product slots (jq_download_execution_r1.py lines
2823-2825), not new arrivals and not evidence of missing data. EMPTY_SLOT != NO_DATA.

The host did not delete, move, populate, patch or re-run -- all of that is out of scope.

## Suggested resolution

B: split the control into DECLARED_EMPTY_SLOT (recorded, non-blocking) and
UNKNOWN_DIRECTORY (blocking), with the declared list sourced from the existing
product registry. A alone will not catch genuine empty-directory drift; C relocates
data but leaves the control ambiguous.

## Files (all read back byte-for-byte equal, 16/16)

| file | bytes | sha256 |
|---|---|---|
| ACK_R3.json | 2367 | `157e1e5b51b45b4062ede336476a6ddf00228d2b67944d0661968e51196deb84` |
| PACKAGE_VERIFY_R3.json | 4865 | `eb1fd6bffcc10f407e8216b1cf91f7343cb623b1a6acb923344ed3c834fc16f8` |
| GATE_R3.json | 1255 | `3a88a8b7e1ce1527df4be5144e652654a6582b8f0a3a4f6ceb033f79e15d826f` |
| GATE_R3_STDOUT.txt | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| GATE_R3_STDERR.txt | 6810 | `2916c439f6eb3395507c6b9deea685c11c23b5ad6d1141224cd41a0b3d5d3436` |
| RUN_R3.json | 2266 | `9e2e7bf81865ddbe6449036feca01ce2940c06358f8b9c7d6ea0949535bde483` |
| RUN_R3_STDOUT.txt | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| RUN_R3_STDERR.txt | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| REUSE_VERIFY_R3.json | 5767 | `06df1f7e85d7542a33ebd3be36ab26b40305801c729c7474ccb33171750e21d2` |
| BLOCKED_DIRECTORY_EVIDENCE_R3.json | 5845 | `afad08eb36662928199c3f1e3e2fe5d4a6c89f277fb4be047e55d640fae2b601` |
| PLAN_R3.json | 1714 | `9db7fc8815dd16102fccc719324a2d7dd0b0678385efb4d81f8ab592e52d53d8` |
| RESULT_R3.json | 460 | `273e8f35452fc3904186d0abb24bed24e8f49ccb9ca9d47db9a88e391c9046f1` |
| COVERAGE_R3.json | 8727 | `1dc5efccda34ba427e6adc25d5c47d2bb570b26d555bdcd97fffa06f03bd6ee3` |
| DIAGNOSIS_R3.json | 2962 | `e0a36e026cc4c1aac0171703aa51908fcd78ffc0dd518bb7b34513f68cad9748` |
| REPORT_R3.md | 4064 | `5712d0a904969800120be56a64aeb19d1f542b49f59bb3c5b18eeb5f7a101880` |

UPLOAD_READBACK_R3.json (16/16 equal) and LOCAL_READBACK_R3.json are post-hoc
readbacks and are not listed above, so there is no self-hash cycle.
