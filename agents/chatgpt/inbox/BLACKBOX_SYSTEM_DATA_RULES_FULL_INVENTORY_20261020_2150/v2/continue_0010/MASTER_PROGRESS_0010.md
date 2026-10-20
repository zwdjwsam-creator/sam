# CONTINUE_0010_PROGRESS

status: **PARTIAL_CONTINUE_WITH_CHECKPOINT**
worker_pid: 39980
elapsed_sec: 396.4
parser_v3_pass: True
broken_confirmed_v3: 1551
edge_status_counts: {'RESOLVED': 1087, 'BROKEN_CONFIRMED': 1551, 'LEGACY_HOST_SPECIFIC': 13, 'DYNAMIC_OR_PLACEHOLDER': 28, 'NOT_A_PATH': 15, 'EXTERNAL': 6, 'SECRET_PATH_REF_NOT_READ': 26}
products_denominator: 75
queue_status_counts: {'VERIFIED_PARTIAL': 67, 'VERIFIED_WITHIN_DECLARED_SCOPE': 4, 'NOT_IN_MAIN_CACHE_ROOT': 4}
probes_written: 53

## 口径
- 主 Cache 缺失 ≠ 丢数据（NOT_IN_MAIN_CACHE_ROOT / sidecar / clean）
- DYNAMIC/<asof> 不进 BROKEN_CONFIRMED
- 日线按 year 分区抽样

local: `E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010`
