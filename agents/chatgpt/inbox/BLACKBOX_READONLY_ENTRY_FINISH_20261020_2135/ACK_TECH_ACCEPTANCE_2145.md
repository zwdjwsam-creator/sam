# ACK_TECH_ACCEPTANCE_2145

host: ZHANGWEI
review_id: BLACKBOX_READONLY_ENTRY_TECH_ACCEPTANCE_20261020_2145
task_closed: BLACKBOX_READONLY_ENTRY_FINISH_20261020_2135
status: BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED / CLOSED
COPY_AUTHORIZED=false
written_at: 2026-10-20T21:41:54

## 入口身份（安装位，未改代码）
- path: E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\
- python: D:\Anaconda3\envs\blackbox_bt_py310\python.exe (3.10.20)
- entry py SHA256: 2ae78cbd302cced9591999f92dad25a120357828ae466c3f85c5b686c2ab7680
- entry ps1 SHA256: 7dfbac9179fc869de400d66d36d21ab72162cd0e970ce603b45a8cc7d9a7c170
- runtime_v4 三个审定 SHA 保持 2135/2110 冻结（未重跑全套测试）

## 已结案范围
- STOCK_DAILY_PIT_R1 双端点有限只读入口技术验收通过；停止该项修复迭代。
- 管理状态已标 BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED/CLOSED，指向 2145。

## 未验收 / 不得启动
- FULL_HISTORY=UNPROVEN；全历史/全资产/证券全量/因果回测未验收。
- 原 E .venv Python3.12.10 源机路径问题未修。
- 业务日增、研究 autorun、策略/交易不在验收内；不得用本接受令启动或覆盖原脚本。
- 不得重新跑迁移/verify-existing/全库 hash。

## 管理索引路径与摘录
- START_HERE: E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\START_HERE.md
- OPERATING_MAP: E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\OPERATING_MAP.md
- QUERY_CAPABILITY: E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\QUERY_CAPABILITY.md

### START_HERE 摘录
```
## 有范围只读查询入口（2110/2135 / V4，独立 _OPS）
- status: **BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED**（2145 技术验收结案）
- 目录：`E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\`
- 能力说明：`READONLY_QUERY/QUERY_CAPABILITY.md`
D:\Anaconda3\envs\blackbox_bt_py310\python.exe -u E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\query_stock_daily_bounded_r1.py --code 000001.XSHE --start-date 2026-09-02 --end-date 2026-09-10
| **有范围日线只读（V4）** | `_OPS/BLACKBOX_HANDOFF/READONLY_QUERY/query_stock_daily_bounded_r1.py` | **INSTALLED 2110**；仅 STOCK_DAILY_PIT_R1+双端点 |
```

### QUERY_CAPABILITY 摘录（前部）
```
# READONLY_QUERY — 有范围只读入口（V4）

status: BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED / CLOSED  
task: BLACKBOX_READONLY_ENTRY_FINISH_20261020_2135（收尾） / 2110（安装）  
COPY_AUTHORIZED=false  
filter: pyarrow.dataset code+date 下推；UTF-8 严格 stdout  

## 入口（唯一）

```text
D:\Anaconda3\envs\blackbox_bt_py310\python.exe -u E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\query_stock_daily_bounded_r1.py --code 000001.XSHE --start-date 2026-09-02 --end-date 2026-09-10
```

或：

```powershell
powershell -File E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\query_stock_daily_bounded_r1.ps1 --code 000001.XSHE --start-date 2026-09-02 --end-date 2026-09-10
```

自然语言用例：查询平安银行 000001.XSHE 在 2026-09-02 至 2026-09-10 的日线（只读、有范围）。

## 解释器（勿混用）

| 项 | 值 |
|---|---|
| 本入口 | `D:\Anaconda3\envs\blackbox_bt_py310\python.exe` = **3.10.20** 64bit |
| pandas / pyarrow | 2.3.3 / 23.0.1 |
| 原 `.venv` 3.12.10 | **未修好**；本入口不冒称业务 venv 可用 |

## runtime_v4 SHA（与审定一致）

- common `0c018fb5f4cd31fc6fc05d783bf66f7bc54503e5464825259c462682fb980769`
- gate `98faa2945ff9b056936ac87b5e39be87a1adf618120805c2f96e269169798fd3`
- resolver `5d232abbded4043426a51b57b45afa3d799152c368f7b235a4fff2d9cb26c8d6`

```

## HUB
- 本 ACK 写入 2135 包；更新 INBOX_FOR_CHATGPT。
- 巡视保持用户既有 10h/5m 授权；本 review 不延长/重建巡视。
- 无新任务则待命；不自造更高权限继续修复任务。
