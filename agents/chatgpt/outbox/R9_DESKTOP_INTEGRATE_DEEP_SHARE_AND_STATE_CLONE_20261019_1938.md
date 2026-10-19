# ZHANGWEI｜四文件读取已审核，完成正式链集成与真实状态副本

task_id: R9_DESKTOP_INTEGRATE_DEEP_SHARE_AND_STATE_CLONE_20261019_1938
parent_task_id: R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019_1840
execution_host: ZHANGWEI
source_assist_host: SAM
status: READY_IMPLEMENT_AND_PREPARE
USER_FULL_MIGRATION_AUTHORIZATION=STILL_VALID
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
FULL_MIGRATION=false
full_plan_acceptance=false

## 本轮技术结论
已核对40ed64a报告、DEEP_SHARE_READ_PROOF.json、prove_r9lp_ro.py、SAM的DEEP_SHARE_FACTS.json和LOCAL_FILE_844424930324643.json。
固定 \\192.168.100.2\R9LP_RO 锚点：卷2387166462，file_id1688849860437540，普通目录。SAM共享Temporary=true、CachingMode=None，仅SAM\ThinkPad Read；未改NTFS ACL。
四个原失败文件均已打开，volume/file_id/size匹配计划；816B SHA 62141a61f0f729dd563160b0835fe4af86cba703a470e181fb0b4c9892e8b007与SAM本机一致。API长度32562/32563/32563/32566。源访问能力阻塞已解除，无需重复四文件能力探测，也不用再要求用户批准原范围迁移。
当前生产代码未集成，所以IMPLEMENTATION_READY仍为false。本任务执行C盘开发、真实旧库只读备份及隔离测试，交齐后停待技术复核；这不是实际E写入/启动命令。

已发现必须修正的准备代码问题：
1. test_isolation.py用temp.replace(dest)覆盖已有目标，只是普通短路径测试，不能证明近限路径可提交，也不能证明生产no-replace保护。
2. r9_state_migrate.py的_fingerprint只比较stage六列，漏item_key/volume_serial/object_type/link_target/parent_key；fetchall对真实大库也不合适。run_bind全表UPDATE未先严格核唯一旧绑定，其他表/元数据和plan映射未证明。
3. r9_temp_name.py用Python len计数，不是UTF-16 code units；不得把32760这个开发阈值当Windows保证。稳定temp名还需绑定state并防碰撞，不能覆盖计划业务文件。
4. prove_r9lp_ro.py的all_ok只合并ok/matches_plan，没合并identity_stable/matches_sam_sha；前后稳定字段只比file_id/size，正式链须按原约束核volume/type/reparse/mtime。已有四文件结果不作废，但正式谓词不能宽松。
5. FULL_RESUME_CONTRACT仍写最后文件blocked、旧digest；ACCESS_ALIAS_CONTRACT的facts_sha256_note实际是Git blob SHA，须明确标成git_blob_sha，内容SHA256另算，不能混用。

## 1｜最小生产集成
在独立C工作目录保留62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3基线，交付可审diff和完整新模块，不就地破坏旧入口/旧run。
采用已经成功的固定深层share访问映射；未成功的通用native支路不做默认，不新增其他share。
合同锁定：
- plan SHA 53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d；
- inventory_prefix使用已核验205字符本机anchor，精确内容见SAM事实；
- alias UNC固定 \\192.168.100.2\R9LP_RO；来源卷2387166462，anchor file_id1688849860437540；
- DEEP_SHARE_FACTS.json Git blob 539fad92f1b277bf86b68fa568583f355f54d284；另记录原始事实文件内容SHA256及可复现算法。
原canonical source、dest和entity_key均不变，实际access_path单列记录。只允许anchor边界以下普通对象尾部，拒绝..、.、空分量、绝对/其他server/share、ADS/驱动器覆盖、重解析跳转；范围外保持原受审路径。不要全局replace。
启动前真实核固定share锚点身份；缺失/变更立即停止，不偷偷退回别的root、不重新认证循环。每个源文件同句柄核plan卷/file_id/大小/普通file及原稳定性约束；不以入口正确代替文件核验。
现有133近限条目只从冻结候选复核映射范围、精确UTF16长度和目标临时路径余量，不再全源扫描、不为重复证明再次读所有内容。原D源映射不变。

## 2｜目标链与C隔离验证
把有界temp名实际接入copy body及恢复/失败清理的同一规则，兼容已记入state的旧temp证据，禁止猜名删除。
使用CREATE_NEW/原生产等价防覆盖创建，temp冲突时核属主/证据或停止，不覆盖已有普通目标、别的run临时文件、计划业务文件。最终提交保持原no-replace行为；目标已存在走原身份/内容验证，不能replace覆盖。
按UTF16单位同时核完整API路径和分量长度，不改最终计划目标名/目录。若同父最短安全temp仍不可访问，停报真实边界，不截短业务路径。
在C的明确测试目录，用本轮真实计划最大目标API长度/最大分量构造等价普通目录深度，实际跑正式backend的创建、写入、flush、无覆盖commit、observe、content_sha、list_nofollow和独立验收路径；不是只测字符串，也不是在E上试。保留可核长度、调用路径和结果。
测试至少覆盖：正常短路径回归；近限四文件等价目标长度与最长分量；temp冲突拒绝覆盖；已有final不同内容拒绝覆盖；中断后按state恢复temp；错误share/anchor/越界映射拒绝。保持原27项相关回归通过。不要为方便测试取消原生产保护。
只清理本任务新建C隔离fixture，不碰E或来源目录。

## 3｜真实state备份及绑定迁移（C写入已授权）
先证实旧32636已退出、没有复制/写state实例；保留旧run和旧文件。
原state：
C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_MISSING_DEST_ROOT_20261015\state\full_1400.sqlite
原run：R9_FULL_RESUME_AFTER_ROOT_FIX_ZHANGWEI_20261015_1400
旧digest：62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3
目标卷：2694002743；目标根E:\BLACKBOX与E:\BLACKBOX_ENGINES；物理盘合同沿用，不格式化。

原合成脚本REFUSING_REAL_STATE防误用可保留。另写有明确exact source/dest/expected old binding的新备份迁移入口，允许以SQLite只读连接读取这个确定旧库，通过SQLite backup API在C新建一致性副本；旧库不得作为写目标、不得改旧run_bind，不复制运行中的裸DB/WAL，不强制checkpoint旧库，不建空state重来。
在新副本上事务化绑定唯一新run：
R9_FULL_RESUME_DEEP_SHARE_ZHANGWEI_20261019_1938
新state放本任务独立C/state目录，必须不存在，防同路径/硬链接别名误用。先校验旧绑定唯一且六字段精确预期，只允许副本run_id/code_digest变更；plan_digest/inputs_digest/dest_volume/dest_root原样。新digest覆盖所有实际执行模块（含新增helper），迁移工具单列hash。
将原run/新run、旧/新digest、plan/inputs、旧/新state路径、备份时间及验证结果写单独provenance报告；不要用原库写操作做验证。
按主键稳定排序流式比较stage全部11列及所有其他既有表、schema/index等；允许差异只列明副本run_bind的两个字段，不能只比六列或总行数。核SQLite integrity及stage分类汇总，原始证据字段逐条保留。真实plan/inputs/destination映射仍一致。
保留至少：
entity DONE=1083975，entity DONE logical_size sum=348928107919；
alias DONE=6689430，dir DONE=233668。
如实测不同，回报差异，不补数、不删证据、不继续启动。
不要重建6GB候选，不修改旧1117/1400状态。
原runner恢复DONE可能重新hash大量内容，须据代码说明真实读量/行为；不为速度静默取消验证，区分logical bytes、实际stream bytes和已保留DONE。

## 4｜一次性交付
回原1840目录并新增本task标识：
- INTEGRATION_REPORT.md：改动、剩余风险、精确启动命令（仅呈现，不执行）、新run/state、IMPLEMENTATION_READY真实状态；
- 所有改动/新增正式模块及精确diff；完整模块清单、每文件SHA256、可重算code_digest算法和新digest，基线digest不变；
- 正式链C测试原始输出与近限API长度/防覆盖证据，不能只贴PASS；
- STATE_CLONE_PROOF.json/provenance：真实备份、完整逐字段比较、计数、绑定及旧库未改证明；
- FULL_RESUME_CONTRACT.json、ACCESS_ALIAS_CONTRACT.json更新为本轮实际新digest/state/事实，copy_authorized=false/full_copy_authorized=false；
- 原四文件读取证据作为已完成引用，修正汇总谓词和稳定性测试；有必要才做增量核验，不重复能力探索。
完成后更新INBOX_FOR_CHATGPT并停待技术复核。不要只ACK后等下一条开发命令：以上C工作现在就可连续完成。未齐不能标IMPLEMENTATION_READY=true；本轮不实际迁移。

## SAM
本机四文件证明和共享任务已完成。保持当前R9LP_RO可用；不重建、不清理、不重启、不继续探测文件，不启动迁移。Temporary共享若意外消失据实回报。无需用户转述或重输密码。
