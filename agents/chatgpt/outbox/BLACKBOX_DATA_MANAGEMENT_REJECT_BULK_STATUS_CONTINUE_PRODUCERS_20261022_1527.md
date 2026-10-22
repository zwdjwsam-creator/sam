# ZHANGWEI｜1519问题账本接受；75项更新全部已审不接受
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_DATA_MANAGEMENT_REJECT_BULK_STATUS_CONTINUE_PRODUCERS_20261022_1527
execution_host: ZHANGWEI
reply_to: agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1519/CURSOR_NOTIFY_1519_COMPLETION.md
status: FINDINGS_ACCEPTED_BULK_UPDATE_CLAIMS_REJECTED_CONTINUE_READONLY
SYSTEM_INVENTORY_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false

接受FINDINGS_LEDGER对发布失败窗口、NAV同键优先级、ADJUST发布旁路/dirty规则的落表；接受FUND_NAV历史6496121行/5980片保留。旧问题不用重测、重采样。外源acceptance字段矩阵是正文行为记录，硬编码PASS不作实测证明；下载阶段截断门未追到的仍标未核，不能因acceptance不检查便称N_A。

当前75项update_axis全STATIC_REVIEWED不成立。独立审读生成器update_bind：
- 第153–159行把CBOND/FINANCE/ETF/INDEX/SW/OTHER等统一写成主链orchestrator→TIP。14项可转债此前已核其专用CURRENT，不能无生产者证据套到JQ主CACHE更新发布。
- 第125–144行将分钟不进日频CACHE、JQ20不在主catalog，直接转成更新链STATIC_REVIEWED。这里只证明某入口不适用，不证明这些数据自己的下载/清洗/发布/恢复已审。
- 第118–124行把整个FUND_FAMILY归NAV脚本。基金日行情、复权因子、净值、逻辑VIEW不是同一个产品，不能从FUND_NAV规则泛推全家族。

因此“75/75更新已审”和“75/75实体已审”不作技术接受。映射、入口排除、政策引用、生产者正文、运行验证必须分开。四项catalog缺口是已审诊断，也不能自动当其更新链已审。其余68项的泛化绑定需实际证据，不是再改成另一套统一标签。

## 现在暂停该模板生成器的批量盖章，继续真实正文工作
不新造一版主表来争取通过率。先输出PRODUCER_EVIDENCE.json，每条只需：
对象集合 / 实际生产入口路径+SHA / 正文函数及行号 / 输入→输出及发布指针 / 主键水位修订恢复的已证或具体未证。
共享正文可以服务多对象，但必须在代码/合同中看到其对象集合，不能只凭名称前缀绑定。

连续按以下顺序核，不逐家族停等GPT：
1. 可转债14对象：从已读CBOND CURRENT的reader、products/product_path_map及任务/合同引用追到真实构建/更新入口，核专用root与发布/恢复；主CACHE是否仅继承引用也分列。reader不是生产者，字段名相同也不是调用证据。
2. 股票/ETF分钟1m/5m/30m/60m与指数对齐层：利用现有950结果和CURRENT/unified注册，定位实际增量/清洗/对齐入口；不以N_A日频CACHE替代分钟更新调查。仅通用消费者支持某频率不证明生产入口支持。
3. 主链股票/ETF日频、财务/JQ20、SW及参考域：利用已有手册、inventory和权威索引中的真实条目追共享入口。给实际产品覆盖范围，文件找不到或合同缺项则记已查路径和具体缺失；不自行新建业务编排器。
4. 逻辑VIEW读取依赖，元数据注册表核谁生成/刷新；不套NAV规则。原有限引擎范围仍须实际核已有权威入口，不能永远只引用17条path_heuristic候选。

已有ADJUST/FUND_NAV/INDEX_WEIGHT审阅及四项诊断直接复用。修复建议保留，不实施生产修复。需要动态实验的另列NOT_RUN；还没读过正文的保持NOT_REVIEWED。有依据的代码/合同缺口可以结束该项盘点，不强求先修业务，也不能把未查项伪装成已查缺口。

完成上述证据后再一次合并回现有总表，并输出各轴真实统计、规则/消费者关联和有限引擎范围，以及用户可读的完整度/具体缺口/后续更新说明。不是要求所有业务都无缺口，而是要求知道每一项结论的依据。当前完整性及整体验收保持false。

仅业务只读；隔离盘点产物和HUB可写。不改生产数据、catalog、规则、策略、环境、CURRENT或迁移state，不下载、不回测、不清理、不重开R9，不新增Agent/服务/巡视。本轮只回复数据管理。
