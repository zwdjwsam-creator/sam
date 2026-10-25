# HANDOFF_TO_DESKTOP — 交接与复验说明

- from: SAM（笔记本）· to: ZHANGWEI（台式机）
- dispatch: `SAM_LED_DESKTOP_RECTIFICATION_20261025`
- status: **SAM_HANDOFF_READY_FOR_DESKTOP_REVERIFY**
- 交付位置（台机本机）：`E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\sam_led_rectification\`
- HUB 同名：`agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/sam_led_rectification/`

---

## 1. 已落地（不是建议清单）

| 文件 | 字节 | sha256（前16） | 备份 |
|---|---|---|---|
| `candidate/run_r15_cleaning_replay.py` | 25,832 | `2719c17eec5589ac` | `.bak_sam_led_r6` |
| `tools/run_connected_pipeline.py` | 28,893 | `4964f27cc325c8e8` | `.bak_sam_led_r7` |
| `脚本/run_blackbox_daily_incremental_data_plane_r1.py` | 46,492 | `949e95c758b2064c` | `.bak_sam_led_20261025` |
| `sam_led_rectification/RUN_CHAIN_R1.py` | — | — | 新增 |
| `sam_led_rectification/RUN_CHAIN_R1.cmd` | — | — | 新增 |

> 注意：跨机复制会把 CRLF 归一成 LF（实测 591 行差 591 字节）。核对身份时**先归一化 EOL**，否则会把换行差异误判成版本差异。

---

## 2. 台式机复验步骤（按顺序，约 15 分钟）

```cmd
cd /d E:\BLACKBOX
:: (1) 三条只读检查
.venv\Scripts\python.exe -c "import sys,pandas,pyarrow;print(sys.version)"
.venv\Scripts\python.exe -X utf8 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode status --date 2026-09-24
.venv\Scripts\python.exe -X utf8 脚本\run_blackbox_daily_incremental_data_plane_r1.py --mode status --date 2026--0-9-

:: (2) 原链同产物
cd /d E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\sam_led_rectification
E:\BLACKBOX\.venv\Scripts\python.exe -X utf8 RUN_CHAIN_R1.py
```

---

## 3. 通过条件（逐项，必须来自台机进程）

`LOCAL_RUN_EVIDENCE.json`：
- [ ] `identity.hostname` == `ZHANGWEI`
- [ ] `steps.A_chain.exit_code` == 0
- [ ] `steps.B_status_iso.exit_code` == 0
- [ ] `steps.C_bad_date.exit_code` **!=** 0
- [ ] `digests.after_status_iso` == `digests.after_chain`（status 没写盘）
- [ ] `digests.after_bad_date` == `digests.after_status_iso`
- [ ] `verdicts` 全 true

`deliverables\CONNECTED_PIPELINE.json`：
- [ ] `CONNECTED_PIPELINE_RESULT` == `PASS`
- [ ] `verdicts.lineage_same_artifact` == true
- [ ] `verdicts.compiler_read_r15_tree` == true
- [ ] `stages.compiler.seal_all_pass` == true
- [ ] `stages.cleaning_r15.release_id` == `R15_REPLAY_20260924_R3`
- [ ] `LINEAGE.retained_batches[*].retained_equals_r15_sealed` 全 true
- [ ] `stages.same_input_replay.status` == `PASS`
- [ ] `PRODUCTION_CURRENT_WRITE` == `NONE`

---

## 4. 阻断条件（命中任一即为 BLOCKED，不要勉强判 PASS）

| 命中 | 处置 |
|---|---|
| R15 步骤 >5 分钟且 CPU 满、`r15_releases` 为空 | 停下，附 `run_r15_cleaning_replay.py` 的 sha256 与 `pipeline_runs\r15_cleaning_*.log`，报 SAM |
| `status` 前后 CURRENT/STATE digest 变化 | D2 回归，停 |
| 非法日期 exit 0 或建出 `2026--*` 目录 | D1 回归，停 |
| `lineage_same_artifact=false` | 链未真正贯通，停 |
| 编译器 `SKIP_NO_SOURCE` / `missing=['VALUATION_PIT_R1']` | 定向物化失效，附 compiler 日志报 SAM |
| 任何生产 `CURRENT` 被写 | 立即回滚 + 报警 |
| 需要联网下载才能继续 | 超出授权，BLOCKED |

---

## 5. 预期结论怎么写

- 全通过 → 写 `DESKTOP_REVERIFY_RESULT.json`：`{"status":"PASS","evidence":"LOCAL_RUN_EVIDENCE.json","reviewer_host":"ZHANGWEI"}`
- 有阻断 → `{"status":"BLOCKED","blockers":[...],"evidence":[...]}`，并把 SAM 需要补的点列清楚

**不要**因为文档通顺或 SAM 报了 PASS 就直接写 PASS；只认台机自己的进程证据。

---

## 6. 仍未解决（与本次改动无关，写进复验结果一起提交）

1. 供应商分页完整性 `UNKNOWN`（retained 语料无请求记录）
2. 复权因子 2026-08-10 起恒 1.0、17 份文件日期为整数 0..299，成因未分离 → 不得断言"供应商造假"或"必须重下"
3. V4 `BLOCKED_INPUT_INCOMPLETE`（0 成交 0 订单，`diagnostic_only=true`）
4. 08-31 / 09-01 只在候选分区，生产 CURRENT 未切换（未授权）
5. `is_st` / 历史成分未绑定
6. `BLACKBOX_DEST` 共享在卸载后仍可匿名读，建议收紧（未擅自改）
