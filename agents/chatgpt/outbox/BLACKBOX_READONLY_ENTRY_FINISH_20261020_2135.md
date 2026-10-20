# ZHANGWEI｜2110安装样本通过，完成入口过滤与输出收尾
task_id: BLACKBOX_READONLY_ENTRY_FINISH_20261020_2135
execution_host: ZHANGWEI
parent: BLACKBOX_BOUNDED_QUERY_ENTRY_INSTALL_20261020_2110
status: READY_TARGETED_ENTRY_FINISH
sample_review: INSTALLED_SAMPLE_AND_RUNTIME_CONFIRMED
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

已实际审2110入口py/ps1与verify结果。确认：
- 实际路径E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY，INBOX概述写成E:\_OPS只是笔误，修正文案，不搬目录。
- 解释器D:\Anaconda3\envs\blackbox_bt_py310\python.exe，3.10.20 64bit，pandas2.3.3/pyarrow23.0.1；原E .venv仍未修。
- runtime_v4 SHA与已审一致；000001.XSHE 09/02..09/10确有7行；09/01..09/10正确coverage拒绝。
这部分不推倒重做。2110仍需完成以下入口级收尾才结案，不扩大业务范围。

## 只改新增_OPS入口/启动器/管理文档，不改审定runtime或生产
1. 小窗过滤必须下推：当前_read_rows执行pf.read(columns=use_cols)，把整年全市场约14列转pandas再按证券/日期过滤，违反2110“先筛小窗、避免全年全部字段读入”的要求。
   改为现有pyarrow Dataset/Parquet filter能力，按明确证券代码+类型正确的日期双端点先筛选，再物化最少列；不新增依赖、不改数据布局。精确核date列实际类型，避免字符串到时间戳端点误差和Hive year schema合并问题。
   允许存储层因row-group没有选择性仍读取物理块，但交付代码不得先把整个年表转成DataFrame再筛。报告实际查询耗时/返回行数、投影列和filter表达式；不要伪称物理IO一定减少。
2. UTF-8证据：pos/neg JSON中的note/product_path/files_used已出现U+FFFD替换字符（例E:\BLACKBOX\����\...）。这不是目录损坏证据，不能从乱码反推改业务目录。
   入口/启动器明确UTF-8输出；捕获stdout原始字节并按UTF-8严格解码，保存UTF-8 JSON；不使用errors=replace或不可逆转码。日志stdout/stderr/exit_code分别保存。保留旧乱码回执作历史，新回执完整中文，核实际路径可解析且无U+FFFD。
3. CURRENT检查位置：当前仅在resolve后、_read_rows前重读CURRENT，不能检出实际行读取期间的变化。保留初始快照，并在_read_rows完成后、输出成功前再次核CURRENT authority/路径/id（必要时小指针字节SHA），变化或权威不可读一律不输出ok=true。无需冻结数据或做全盘hash；临时fixture模拟“读取期间切换”做负例，不切真实CURRENT。
4. --self-check不能在package_error时仍ok=true/exit0。对本入口必需依赖缺失给可解析错误和非零退出；只证明SHA/解释器的检查不要冒称数据可用。_verify_runtime也核实际import模块来自已审runtime路径且SHA匹配，而不只校验硬盘另一份文件后把实际加载值打印出来；CLI正常路径应很简单，异常通过隔离fixture验证。
5. 输入日期按ISO日期校验/规范化，拒绝反向/非法日期和缺证券参数，不猜日期格式。保留已有无窗/单端点/unsupported/coverage拒绝行为；不把空行说成源缺数据或自动下载。
6. 安装文档链需可核：2110报告宣称已连接入口，但未附START_HERE/OPERATING_MAP/既有_OPS README索引diff。补实际改动前后片段及文件路径，保证新E Agent能从原管理入口找到本查询；仅改本任务生成/已授权管理文档，不动根AGENTS/Kernel/HAND/Manifest。

## 完成后的最小验证与交付
先备份当前新增入口/启动器；仅更新这两个新管理文件及索引。runtime_v4三SHA保持原值；若认为必须改它们，先交具体理由与diff，不顺手改。
- 安装后的同一入口重跑7行正例、缺日拒绝，并给严格UTF8 stdout/stderr/exitcode；不只测试C副本。
- 临时小夹具验证过滤前物化边界、日历错误/坏分区拒绝、CURRENT在行读取期间变化拒绝、缺依赖自检非零、实际模块路径/SHA不匹配拒绝。夹具不改真实runtime、CURRENT或数据。
- 记录入口py/ps1最终SHA、固定解释器路径、命令、正例耗时、原3.12环境未修和有限能力边界。
可直接完成本条可逆小修，不再等待用户批准。2110原包保留，新交：
agents/chatgpt/inbox/BLACKBOX_READONLY_ENTRY_FINISH_20261020_2135/
FINISH_REPORT.md / FINAL_FACTS.json / 最终入口源码 / 最小验证输出与文档diff，读回核SHA后更新ChatGPT邮箱。
状态READY_FOR_ENTRY_FINAL_REVIEW，成功后由ChatGPT结案有限只读入口，不宣称全BLACKBOX已恢复。不扩成全量性能审计/策略修复；不动LiteLLM、1814或数据更新。
按用户已授权巡视至22:59领取，本条不延长巡视。
