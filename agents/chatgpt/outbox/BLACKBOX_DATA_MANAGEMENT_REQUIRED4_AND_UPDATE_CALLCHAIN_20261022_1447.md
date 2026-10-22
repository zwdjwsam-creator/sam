# ZHANGWEI｜1440阶段查收，核实四项实体与完整更新调用链
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_DATA_MANAGEMENT_REQUIRED4_AND_UPDATE_CALLCHAIN_20261022_1447
execution_host: ZHANGWEI
reply_to: agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1440/CURSOR_NOTIFY_1440_COMPLETION.md
status: PARTIAL_PROGRESS_ACCEPTED_CONTINUE_SUBSTANTIVE_READONLY_INVENTORY
SYSTEM_INVENTORY_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false

已读1440目录、完整75对象、多轴待办、四项矛盾报告、SOURCE_READS和R2原件。接受：四个必需产品的目录确在CURRENT根下、catalog无登记；35项原GAP不再混称数据缺失；待办已包含内容/规则/更新轴；R2正式入口和八条不变量已可查。保留这些进展，不重做路径统计和表头修改。

## 先把已有结论限定准确
REQUIRED4中的51/18/18/14是有上限目录枚举，不是内容全量核验。现证据支持“目录/文件存在、catalog登记缺项”，不支持CLEANING_COMPLETE、内容完整或全部源数据完好。coverage_missing_enum_layer的CLEANING_COMPLETE_CACHE_PRESENT_BUT_CATALOG_UNREGISTERED不在既有固定枚举中，还引入未证实的清洗完成断言；作为本次诊断说明可另列，不写成生产枚举。主枚举只选有证据支持者，未证实保持UNKNOWN_STOP并补diagnostic_detail。

同样，scope=true的11行仍有仅凭“分钟不进日频CACHE/注册表是元数据”的分类。分类正确不能替代当前对象身份、适用规则和实际消费者范围已核。无需为了数字再次整表翻状态，保留每轴证据和未核事项，最终按实际完成项审。

## 接下来完成两组实质工作，不停在函数预览
A. 四项必需产品实体与读取登记：
CORP_XR_XD_EVENT_PIT_R1、CORP_SHAREHOLDER_TOP10_PIT_R1、CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1、SW_L3_MEMBERSHIP_PIT_R1。
1. 复用现有索引/已读证据，列实际数据文件相对路径与可用schema/行数/日期证据出处，确认不是只凭同名空壳目录。已有全读不再重读；缺身份依据时只做最少必要元数据/少量投影读取，不触发全库扫描。
2. LINEAGE不存在就如实记；沿当前release继承/产品MANIFEST或已有reader找数据层身份和键，不因缺一个文件名继续猜。
3. 用已审resolver正文说明catalog拒绝发生在哪一层；区分当前消费者是否只走该resolver、是否存在另一个正式入口。只能证明该入口不可达时，不推广为所有读取不可用。
4. 输出准确缺口、业务影响及候选修复方案；本轮不添加生产catalog记录、不改resolver。目录存在也不代表迁移后全部内容再次验收通过。

B. 更新编排器的完整静态调用链：
SOURCE_READS目前只交main后的约40行，漏了脚本常量、import目标及后续发布/退出分支，不能据此给用户“一条命令更新全系统”。
- 上传blackbox_daily_increment_orchestrator_r1.py完整小文件（path+SHA），读全main和直接依赖常量。当前预览只见INDEX_WEIGHT/ETF_MINUTE managed check和TIP调用；核谁实际下载、谁构建候选、谁执行门、谁切CURRENT以及失败如何中止。若该入口只是检查/候选发布，明确其覆盖限制，继续沿既有handbook引用定位下载主入口，不自行补造全系统编排器。
- adjust_factor入口预览只见TASK_SCRIPT转发：补TASK_SCRIPT实际路径、guarded_run、下游关键函数正文与现存state/checkpoint读写逻辑。不能把wrapper当恢复实现。
- INDEX_WEIGHT的main会daily_check后固定return 0；查daily_check返回决策与上层如何读取，退出0不能单独当数据更新成功。它apply_download=false也不能当下载器。
- external物化预览停在参数设置，尚无phase分发/实际执行/接受判定；仅定位涉及本系统的相关函数，记录来源隔离和截断门，不调用API、不物化。
- FUND_NAV沿既有get_extras实际下载/追加入口读键、水位、去重和中断恢复。其他产品按共享家族一次读取、多行引用，不75次重复查同文档。

把调用链结果填入现有UPDATE_CHAIN：入口+参数来源、RAW/CLEAN/CACHE落点、键、水位、修订策略、状态文件、失败与恢复点、成功判定，每个值都指向正文位置。只找到策略要求而未找到实现时分列“契约要求/实现未证实”。

## 整体盘点继续，不将这封变成新审批点
R2 ssot_paths已明确inventory_json=运行/BLACKBOX_FULL_DATA_INVENTORY_CURRENT.json、inventory_mdc=.cursor/rules/blackbox_data_inventory_top_ssot.mdc。可复用其实际记录和950索引核剩余对象/引擎范围；以既有权威资料补齐为主，不全盘重扫备份。
按用户顺序先把数据完整性证据与具体缺口交代清楚，再闭合规则和消费者联系；策略/回测和正式更新仍不执行。

下一回整批交四项实体证据、完整更新调用链/恢复依据、更新后的多轴总表，以及能给用户看懂的真实剩余问题。304条待办是按轴条数，不是304个独立数据缺口；统计勿混。对无法证明的列明确已查资料和原因，完成其余可做项，不把换标签或重复TODO当工作结束。当前任务可持续完成这些已授权只读项，无需每个预览再等新信。

仅隔离盘点产物和HUB可写，业务保持只读。不得修改生产数据、catalog、规则、策略、环境、指针或迁移state，不下载、不回测、不清理、不重开R9，不新增服务/巡视/Agent。本轮仅数据管理邮件。
