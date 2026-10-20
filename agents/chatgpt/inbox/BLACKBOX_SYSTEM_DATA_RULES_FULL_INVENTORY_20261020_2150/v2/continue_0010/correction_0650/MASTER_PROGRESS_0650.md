# CORRECTION_0650_PROGRESS

status: **RUNNING_OR_CHECKPOINT**
worker_pid: 40084
elapsed_sec: 0.8
pid39980_exit: NATURAL_END_AFTER_SINGLE_BATCH_BUDGET
parser_v4_pass: True
broken_confirmed_v3_preserved: 1551
broken_confirmed_v4: 847
edge_status_counts_v4: {'RESOLVED': 1132, 'BROKEN_CONFIRMED': 847, 'LEGACY_HOST_SPECIFIC': 13, 'DYNAMIC_OR_PLACEHOLDER': 28, 'RULE_ID_OR_STATUS_UNRESOLVED': 612, 'NOT_A_PATH': 62, 'EXTERNAL': 6, 'SECRET_PATH_REF_NOT_READ': 26}
deep_probes: 55
deep_status_counts: {'VERIFIED_PARTIAL': 55}
denominator_queue_objects: 75  # NOT business-data classes

## 口径纠偏
- 75 = 队列对象分母（含 registry），不是 75 类业务数据
- VERIFIED_WITHIN_DECLARED_SCOPE 中 registry/sidecar 分开计
- 1551 BROKEN_CONFIRMED(v3) 不可当故障数；见 v4 重分类
- 统一 published/generated_at ≠ 每源数据水位（见 WATERMARK_FIELD_PROVENANCE.csv）

local: `E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650`
