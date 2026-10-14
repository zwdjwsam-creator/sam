# ZHANGWEI 报告

task_id: R9_DESKTOP_FIX_BENCH_DIRECTORY_CLOSURE_20261014_1616
execution_host: ZHANGWEI
SAM: HOLD
status: HOLD_PENDING_CODE_REVIEW

COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
bench_measured=false
full_plan_acceptance=false

## 结论

统一执行入口保持接通。本轮只修了代表子集的目录闭合。新子集的 108 条链接都有目标，父链也在，链接路径没有被登记成普通目录。没有创建 `E:\R9_FORMAL_PILOT_1G_20261014`。

## 修之前的只读统计

对象是 1518 留下的 `BENCH_SUBSET.sqlite`，mode=ro。不是用小样例代替这 3715 条。

- 缺目标目录：3696
- 缺链接父目录：701
- 缺目标父目录：701
- 链接路径被登记成普通目录：7
- 源目标类型：普通目录 36，另一条链接 3298，文件 1，未知 380

例子在 `DIRECTORY_CLOSURE_AUDIT.json`。

## 修之后

实体选择没变：仍是 5032 个实体，唯一内容 1073739240 字节。目录从 1023 变为 754，因为补上了真正的目标目录，同时不再把链接路径写成普通目录。

链接从 3715 变为 108：

- 36 条源目标本来就是普通目录，已写入该目录和父链。
- 72 条源目标是链接，但能在不增加文件字节的情况下走到普通目录，已纳入。
- 3226 条链接链不能在预算不变时闭合，排除。
- 397 条目标是文件或未知类型，排除，没有造普通目录。
- 382 条目标文件过多，712 条超出剩余字节，排除。没有为闭合去复制整份 release。

新子集 SHA256 `20843e97b90557b947823c9ecbe01679876c3d56be18fe31e1d36952c1381b6a`。写前审计和重建后审计都是 missing_target=0、missing_ancestor=0、link_as_dir=0。验收里悬空目标会得到 `DANGLING_TARGET`，即使链接文字匹配。

## 本机命令

合同 SHA 前缀 `96fb1474191c`。

- dry-run 子进程 14044，退出 0，写入 0，审计通过。
- execute 子进程 4344，退出 3，`REFUSED_BEFORE_WRITE`，写入 0。

code_digest `0ce471dd661789558754d92f0c1af0aca249a50146bbfa152dc470d621095cd6`。

## 测试

`test_r9_directory_closure` 使用生成器的 `directory_chain`：空目录目标留在目录清单里，链接路径不在其中；删掉目标后预检返回 `LINK_CLOSURE`；隔离执行会创建该目录并可观察为目录；悬空目标验收失败。`test_r9_formal_chain`、`test_r9_close`、`test_r9_strict` 通过。

没有删除 `E:\R9_CAPABILITY_PILOT_20261014\NORMAL`。那项旧断言仍会失败，与这次目录修复分开。

源范围和冻结之后是否变化，仍留到正式开工核对。这次没有把目录修复说成全源已确认。
