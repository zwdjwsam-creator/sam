# ZHANGWEI台式机｜接入SAM事实、补真实计划绑定并完成准备审核

task_id: R9_DESKTOP_BIND_SOURCE_FACTS_AND_FINAL_PREP_20261013_2016
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
supersedes: R9_NOTEBOOK_SOURCE_LINK_AND_SHARE_FACTS_20261013_1957
SAM: HOLD
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true

## 调度与已审核事实

下一轮回到台式机ZHANGWEI，SAM停止待命。保持不格式化、不复制、不实盘写链接。
SAM本轮4份文件的原始字节SHA/大小已由ChatGPT独立核验全部匹配。
16项id25–40的source_path/目标逐条与R3匹配，FileAttributeTagInfo与FSCTL_GET tag一致：
数字2684354563 / 0xA0000003，共16个mount point tag，属性含directory，目标为E:\BLACKBOX内路径。
这些是SAM源D链接本体现场证据，不再猜类型。
SAM现有普通共享E_DRIVE -> E:\、D_DRIVE -> D:\，192.168.100.2仍在SAM。
DESKTOP_SMB_ACCESS_VERIFIED=false；本机共享存在不代表桌面认证已经成功。

桌面1934的37项模拟单测已独立复跑通过，已修复的严格验收、FILETIME及A/B/C保留。
尚须本轮完成：真实计划内容绑定、查询开销修复、来源tag/UNC接入及一次只读桌面源访问核验。
IMPLEMENTATION_READY未通过审核，任何源访问成功也不构成复制授权。

## 1. 下载并绑定两个源事实输入，补类型与UNC映射

目录：
agents/chatgpt/inbox/R9_NOTEBOOK_SOURCE_LINK_AND_SHARE_FACTS_20261013/
D_REPARSE_TYPE_OVERLAY.json：
SHA256 1f6d3bf2a92271c17c9fd6eab03a00934bac5ce6496c9f7ed10ec32d105c15eb
39583字节
SOURCE_SHARE_FACTS.json：
SHA256 4355f96696033bdc65d730ece09b7ada309a2c1583cf9664460f1d7c39b137b5
3608字节

下载到C核对原始字节，不把JSON重排后的hash当文件hash。
sidecar的kind字符串junction_or_mount_point供说明，实际按数字tag判断junction。
以normalized Windows source_path精确匹配16个D reparse及R3 map id25–40；校验source D serial3187598165、map/d snapshot SHA、目标一致、status OK/errors空。
duplicate/conflicting/missing或改变目标的sidecar必须失败。

仍使用旧三份冻结SQLite、R3地图：
E base a5590154ed4da7b45c1ad19dfe82989cd2bb058702aad9b6ea58c2868d0a5572
E delta aa58ed8bd7b22e015a041133007a9b031514eb82baf27d80ace0e48f2a48bd1c
D repaired 4c094df43ca348acdc89498a49660ad9120d7ca3ef9bfe21f8b3c9e414257795
R3 map 1c00ece5db519bf39de33473b5cbb81728cbdd65d8d38d6e00532f4a136084fe
加入上面两份事实文件构成明确输入合同，来源文件不得修改。

派生计划在C事务更新numeric reparse_tag及出处，保留旧plan/备份，不能重新build_plan/unlink 6GB计划。
E4809按绑定base实际tag接入，D16按sidecar接入。reader/runner/acceptance同一条链都能读取，不只报告里写类型。
全部4825链接无LINK_TYPE_DEFICIT；逐条目标/范围/类型/循环核验不以status当证据。
不覆写旧D/E输入SQLite，不扫描业务树。

来源合同固定业务直连端点：
E本地根E:\BLACKBOX -> \\192.168.100.2\E_DRIVE\BLACKBOX
D本地根D:\ -> \\192.168.100.2\D_DRIVE（只允许已选定D根/计划路径）
目标E:\BLACKBOX及选定E:\BLACKBOX_ENGINES保持既有布局。
使用已经现场证实的普通D_DRIVE共享，不选择D$，不用其他WiFi/Tailscale地址。
共享根D:\不等于允许扫描/迁移整个D盘，allowlist取既有selected D scope/绑定清单。
SOURCE_SHARE_FACTS的E_DRIVE_share字段实际指BLACKBOX共享，命名不准确；
以shares_relevant中Name=E_DRIVE、Path=E:\的实际条目为依据，规范合同写清选用哪个根，不被字段名误导。

## 2. 真实计划内容绑定（当前只hash计数不够）

当前reader.plan_digest仅hash表计数/stat数值。
ChatGPT独立复现：正常完成小计划后UPDATE entities SET mtime='changed-expected-time'，行数不变；
plan_digest前后相同，full_acceptance仍true。因此不能把计数摘要当执行计划身份。

替换为可复核真实内容绑定，以下两种实现任选最简可靠的一种：
- 最终冻结SQLite计划文件的原始SHA256（无未纳入WAL/SHM、写入结束后冻结）；或
- 按稳定排序、带类型和长度的规范化流，对影响执行的schema/实体身份size/path_count/路径映射/目录/链接目标与tag等内容hash，外部metadata与scope由输入SHA共同绑定。
不能只hashcounts，也不能仅信任caller传"plan"字符串。
计划摘要不得把存放自身摘要的字段再循环hash。实际输入/代码摘要也由文件SHA清单规范绑定，不用任意字面量。

run-state、production runner、reader、full_acceptance/CLI使用同一绑定；在进入任何写入前验证。
不反复重hash原9GB E输入；允许对完成overlay的最终6GB派生计划做一次真正冻结绑定，报告耗时/结果。
后续读取用只读连接，计划改动后拒绝复用旧run-state；不能在校验后又修改计划。
测试：mtime/size/path/目标/tag被改但计数不变，摘要改变且旧绑定拒绝；错input/code/sidecar/scope也拒绝；索引/排序策略说明。

## 3. 修孤立实体核查的平方扫描

现有索引ix_entity=(is_dir,is_reparse,volume_serial,file_id)。
full_acceptance的orphan查询只用volume_serial/file_id，不带前两列。
ChatGPT按实际索引形状EXPLAIN复现：
旧查询=SCAN e + CORRELATED SUBQUERY + SCAN p；
添加p.is_dir=0 AND p.is_reparse=0后=SEARCH p USING COVERING INDEX ix_entity。
1223721实体对8715067路径逐实体全表扫不可接受。

修orphan查询或一次group/join索引，语义仍只针对普通文件实体，不把目录/reparse同号当有效路径。
检查reader/path_count/验收stage joins及tag/mtime查找的实际query plan，缓存schema/列查询，避免每实体全表扫或反复PRAGMA。
有限只读EXPLAIN/计数即可，不做全量业务性能试验。
hash次数维持唯一实体数，1MiB块/磁盘SQLite暂存及完整覆盖保留。

## 4. 一次只读桌面源访问预检，不修改认证

代码/绑定完成后，ZHANGWEI只读查以下来源：
\\192.168.100.2\E_DRIVE\BLACKBOX
\\192.168.100.2\D_DRIVE\（仅选定根的metadata）
可从plan取E/D各一个普通文件代表，以元数据只读HANDLE核验真实volume/FileId/size/mtime，
以及16个junction本体的必要tag匹配；不递归扫描、不读取/复制业务payload、不做业务hash。

使用现有Windows会话，不读凭据库，不要求用户现在输入密码，不net use自动连/断会话，不改密码/ACL/共享/网络/MWB。
若1326/5等错误，尝试一次后记录准确WinError/阶段/路径，不盲重试；离线代码工作仍完成并交付。
SAM源E=2387166462、D=3187598165是现场事实，用作身份核验；目标桌面E格式化授权仍false。
SOURCE_ACCESS_VALID只有桌面真正读取成功才true；本地C缓存/HUB元数据通过不等于源访问通过。
源共享存在但认证失败时SOURCE_LIVE_PREFLIGHT_PENDING=true、overall_copy_ready=false，实盘不能放行。

这项是只读预检，用户手动格式化前可做；本轮绝不执行C/E真实文件复制、hardlink/junction创建测试。

## 5. 完整准备交付与回归

回传：
agents/chatgpt/inbox/R9_DESKTOP_BIND_SOURCE_FACTS_AND_FINAL_PREP_20261013/
ZHANGWEI_REPORT.md
完整生产源码/common/config/CLI/测试
FILE_SHA256.json（清单列的文件实际全部存在）
SOURCE_INPUT_CONTRACT.json
D_TYPE_JOIN_AUDIT.json（16条逐项）
FINAL_PLAN_BINDING.json
QUERY_PLAN_AUDIT.json
READONLY_SOURCE_PREFLIGHT.json
TEST_RESULTS_FULL.json（逐项）
RESUME_TEST_TRACE.json / FULL_ACCEPTANCE_TRACE.json
EXECUTOR_READINESS.json

37项原回归+同计数内容变动拒绝+sidecar冲突/类型缺失/正确D UNC映射+实际schema query plan验证。
验证类型及source合同贯通真实schema的小型测试plan -> production runner -> 虚拟后端 -> 全计划验收。
未授权gate对真实后端仍零写入，A/B/C及所有严格验收反例不能回退。
将1934清单里的两份旧trace补上传或重新生成本版trace，清单不能引用不存在的文件。
大plan/state留C。普通统计基线files8715067、entities1223721、unique_bytes365007198749、
logical_bytes5085136765894、dirs233660、links4825，类型补丁不改普通内容统计。
目前主计划不是今日业务停更后的实时冻结；离线准备通过也不宣称源无漂移或D全盘完整性。

报告分别列：
CODE_SIMULATED_REVIEW_READY、PLAN_BINDING_VALID、LINK_TYPES_BOUND、
SOURCE_INPUT_CONTRACT_VALID、SOURCE_ACCESS_VALID、
SOURCE_LIVE_PREFLIGHT_PENDING、WRITE_TESTS_NOT_RUN=true、
FORMAT_DONE=false、COPY_AUTHORIZED=false、FULL_MIGRATION=false。
完成离线代码和绑定后回传待ChatGPT审核；只有外部认证阻塞也应如实上传完整结果，不能因它结束为一堆TODO。
在本轮范围连续完成，30分钟可以报进度检查点后继续。

执行电脑=ZHANGWEI；SAM=HOLD。
有后续任务，本文件即桌面下一轮。台式机可继续；笔记本停止待命。
不格式化、不复制、不实盘写链接、不在E写入，不改源数据/账号/网络/MWB/P7。
用户本人未来手动格式化台式机E后才进入真实试验，当前仍准备期。保留有价值HUB证据。
完成后更新INBOX_FOR_CHATGPT.md。
