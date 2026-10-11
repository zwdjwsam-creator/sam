# 给笔记本 AI（SAM）｜建立选定D范围的完整清单，补齐逐条依赖

任务ID：R9_NOTEBOOK_SELECTED_MANIFEST_20261011_1354
状态：待执行。
取代：R9_NOTEBOOK_SCOPE_CLOSURE_20261011_1330（报告已收，覆盖尚未闭合）。
执行方：笔记本SAM。台式机ZHANGWEI保留已验收样本待命。
授权范围：C盘代码、测试、报告及清单写入；源E/D只读。允许下述选定D子树完整元数据枚举，不复制业务数据。

## 1. 本轮审核结论和需修正项

ChatGPT已阅读本轮主报告、2份JSON、抽样程序和队列：
- D_GLOBAL_COVERAGE_PROVEN=false、SELECTED_SCOPE_COVERAGE_PROVEN=false是正确结论；255目录0差异仅限抽样。
- 当前程序每目录只取40项、深度限2；db_has_child使用“精确路径或后代LIKE存在”，不能证明直接条目存在/类型正确。
- R9_SAM_COVERAGE_RESUME_QUEUE.json的queue只含部分差异/错误，未保存qdirs和未访问根，也没有超过40项/深度2的续接信息；queue=0不能用于恢复全树核验。不要拿它直接当正式扫描完成证据。
- 对1450错误文件只stat成功，Win32卷+File ID身份仍未恢复。
- E→D24、D→E16只有计数，缺逐条实际路径/映射。HUB没有ED_LINKS_RECHECK.json；该材料若本机存在必须补交。
- R9_SAM_MIGRATION_SCOPE.json还写F盘布局，而最新台式机已核验目标为E盘MarketData；旧F映射不得进入执行配置。
- 目录名、旧启发式分类、旧path map不足以支撑HIGH依赖置信度。

样本验收已完成，不重做。P7仍禁用。历史R8 READY不复用。
原始D DB、抽样结果与失败证据保留；新增交付单独命名，不能覆盖成“历史已经完整”。

## 2. 先落地实际依赖表，确定本轮枚举根

读取已有ED_CROSS_VOLUME_LINKS.sqlite、ED_LINKS_RECHECK.json和D inventory重解析记录；
复用E索引，只对已知链接做只读核验，不扫描整棵E文件树。
把24条E→D、16条D→E分别逐条列出，另外列清D库存其余junction的处理：
源主机/卷、链接绝对路径、类型、记录目标、当前解析目标、存活状态、
是否环/逃逸、目标是否属于迁移范围、拟迁移后的链接路径与目标。
区分“这个链接存在”和“目标内容已纳入”，不能用24/24存活代替闭包。
链接目标跨卷则记录为junction/symlink，不当硬链接；不跟随重解析点自动展开。
必要依赖按显式目标加入队列，并消除重叠根；同卷关联也要记录。

本轮必查D范围：
1. D:\backtest_lab
2. D:\backtest_lab_backups
3. D:\backtest_lab_candidate_releases
4. D:\backtest_lab_shadow_experiments（先核元数据/保留建议，不宣称运行必需）
5. D:\blackbox_data
6. D:\JQ
7. D:\BLACKBOX_DESKTOP_INIT_R1
8. D:\BLACKBOX_REMOTE_LINK_R1
9. 上述已知E→D真实目标及为独立使用所需的D侧依赖子树（如archive内实际被引用的子树，精确列路径；不要用**/pit_products/**通配符当清单）。
若显式目标只能通过全MIN_sandbox/全CURSOR_TASK_ARCHIVE等大树确定，先列证据与条目量，单独标未授权扩展；本轮不无差别扫描这些整棵大树。
其他RELATED/UNKNOWN根可查现有DB、少量入口配置和已有引用，不扩大为全D枚举。

将选定根、显式依赖、未授权/未确定边界写入配置并计算SHA。
旧8,161,681,208字节只是历史候选基线；不能当新清单的硬期待结果。

## 3. 实现真正可续接的元数据对账，运行一个30分钟批次

不要继续加抽样，不读业务文件内容hash，不写源E/D。
新清单和完成账本写C:\LAN_SHARE_REPORT，原DB以只读方式查询。

要求：
- 对选定普通目录枚举全部直接子项，递归全部普通子目录，无40条/深度2裁剪。
- 所有存在性/枚举/属性/身份API用扩展长路径；检查FILE_ATTRIBUTE_REPARSE_POINT，不能仅靠is_symlink排除Windows junction。链接记录但不跟随。
- 对账精确path/parent、类型及身份元数据；live有DB无、DB有live无、size/mtime/身份漂移分别记录。后代存在不能替代该条目存在。
- 避免每子项“OR LIKE全表”查询。一次读取选定条目建立精确路径/父子映射，或在C副本建立必要索引；不修改原DB。
- 在独立清单中补录live新增条目与身份，保留历史差异。普通文件必须有可用源卷身份+File ID、大小、mtime及所有范围内路径；不能用stat尺寸代替错误身份已恢复。
- 目录只有完整枚举EOF成功且所有子项已持久化后才记ENUM_DONE；枚举失败/中途停止留PENDING或ERROR。空目录也要记录，不能仅从文件表推断。
- 队列必须保存所有未访问根、全部发现子目录、当前未完成目录；不得截断。停止在目录中途时，允许下次从该目录开头重枚举并幂等upsert，禁止丢后半段。
- 使用SQLite事务/原子checkpoint；配置SHA、源主机/卷身份、起止时间、处理数、剩余数均绑定；恢复时配置/源卷不符则停止。
- 对发生变化/访问或身份错误的条目列阻塞；每目录检查前后可用元数据变化，检测到变更不记稳定完成。这仍是扫描时间窗口内证据，正式复制前再检测漂移。
- 累计运行最多30分钟；每5分钟落checkpoint并显示进展。时间预算到即上传PARTIAL结果和完整续核状态，不从头重跑、不静默无限运行。
- 遇系统保护目录、凭证文件访问或权限拒绝，不提权/接管；如属于必需子树则如实阻塞。源文件内容不上传。

先在C盘专用合成目录做必要测试：
超过40直接子项、深度超过2可全部入库；中途停止/恢复不漏项且不重复计数；
真正缺项/错类型/枚举错误不会PASS；junction只记录不展开；“父项缺失但后代DB有记录”仍识别为差异。
提交实际程序与逐项结果，不能mock最终PASS。

SELECTED_SCOPE_COVERAGE_PROVEN=true须同时满足：
非空配置的全部选定根和显式依赖均有完整枚举账本；pending=0；
无未解决枚举/身份错误或被遗漏的依赖；全部live普通文件/目录在新清单中；
所有历史差异已明确归因/补入/标为源漂移，清单统计完整可重算。
只证明当前选定D范围，D_GLOBAL_COVERAGE_PROVEN继续false。
未知依赖未闭合时可写enumeration_complete=true，但selected scope overall仍false。

## 4. 同时交付可用的范围/路径方案

以最近真实台式机证据为准：
ZHANGWEI E: NTFS MarketData，serial806508DF，GUID Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}。
不要借笔记本或旧F盘映射声称已核验新目标；正式运行仍由台式机重新预检。
仅建议E:\BLACKBOX、E:\BLACKBOX_ENGINES等布局；配置中标PROPOSED，不创建目录或切换链接。
原D绝对路径兼容方式与新映射分列，防止配置里残留笔记本路径/UNC而依赖笔记本在线。

交付两套“建议范围+容量”，不让用户逐个判断陌生技术目录：
A. 独立运行最小范围：E BLACKBOX基线 + 已证实D依赖；
B. 保留研究资料的范围：A + 相关/未知资料作为独立存档，QMT安装树保存不等于可运行安装。
对shadow、MIN_sandbox、archive、QMT、UNKNOWN用已有入口/引用/内容类别给依据；
未查清项默认UNRESOLVED，不能仅因名字陌生就建议丢弃。
范围建议不是复制授权，本轮不复制/删除任何业务文件，也不自动启用存档代码或交易程序。
唯一实体字节、分配估计、额外余量、现有E基线出处分别列出；按卷+File ID去重，重叠根/跨分类重叠列清。
未知总量标PARTIAL，不把旧全D59.48GB当已证明总量。
正式复制器开发放在此清单可用之后，不改r9_1g硬上限或固定试验目标。

## 5. 上传HUB并停止

原包R9_PILOT_FIX_20261011/新增：
- R9_SAM_SELECTED_MANIFEST_REPORT.md
- R9_SAM_SELECTED_MANIFEST_SUMMARY.json（配置SHA、清单SHA、覆盖/错误/队列数、时间、去重统计）
- R9_SAM_DEPENDENCY_MAP.json（逐条实际链接和拟映射，包含已核验/未知边界）
- R9_SAM_SELECTED_SCOPE_CONFIG.json
- 核验/建清单程序、小型测试源码及结果
- 续核状态摘要与完整队列（过大则完整状态DB留本机，HUB交路径/SHA/全部计数和无截断说明）
清单SQLite留本机，不上传大DB或业务文件；附schema和统计查询以便审核。
补交本机ED_LINKS_RECHECK.json实际材料；如不存在，明确不存在。
更新INBOX_FOR_CHATGPT.md，FULL_MIGRATION=false。
保留本轮以前的报告作为历史；本次只做选定D元数据闭合，不全E重扫、不全量复制。
完成或预算到都停止等待下一调度。
