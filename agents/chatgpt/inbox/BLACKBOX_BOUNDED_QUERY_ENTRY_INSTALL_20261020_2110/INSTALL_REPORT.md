# INSTALL_REPORT — BLACKBOX_BOUNDED_QUERY_ENTRY_INSTALL_20261020_2110

status: OPS_READONLY_ENTRY_INSTALLED_AWAITING_REVIEW  
host: ZHANGWEI  
installed_at: 2026-10-20T21:12:00+08:00  
MUST_READ_PRECHECK(DATA)=PASS  

## 做了什么

1. 审定 V4 三模块安装到 `E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\runtime_v4\`，SHA 字节一致。  
2. 新增入口 `query_stock_daily_bounded_r1.py` + `.ps1` 启动器（钉死 Anaconda 3.10.20）。  
3. Windows 实测正/反例写入 `verify_2110/`。  
4. **未改** `脚本/` 原件、`.venv`、Kernel/HAND/Manifest、CURRENT/RAW/sealed、数据。  
5. 不宣称整个 BLACKBOX 恢复。

## 实测摘要

| 用例 | 结果 |
|---|---|
| 000001.XSHE 2026-09-02..09-10 | ok，**7 行**，scope=BOUNDED_WINDOW_VERIFIED |
| 09-01..09-10 | COVERAGE_GATE_REJECT，missing 2026-09-01，未读业务绕过 |
| 无窗/单端点 | BOUNDED_WINDOW_REQUIRES_CODE_AND_BOTH_ENDPOINTS |
| unsupported 产品 | UNSUPPORTED_PRODUCT_FOR_ENTRY |
| 日历 OSError fixture | coverage_ready=false + coverage_error |

## 回退

移出/停用本 `READONLY_QUERY` 版本目录与 START_HERE 索引条目即可；不删业务数据。
