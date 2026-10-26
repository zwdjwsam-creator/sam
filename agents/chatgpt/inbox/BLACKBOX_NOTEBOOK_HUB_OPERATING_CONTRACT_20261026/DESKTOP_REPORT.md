# DESKTOP_REPORT — HUB 操作契约落地 + 三项实测分歧

```
TASK_ID                     BLACKBOX_NOTEBOOK_HUB_OPERATING_CONTRACT_20261026
EXECUTION_HOST              DESKTOP_ZHANGWEI
ACCESS_MODE                 LOCAL_FULL
TASK_CLASS                  GENERAL
PREFLIGHT                   MUST_READ_PRECHECK=PASS
                            KERNEL_STATUS=VERIFIED
                            KERNEL_SHA256=b05a69958e29f7c90cf1ea794a4c437d36120bb960515ce9e26d3f4d5bdf197a
                            HAND_READ=NOT_SUFFICIENT
                            AUTHORITY_READY=YES
                            TASK_EXECUTION=ALLOWED
                            TASK_EXECUTION_FORBIDDEN=FALSE
                            rules_loaded BOOTSTRAP status=VERIFIED (sha 一致)
MANIFEST_ID                 DAILY_DATA_MANIFEST_20260924
DATA_GENERATION_ID          DG1-373cf01dd3e066bd6a21c74154b8e3606b8ede05dffa91ffd4338a225db1811b
ASOF                        SOURCE=2026-09-24 / CLEAN=2026-09-24 / CACHE=2026-09-24
PIT_PASS                    true
LANES                       A:PASS(VERIFY_ONLY) B:PASS(ALIGN)+PARTIAL(MATERIALIZATION)
                            C:PASS(17) D:PASS(4 rep/26 evt) E:PASS(8 evt) F:PASS(CLOSE_COLLECTED)
DOUBLE_GATE                 NOT_RUN（本轮未执行日增，未评估）
BLOCKERS                    无（但见下方 3 项分歧）
NEXT                        WAITING_FOR_USER
```

## 0. 本轮做了什么

读取 HUB `agents/desktop/inbox/BLACKBOX_DESKTOP_RUNBOOK_20261026`，
逐文件验 SHA256，核对包内声明的终态与台式机磁盘实况，
然后把「笔记本端口操作规程」固化为台式机硬规则并落盘。

## 1. 包完整性（逐文件重算，非引用）

```
PACKAGE_INTEGRITY = PASS
generated_at_cn   = 2026-10-26T20:41:18+0800
issued_by         = notebook_SAM
```

| 文件 | bytes | sha256 |
|---|---|---|
| `BLACKBOX_DESKTOP_AI_RUNBOOK_R1.md` | 14192 | `eaf2ac9daeaae8c238692376e816505680f2b5954ca4b9c54a0c127423e03583` |
| `DAILY_INCREMENTAL_RUNBOOK.md` | 13723 | `088e245b7ee815d76caf14314e8aac646026274788dec9f98f9c96149b09901a` |
| `INBOX_FOR_DESKTOP.md` | 1618 | `e5f55ccd95693d2891aeae1c4188518661cc3af2503bad0e33dab2b0782d2648` |
| `PRECONDITION_MATRIX.csv` | 2072 | `c94e1ced40b643ca21572a72ce6f3cd7d42dac13eaae265ab458cc2043f52dcd` |
| `START_HERE.md` | 4285 | `0ac97d122c8e049eabd02b7a605b6cb63ea2b2e409c2beb42b73e05d93249a69` |

## 2. 声明终态 vs 台式机磁盘（逐字段）

| 字段 | 笔记本声明 | 台式机磁盘 | 结论 |
|---|---|---|---|
| `manifest_id` | DAILY_DATA_MANIFEST_20260924 | 同 | MATCH |
| `CN_RESEARCH_DATE` | 2026-09-24 | 同 | MATCH |
| `ALL_LANES_READY` | YES | YES | MATCH |
| `DAILY_INCREMENTAL_READY` | YES | YES | MATCH |
| `DEGRADED_LANES` | [] | [] | MATCH |
| cleaning release | `...R33_FUND_NAV_ASOF_20260924_20260924_200439` | 同 | MATCH |
| cache release | `BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439` | 同 | MATCH |
| SOURCE/CLEAN/CACHE | 2026-09-24 ×3 | 同 | MATCH |
| `PIT_PASS` | true | true | MATCH |
| **`DATA_GENERATION_ID`** | `DG1-7fd2bf71…` | `DG1-373cf01d…` | **MISMATCH** |

`VERDICT = TERMINAL_STATE_MATCH_WITH_DG1_SNAPSHOT_DIVERGENCE`

## 3. 三项必须反馈给笔记本的分歧

### 3.1 DG1 跨机不可比（不是数据缺陷）

- 笔记本：`DG1-7fd2bf71248bbe7d8b52798ae0a77aaf0c8362ba407112fffe6445122e2c2b13`
- 台式机：`DG1-373cf01dd3e066bd6a21c74154b8e3606b8ede05dffa91ffd4338a225db1811b`
- 根因：`DG1 = sha256(manifest 剔除 BUILD_TIME/DISPLAY 等)`，但
  `PATH_MAP` + 6 个 Lane 的 `FIXED_PATHS` 内含 **29 条 `E:\BLACKBOX` 绝对路径**。
  跨机（如 `\\192.168.100.2\BLACKBOX`）必然变。
- 判定：`SNAPSHOT_DIVERGENCE_DG1`，**数据一致，哈希不可比**。
- 建议：跨机一致性改判 `ASOF 三元组 + release_id + 产品级内容哈希`；
  若要 DG1 可比，需把 `PATH_MAP` / `FIXED_PATHS` 纳入语义排除或做根路径归一化。

### 3.2 Runbook 第 6 节的 manifest 键位与实际不符

`DAILY_INCREMENTAL_RUNBOOK.md` §6 验收表写 `B.T_EXTERNAL.ALIGN_PASS` / `F.OPEN_READY`。
台式机磁盘实测：**Lane 键在顶层**，没有 `d['B']` / `d['F']`。

```
d['JQ']  d['T_EXTERNAL']  d['GLOBAL_SELLSIDE']
d['DOMESTIC_RESEARCH']  d['US_NEWS']  d['US_MARKET']
```

照抄会 `KeyError` 或误判为「字段缺失」。建议改为标注「概念 Lane 标号」并给出真实 JSON 路径。

### 3.3 Lane B PARTIAL 约束已确认生效

`EXTERNAL_EVIDENCE_MATERIALIZATION_FINAL.json` = `EXTERNAL_EVIDENCE_MATERIALIZATION_PARTIAL`。
已固化为硬约束：Lane B 只能报 `PASS(ALIGN)+PARTIAL(MATERIALIZATION)`，禁写 COMPLETE、禁据此改 manifest。

## 4. 落地的硬规则（台式机侧）

```
规则 SSOT    E:\BLACKBOX\规则库\hand_hard_rules\BLACKBOX_HAND_NOTEBOOK_HUB_OPERATING_CONTRACT_R1.json
CURRENT      E:\BLACKBOX\运行\BLACKBOX_NOTEBOOK_HUB_OPERATING_CONTRACT_CURRENT.json
Cursor 规则  E:\BLACKBOX\.cursor\rules\blackbox_notebook_hub_operating_contract.mdc  (alwaysApply=false)
HAND 指针    HAND.txt  → NOTEBOOK_HUB_OPERATING_CONTRACT_R1
AGENTS 指针  AGENTS.md item 28
```

固化要点：权威链不可跳；`TASK_CLASS` 封闭枚举；预检三件套；四开关默认 FALSE；
`ACCESS_MODE` 三态；`EMPTY != NO_DATA`（五态枚举，只有 `CONFIRMED_ABSENT` 可说「不存在」）；
三层分述；5000 静默门；日增双门 + `DEGRADED=FAIL_CLOSED`；`PATH_MAP` 唯一；
不可变（RAW/sealed/CURRENT/外源隔离）；六种时间戳；120s/300s 静默门；FAIL_CLOSED 矩阵；
HUB 回报三铁律；网络硬边界；`DG1` 禁作跨机一致性判据。

## 5. 自检

```
NOTEBOOK_HUB_CONTRACT_LANDING = PASS   (18/18)
包完整性                      = PASS   (5/5 SHA 一致)
```

HEAD 一条提示：`alwaysApply` 三件合计 4375B，超 4KB 预算 279B（既有，不是本轮造成；本轮规则为 `alwaysApply=false`，注入预算 delta = 0）。是否压缩那三条触发章程，等 USER 定。

## 6. GATES（只写实跑过的）

| Gate | 结果 | 方式 |
|---|---|---|
| `blackbox_must_read_preflight_r1.py --task-class GENERAL` | PASS | 实跑 |
| HUB 包 SHA256 逐文件复算 | PASS 5/5 | 实算 |
| 笔记本声明 vs 台式机磁盘字段比对 | MATCH 9 / MISMATCH 1(DG1) | 实读 |
| 日增双门 | NOT_RUN | 本轮未执行日增 |

## 7. ARTIFACTS

| path | bytes | sha256 |
|---|---|---|
(`_OPS/.../sam_led_rectification/` 下)
- `HUB_READ_R1.py`
- `HUB_RUNBOOK_SHA_VERIFY_R1.py`
- `HUB_NOTEBOOK_CLAIM_VS_DESKTOP_R1.py` / `.json`
- `HUB_TREE_R1.txt`
- `APPEND_HAND_AGENTS_NOTEBOOK_CONTRACT_R1.py`
- `VERIFY_NOTEBOOK_CONTRACT_LANDING_R1.py`

（sha256 见同目录 `ARTIFACTS_SHA256.json`）
