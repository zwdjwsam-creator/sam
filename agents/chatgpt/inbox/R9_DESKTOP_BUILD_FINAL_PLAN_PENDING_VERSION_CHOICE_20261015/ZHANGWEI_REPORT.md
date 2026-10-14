# ZHANGWEI 报告

task_id: R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015_0725
execution_host: ZHANGWEI
SAM: HOLD
ACK: agents/chatgpt/inbox/R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015/ACK.md commit 17ff593fff94
decision_id: R9_USER_VERSION_CHOICE_AS_IS_20261015_0727

SOURCE_RECONCILE_REVIEW_ACCEPTED=true
VERSION_CHOICE=AS_IS_MIGRATE_MARKED
VERSION_CHOICE_CONFIRMED=true
COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

## 候选

新候选只在 C：`C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015\FINAL_CANDIDATE.sqlite`
SHA256 `23074f64d1d60297a320cbe695ae96f40863b8974965591c0e93caab41054b5c`，6025408512 字节。quick_check=ok，WAL=0。6GB 没有上传。用户选择方案 1 之后，侧表已从 PENDING_USER 改为 AS_IS_MIGRATE_MARKED，所以上一版候选摘要 `341d7b19afcf95c852050d2bd8042d51f454a35b57280ca39d2f6b124f4a9786` 作废。

原计划复制前后都是 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`。旧候选 e6c49 没有改。

| | 原 94e6 | 新候选 |
| --- | ---: | ---: |
| 普通文件路径 | 8715067 | 8715026 |
| 普通目录 | 233660 | 233660 |
| 重解析 | 4825 | 4824 |
| 实体 | 1223721 | 1223721 |
| 唯一字节 | 365007198749 | 365004408054 |
| 链接 | 4825 | 4824 |

唯一字节减少 2790695，等于 140 个文件从旧合计 2790949 字节改记为实测 254 字节。path_count 不一致为 0。静态检查 outside_paths=0。

## 140 与 42

140 条按 SAM 实测写入侧表 suspect_version_140：当前大小合计 254，身份与证明一致。用户已选方案 1，侧表版本选择是 AS_IS_MIGRATE_MARKED。accepted_as_correct_version 仍是 0：纳入候选并标记异常，不表示内容正确，也没有恢复旧内容。

42 条 junction 视图已从普通文件路径里去掉，实体仍由普通代表保留。处置全部是 REMOVED_DUPLICATE_JUNCTION_VIEW。没有在 junction 下新建硬链接。

目标修复重放了既有 overlay 3694 条，SHA 仍是 `079537ac33b5b7bc3a9001c32c78eff0788ce5affe6f7d493402dcb8a651ea0e`。JSON CLEAN 路径改为 ASOF 文件的目标别名，不是新的来源文件。1130 条原直达边没有改目标。缩短后有 96 条目标落在 `E:\BLACKBOX_ENGINES\...`，它们对应的 `D:\` 库存路径都是普通目录。

## 52 条没有补进候选

对 51 条新增和 mcp.json 做了只读打开，没有读文件内容。52/52 都是 WinError 1326（现有来源会话登录失败）。没有新建登录，没有改凭据，没有把缺字段填 0，没有把 mcp 930 改成 1201。这 52 条是当前技术阻塞，不是已完成的元数据。

## 执行链

只改了 `r9_formal_chain.py`。正式计划的写闸只接受当前这一份候选 SHA，不接受任意计划。BENCH 仍绑定原 94e6。COPY_AUTHORIZED 不是 true 时闸门关闭。

代码摘要 `7435b253e49bec9fe9a605afa7425477d3f822bbfeade4cc7d0048f763dc5a43`。写闸只接受当前候选 SHA。版本选择已是 AS_IS_MIGRATE_MARKED，但 COPY_AUTHORIZED=false，所以闸门仍然关闭。
绑定测试 3/3。既有 `test_r9_formal_chain.py` 3/3。

合同 `FINAL_PLAN_CONTRACT.json`。dry-run：plan_audit ok，gate_open=false，write_calls=0，full_plan_acceptance=false。
未授权 execute：拒绝于写入前，退出码 3，write_calls=0。C 盘出现拒绝用的 state\candidate.sqlite，没有目标写入。

只读目标核对：磁盘 `eui.E8238FA6BF530001001B448B42E694AE`，NTFS 卷序号 3630886530。`E:\BLACKBOX` 和 `E:\BLACKBOX_ENGINES` 都不存在。没有格式化，没有删除旧试验。

## 还不能开始迁移

1. 52 条新增/变更元数据因 WinError 1326 没有进入候选。补充决定之后又探测了一次，仍然是 1326。需要已有会话恢复后补探测，不能由本机新建登录。
2. 来源扫描稳定性和历史内容一致仍是 UNPROVEN。邮箱是活动目录，扫描之后还可以变。
3. 旧计划没有历史 mtime/内容哈希，USN 锚点仍是 ABSENT。140 的本次 mtime 和 SHA 只在侧表。
4. 目标根目录还不存在。本轮指令禁止格式化。这次版本选择不是复制授权。

准备停止，等审核。SAM 本轮 HOLD。
