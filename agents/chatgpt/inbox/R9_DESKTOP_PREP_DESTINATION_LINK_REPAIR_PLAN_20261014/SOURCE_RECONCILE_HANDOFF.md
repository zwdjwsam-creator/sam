# 来源一致性核对交接

SOURCE_CURRENT_MATCH=NOT_RUN。

## 三层不要混

- 来源基线仍是冻结计划 SHA `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`。原链接和原文件都还在这份计划里。
- 目标修复是另一层：目录链 overlay SHA `079537ac33b5b7bc3a9001c32c78eff0788ce5affe6f7d493402dcb8a651ea0e`，以及 JSON 指针改成既有文件的目标别名。
- 候选计划 SHA `e6c49ecdf925c923351267883db7bfb2cf83ed7e02f2038ec4bd997ef2f43be2` 只在 C 盘。来源若有变更，要按同一规则对新的来源基线重放，不能把这份候选当成来源已经冻结。

## 下一轮 SAM 本机

对 `E:\BLACKBOX` 和已选 D 子树做 no-follow 枚举。`CURSOR_TASK_ARCHIVE` 只含 pit_products，18 个文件路径和 16 条链接。没有 USN 连续锚点。不要从台式机经 SMB 打开 871 万条路径。
