# R5_FIXTURE_R2 回传 HUB 逐项核对表

任务: `BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_ISOLATE_RESUME`  
派发: `BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_FIXTURE_R2`

回传根: `agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/r5_isolate_resume_fixture_r2`

远端现状: 根目录 **20** 个文件 + `staging_output/` **1309** 个 JSON

## A. 第四节（Exactly one continuation command, only after both gates）

| 条款 | 回传到 HUB 的证据文件 | 事实 | 缺口 |
|---|---|---|---|
| 4.1 | `GATE_R5.json`<br>`PREFLIGHT_RUN_R5.json`<br>`PREFLIGHT_STDOUT_R5.txt`<br>`PREFLIGHT_STDERR_R5.txt`<br>`TESTS_RUN_R5.json`<br>`TESTS_STDOUT_R5.txt`<br>`TESTS_STDERR_R5.txt`<br>`WRAPPER_RUN_R5.json` | gate 在 execute 前生成并上传；execute 起始时 gate 年龄 21 秒 | WRAPPER_RUN_R5.json（wrapper 自身 real exit 回执）是交付结束后补录的，provenance 已写在文件里 |
| 4.2 | `EXECUTE_RUN_R5.json` | argv 逐字一致；run_count=1 retry=false attached_and_waited=true actual_os_exit=0 elapsed_ms=150308 | — |
| 4.3 | `EXECUTE_RUN_R5.json (acquire_daily_execute_run=false)`<br>`REPORT_R5.md` | acquire_daily_execute_run=false；本次只执行 acquire_r5.py 一次 | 无独立进程审计日志；只是自我声明 + 唯一一次 execute 回执 |
| 4.4 | `GATE_R5.json`<br>`ACK_R5.json`<br>`BASELINE_R5.json(gate 段)`<br>`EXECUTE_RUN_R5.json` | gate 内 rule_bindings=10 条、preflight exit 0、tests 128/128；execute 时 gate 21 秒新 | — |
| 4.5 | `EXECUTE_RUN_R5.json (run_count=1, retry=false)`<br>`REPORT_R5.md` | 本次无失败、无重跑；上一包（ISOLATE_RESUME 首包）失败原件仍完整保留，未覆盖 | — |
| 4.6 | `BASELINE_R5.json (values 四指针 + gate.rule_bindings 10 条)`<br>`PLAN_R5.json`<br>`REUSE_MANIFEST_R5.json` | BASELINE.values 四个 CURRENT 指针键齐全；PLAN 带 51 天日历；REUSE r1/r4 复用清单在 | 没有单独的“登录前校验回执”文件；校验结果只体现在 BASELINE/PLAN/REUSE 内容与 exit0。空槽 5 个的检查也无独立落盘 |
| 4.7 | `REUSE_MANIFEST_R5.json (r4 段)`<br>`PARQUET_MANIFEST_R5.json` | r4 段记录 references/days/last_universe/remaining/expected_by_day | 3363/1098/1097 三个计数没有单独汇总字段落到 HUB（明细在 reuse 清单里），需 GPT 侧自行点数 |
| 4.8 | `ADMISSION_R5.json (2026-10-27_03360_R4.parquet 条目)`<br>`QUARANTINE_R5.json`<br>`RESULT_R5.json` | ADMISSION 批次条目直接写着 path=`...\2026-10-27_03360_R4.parquet`、bytes=15489、sha256=`fb1a0ccb…`、admitted=79、quarantined=1；隔离行 600621.XSHG；RESULT quarantined_rows=1 status=RAW_STAGED_UNREVIEWED | — |
| 4.9 | `PLAN_R5.json (stock_remaining / stock_batches)`<br>`ADMISSION_R5.json (10-27 stock 新采批次)` | PLAN stock_batches=23、stock_remaining=1784 条；ADMISSION 里 10-27 stock 新采批次 = 23 批 1784 码（22×80+24=1784 逐条可点） | — |

## B. 回传清单（Results, uploads and END）

| 要求项 | 文件 | 状态 |
|---|---|---|
| ACK | `ACK_R5.json` | RETURNED |
| package verification | `PACKAGE_VERIFY_R5.json` | RETURNED |
| precheck wrapper raw stdout/stderr/real exit | `WRAPPER_RUN_R5.json`<br>`WRAPPER_STDOUT_R5.txt`<br>`WRAPPER_STDERR_R5.txt` | RETURNED (exit 回执事后补录) |
| native preflight raw stdout/stderr/real exit | `PREFLIGHT_RUN_R5.json`<br>`PREFLIGHT_STDOUT_R5.txt`<br>`PREFLIGHT_STDERR_R5.txt` | RETURNED |
| native tests raw stdout/stderr/real exit | `TESTS_RUN_R5.json`<br>`TESTS_STDOUT_R5.txt`<br>`TESTS_STDERR_R5.txt` | RETURNED |
| GATE_R5.json | `GATE_R5.json` | RETURNED |
| attached execution argv/raw streams/real exit | `EXECUTE_RUN_R5.json`<br>`EXECUTE_STDOUT_R5.txt`<br>`EXECUTE_STDERR_R5.txt` | RETURNED |
| R5 staging JSON outputs | `staging_output/ (RESULT/BASELINE/PLAN/SDK/REUSE_MANIFEST/ADMISSION/QUARANTINE/COVERAGE/per-date coverage/universes/receipts/quality)` | RETURNED |
| zero-byte streams kept as real zero-byte | `PREFLIGHT_STDERR_R5.txt`<br>`TESTS_STDOUT_R5.txt`<br>`WRAPPER_STDOUT_R5.txt`<br>`WRAPPER_STDERR_R5.txt`<br>`EXECUTE_STDOUT_R5.txt`<br>`EXECUTE_STDERR_R5.txt` | RETURNED (6 个 0 B，sha e3b0…) |
| Parquet list path/length/SHA256 (local only) | `PARQUET_MANIFEST_R5.json` | RETURNED (405 个 / 6378681 B) |
| COVERAGE enum + admitted/quarantined/unacquired sets | `COVERAGE_R5.json`<br>`staging_output/coverage/*.json`<br>`QUARANTINE_R5.json`<br>`ADMISSION_R5.json` | RETURNED (51/51 ACQUIRED) |
| acyclic DELIVERY_MANIFEST_R5.json | `DELIVERY_MANIFEST_R5.json` | RETURNED |
| LOCAL_READBACK_R5.json | `LOCAL_READBACK_R5.json` | RETURNED |
| UPLOAD_READBACK_R5.json byte-for-byte | `UPLOAD_READBACK_R5.json` | RETURNED (1328/1328 BYTE_EQUAL) |
| END | `REPORT_R5.md` | RETURNED |

## C. 根目录 20 个文件（字节 / SHA256 / 远端 blob / 回读）

| 文件 | 字节 | SHA256 前16 | 远端 blob | HUB | 回读 |
|---|---|---|---|---|---|
| `ACK_R5.json` | 9422 | `0d2fc8c29a1128a3…` | `33e366cfa1d6` | YES | BYTE_EQUAL |
| `PACKAGE_VERIFY_R5.json` | 9365 | `1089563e81e0c296…` | `444e02acee59` | YES | BYTE_EQUAL |
| `GATE_R5.json` | 5106 | `5dfe90ab183a3d24…` | `a73fc20109d0` | YES | BYTE_EQUAL |
| `WRAPPER_RUN_R5.json` | 3011 | `bf661648d874b0a7…` | `23c3cac28a69` | YES | BYTE_EQUAL |
| `WRAPPER_STDOUT_R5.txt` | 0 | `e3b0c44298fc1c14…` | `e69de29bb2d1` | YES | BYTE_EQUAL |
| `WRAPPER_STDERR_R5.txt` | 0 | `e3b0c44298fc1c14…` | `e69de29bb2d1` | YES | BYTE_EQUAL |
| `PREFLIGHT_RUN_R5.json` | 659 | `7d806232adafd155…` | `11601b1ffd21` | YES | BYTE_EQUAL |
| `PREFLIGHT_STDOUT_R5.txt` | 1157 | `81ecb2b27c183e00…` | `3b3d69a75d12` | YES | BYTE_EQUAL |
| `PREFLIGHT_STDERR_R5.txt` | 0 | `e3b0c44298fc1c14…` | `e69de29bb2d1` | YES | BYTE_EQUAL |
| `TESTS_RUN_R5.json` | 684 | `ef1d231a3ab69cb9…` | `b85db2f87453` | YES | BYTE_EQUAL |
| `TESTS_STDOUT_R5.txt` | 0 | `e3b0c44298fc1c14…` | `e69de29bb2d1` | YES | BYTE_EQUAL |
| `TESTS_STDERR_R5.txt` | 14363 | `d68c7ce207d7e662…` | `41ccb1dc105c` | YES | BYTE_EQUAL |
| `EXECUTE_RUN_R5.json` | 2075 | `10155653b5ad18c8…` | `f9df4f2cae10` | YES | BYTE_EQUAL |
| `EXECUTE_STDOUT_R5.txt` | 0 | `e3b0c44298fc1c14…` | `e69de29bb2d1` | YES | BYTE_EQUAL |
| `EXECUTE_STDERR_R5.txt` | 0 | `e3b0c44298fc1c14…` | `e69de29bb2d1` | YES | BYTE_EQUAL |
| `PARQUET_MANIFEST_R5.json` | 164981 | `048709d11368b340…` | `7b4566f546e0` | YES | BYTE_EQUAL |
| `REPORT_R5.md` | 8756 | `5fd652eaaa625a10…` | `9741072ea88c` | YES | BYTE_EQUAL |
| `DELIVERY_MANIFEST_R5.json` | 241636 | `4397c14f4f37ff70…` | `23bd18a5e2b7` | YES | BYTE_EQUAL |
| `LOCAL_READBACK_R5.json` | 283195 | `20f36bcd1b87fda8…` | `8b9c56d12789` | YES | BYTE_EQUAL |
| `UPLOAD_READBACK_R5.json` | 622711 | `7c19eb8087826a7e…` | `d407d0064d68` | YES | BYTE_EQUAL |

## D. staging_output 分组

| 组 | 文件数 | 字节 |
|---|---|---|
| `ADMISSION_R5.json` | 1 | 8282830 |
| `BASELINE_R5.json` | 1 | 14028 |
| `COVERAGE_R5.json` | 1 | 22738 |
| `PLAN_R5.json` | 1 | 34558 |
| `QUARANTINE_R5.json` | 1 | 1188 |
| `RESULT_R5.json` | 1 | 568 |
| `REUSE_MANIFEST_R5.json` | 1 | 3682285 |
| `SDK_R5.json` | 1 | 971 |
| `staging_output/coverage` | 35 | 657978 |
| `staging_output/quality` | 405 | 5504333 |
| `staging_output/receipts` | 844 | 955915 |
| `staging_output/universes` | 17 | 3710307 |

## E. 我自己发现的缺口（先交底）

- WRAPPER_RUN_R5.json 缺失 → 已于交付结束后补录并回读（provenance 写在文件内，未改 gate/streams/exit）
- 第一次刷新账本时 UPLOAD_READBACK 抢在上传前抓取，DELIVERY_MANIFEST/LOCAL_READBACK 两行曾为 False，已后置复核为 True
- 4.6/4.7 没有单独的“登录前校验回执”文件，证据只在 BASELINE/PLAN/REUSE 的内容里（4.8/4.9 已在 ADMISSION 批次条目里可直接点数）

合计: 控制/伴随文件 20 个，staging 1309 个，staging 字节 22867699。上传回读 1328/1328 BYTE_EQUAL。
