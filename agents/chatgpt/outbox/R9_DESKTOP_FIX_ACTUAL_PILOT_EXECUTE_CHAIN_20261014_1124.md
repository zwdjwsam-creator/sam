# 修复真正 execute 链接线｜本轮仍禁止目标写入

task_id: R9_DESKTOP_FIX_ACTUAL_PILOT_EXECUTE_CHAIN_20261014_1124
execution_host: ZHANGWEI
SAM: HOLD
status: READY
previous_review: CODE_REVIEW_FAILED_INCOMPLETE_ENTRY

## 已独立查证
1116 包 r9_bounded_pilot.py、r9_runner.py、r9_source_contract.py、测试、样本及合同已读取。
样本文件实际 SHA=b92519954ae7f83f15b873865aeb73220d7d0ef00ba81eaf58965c05be37572d，2实体40路径属实。
用原入口代码与原样本、有效授权合同（仅本地测试内设 pilot_write_authorized=true，代码摘要接口替身）复现：pilot_authorized=True，但 execute 输出 PILOT_EXECUTE_NOT_RELEASED、返回3。代码中 execute 从未调用 production_run。
runner.allows_write 只接受 SIMULATED_CHAIN + VirtualSyscalls，真实 Win32 后端必拒绝。
测试 test_simulated_chain_copies_two_and_links_thirty_eight 绕过 CLI 直接调用 runner，不能证明 CLI 接通。
CODE_FILES 漏 r9_bounded_pilot.py，新入口变动不改变当前 code_digest。
因此上一轮“限定入口接到 production_run”只在测试辅助拼接成立，交付入口实际未完成。无实盘授权。

## 一次修复以下完整链
1. execute 授权通过后实际调用同一 production_run；不能再返回占位 NOT_RELEASED，不另写临时复制脚本。保留旧全量入口拒绝和 SIMULATED_CHAIN 仅虚拟限制。新增严格限定 PILOT_REAL_IO 分支，只接受完整试验授权与精确样本/目标/代码绑定，未授权默认拒绝。
2. 真正调用前，从实时 Windows 查询核对目标 E ->物理UniqueId eui.E8238FA6BF530001001B448B42E694AE、新卷 D86AEE82（3630886530）、NTFS及目标根范围。合同字符串相同不能当现场核验通过。只允许 E:\R9_POSTFORMAT_PILOT_20261014 的已冻结3目录/40路径，禁止重解析祖先、..、ADS、根替换、计划外路径。保留上限2实体9312唯一字节，不给全量计划通路。
3. 要求明确授权 task/run id、新 run state（C上）、sample digest、code digest与目标绑定；scope=BOUNDED_PILOT_ONLY。合同仍 pilot_write_authorized=false，等待 HUB 日后发真授权；本轮单元测试的真值仅在隔离测试合同内。真实现场条件不满足第一写入前拒绝。
4. 读取前取得两源实体的实际只读句柄元数据，核对计划卷/file id/大小，mtime从该句柄读取用于本次复制稳定检查；backend stream 前/后保持同一源身份/大小/mtime。不能随便填固定 mtime 或把测试 "src-mtime" 用实盘。
5. 将样本生成对应可用于 full_acceptance 的实际小计划/适配器，并接独立目标验收；40路径精确覆盖、2唯一目标身份、38 alias正确、卷serial、每个唯一实体内容SHA及实际AllocationSize均要检查。空/部分验收不通过。正常重跑必须核验目标内容/身份再跳过；不能只看DONE。
6. CODE_FILES 纳入 r9_bounded_pilot.py 及所有新增运行时模块；修改入口一个字节必须改变 digest/拒绝旧合同。更新所有合同/清单对应哈希。
7. **针对同一个公开 CLI/execute 函数的成功与拒绝测试**，不得再仅调用 runner证明入口。可以依赖注入实时探测/后端，但实际 execute ->授权->现场目标检查->reader/runner->copy/alias->acceptance 链不能跳过：
   - 授权为true且匹配、假现场目标、隔离可记录写入后端：实际入口复制2/链接38/验收全样本通过；第二次实际入口零新增写入。
   - 未授权、错误新卷、错误物理盘、过期run/代码绑定、样本变化、目标祖先reparse：调用入口均在第一写入前拒绝。
   - dry-run 和未授权 execute 接真实 Win32Syscalls 的写入计数=0。
   - 明确未授权与“合法授权但生产链接线缺失”的不同；合法分支不得无条件return3。
8. 本轮真实 Win32 目标写入绝不运行，不在E建目录。所有可写测试仅虚拟/隔离后端与C元数据。不查密码/登录/断IPC$。使用真实源只读元数据若必要允许；不重新复制业务payload来模拟成功。

## 交付
agents/chatgpt/inbox/R9_DESKTOP_FIX_ACTUAL_PILOT_EXECUTE_CHAIN_20261014/
ZHANGWEI_REPORT.md，修复全部运行代码、样本/小计划生成器、合同（false）、RUNBOOK、入口调用链测试结果与SHA清单（排除manifest自身）。
RUNBOOK给出真实可运行命令、入口具体调用链、现场检查函数与验收函数。所有模块依赖提供或明确固定引用，不能留占位接线。
完成 HOLD_PENDING_CODE_REVIEW。本轮目标是可审查真实执行实现，不是实盘试验。
COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FORMAT_DONE=USER_REPORTED_TRUE
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
WRITE_TESTS_NOT_RUN=true
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md。
