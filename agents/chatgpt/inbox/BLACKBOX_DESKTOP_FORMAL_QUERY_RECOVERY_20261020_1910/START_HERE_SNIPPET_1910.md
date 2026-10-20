配置\secrets\github_hub_token.TXT` | 存在（未复制到 E） |
| 双挂 secrets | `D:\CursorDualRouteConfig\cursor_ai_stack\secrets` | 只读引用保留 |
| 记忆盘 | `E:\BLACKBOX\记忆盘` | 目录存在（经验包 00–04）；**不是**独立磁盘/junction |

## 禁止误操作

- 不跑 R9 全量 execute / verify-existing / 全盘 hash
- 不就地改 sealed/CURRENT/RAW；不猜路径
- 无 LIVE_EXECUTION_SESSION 不下单；不打印密钥
- 空表 ≠ NO_DATA（走 DATA_ABSENCE_GATE）
- `.venv\Scripts\python.exe` **当前无法直接启动**（pyvenv.cfg 指向缺失的 ThinkPad Python312）；site-packages 仍含 pyarrow/pandas，可用系统 Python312+`PYTHONPATH=.venv\Lib\site-packages` 做兼容探测。**正式修复=按权威清单重建 venv（待核），不要把系统 Python 直接写成业务默认替代。**（1900 已核）
- 1824 网页对接消息按 1834 **不要重发**；1814 HOLD；LiteLLM 不动

## 相关 HUB

https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/BLACKBOX_DESKTOP_RULES_AND_DATAFLOW_HANDOVER_20261020_1834


## 1910 正式查询恢复（2026-10-20T19:09:48+0800）

- MUST_READ_PRECHECK(DATA/CACHE)=**PASS**（系统 Python312 跑预检脚本）
- 正式查询 **BLOCKED**: `脚本/blackbox_data_coverage_common_r1.py` 为空壳(2B)；`cache_stock_daily_pit_r1_reader_r1` 模块不存在
- 禁止用 pyarrow 直读当正式 PASS；详见 HUB RECOVERY_REPORT
- SAM 约定: tip 与 BRIEF 分流程；台式机保留 `E:\BLACKBOX_ENGINES`（源机可无）
- 报告: `C:\LAN_SHARE_REPORT\BLACKBOX_DESKTOP_FORMAL_QUERY_RECOVERY_20261020_1910\RECOVERY_REPORT.md`
