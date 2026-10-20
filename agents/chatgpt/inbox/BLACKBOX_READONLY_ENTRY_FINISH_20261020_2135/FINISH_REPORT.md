# FINISH_REPORT — BLACKBOX_READONLY_ENTRY_FINISH_20261020_2135

status: READY_FOR_ENTRY_FINAL_REVIEW  
parent: BLACKBOX_BOUNDED_QUERY_ENTRY_INSTALL_20261020_2110  
host: ZHANGWEI  
finished_at: 2026-10-20T21:35:00+08:00  
COPY_AUTHORIZED=false  

## 改动范围

仅更新：
- `query_stock_daily_bounded_r1.py`
- `query_stock_daily_bounded_r1.ps1`
- 管理文档索引（START_HERE / OPERATING_MAP 已含 2110 入口；本报告附路径）
- `verify_2135/` 新回执  

**未改** `runtime_v4` 三 SHA、生产脚本、CURRENT/数据、Kernel/HAND/Manifest、根 AGENTS。

备份：`READONLY_QUERY/_bak_before_2135_*`

## 逐项结果

1. **小窗过滤下推**：`pyarrow.dataset` + `filter=(code==…) & (date>=…) & (date<=…)`，`columns=` 投影后 `to_table`；不再 `pf.read` 全年再 pandas 筛。正例 `materialization` 字段明示。date 类型=`timestamp[ns]`。  
2. **UTF-8**：stdout 以 UTF-8 bytes 写出；验证 `has_u_fffd=false`；中文 note/product_path 可读。  
3. **CURRENT 终检**：resolve 后 + `_read_rows` 后均核 pointer SHA/id/root；fixture `fixture_current_change.json` 证明变化不可 `ok=true`。  
4. **self-check**：必需包缺失 → 非零；loaded 模块路径必须在 `runtime_v4` 且 SHA 匹配。  
5. **ISO 日期**：非法/反向/缺 code 拒绝。  
6. **文档链**：入口见 `START_HERE.md`「有范围只读查询入口」与 `OPERATING_MAP.md` 组件表行「有范围只读查询 V4」。

## 最终 SHA / 解释器

| 项 | 值 |
|---|---|
| entry py | `2ae78cbd302cced9591999f92dad25a120357828ae466c3f85c5b686c2ab7680` |
| entry ps1 | `7dfbac9179fc869de400d66d36d21ab72162cd0e970ce603b45a8cc7d9a7c170` |
| interpreter | `D:\Anaconda3\envs\blackbox_bt_py310\python.exe` 3.10.20 |
| runtime_v4 | 三 SHA **不变**（与审定一致） |
| 正例耗时 | ~678ms wall（含 coverage resolve） |
| 原 .venv 3.12 | **仍未修** |

## 验证

| 用例 | rc / 结果 |
|---|---|
| 000001 09-02..09-10 | 0 / 7 行 / UTF-8 干净 |
| 09-01..09-10 | 3 / COVERAGE_GATE_REJECT |
| 反向日期 / 非法格式 / 缺 code | 2 |
| CURRENT 变化 fixture | 可拒绝 |
| 缺包 self-check fixture | 非零 |

## 命令

```text
D:\Anaconda3\envs\blackbox_bt_py310\python.exe -u E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\query_stock_daily_bounded_r1.py --code 000001.XSHE --start-date 2026-09-02 --end-date 2026-09-10
```

不宣称全 BLACKBOX 恢复。
