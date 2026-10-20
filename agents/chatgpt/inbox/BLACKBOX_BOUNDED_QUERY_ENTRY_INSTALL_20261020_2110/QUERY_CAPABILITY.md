# READONLY_QUERY — 有范围只读入口（V4）

status: OPS_READONLY_ENTRY_INSTALLED_AWAITING_REVIEW  
task: BLACKBOX_BOUNDED_QUERY_ENTRY_INSTALL_20261020_2110  
COPY_AUTHORIZED=false  

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

## 能力边界

- 仅 `STOCK_DAILY_PIT_R1` + 双端点窗 + 证券代码  
- `coverage_ready` 且 `BOUNDED_WINDOW_VERIFIED` 后才读行  
- 非全历史 / 非证券全量 / 非因果回测 / 无交易建议  
- `known_at=null` / `price_adj_tag=RAW_NONE` 原样保留  
- 原业务日增/研究/策略 **未验收**
