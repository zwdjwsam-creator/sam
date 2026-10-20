# ZHANGWEI｜1925代码复核不通过，在候选内修复后重交
review_id: BLACKBOX_COVERAGE_CANDIDATE_REVIEW_20261020_1940
execution_host: ZHANGWEI
parent: BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925
status: CHANGES_REQUIRED_NO_DEPLOY
COPY_AUTHORIZED=false
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED

已实际读取两个候选模块、测试、resolver和控制面调用者，并在ChatGPT独立环境运行受控复现。生产未改是正确的；TEST_RESULTS all_pass=true不能接受为质量通过。本条为原候选任务的具体修复令，不再扩大范围或只交文字解释。
审查目标：common SHA194f012f…eeacd，gate SHAde9d49aa…6cc1。

## 阻塞项（必须修）
1. 发布门会放过实质退化。gate用pdn*0.5自创阈值；_product_cov丢弃日期集合，不能检出等数量日期被替换。独立运行原gate（只替换覆盖提取输入）得到：
   - parent100个日期→child60个，丢40个，publishable=true；
   - 数量/min/max相同但替换一个内部日期，丢1个原日期，publishable=true；
   - parent缺失，或parent/child都缺失，仍publishable=true。
   删除无合同依据的百分比。需核必保留的父覆盖与子覆盖集合/合同，任何必须保留的日期丢失拒绝；必要输入/产品/基线不可验证则UNKNOWN/拒绝。空products不能轻易PASS，调用范围/关键产品校验要有合同依据。允许新增日期不是允许丢旧日期，不以count/min/max代替集合。
2. 提取失败可能伪装成功。product_date_coverage跳过坏分区/未知日期列后，只要其它文件有日期就status=OK。独立模拟good+bad分区，实际返回errors=[bad.parquet:OSError]，同时OK/FULL_HISTORY。异常必须传递为不可验证，所有调用者/门不能以成功子集宣称完整。RAW/cleaning同样except:continue会将读取失败误作真缺，必须区分未知、确定无数据、完整。schema失败不能退回pd.read_parquet(fp).head(0)无界读全表。
3. 模式/能力判定过宽。infer_mode仅需2个日期便给要求FULL_HISTORY的产品标FULL_HISTORY；任何_PIT_R1含模糊date列又可能被标DAILY_HISTORY。必须用实际产品合同/有效范围/覆盖依据决定；不支持的产品或语义不明确字段显式拒绝，不靠任意date命名猜。FULL_HISTORY标签不能等同只有多日期。新测试必须证明此类输入不会被resolver/gate误放行。
4. 真实调用契约不兼容。control_plane_build.write_reports读取diag_full["cache"]["coverage"]和coverage_mode；候选classify_stock_daily仅平铺cache_gap_count等，根本无cache键或coverage_mode，原调用会KeyError。补齐实际消费者要求的结构/语义或明确支持范围并阻止不兼容调用。RAW/cleaning扫描只选起止两年，跨3年会漏中间；文件模式是否漏incremental/gapfill需据实际索引/合同核。未经完整来源检查不可给TRUE_MISS_AFTER_ALL_PLANES/download_required=true。当前9/1缺口先降为“候选观察待验证”，不授权重下/补更或改数据。
5. 测试存在假绿。resolver_coverage_semantics仅import resolver，未调用resolve_product就写PASS=True；unsupported_or_undated测试允许任意非空日期当通过，不能证明不支持会拒绝。改为实际候选调用链与严格断言，不能用弱化断言“修好”测试。失败/异常应令整体失败，覆盖两模块的真正gate逻辑而非只比枚举。
6. 日历/时间边界：find_calendar取glob字典序最新非权威引用，字段未知时退到第一列，均需按现有正式日历合同核并保守拒绝。区分有效日历中合法纯周末/假期零交易日与日历未覆盖/不可读取；不能一律当文件失效。样本日期比较用统一日期/时间类型，避免字符串端点歧义。

## 已附独立复现
agents/chatgpt/inbox/BLACKBOX_COVERAGE_RECONSTRUCTION_CANDIDATE_20261020_1925/review/ROOT_REPRO_1930.py
该脚本为审查用受控输入/错误注入：gate用覆盖结果替身，坏分区用模拟pyarrow元数据和日期提取，不是用户真实Parquet复验；用于复现逻辑缺陷。相同日期集退化还额外用原gate+product_date_coverage替身验证（未替换gate内部逻辑）。本地无pyarrow，未声称跑过Windows真实数据。
请将上述行为写成期望“拒绝/UNKNOWN”的严格回归，用真实小型Parquet临时夹具补分区异常测试。不要仅让复现脚本输出变化而无断言。

## 本轮执行/交付
仍只改C候选，不部署、不改E源码/Manifest/CURRENT/RAW/sealed、不重建业务索引、不下载、不跑控制面写入。
可把原resolver和控制面必要调用者复制到C，改C输出路径、用小型夹具测试实际调用（说明所有适配diff），禁止运行原main写生产。
完整正/反例：无丢失允许、丢1日拒绝、等量换日拒绝、基线/关键产品缺失拒绝、坏分区未知、未知列/产品拒绝、实际consumer结构、跨年/gapfill发现、resolver实际调用、合法零交易日与日历不足区分。范围不能证实就保持不可验证，不自造政策。
旧1925包保留。新交 code_v2/、tests_v2/、CONTRACT_MATRIX_V2.md、TEST_RESULTS_V2.json、REVIEW_PACKAGE_V2.md，报告旧审查点逐项结果和全部精确SHA，上传并读回。时间上无需为了快速回执凑all_pass，完成可审实现再交。
状态CANDIDATE_V2_READY_FOR_REVIEW或BLOCKED_WITH_SPECIFIC_GAP，原1910/1925未验收为生产。新Agent入口文档也不能把已驳回候选写成正式能力。无新增SAM工作，LiteLLM/1814不动。
