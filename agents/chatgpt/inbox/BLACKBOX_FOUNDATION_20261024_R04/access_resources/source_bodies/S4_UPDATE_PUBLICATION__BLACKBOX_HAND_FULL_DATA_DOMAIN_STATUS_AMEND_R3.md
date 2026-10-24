# HAND 正式域名口径修订 R3

- authorized_at_cn: `2026-08-12T01:18:42+0800`
- rule: `BLACKBOX_HAND_FULL_DATA_DOMAIN_STATUS_AMEND_R3`

## 对照表

| Dataset | 人话 | 新状态 |
|---|---|---|
| full_factor_values_library | 全量因子历史值库 | **需要下载**（可取尽取历史全量，之后交易日增量） |
| financial_indicator | 财务指标历史库 | **需要全量下载**（旧 BLOCKED 作废→须重探） |
| money_flow_abnormal_lock_subscribe | 资金流/异常/锁仓/申购 | **需要全量下载** |
| jq260_factor_values_library | 聚宽260因子完整历史值库 | **目标需要**；**权限必须重新实测** |
| jq260_factor_values | 260 实际因子值 | 同上，不得凭旧 policy 直接跳过 |
| fq_pre_post | 前/后复权价格整库 | **目前不需要**（有复权因子可动态生成） |
| QMT_live | QMT 实时盘中 | **仍不属于**历史全量建设 |

## AG 行为

- 「数据更新」规划必须纳入上表 REQUIRED / TARGET 域。  
- JQ260：先 live probe，再下载；禁止写「因旧规则跳过」。  
- 未实测权限不得宣称 financial_indicator 仍 BLOCKED。  
- 不下载 fq 整库；不把 QMT 实时并入历史主轨。
