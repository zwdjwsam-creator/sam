# ZHANGWEI 报告

task_id: R9_DESKTOP_CORRECT_FULL_LINK_RESOLUTION_READONLY_20261014_2157
execution_host: ZHANGWEI
SAM: HOLD
status: HOLD_PENDING_LINK_RESOLUTION_REVIEW

CORRECTED_AUDIT_COMPLETE=true
FULL_LINK_GRAPH_CLOSED=false
WINDOWS_LONG_CHAIN_STATUS=ONE_REPRESENTATIVE_WINERROR_1921
SOURCE_CURRENT_MATCH=NOT_RUN
full_plan_acceptance=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

生产代码摘要前后都是 `a1ce1ae5e2d0490d6b6c415917200f7c84bb502d9befb397a38fe974e43e5bfd`。计划 SHA 前后都是 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`。没有改生产代码，没有改计划，没有删链接，没有复制，没有写 E。

## 修正

离线解析使用正式 reader 的目录和链接映射。已经落在 `E:\BLACKBOX` 或 `E:\BLACKBOX_ENGINES` 的路径直接当目标，不再送回 `map_inventory_path`。父级 junction 会带上剩余后缀继续解析。循环按完整路径识别。保护上限 4096 步，触顶记为 UNRESOLVED_RESOURCE_LIMIT，这次没有触顶。

6 项离线测试通过。70 步有限链能到普通目录。旧的 8/32 跳截断会把这种链报成 hops。

## 4825 条重算

分类合计 4825：CLOSED_DIRECTORY 4824，TARGET_FILE 1。CYCLE、MISSING_TERMINAL、SCOPE_ESCAPE、UNRESOLVED_RESOURCE_LIMIT 都是 0。
最长链 64 步。超过 32 步但仍闭合到目录的有 1007 条。这些不是坏链接。
唯一问题组：1 条 junction 的终点是文件
`E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_ADJFACTOR_PIT_ASOF_20260814_20260816_034243\CURRENT_POINTER_COPY.json`。
来源链接是同名 `CURRENT_POINTER_COPY.json` 的 CLEAN release。不建议删除或摊平。它不应当被当成目录终点。

本机全量记录 `LINK_RESOLUTION.jsonl` SHA256 `03318d69ce1db041b34c314e3c2b8244df6fa92efe8341916e7162386c45ef82`，2881815 字节。

## Windows 跟随

只探了 2 个代表，没有读内容，没有重试。
文件终点那条：no-follow 看到重解析点；跟随打开 WinError 267，系统文案是目录名称无效。
64 跳代表 `BILLBOARD_DAILY_PIT_R1`：no-follow 看到重解析点；跟随打开 WinError 1921，系统文案是系统无法辨识文件名。
这不是全部 1007 条长链的测量，也没有编造跳数上限。数学上闭合和 Windows 能否跟随是两件事。

## 范围

纳入集合仍以冻结计划为准。HUB 上的 `R9_SAM_MIGRATION_SCOPE.json` 把目标写成历史 `F:\BLACKBOX_ENGINES`，不能当现在的目标。`needs_user_decision` 不扩大范围。USN 连续锚点仍是 ABSENT。SOURCE_CURRENT_MATCH=NOT_RUN。

全量未授权。等待审核。
