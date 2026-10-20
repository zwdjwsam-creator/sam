# QUERY_CAPABILITY — V4 bounded (2005)

status: CANDIDATE_V4_BOUNDED_QUERY_READY_FOR_REVIEW  
COPY_AUTHORIZED=false  
host: ZHANGWEI  
code: `C:\LAN_SHARE_REPORT\BLACKBOX_COVERAGE_BOUNDED_QUERY_REVIEW_20261020_2005\code_v4\`

## SHA256

| file | sha256 |
|------|--------|
| blackbox_data_coverage_common_r1.py | `0c018fb5f4cd31fc6fc05d783bf66f7bc54503e5464825259c462682fb980769` |
| blackbox_cache_coverage_non_regression_gate_r1.py | `98faa2945ff9b056936ac87b5e39be87a1adf618120805c2f96e269169798fd3` |
| blackbox_data_access_resolver_r1.py | `5d232abbded4043426a51b57b45afa3d799152c368f7b235a4fff2d9cb26c8d6` |

## 可用（有范围请求）

| 请求 | 条件 | 结果 |
|------|------|------|
| `STOCK_DAILY_PIT_R1` + `--start-date` + `--end-date` | 提取 OK、日历可读、请求交易日 ⊆ 数据日集 | `coverage_ready=true`，`coverage_scope=BOUNDED_WINDOW_VERIFIED`，附注「仅该窗已验证；非全历史/非证券全量/非因果回测」 |
| 实测正例 | `2026-09-02`..`2026-09-10` | ready（本机 Cache 实测） |
| 其它 `SUPPORTED_DATE_PRODUCTS` | 同上双端点窗 | 同样按日集 ⊆ 判定 |

## 仍拒绝 / 未证实

| 情况 | 结果 |
|------|------|
| 无请求窗 + 无独立应有范围权威 | `full_history_status=UNPROVEN`，`coverage_ready=false`，`historical_ready=false`（`DAILY_HISTORY` 不许可无范围） |
| 只有一个端点 | `BOUNDED_WINDOW_REQUIRES_BOTH_ENDPOINTS`，ready=false |
| 有窗但缺日（如 `09-01`..`09-10` 缺 09-01） | ready=false + `missing_trade_days` |
| 日历异常（有窗/无窗权威路径） | 错误传播，ready=false；不吞成 DAILY_HISTORY+ready |
| `FULL_HISTORY` | 本轮生产无独立权威 → **不输出 FULL_HISTORY**；仅 fixture 权威可证 |
| `CACHE_RELEASE_PUBLISHABLE` | 集合保留 OK ≠ 可发布；全历史未证 → `REJECT_FULL_HISTORY_UNPROVEN` |
| UNVERIFIABLE / UNSUPPORTED | ready=false |

## 调用方须分清

- `FULL_HISTORY_UNPROVEN` ≠ 提取失败  
- `BOUNDED_WINDOW_VERIFIED` ≠ 全历史 / 证券全量 / 因果回测许可  
- 未部署生产；`COPY_AUTHORIZED=false`
