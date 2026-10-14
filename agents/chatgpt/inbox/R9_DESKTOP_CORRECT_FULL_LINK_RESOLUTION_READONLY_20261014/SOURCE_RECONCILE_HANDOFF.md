# 来源一致性核对交接

SOURCE_CURRENT_MATCH=NOT_RUN。这不是已完成的来源核对。

## 已纳入集合

- E：只核 `E:\BLACKBOX`。目标同路径。
- D：只核冻结计划里出现的路径，不是 9 棵完整一级树。文件路径数与 SCOPE_GAPS 一致。`CURSOR_TASK_ARCHIVE` 只有 `JQ_DAILY_20260903_SUCCESSOR_BUILD_AND_ATOMIC_PUBLISH_R1\pit_products`，18 个文件路径、16 条 D junction。
- 历史范围在 HUB `agents/chatgpt/inbox/R9_PILOT_FIX_20261011/R9_SAM_MIGRATION_SCOPE.json`。里面的 `F:\BLACKBOX_ENGINES` 和旧卷不是当前目标。`needs_user_decision` 是 2026-10-11 的历史建议，不能扩大范围。

## 链接图

修正解析后 4824 条终点是计划内普通目录，1 条终点是文件 `CURRENT_POINTER_COPY.json`。没有把超长链算成缺失。
Windows 跟随不是这次的全量证明。一个 64 跳代表跟随打开返回 WinError 1921（系统无法辨识文件名）。那条文件终点的跟随打开返回 WinError 267（目录名称无效）。

## 仍缺

- USN JournalId / 起止 USN = ABSENT。
- 计划没有历史 mtime 和内容哈希。
- 下一轮若要证明来源没变，在 SAM 本机对上述准确范围做 no-follow 枚举。不要从台式机经 SMB 打开 871 万条路径。
