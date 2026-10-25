# 移交：台式机 BLACKBOX 副本整顿权 → SAM 端 Cursor

- 移交时间（CN）：2026-10-25 15:1x
- 移交方：台式机 `ZHANGWEI`（Cursor Agent）
- 承接方：**笔记本原 BLACKBOX 的 Cursor**（SAM 端）
- 主人指令原文："让笔记本原 BLACKBOX 的 Cursor 主导、直接整顿台式机副本"
- 台式机角色：**只读待命**（冻结旗标见第四节）

---

## 0. 一句话

台式机副本现在是"主链可跑、身份待定"的状态：数据没丢，`DG1` 与源机只差 3 个 `MODE`。**别在台机侧继续猜字段**——请你在自己那套权威树上决定口径，然后直接对台机副本下手。

## 1. 你现在就能拿到的东西

| 内容 | 位置 |
|---|---|
| 台机状态快照（机器可读） | `desktop_structure_audit_20261025\desktop_reply_Q1_Q9\DESKTOP_STATE_SNAPSHOT_FOR_SAM.json`（随包上传时同名） |
| 终态核验 | `...\output\AFTER_SAM_Q1_Q9_VERIFY.json` |
| DG1 残差证明 | `...\output\DG1_REVERT_PROBE.json` |
| 事故台账（我自捅的） | `...\output\BAD_DATE_CLEANUP_LEDGER.json` / `CURRENT_RESTORE_LEDGER.json` |
| 跨机写入登记 | `...\output\CROSS_MACHINE_WRITE_LEDGER.json` |
| HUB 文件夹 | `agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/desktop_reply_Q1_Q9/` |

**直连写入通道**：台机已开共享 `\\192.168.100.1\BLACKBOX_DEST` → `E:\BLACKBOX`（另有 `E$`、`E_DRIVE`）。你有两条路：

- **只读读取（推荐用于核验）**：`\\192.168.100.1\E_DRIVE` → `E:\`，账号 `ZHANGWEI\sam_ro`（只读，2026-10-25 开通）。
  凭据与挂载说明：`desktop_reply_Q1_Q9\SMB_READONLY_ACCESS_FOR_SAM.md` + `desktop_reply_Q1_Q9\secrets\sam_smb_readonly.TXT`。
- **MODEL_A（写入）**：你经 `BLACKBOX_DEST` 直接写台机副本 → 速度快，但**每次写入必须回填台账**（第六节）。
- **MODEL_B（写入）**：你在自己树上产出 `DIRECTIVE_*.md` + `PATCH_*.diff`，台机按你指令执行并回执 → 慢一轮，但每一步有落地记录。

> 建议：**核验走 `E_DRIVE` 只读**，**真要改才走 `BLACKBOX_DEST`**——只读通道不会误伤台机生产树。

两种都可以；如果走 MODEL_A，请在写之前把"要改哪些文件、为什么"写成一页，台机侧据此留账。

## 2. 台机副本当前事实（可复算，勿凭记忆）

```
root                 E:\BLACKBOX（与源机同根同相对结构）
代码逐字节            90/90 与源机一致（本轮未改任何业务 .py）
manifest_id          DAILY_DATA_MANIFEST_20260924
CN_RESEARCH_DATE     2026-09-24   （manifest / plane / input_pack 三处一致）
DATA_GENERATION_ID   DG1-373cf01dd3e066bd6a21c74154b8e3606b8ede05dffa91ffd4338a225db1811b
源机 DG1             DG1-7fd2bf71248bbe7d8b52798ae0a77aaf0c8362ba407112fffe6445122e2c2b13
残差                 仅 .JQ.MODE / .T_EXTERNAL.MODE / .GLOBAL_SELLSIDE.MODE（INGEST vs VERIFY_ONLY）
cache 产品目录        51（+7 顶层文件；别再报 58）
固定路径              DATA_PLANE_PATH_MAP.json 38 条，missing=[]
cache 日历            JQ20_STK_EXCHANGE_LINK_CALENDAR_R1 14 parquet / 32,428 行 / max=2026-12-31
US 细粒度产物         1,482 B STATUS=PASS / snapshot 3,786 B STATUS=PASS / mapping 2,375 B
D:\CURSOR_TASK_ARCHIVE 存在且可写（故 Q1 的 11 处归档写入当前不阻断）
研究记忆             DAILY_BRIEF 仅 2026-08-30；09-02…09-24 无
```

## 3. 我已经替你做完的（**不要重做**）

1. 删 `US_MARKET.FIXED_PATHS.alignment_csv`（0 消费者）。
2. `DISCOVERY_ASOF` 保持 `2026-09-24`（未改回 09-25）。
3. `US_FINE_GRAINED_STATUS` / `A_SHARE_MAPPING_PRIOR_STATUS` 改为**按产物派生** → `PASS` / `PASS`（不是硬写）。
4. 修复我自己造成的 `2026--0-9-` 污染（生产树残留 = 0）。
5. 跨机写入留账。

> 也就是说：**Q1–Q8 已落地，剩下的全是判断类问题，不是数据类问题。**

## 4. 冻结旗标（台机已置）

`运行\BLACKBOX_DESKTOP_REPAIR_DELEGATION_CURRENT.json`

```json
"desktop_write_freeze": {
  "manifest_and_plane": true,
  "data_plane_current": true,
  "business_code": true,
  "data_artifacts": true
}
```

解除条件：**主人显式指令**，或**你以 `SAM_DIRECTIVE` 形式下发并注明解除范围**。台机侧任何 AG 在冻结期内不得自行改上述四类。

## 5. 请你决的四件事（我给意见，不定调）

### D1 — `MODE` 是否该计入 `DG1` 语义哈希？

- 事实：把 3 个 `MODE` 置 `INGEST` 后，DG1 精确回到你的 `7fd2bf71…c2b13`。
- 事实：`MODE` 由 `run_blackbox_daily_incremental_data_plane_r1.py` 219/252/280 行按 `ingest` 布尔写出，是"动作"，不是"数据"。
- 我的意见：若 `DG1` 语义要表示**数据身份**，`MODE` 应像 `BUILD_TIME` 一样排除（方案 C）；若坚持现状，台机只能记 `DIVERGENT_MODE_ONLY`（方案 A）；方案 B（真跑 ingest）需主人授权采集。
- **请给一条：A / B / C，以及若选 C，历史 DG1 的重算与回归方案。**

### D2 — `--date` 格式与 `status` 写副作用是否修？

- 事实：`--date 2026-09-24`（ISO）→ `cn_iso='2026--0-9-'`；且 `--mode status` 会写 CURRENT/STATE/DAILY。
- 我的意见：932 行接受 ISO 并校验、非法即 `FAIL_CLOSED`；`status` 默认不写。
- **代价：会改变你审计过的文件字节（破坏 90/90 一致）。请给：改 / 不改。**

### D3 — 研究记忆缺口口径

- 我：`08-31→09-24` 含 09-02/09-03 = 17 天；你：`09-04` 起算 = 15 天。两者不矛盾。
- **请给：以哪个交易日集合为准；回补顺序（逐日 `run-day` + `seal`）是否由你出脚本。**

### D4 — `D:\CURSOR_TASK_ARCHIVE` 硬编码

- 台机有 D: 盘，当前不阻断；换无 D: 机器会真失败。
- 我的意见：注入可覆盖的归档根（env 或参数），**不改业务算法**。
- **请给：现在改 / 以后改 / 只登记。**

## 6. 你动手时的硬约束

1. 禁：新数据采集、清洗重跑、CURRENT 无关切换、下单（`ORDER_ALLOWED=false`）。
2. 禁：改 `sealed/`、`CURRENT` 的原地覆盖而不留备份。
3. 每次写台机必须留：`谁改了什么、为什么、备份在哪、回读 SHA`。
4. 改完必须跑台机侧只读核验：`任务\BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1\脚本\verify_after_sam_q1_q9_r1.py`（硬门 8 项）。
5. 若你要动 `MODE` 口径（D1 选 C），必须同时给历史 manifest 的回归证据，否则台机会 `FAIL_CLOSED`。

## 7. 验收标准（你交回来时我按这个核）

```
1. DG1 与源机关系写明：IDENTICAL / DIVERGENT_MODE_ONLY / OTHER(列键)
2. manifest/plane/input_pack 三处 manifest_id 与 CN_RESEARCH_DATE 一致
3. 38 条固定路径 missing=[]；cache 产品目录 = 期望值（口径注明）
4. 生产树无 "2026--0-9-" 残留
5. 每条修改都有 备份路径 + 回读 SHA
6. flags: ORDER_ALLOWED=false, NEW_DATA_ACQUISITION_AUTHORIZED=false
```

## 8. 回传格式

写回 `agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/desktop_reply_Q1_Q9/`，文件名建议：

```
SAM_DIRECTIVE_Q1_Q9_D1_D4.md      # 四项裁决
SAM_PATCH_PLAN_<date>.md          # 若要改代码/字段，逐文件列
SAM_REGRESS_RECEIPT.json          # 可复算数字（DG1 / 路径 / 产品数 / 残留）
```

台机侧收到后：先跑核验 → 按你的 directive 执行 → 回 `DESKTOP_EXEC_RECEIPT_*.json`。

## 9. 我不替你做的事

- 不替你决定 `MODE` 是否进哈希（D1）。
- 不替你决定改不改生产脚本（D2）。
- 不在冻结期内自行"顺手修好"——**这正是上一轮出错的原因**。
