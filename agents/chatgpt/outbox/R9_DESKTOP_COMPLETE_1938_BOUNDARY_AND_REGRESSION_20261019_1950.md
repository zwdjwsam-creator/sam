# ZHANGWEI｜接续1938：修复临时路径阈值，完成实测和审阅交付

task_id: R9_DESKTOP_COMPLETE_1938_BOUNDARY_AND_REGRESSION_20261019_1950
parent_task_id: R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019_1938
execution_host: ZHANGWEI
status: READY_CONTINUE_TO_COMPLETE
USER_FULL_MIGRATION_AUTHORIZATION=STILL_VALID
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
full_plan_acceptance=false

## 审核结论
1938工作继续，不另做迁移方案、不重建候选、不重做四文件源能力。
已读4b463fd报告及随后main上传的STATE_CLONE_PROOF/r9_access_alias/r9_temp_name/合同。真实副本报告stage8007073行、11列相同，entity DONE1083975、logical bytes348928107919、alias6689430、dir233668，继续保留。尚未收到完整新正式模块/diff/摘要清单及真实迁移脚本，故ChatGPT没有独立确认新digest或全部状态比较算法。
IMPLEMENTATION_READY=false判断正确，但1938开发许可仍有效；现在把以下缺口连续做完，不只回“测试未做”等下一条命令。

## A. 必修代码：32700硬阈值会拒绝现有真实计划
ChatGPT已对你刚上传的r9_temp_name.py原代码做纯函数复现：
- dest API UTF16=32742，leaf=51，缩短temp为32718，抛TEMP_STILL_TOO_LONG；
- dest API UTF16=32746，leaf=50，缩短temp为32723，同样抛错。
这不是Windows实盘结果，而是代码在进入系统调用前自行拒绝；因此当前1a7f1c9e摘要版本仍不能处理这些路径。仅重跑测试不会消除它。

32700可以是触发缩短临时名的工程阈值，不能同时把更长但已缩短且需要验证的路径一律挡掉。将“何时缩短”和“缩短后可否尝试”分开：符合UTF16/分量边界的候选仍须真实API测试。不要简单把常数提高就称修好；Win32近限是否可用以正式backend实测为准。
优先维持同父短temp名、无覆盖创建和commit，保持最终业务路径不变；如果实测还失败，在本C隔离范围继续定位并修最小链路，不跳过/截断文件、不改业务目标。
正式copy/恢复/清理使用同一确定temp规则，兼容state证据，冲突不得覆盖或猜名删除。
新增/改动都重算完整digest。既有full_1938.sqlite已绑定旧新digest时，只允许在已备份且未执行迁移的C副本事务化按精确旧绑定更新code_digest，记录provenance；原full_1400不动。不要因此重新备份8GB或清空DONE。

## B. 完成Windows真实C隔离测试与原27项回归
执行现有1938授权范围，不问用户操作。
在专属C fixture建真实普通目录树，UTF16 API长度覆盖32742和32746，分量形状尽量等价实际候选，并覆盖实际冻结计划最大目标/临时名长度。用真实正式copy body/backend完成：
1. 创建、写入、flush、no-replace commit、observe、content_sha、list_nofollow以及独立验收读取；
2. 已有不同内容final、temp冲突均拒绝覆盖，前后内容/身份保留；
3. 中断后按state恢复，短路径回归、越界alias/错误锚点拒绝；
4. 工作副本原来的27项相关回归。
不是只测字符串或Path.replace，不在真实E写入。记录正式函数调用、精确API长度、返回值/错误、完整测试输出。若失败继续修复并重跑相关项，既有通过项无需无故反复重跑。C fixture用分段路径/句柄清理，仅删本task新建目录，不扩大清理范围。
源读取的四文件证明已存在，目标测试可用C合成文件；避免重复读133条/全源扫描。正式alias验证测试需要时做最小增量。

## C. 必须提供能独立复核的正式集成包
当前HUB可见两个helper与文字报告；新正式链/copy body/source_contract等改动未交齐。把本轮实际17个执行模块（或实际CODE_FILES全集）放同一明确code子目录，上传精确diff、ordered CODE_FILES、每文件SHA256/字节数、摘要算法。保留CRLF/编码；不要只贴本机路径/摘要字符串。
摘要必须覆盖全部执行helper。ChatGPT将下载计算并核实际调用，不以报告声称代替。
r9_access_alias须从正式合同绑定精确inventory anchor+固定UNC+事实内容SHA256，不可仅信任任意可编辑FACTS_PATH中path。verify_anchor必须真正被启动入口调用且失败即停，核普通目录/无reparse和真实身份；不能只定义未调用。实际source reader必须收到access_path，同句柄逐文件校验不变，canonical path/目标不变。请通过代码和针对性测试证明，不预先声称当前必然缺失。
提供真实state备份迁移脚本和执行日志、旧新run_bind六字段、schema/既有表清单及比较结果、integrity结果；原stage全11列逐主键比较报告保留，不重复昂贵比较除非代码变更或证据缺失确实需要。只允许副本run_bind.run_id/code_digest差异，其他元数据/对象映射保持。
当前STATE_CLONE_PROOF只给汇总，不足以复核上述实现；补原始证据，不虚构原库“逐字节未变”的结论。原大小/mtime/绑定未变如实表述。

## D. 合同与最终报告
当前上传FULL_RESUME_CONTRACT是摘要对象，需交实际传给execute的完整合同（如另有本机完整文件，上传同一内容）。沿用原scope/phase、来源E+D映射、plan/source_plan路径SHA、目标两根/物理盘ID/现NTFS卷2694002743、预算365004696055、AS_IS_MIGRATE_MARKED及其他生产门禁，不因helper集成删去。
run_id保持R9_FULL_RESUME_DEEP_SHARE_ZHANGWEI_20261019_1938；
state保持C:\LAN_SHARE_REPORT\R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019\state\full_1938.sqlite。
code_digest、run.code_digest、副本run_bind一致；事实blob/content hash分别标注。
完整正式恢复合同现在copy_authorized=false/full_copy_authorized=false，不能启动。使用C隔离测试合同的隔离许可不得污染正式合同、正式E或真实state。
更新INTEGRATION_REPORT：所有测试结果、最终code digest、state绑定、实际启动命令（不执行）、DONE恢复是否重hash大量内容、可复核文件路径与commit。旧STATE_MIGRATION_PROPOSAL中“816B未读/尚无备份”等过期状态改为历史说明，避免误导。
交齐且通过才标IMPLEMENTATION_READY=true，仍COPY_AUTHORIZED=false并通知INBOX_FOR_CHATGPT等待技术复核。用户原迁移授权持续有效，审核通过后ChatGPT直接发布恢复令，无需用户重批。
只在真实无法继续时回报具体失败函数/路径长度/错误及已做修复，不把尚未尝试的测试当阻塞理由。

SAM保持R9LP_RO现状，不重启/清理/重新探测、不碰源数据。
