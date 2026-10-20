# ZHANGWEI｜独立有范围只读查询入口技术验收通过
review_id: BLACKBOX_READONLY_ENTRY_TECH_ACCEPTANCE_20261020_2145
execution_host: ZHANGWEI
task: BLACKBOX_READONLY_ENTRY_FINISH_20261020_2135
status: BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

## 验收结论与证据
已实际读最终入口py/ps1、FINAL_FACTS、Windows严格UTF8正反例、runtime身份结果。2110/2135独立有限只读入口通过技术验收，停止该项修复迭代。
- 安装位置 E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\
- Python D:\Anaconda3\envs\blackbox_bt_py310\python.exe，3.10.20 64bit，pandas2.3.3、pyarrow23.0.1。
- entry py SHA 2ae78cbd302cced9591999f92dad25a120357828ae466c3f85c5b686c2ab7680
- entry ps1 SHA 7dfbac9179fc869de400d66d36d21ab72162cd0e970ce603b45a8cc7d9a7c170
- runtime_v4三个审定SHA未变（common0c018fb5…80769；gate98faa294…98fd3；resolver5d232abb…6c8d6）。
- 真实安装入口000001.XSHE 2026-09-02..09-10：rc0、7行、UTF8严格解码成功、无U+FFFD；读取约35.993ms，完整进程约678.403ms。这是该样本，不承诺所有查询同速。
- 09-01..09-10：rc3、missing09-01、coverage拒绝，无行结果绕过。
- 源码已落实dataset证券/日期filter后物化、列投影、实际模块路径/SHA验证、缺包自检拒绝、ISO输入校验、解析后和实际行读取后的CURRENT终检。
- ChatGPT另对实际入口main做5项受控检查：读后指针变化拒绝、读后权威失败拒绝、未变返回样本、反向日期/单端点在读数据前拒绝，全部通过。控制输入/读行替身，不冒称Windows实盘复跑；代码与结果在2135包review目录。

## 已可使用的能力
首版仅STOCK_DAILY_PIT_R1，证券代码+ISO起止双端点，按正式缓存解析、覆盖门和日历核对后只读。
台式机AI收到类似“查询平安银行000001.XSHE在2026-09-02到09-10的本地日线”可按既有规则预检后直接调用本入口，无需用户敲命令或跨机转述。
每次请求仍要保留coverage_scope、cache release/asof、实际日期与口径；空行不推断源缺，不自动下载，不把产品日期覆盖当证券全量或因果回测许可。

## 未宣称恢复的部分（保留独立状态）
FULL_HISTORY=UNPROVEN；全历史/全部资产/证券全量/因果回测均未验收。
原E .venv Python3.12.10仍有源机路径问题，原覆盖模块2B仍保留。原业务日增、研究autorun、策略/交易不在本次验收内，不能用此接受令启动它们或覆盖原脚本。
R9迁移结论不变，本入口为迁移后授权管理文件。不得重新跑迁移/verify-existing或全库hash来收尾。

## 本机结案动作（已授权，仅文档/ACK）
1. 在相关管理状态与QUERY_CAPABILITY标BOUNDED_READONLY_ENTRY_TECHNICALLY_ACCEPTED/CLOSED，指向此review；保留全部代码/候选/回执，不再优化或重跑全套测试。
2. START_HERE/OPERATING_MAP及原_OPS索引连接仍按既有授权管理文档维护；ACK附实际索引路径和包含入口的必要短摘录。若2110/2135未真正补过某个管理链接，直接补这一条链接并给diff，不动根AGENTS/Kernel/HAND/Manifest。
3. 一次写回2135包ACK_TECH_ACCEPTANCE_2145.md，含主机、入口身份、已结案范围、原环境/日增未验收、管理索引摘录；更新INBOX_FOR_CHATGPT。若无新任务随后待命，不自造更高权限“继续修复”任务。
4. 现有HUB巡视按用户在本机实际授权设置运行；本review不新增/延长/重建巡视，不以force_complete字段绕过任务范围或失败门，不重复已完成任务。

验收包：
agents/chatgpt/inbox/BLACKBOX_READONLY_ENTRY_FINISH_20261020_2135/
原代码、候选、R9冻结证据均保留。下一阶段若有明确新目标再安排，不把有限入口结案写成整个BLACKBOX恢复。
