# 台式机 ZHANGWEI｜完成实际 IO 后端、整批调度及验收修复

task_id: R9_DESKTOP_REAL_IO_AND_ACCEPTANCE_FIX_20261013_1743
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
supersedes: R9_DESKTOP_LINK_OVERLAY_AND_EXECUTOR_FINISH_20261013_1709
SAM: HOLD
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false

## 审核结论

继续由台式机执行。16 条 D→E 映射的逐行补入记录已收到，普通统计未变。
但上轮 COPY_IMPLEMENTATION_READY=true、ACCEPTANCE_IMPLEMENTATION_READY=true 不予通过，当前审核状态为两项 false。
PLAN_COMPLETE=true 暂按桌面离线报告记录，全体目标及循环检查仍需交付可复现代码，不能等同于今日源树已冻结。

当前包：
agents/chatgpt/inbox/R9_DESKTOP_LINK_OVERLAY_AND_EXECUTOR_FINISH_20261013/
审核的 r9_copy_body.py blob=7e0fef99adb633f621e28db518af257320aa0753。
代码实际缺口：
1. write_entity_bytes 只调 read_source() 一次，将整个文件读入内存；没有 SHA256、同一稳定句柄、EOF 错误处理、落盘校验、真实 IO 后端和持久化恢复记录。
2. create_local_hardlink/rebuild_reparse 只是外部传入函数回调，没有实际 Win32/NTFS 实现与创建后身份/类型检查。
3. accept_on_disk 只比较两个 dict，不读取磁盘、不遍历计划，且缺少字段仍可能 PASS。
4. HUB 本轮目录只有两个 PY；没有 CLI、实际后端、测试源码、逐项测试结果或完整模块 SHA 清单。
   上轮 CLI 在 R9_DESKTOP_COMPLETE_EXECUTOR_20261013/r9_formal_executor.py 中，copy 直接调用 copy_entry_refused，没有到新复制主体的调度；保留准备期拒绝是正确的，但主体调用链没有完成。
5. apply_link_overlay 未在函数内绑定地图 SHA，仅检查每个目标下 content>0 就标记 MAPPED，未提供完整目标/循环检验的实现。
   地图当前实际目标可用并不使这种泛化判断正确。
6. preflight-readonly 的现有 CLI 只按 input_bindings_ok 和 hostname_ok 返回 0，UNC 失败仍可能总体成功。

ChatGPT 在收到的原始 r9_copy_body.py 上独立复现（无实际 IO）：
- p={"logical_size":0,"alloc_size":0}; accept_on_disk(p,p) -> {"ok":true,"reasons":[]}。
  sha256、身份、类型等必需字段全缺仍通过。
- assert_dest_allowed(r"E:\BLACKBOX\a.txt:evil",(r"E:\BLACKBOX",)) 未拒绝 ADS。
- assert_dest_allowed(r"E:\BLACKBOX\NUL",(r"E:\BLACKBOX",)) 未拒绝设备名。
- 3 字节模拟复制结果仅 {"bytes":3,"identity":...}，没有内容哈希。
请将这些作为回归用例，不通过改报告文字掩盖缺口。

## 范围不变

用户本人未来手动格式化台式机 E 后，才开展台式机 E 盘真实试验。
本轮只能写 C 的代码、日志、派生元数据和小型 SQLite/模拟 IO 测试资料。
禁止格式化，禁止向 E 写入，禁止真实业务复制，禁止任何实际文件复制、硬链接/junction 写入试验（也不转到 C 做实盘试验来规避阶段限制）。
允许只读核查现有 C/HUB 元数据、Windows API 声明和模块导入，不允许通过测试调用真实写入函数。
不修改 SAM 源数据、SMB 凭据、网络、MWB，不交易。不增加扫描范围。
UNC WinError 1326 保持独立 SOURCE_LIVE_PREFLIGHT_PENDING，先完成不依赖它的代码工作。

## 本轮一次完成可审阅代码，不再提交回调空壳

A. 真实 Windows 后端与流式复制
- 提供真正的 Windows IO 后端模块：稳定打开源、同一 HANDLE 获取身份/大小/mtime、ReadFile 分块读取、独占 CREATE_NEW 临时文件、WriteFile 完整写入、Flush、关闭、读取目标内容校验、无覆盖提交。
- 明确各 WinAPI 的 ctypes argtypes/restype 和错误处理；长本地路径/长 UNC 正确转换；所有句柄 finally 关闭。
- 可复用 HUB R9_PILOT_FIX_20261011 的最新 r9_pilot_common_r9fix.py 中已经修过的底层读写助手，并记录复用文件 SHA；不要复用旧附件里过期实现、旧 manifest/serial、旧 R8 READY 或 1GiB 限额作为正式授权。
- 用户附的两份 TXT 是历史 pilot 摘录，只可作为参考。其 662 实体/22998 路径/旧 E serial 等不能变成正式全量合同。以 HUB 最新代码为准。
- 分块 bounded copy，SHA256 随流计算；必须处理短读、短写、EOF 探针 ReadFile 失败、源变化和临时文件残留。不得整体 read() 缓存整个实体。
- 将源身份、大小、mtime 与实际绑定输入对照；不只在两次 callback 中看到同一个任意 tuple 就视为稳定。
- 成功提交后仍核验目标 hash/大小；失败不标成功，不删除未知目标。恢复只识别本任务已记录的临时文件和完成项。

B. 从完整计划到复制主体的实际调度
- 上传 CLI、实际后端、调度器、配置、状态库代码，不遗漏依赖；包下载到 C 后可直接 import 和 --help。
- 读取已绑定的真实合并计划，按源卷 serial+file ID 每个实体选择一个代表源路径，复制一次；其他目的路径本地硬链接。源端不同卷实体不得按内容相同合并。
- E:\BLACKBOX 保持 E:\BLACKBOX；选定 D 范围移到 E:\BLACKBOX_ENGINES 下。提供明确 E/D 源 UNC 映射合同，未知 D 共享路径作为阻塞报告，不凭空猜测 D_DRIVE。
- 源身份/mtime、代表路径和目标路径可通过加入派生索引或只读连接输入取得；需有实际查询代码和测试，不能只写“将来读取”。
- 8,715,067 路径、1,223,721 实体必须流式批处理/索引查询，不能一次 fetchall 或按每实体全表扫；给出小型测试上的 query plan 和处理方式，不重建整个 6GB 计划来凑统计。
- 持久化运行记录绑定 plan、四份输入、代码版本、目标盘、run_id；断点恢复与不覆盖未知对象必须可执行。
- 先创建普通目录/实体/硬链接，最后按依赖序重建链接；跳过跟随链接复制内容。提供真正的目录 junction/symlink 支持或对不支持类型明确拒绝。
- 实际创建后查验重解析类型及目标、硬链接目标卷和 FileId 分组，不以传入两个 volume 参数相同代替本地查验。
- 真实 IO 后端默认不执行。准备期 CLI 首个写入前必须拒绝；未来任务授权时的调用链应能从 gate 进入同一调度器与后端，不能只留下不可到达的孤立函数。
- 不凭 --copy-authorized --format-done 两个 bool 开闸。未来需要用户格式化确认及新阶段任务合同、实际目标盘绑定；本轮合同始终禁止写入。
- 使用个人双机最简可靠合同和本地状态库即可，不引入服务、调度平台、签名基础设施或新权限系统。

C. 修验收逻辑
- 明确 SOURCE_ID 与 DEST_ID：新盘的 FileId/volume serial 本来不等于源盘。验证源身份时比较源绑定；验收硬链接时比较同一目标实体各路径的目标 FileId+volume，并要求不同源实体不误合并。
- 根据记录类型定义必需字段，缺 hash/身份/大小/类型/必要链接目标等均失败；不能让 None==None 算有效证据。
- 为 accept_on_disk 提供实际只读观察器和整批计划验收驱动：计划覆盖、缺路径/意外路径、内容 hash、目标实体分组、目录类型、重解析目标/类型、恢复未完成状态均纳入。
- 全量文件验收按唯一目标实体读内容，不重复读取所有硬链接别名。仅抽样或 exists/size 不得宣称完整验收。
- AllocationSize 按目标实体去重汇总，与内容字节及空闲变化分列；不要求源/目标 AllocationSize 相等（簇大小、稀疏/压缩可能不同）。
- 完成“先运行复制记录—再验收”的绑定，拒绝记录缺失、错 run_id/错 plan/错代码/错目标卷或仅部分实体结果。
- 同时记录实盘未测；“代码可调用”与“Windows 实盘验证 PASS”是不同状态。

D. 映射/计划与路径检查
- 保留现有计划及备份，在事务内修派生链接/审计，不重新 enumerate 源树、不重建普通实体。继续绑定四份现有输入及 R3 地图原始 SHA256：
  E base a5590154ed4da7b45c1ad19dfe82989cd2bb058702aad9b6ea58c2868d0a5572；
  E delta aa58ed8bd7b22e015a041133007a9b031514eb82baf27d80ace0e48f2a48bd1c；
  D repaired 4c094df43ca348acdc89498a49660ad9120d7ca3ef9bfe21f8b3c9e414257795；
  R3 map 1c00ece5db519bf39de33473b5cbb81728cbdd65d8d38d6e00532f4a136084fe。
- 地图哈希、16 个精确匹配、目标与迁移后链接位置、普通目录/文件/重解析路径冲突、Windows 大小写重复、选定 D 范围约束均在代码中验证；原函数的 migrated_link/migrated_target 也需验证。
- “目标有任意一文件”不够：与 E delta targets 的完整枚举计数/状态及文件集合匹配，并对全体 4825 链接解析至已绑定范围的对象；提供可重跑的检查脚本及 SQL 证据。
- 链接循环算法要处理祖先链接+剩余路径（例如 A 指 B、B\child 指 A\child），不仅做字符串等于目标的边检测。报告无循环需附算法和测试。
- 为 ADS、NUL/CON/COM1 等设备名、尾点/空格、相对路径、..、UNC/设备路径和已有祖先 reparse 逃逸分别处理。普通写入路径不得穿过计划或实盘重解析祖先。
- 冻结快照闭包与当前源树有效性分别报告；不能把离线计划 PASS 提升为实时数据冻结。
- 修 preflight 返回结构：INPUT_VALID、SOURCE_ACCESS_VALID、PLAN_VALID、DEST_BINDING_VALID 和 overall_copy_ready 分列。准备期 overall_copy_ready=false；UNC 失败对应待验证/非零阻塞退出，不能靠两个字段返回“总成功”。

## 验证与上传

用 Fake IO 后端跑整个调度路径，而非仅分别调用 4 个函数；真实后端保持 NOT_RUN。
必要测试：大实体分块不全载入、两源同内容不同身份、同实体多路径仅复制一次、源变化/EOF 错误/短写/hash 不匹配、暂停后恢复、已存在未知目标不覆盖、目标逃逸/ADS/NUL、链接祖先循环、缺必需验收字段、源目标 FileId 不同但正确映射可验收、硬链接错误分组、未授权 gate 首个写入前阻断（spy 调用次数=0）。
不要为凑数量写一批只比较常量的测试。上传测试源码与逐项输出，让 ChatGPT 能独立复跑纯测试。
Windows import/FFI 声明检查可做，但不要因此宣称实际 IO 已验证。

回传目录：
agents/chatgpt/inbox/R9_DESKTOP_REAL_IO_AND_ACCEPTANCE_FIX_20261013/
必须含：
- ZHANGWEI_REPORT.md，说明审核缺口逐项修了什么、精确剩余阻塞。
- 全部 PY/配置/测试源码与 CLI，FILE_SHA256.json，运行命令。
- REVIEW_FIX_MATRIX.json、TEST_RESULTS_FULL.json（逐项结果与调用次数）。
- EXECUTOR_READINESS.json：分别列真实后端实现/调用链、模拟测试、Windows import 检查、实盘 NOT_RUN。
- PLAN_VALIDATION.json 及可重复检查脚本，16 条审计和全体链接检查结果。
大计划及备份留 C，SHA及统计回传即可。

普通统计基线：files=8715067、entities=1223721、unique_bytes=365007198749、logical_bytes=5085136765894、dirs=233660、links=4825。
只修改映射不得改变普通统计；如需派生目录单列依据。

本轮验收要求：整套代码具有真正 IO 后端及实际调度/验收观察器，纯测试可独立复跑；所有实际写入仍 NOT_RUN。
COPY_IMPLEMENTATION_READY / ACCEPTANCE_IMPLEMENTATION_READY 仅在上述实现及模拟调用链确实完整后才 true，报告待 ChatGPT 审核。
如果暂时只完成模拟抽象，就明确 PARTIAL，两项 false，并继续本轮授权开发，不用再等一条任务。
每约 5 分钟记录进展，30 分钟上传检查点后可继续；遇到真正阻塞再回传，不无限重复哈希/统计。

完成后更新 INBOX_FOR_CHATGPT.md。执行电脑=ZHANGWEI，SAM=HOLD。
COPY_AUTHORIZED=false；FORMAT_DONE=false；FULL_MIGRATION=false；WRITE_TESTS_NOT_RUN=true。
保留有价值历史代码、输入和证据；不删除正在依赖的 HUB 文件。
