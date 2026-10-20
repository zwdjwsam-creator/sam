# ZHANGWEI｜SQL修复已审；条件满足后只替换验收，不重跑迁移

task_id: R9_FULL_READONLY_ACCEPTANCE_OPT_20261020_0830
parent_task_id: R9_FULL_RESUME_DEEP_SHARE_AUTH_20261019_2037
execution_host: ZHANGWEI
status: AUTHORIZED_CONDITIONAL_COPY_COMPLETE_THEN_READONLY_VERIFY
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
START_COPY_AGAIN_AUTHORIZED=false
STOP_17904_AUTHORIZED=ONLY_AFTER_ALL_PRECONDITIONS_BELOW
full_plan_acceptance=false

这是原迁移/验收目标内的技术处置，不要求用户重复批准。不得把本任务理解为立刻终止仍可能在复制的进程。
先完成C验收副本准备和只读复制完整性检查；只有明确所有复制/链接记录齐全，才可结束旧验收并启动一份优化后只读验收。不需要重新复制，不重绑state，不改原运行树。

## 已审证据及固定版本
已读8cf39c97报告、实际schema/SQLite3.49.1的SCAN s/SEARCH结果、diff、优化模块和合成测试。ChatGPT独立确认：
- 17模块中只改变r9_acceptance.py的MISSING_ENTITY一条SQL；
- 模块UTF8原字节20110，SHA256=0d1f4026d11452a4ad398ed53f5cd83a6d53cc484d5486408995444fb4b0ed6f；
- 使用其余16个27af原模块，按原CODE_FILES算法重算17模块 verifier digest=
9e8c605df4a9cace1d048ffbade85f1b4684571983f88e2c43474058239ecbf0；
- 六种语义合成测试独立重跑通过。正常/缺失/错phase/错parent结果不放宽，畸形item_key更严格拒绝；
- ChatGPT本机5000 plan测试也由SCAN变SEARCH。两机合成耗时不能当百万规模或整轮验收的准确加速比。
此优化解决确定的算法风险；尚未证明旧进程当前正执行该句，不用它解释全部夜间耗时。

## A. 先准备独立只读验收树
在新的C任务目录verifier_code复制当前批准17模块（27af树），只用已审优化r9_acceptance.py覆盖副本，所有原代码树不改。
就地核每文件hash/字节数及上述9e8整体digest；其余16模块与27af原件字节相同。不同就停止回报，不临时加改代码或run_bind。
用该副本跑相关验收回归（严格内容/身份/缺失/多余/alias split等）并确认实际import的是verifier_code，保留输出。不要为过测试改变保护或改生产代码。
批准合同：
agents/chatgpt/outbox/R9_FULL_READONLY_ACCEPTANCE_OPT_20261020_0830_CONTRACT.json
保存本任务C目录FULL_READONLY_CONTRACT.json。
scope=FULL，目标两根/盘/预算不变；全部copy许可=false。
run六字段和顶层code_digest保持历史COPY digest27af138391d66219ebc6d03609cec6933aecfce3aacba48c215d5de9f14b2551；
verifier_code_digest单列9e8，不得为了让校验过而把full_1938.sqlite中的绑定改为9e8。
原state/full_1400和所有源/目标/temp不改，不复制一份空state或重建候选。

## B. 只读确认“复制已齐”，才可停止旧验收
1. 读取当前17904准确创建时间/argv/日志。若已退出且已有完整成功验收，先保存并上报结果，不无故重新验收。若已退出但失败，保存错误，以下不满足就不继续。
2. 核固定候选SHA53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d、当前target NTFS2694002743和物理UniqueId eui.E8238FA6BF530001001B448B42E694AE。
3. 本轮允许对state做一次只读分类聚合，并与冻结计划派生数比较，不是重复轮询。短timeout；用进度handler/合理时间上限避免长持读锁。库忙/无法及时完成就停止本核查、回报，不干预旧实例。
   计划entities COUNT及SUM(min_size)，SUM(path_count)，目标dirs（含两根去重）及link总数应与冻结报告一致：
   entity DONE1223767、entity logical_size合计365004696055；
   file paths8715072，alias DONE7491305；
   dir DONE233668，reparse DONE4824；
   stage其他phase=0，分类及总行数与计划一致。
   同时核没有缺失entity：使用已审按item_key主键的高效只读查询，不运行旧parent_key相关全表查询。保持kind/phase/parent_key条件，禁止只看总数凑齐。
   这项为判断是否可以安全停止当前实例，不代替独立目标验收。若实际冻结计划派生数不同于上述固定值，不自动采用新数，回报具体差异。
4. 核四个近限实体仍DONE、hash/目标身份一致，state原run_bind六字段保持27af历史绑定。记录聚合前后state文件mtime/大小及观察时刻；状态若变化、尚有INTENT/缺项/不同绑定，就不停止、不启动另一验收，回报当前实际进度。
5. 只有以上全部满足，才确认已无剩余复制/链接写入工作；按已审代码执行顺序，此后仅为原full_acceptance。此时授权结束旧验收PID17904。
   结束前再次核对PID创建时间20:47:10、精确argv、最新stdout，防PID复用/刚已成功退出。优先已有正常退出通道；没有合作式退出机制时，允许仅对这一确切PID做本机标准定向终止，不杀进程树、不影响Cursor/SMB，不注入或发送影响其他控制台的全局按键。
   必须等待确认原PID已退出，无其他复制/验收实例，才启动新只读验收。
   记录STOPPED_FOR_OPTIMIZED_READONLY_VERIFICATION，不伪造自然exit_code=0；这是取消旧验收，不是迁移失败或全量重来。保留旧日志和r9acc_临时验收库供查，不复用未提交缓存，不删除任何业务/temp对象。
   结束后只读复核run_bind、state文件mtime/大小及四文件记录未变；若不符停止回报。

## C. 仅调用现有只读验收入口一次
旧PID已退出且B全部通过后，在verifier_code目录运行批准Python312：
C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe <本任务verifier_code>\r9_formal_executor.py verify-existing --contract <本任务C目录>\FULL_READONLY_CONTRACT.json

严禁用execute/copy/production_run代替。verify-existing走既有readonly_reverify + ReadOnlyGuard，业务写方法全部拒绝；原state不重绑、不改数据，工作和临时验收结果仅写C。
已审现有full_acceptance在readonly_reverify时初始state用mode=ro；后续ATTACH虽为普通连接，但现有代码对st.stage只有SELECT，没有任何状态写语句。不得在其上执行索引/UPDATE/PRAGMA修改。保留已审SQL之外的所有验收检查。
此验收读台式机目标与本机冻结清单，不通过SMB重新读取所有笔记本源数据，不再次复制。SHA验收会重新读取目标唯一内容，仍需时间；不承诺完成ETA、不虚报整轮速度。

启动前核C盘余量足够容纳与原全验收同规模临时库。原r9acc_缓存留存会占空间，若不足回报实际余量/文件大小，不自动清理他人文件。
记录实际PID/开始时间/argv、verifier digest9e8、历史copy digest27af、完整合同hash/日志/原PID结束证据；只启动一次此只读验收。
不得并发另起全盘扫描、第二个完整验收或新的复制。若验收退出失败，保留全部结果，只报告，不重跑或改判。

## D. 验收结果字段必须区分历史名称
现有verify-existing包装器名字偏向BENCH，stdout中可能出现：
bench_verified=true
full_plan_acceptance=false（包装器硬编码）
不能把这个硬编码false当实际FULL内容失败，也不能悄悄改写原始stdout为true。

保留原始stdout/exit_code，另交独立FULL判定报告：
- scope必须FULL，固定plan SHA/目标双根/盘/历史run绑定均验证；
- 原始acceptance.full_acceptance=true，reasons=[]、missing=0、extra=0；
- expected_entities=checked_entities=content_hash_calls=1223767；
- content_bytes=365004696055，expected_file_paths=8715072，expected_dirs=233668，expected_links=4824；
- ReadOnlyGuard.write_attempts=0，原state/历史绑定未改，verifier/code输入哈希匹配。
仅全部成立才能在新报告中给full_plan_acceptance=true，注明是FULL独立只读验收的综合结论，非原包装器原始字段。否则false并明确哪个条件失败，不能只依据bench_verified或进程exit0宣布成功。
allocation与logical content不要求逐字节相等，但应交actual allocation/硬链接一致性/alias split、entity merge和所有原reasons结果。
用户选择AS_IS_MIGRATE_MARKED仍有效，空/换行140项不改版本、不删文件，验收不提升为“版本内容正确”。

## 回执
agents/chatgpt/inbox/R9_FULL_READONLY_ACCEPTANCE_OPT_20261020_0830/
ACK.md、PREPARED.json（模块hash/回归/余量）、COPY_COMPLETENESS_CHECK.json、OLD_PROCESS_STOP.json（如实际执行）、STARTED.json、原始stdout/stderr、FINAL_FULL_ACCEPTANCE.json及状态绑定/文件未改证据。
每个分支有事实即更新INBOX_FOR_CHATGPT，不把“已批准条件处置”当“已执行”。本任务不要求用户手工操作或另批继续；条件满足后连续完成准备→停止旧只读验收→启动优化只读验收。
SAM当前继续保持来源共享不变。全部迁移最终验收后再安排明确共享清理，不在本任务删除。
