# 正式运行目录阶段停止｜核对失败路径并修补缺失目标根

task_id: R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015_1400
execution_host: ZHANGWEI
SAM: HOLD_SOURCE_UNCHANGED
status: READY
FULL_MIGRATION_AUTHORIZATION: CONTINUES_WITHIN_ORIGINAL_SCOPE
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
reason: CODE_FIX_REVIEW_BEFORE_RESUME

## 已查HUB
1117进程15872已退出，exit=4/PHASE_STOP，CreateDirectoryW error3；directories_done=41，entities_copied=0，write_calls=42；last_done=E:\BLACKBOX\配置，E:\BLACKBOX_ENGINES不存在，未重启。
旧STARTED的PRECHECK_RUNNING已过时，用户必须知道实际STOPPED。不能继续显示在跑/无错误。
保留旧1117 state、日志及41目录，不重启同一旧命令、不删除、不格式化。

## 独立可复现缺口
当前已审chain._directories(FULL)只取reader.iter_directories映射列表排序，没有保证已批准两个目标根在列表中。
最小FULL夹具：
files=[(D:\data\one.txt,4)]
dirs=[E:\BLACKBOX,D:\data]
links=[]
inspect_plan返回ok=true；实际_directories输出：
E:\BLACKBOX
E:\BLACKBOX_ENGINES\data
漏了E:\BLACKBOX_ENGINES。单级CreateDirectoryW必然无法在缺根时创建子目录。
这是独立隔离复现；1117第42次真实API的准确path需本机核对后对应，不能无证据编造。

## 一次修复范围
1. 先ACK，确认15872及同run确无执行进程，不因进程不存在自动重跑。只读查C日志/state并枚举C候选的目录映射前几项，定位41个DONE后实际下一路径与缺父链，记录失败源路径/目标路径/父目录是否存在；不用扫描来源或整个E。
2. FULL生成正式目录序列必须包含批准的E:\BLACKBOX与E:\BLACKBOX_ENGINES两个目标根，映射后统一大小写去重、父先子后。只能加入批准的目标根，不用全路径递归mkdir绕过清单缺父目录审计，不创建reparse对象当目录。
   正式audit须检查实际输出目录序列依赖闭合，不能仅用known_roots兜底而执行器从不创建根。BENCH行为不扩大。
3. 同时检查独立验收：当前r9_acceptance.full_acceptance的expected目录来自reader.iter_directories，observed roots来自run.acceptance_roots，且extra计数严格比较。若只在chain额外创建engine根，会被当unexpected/EXTRA；需使批准目标根的expected与实际目录生成一致，保持普通未知对象/错误类型仍拒绝。不得靠忽略所有extra/禁用验收放行。
4. 增加一个真实语义隔离后端：CreateDirectory只允许父目录已存在、已有file/reparse冲突拒绝，重现“无engine根+有D子目录”的完整FULL execute；验证两个根都创建、D实体实际走UNC、验收通过。正常第二次恢复不重复制，不把VirtualSyscalls无父检查的成功当真实目录语义。
   覆盖目标根已存在正确普通目录的幂等、根为file/reparse拒绝、真正清单缺非根父目录仍拒绝。仅临时C隔离验证，不做新的真实BENCH，不写E。
5. 修复后更新15模块完整digest（如新增模块须纳入），提交精确diff/代码/测试。候选SHA53551d…、内容预算365004696055、来源/目标/新卷2694002743/物理盘eui.E8238FA6BF530001001B448B42E694AE均不变，不重建6GB，不修改源数据、账号或网络。
6. 代码digest改变不能偷偷篡改旧1117 run_bind来“沿用DONE”。本次实体复制为0，仅41个正确目录，准备新run_id R9_FULL_RESUME_AFTER_ROOT_FIX_ZHANGWEI_20261015_1400与新C state，保留旧state不可改。已存在41目录经类型/祖先验证后幂等复用，不能删掉重做。新合同暂copy=false交ChatGPT技术复核；用户原全量授权持续有效，不再向用户问启动许可。
7. 增补失败错误包含当前path及原始WinError，避免未来仅有通用CreateDirectoryW failed。若需要小范围异常上下文，只改本故障相关，不新建监控系统或广泛重构。
8. 回传后停止等ChatGPT技术复核，随后将依据原授权发准确新digest/run/state恢复启动令。不自行恢复旧copy=true合同、不自动无数次重试。

## 交付
agents/chatgpt/inbox/R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015/
ACK.md、ZHANGWEI_REPORT.md、ACTUAL_FAILURE_PATH.json、CODE_DIFF.patch、完整CODE_HASHES、变更模块、针对性测试结果、FULL_RESUME_CONTRACT.json。
旧1117报告可补ZHANGWEI_EXECUTION_REPORT说明真实停止时间/实体0/目录41，保留PROGRESS原证据。
更新INBOX_FOR_CHATGPT为本任务实际ACK/修复完成状态。主邮箱旧1155 READY被本任务替代，不能重放旧启动令。
