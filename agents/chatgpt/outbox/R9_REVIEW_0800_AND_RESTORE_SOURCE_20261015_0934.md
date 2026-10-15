# 0800审核与下一轮：目标冲突校验补齐、恢复来源会话

review_id: R9_REVIEW_0800_AND_RESTORE_SOURCE_20261015_0934
VERSION_CHOICE=AS_IS_MIGRATE_MARKED
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

## 审核事实
已读取4a004ac报告及main补齐的交付代码、合同、GATE_RESULT、SESSION_DIAGNOSIS、合并脚本和SAM LOCAL_52_METADATA/SAM_REPORT。
注意4a004ac时只有报告与ACK；代码等附件在后续main提交，不能把所有交付说成属于4a004ac。
15模块逐文件原始UTF8字节SHA全部匹配，独立code_digest=cddfa2e6bbad0afba633d4afb7f15c5e84224f4662386c24759eda210e7d4a3f。
独立复跑test_full_mapping 6、test_full_closure 6、test_r9_formal_chain 3、test_binding_0725 3，共18通过。审核环境Linux：只为导入提供禁止实际调用的WinDLL替身，屏蔽内存统计，测试临时state路径的C盘检查按Windows临时目录语义适配，runner仍检查声明state与实际state相同。该结果不证明真实Windows API/SMB、C盘路径检查或6GB现场候选本体已经独立验收。
正式_entities确已传shares，E/D隔离读取均走SAM UNC，认可该修复。
SAM 52/52 ok，5目录47文件，无卷号不符/缺身份；merge脚本已审阅。候选53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d仅在本机，6025519104字节；完整统计/该SHA仍是现场报告，未在本审核机重算6GB。
来源会话1326仍未恢复；445可达、Get-SmbConnection拒绝访问不能证明没有可复用会话。历史已有1219/IPC$证据，不能把当前1326直接等同密码错误。

## 仍可复现的结构缺口
audit_full_plan尚未实现0800要求的全部大小写折叠file/dir/reparse冲突检查：
最小夹具paths普通文件 E:\BLACKBOX\a，普通目录 E:\BLACKBOX 和 E:\BLACKBOX\A，无links。
audit_full_plan返回ok=true、collisions=0。Windows同一目录中两者占同一目标名，不能执行。
复现脚本见同目录R9_REVIEW_0800_AND_RESTORE_SOURCE_20261015_0934/reproduce_collision.py。
这不是说6GB候选一定有此坏行；当前collisions=0尚未排除此类目标冲突。

## 台式机ZHANGWEI主执行
task_id: R9_DESKTOP_FINISH_COLLISIONS_AND_RESTORE_SOURCE_20261015_0934
status: READY
先ACK，只继续本轮，不重复扫描/旧复制试验。

1. 补齐FULL统一目标命名空间校验：所有来源路径先按reader同一映射得到实际目标，再统一分隔符和大小写；普通file与dir、file与link、dir与link、不同实体映射同目标、大小写路径重复均须检查；合法同一reparse的paths/links成对行只算同一对象，不能当成冲突。普通路径不能穿实际目标reparse祖先。保留文件流式处理，可用C盘临时SQLite索引，避免将数百万文件装入Python字典。补最小夹具和合法对照；沿实际FULL映射测试，不以BENCH代替。
2. 不变更候选内容、不再复制6GB；修代码后重算完整15模块digest并更新合同，仍COPY_AUTHORIZED=false。当前候选按来源现状、140异常标记保持，不再等待版本选择。对同一冻结候选一次完成完整审核并输出各类冲突计数，若有实际冲突停止并列具体项，不擅自删改来源/计划。
3. 来源认证恢复采用已有明确授权：agents/chatgpt/outbox/R9_DESKTOP_REUSE_SMB_CREDENTIALS_20261013_2222.md。上轮0800只读诊断的“不新建登录”限本轮撤销为该已授权范围；允许复用已存在会话/保存的来源网络凭据，并通过本机内存非交互SMB API连接，不需用户重新输入密码。不扫无关秘密、不读SAM/LSASS、不重置密码、不建账号、不启Guest、不降低策略、不改变网卡/路由/防火墙/分享ACL。
4. 先查已有2222的回报和现有认证状态，不盲目重跑历史尝试。在真正迁移会使用的同一Windows用户/提权/登录会话上下文中验证来源；普通登录上下文可读而Agent不可读，明确两者差别并优先在可复用的授权上下文执行只读探测。不把Get-SmbConnection AccessDenied当无会话，可用当前net use或WNet查询。仅经证实指向SAM的保存凭据，每一不同已证实记录最多一次；已经尝试失败且记录未变的不要重试。遇1219先列出具体冲突连接及是否活跃，不批量断开，不使用net use * /delete，不循环猜密码。
5. 已恢复则用192.168.100.2既定E_DRIVE/D_DRIVE各自读取根元数据、卷号E=2387166462/D=3187598165，并各选正式计划内一个普通文件验证同句柄只读打开/身份/大小后关闭，不读payload。不要用D的目录代替D文件。记录执行上下文、普通UNC与生产long-path是否通过。来源恢复不能自动放开copy。
6. 会话恢复与代码修复可在本机独立推进；与SAM经HUB协调一次有时间戳的探测。无可复用凭据/1219活跃冲突则交准确最小阻塞与可实施下一步，不泛称密码错误，不要求用户承担技术诊断。
7. 回传本次修改模块、完整CODE_HASHES、测试和有界重现输出、同一候选的完整结构审核、新合同、脱敏SOURCE_SESSION_STATUS。保留原run/state和现场；不写目标E，不复制业务文件，不格式化。只写C准备与HUB，完成停止。
回传目录：agents/chatgpt/inbox/R9_DESKTOP_FINISH_COLLISIONS_AND_RESTORE_SOURCE_20261015/

## 笔记本SAM协助执行
task_id: R9_NOTEBOOK_SOURCE_SESSION_ASSIST_20261015_0934
status: READY
52元数据任务已完成并合入台式机候选，不重复52，不扫描、不复查140/42、不找备份。
先ACK；只读确认本机hostname、当前账户名、E_DRIVE/D_DRIVE分享路径与卷号，并与ZHANGWEI约定一次有时间戳来源探测。
针对那次探测查短时间窗现有SMB认证事件，按ZHANGWEI/.1来源筛选；若可读，报告Status/SubStatus及账号名、时区、可关联时间，不上传完整安全日志，不改日志策略。无事件或无权限照实报告，不能推定密码正确/错误。
若历史记录明确指示来源共享连接所需凭据仅存SAM，则只报告目标类别/账户/是否有系统可复用路径，不通过HUB传递秘密。不要跨机上传任何密码、token、凭据摘要。
不改源数据、账号/密码/ACL/网络，不写目标E。
回传目录：agents/chatgpt/inbox/R9_NOTEBOOK_SOURCE_SESSION_ASSIST_20261015/
完成上传SAM_REPORT和脱敏状态，通知ZHANGWEI后停止。

## 结束条件
不需要用户重选版本；不重新扫描；没有复制授权。当前主阻塞是来源共享读取，另需完成已具体复现的结构冲突校验。来源会话恢复后提交具体最终合同和证据审阅，不自动迁移。历史mtime/hash/USN边界继续披露，不扩成重新全盘取证任务。
