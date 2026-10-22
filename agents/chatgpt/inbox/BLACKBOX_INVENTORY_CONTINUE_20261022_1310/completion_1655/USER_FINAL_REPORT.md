# 数据管理追加回执（1655）— 迁移映射定点定位

时间: 2026-10-22T17:01:30+08:00
reply_to: tip_1655
SYSTEM_INVENTORY_ACCEPTANCE: **false**
基于: completion_1635（账本修正批次本轮接受关闭，不重做）

## 映射方法
- 冻结候选: FINAL_CANDIDATE.sqlite SHA=53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d（与合同一致）
- query_only；paths 表 PK exact + prefix LIKE；不建索引/不改 state/不整库 hash
- D→目标规则证据: test_full_mapping.py L26-L33（D_DRIVE → E:\\BLACKBOX_ENGINES\\<rel>）

## A. JQ20 任务树
- 历史源: \D:\\CURSOR_TASK_ARCHIVE\\BLACKBOX_JQ20_FULL_DOWNLOAD_PIT_CLEAN_CACHE_HAND_R1- 计划内? **NOT_IN_FROZEN_SCOPE**（D: 与 UNC 变体 exact/prefix 均 0 行）
- 映射计算目标: \E:\\BLACKBOX_ENGINES\\CURSOR_TASK_ARCHIVE\\BLACKBOX_JQ20_FULL_DOWNLOAD_PIT_CLEAN_CACHE_HAND_R1\（当前不存在）
- 解释: **不能**说成迁移丢失；仅表示未进入该冻结计划/已查变体无行
- 影响: JQ20 RAW 脚本/receipt 绑定仍开放；Cleaning/CACHE 先验仍可用

## B. backtest 引擎
- 历史源: \D:\\backtest_lab\\02_blackbox_jq_compat_engine- 计划内? **是**（paths exact 命中；含子路径样本）
- 映射目标: \E:\\BLACKBOX_ENGINES\\backtest_lab\\02_blackbox_jq_compat_engine- 当前存在? **是**
- 静态核验: 顶层含 blackbox_jq_engine / rule_library / PHASE1_*_REGISTRY.json 等；**未启动**；active_proven=false
- 结论: **IN_PLAN_TARGET_PRESENT**；历史 handoff 的 D 路径声明与本轮 E 引擎根实查对齐到映射目标

## 收口
1635 定点账本修正批次接受关闭。本回执仅追加映射定位结果。
