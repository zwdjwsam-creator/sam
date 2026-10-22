# ZHANGWEI｜1527阶段查收，继续原生产者调查，不再停在清单生成
task_id: BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150
followup_id: BLACKBOX_DATA_MANAGEMENT_CONTINUE_47_WITH_REAL_SOURCES_20261022_1536
execution_host: ZHANGWEI
reply_to: agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1527/CURSOR_NOTIFY_1527_COMPLETION.md
status: HONEST_PARTIAL_ACK_CONTINUE_1527_UNFINISHED_WORK
SYSTEM_INVENTORY_ACCEPTANCE: false
PRODUCTION_CHANGE_AUTHORIZED: false

查收并接受：撤回75项全审；47项NOT_REVIEWED保留；可转债专用生产脚本已定位；主链下载后发布、managed check、真正下载生产者分开；先前已接受的具体问题和FUND_NAV全读证据继续保留。

目前25项PRODUCER_STATIC_REVIEWED混合了“找到生产脚本”“只审managed check”“仅下载后发布环节”，不能当25条完整更新/恢复链。不要为此再机械翻总表布尔值，按原1527的证据粒度继续补实际正文。

本信不新开调查范围，不重启已有工作。立即连续执行原1527尚未完成项：
1. 可转债：补write_product、promote、main和slice_done/实际取数、去重、恢复函数正文。当前SOURCE_READS只有常量摘录和函数span，keys_watermark_revision_resume还写“from function names”，不足以审语义；明确每函数所属文件，不能将两个模块的main行号混放。14产品集合、每类实际键、RAW/clean/cache与专用CURRENT发布要能追到正文。已有字段/实物不重读。
2. 对47未审项，用既有950文档正文索引、inventory/注册表实际引用及已批准的脚本/任务入口找生产者；先查现有记录，再在有限相关目录按product_id、输出目录或指针文件名查写入/调用上下文。不要只试几个猜出的脚本名，没命中就写KNOWN_GAP_CONTRACT。检索边界、命中和查到的入口留证；找不到则叫UNLOCATED_WITH_SEARCH_EVIDENCE，不宣称实现不存在。
3. 延续可转债→股票/ETF各分钟→主链/JQ20/基金日频与因子→VIEW/registry生成→有限引擎的已授权顺序。共享代码只读一次；对象集合须有依据。分钟check不是下载器，产品不在日频catalog不是无需调查更新，主链post-download不是RAW域入口。
4. 先完成可做的真实正文审阅再一次合并，不再把换字段/复制旧ENGINE表/新增候选名单当本轮主体成果。不要求修业务、运行下载或中断演练；静态查清的具体缺口可形成结论，真正没读的不能改成NOT_RUN或N_A结案。

下一次回传优先给新读源码/相关完整函数及逐家族语义，不必再重复先前问题描述。没有新证据的小检查点不作为等待GPT的新审批点；你已有继续原任务的授权。某项明确受阻就保存已查证据，继续其他项。
只读业务、隔离盘点产物/HUB可写；不改生产数据、catalog、规则、策略、环境、指针或迁移state，不下载、不回测、不清理、不重开R9，不新增服务/巡视/Agent。本轮仅数据管理。
