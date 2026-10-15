# 0800原任务审核补充｜目标路径冲突检查尚未闭合

task_id: R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015_0800
followup_id: R9_DESKTOP_0800_TARGET_COLLISION_FOLLOWUP_20261015
execution_host: ZHANGWEI
status: FOLLOWUP_REQUIRED
SAM: HOLD_LOCAL_52_ACCEPTED
original_instruction: agents/chatgpt/outbox/R9_REVIEW_FULL_CHAIN_AND_SESSION_20261015_0800.md
return_path: agents/chatgpt/inbox/R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015/
VERSION_CHOICE=AS_IS_MIGRATE_MARKED
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

## 本次认可的结果
SAM52原始JSON路径集恰为52唯一，与SOURCE_PLAN_PATCH及PROBE_52相等；47文件/5目录，E卷51、D卷1，必要字段齐。SAM四件上传文件SHA/bytes已独立核对。此后台式机报告52已合并；不再派SAM复查。
已读0800报告(blob 65c9a1ba0ac51dfa177de1e000cdcaa444ed481a)、合同、GATE_RESULT、SESSION_DIAGNOSIS、merge_52.py、chain/winio及测试。
15模块原始UTF8字节逐件SHA均匹配CODE_HASHES，完整code_digest独立重算=cddfa2e6bbad0afba633d4afb7f15c5e84224f4662386c24759eda210e7d4a3f。
18项隔离测试复跑通过。复跑环境为Linux：只适配WinDLL导入/禁用真实系统调用、峰值内存读数及临时state路径的C盘判断；未改变目标路径、reader、审计、复制/验收逻辑，不宣称Windows现场实盘复跑。
FULL E/D来源UNC绑定及前轮三种结构缺口的修复认可。53551d…候选的约6GB文件仍留现场，本轮完整候选审核/计数为本机回报，不能声称我已独立读取大库。

## 精确剩余缺口：大小写折叠及映射后同名冲突
audit_full_plan目前保留inventory directories与dest_directories，但冲突只检查link_key in directories和源file path in link_keys，没有完整比较实际目标file/dir/reparse。
最小隔离复现1（使用现有test_full_closure._write及_contract）：
files=[(r"E:\BLACKBOX\A",4)]
dirs=[r"E:\BLACKBOX\a"]
links=[]
inspect_plan返回ok=true，closure.collisions=0；Windows上二者占同一目标名称，不能先建目录再当文件创建。
复现2：
files=[(r"E:\BLACKBOX\one.txt",4)]
dirs=[r"D:\data",r"E:\BLACKBOX\real"]
links=[(r"E:\BLACKBOX_ENGINES\data",r"E:\BLACKBOX\real")]
inspect_plan同样ok=true/collisions=0。实际_directories把D目录映射为E:\BLACKBOX_ENGINES\data，链接清单占同一目标。测试fixture应给该link有效mount-point tag，再用实际_links确认，不能用无tag导致的BAD_LINK_TARGET替代目标冲突检查。
这是审核器隔离漏检，不是断言完整候选必有这些坏行。

## 仅补原任务缺项，不另启任务
1. 在reader实际目标映射后，按Windows规范化/大小写折叠检查file、directory、reparse的目标命名冲突及reparse祖先。覆盖D→BLACKBOX_ENGINES后的冲突，保留同实体合法alias和reparse库存行/link行的合法成对表达。不同类型/不同实体占同一目标须拒绝。
2. 用本次两个最小复现补针对性测试；有效link tag必须经实际reader/_links。原18项回归一次即可。仅隔离/临时C测试，不跑业务复制。
3. 对现有53551d…完整候选进行本机C静态目标冲突核对，交实际计数与少量冲突样例。尽量流式SQL/索引/临时C表，不把870万文件装大Python字典；不访问来源、不重扫、不测速。若零冲突无需重建6GB候选，只更新code_digest/合同绑定和静态审核。
4. 若有真实冲突，只报告具体行/实体映射并给出修订方案，不擅自丢弃/覆盖数据。更新合同准确命令、代码hash、测试输出和报告；保留旧回报，以新补充文件说明差异。
5. 来源访问仍1326是实际阻塞；本轮不再重复会话探测、不处理账号登录、不改SMB/凭据/网络。COPY边界不变。完成停止待审。

SAM=HOLD。ZHANGWEI继续原0800任务；先对本补充ACK，若现有进程仍在跑只接续不重复启动。回传原目录的TARGET_COLLISION_REVIEW.json、测试/代码、更新合同及ZHANGWEI_FOLLOWUP_REPORT.md。任务发布不表示已接单。
