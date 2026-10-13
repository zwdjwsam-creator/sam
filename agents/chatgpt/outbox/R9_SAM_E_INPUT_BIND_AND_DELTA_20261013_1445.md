# 给笔记本 AI（SAM）｜迁移清单最后补齐：E索引绑定 + 16处依赖内容

task_id: R9_SAM_E_INPUT_BIND_AND_DELTA_20261013_1445
target: SAM
status: READY
scope: MIGRATION_METADATA_PREPARATION
COPY_AUTHORIZED: false
FULL_MIGRATION: false

本任务为用户2026-10-13重新推进数据迁移的独立指令，替代旧“输入包已READY”结论；与鼠标键盘/网络/自动收件任务分开。
执行方为笔记本SAM。台式机保留已通过1GiB样本，等待输入包审核后开发正式执行器。
本轮允许C盘代码、清单、日志及HUB回传；源E/D只读。不改网卡、IP、MWB、AUTOHUB调度或账号，不启动业务全量复制。

## 1. 直接复用成果

读取R9_PILOT_FIX_20261011下：
R9_SAM_ED_INPUT_PACKAGE_REPORT.md、R9_SAM_ED_INPUT_CONTRACT.json、
R9_SAM_DEPENDENCY_CLOSURE_EVIDENCE.json、build_ed_input_package_r3.py。
原样本PASS不重做；选定D已审34744文件实体、8163480337内容字节，原DB保留。
原输入快照fbd252446d77df897e5c254f71a0835cc20f33d36d1472bc3013fca9c664767a保留，不覆盖。
先现场核验SAM、源E/D卷身份及C盘可用空间，具体不符就报告。

## 2. 本轮要解决的两个具体缺口

A. E主索引引用未绑定内容：
E:\BLACKBOX_MIGRATION_AUDIT_R1\metadata\filesystem_inventory.sqlite
合同index_sha256=null，约9.38GB索引因大小跳过了SHA。
新40MB包的SHA只覆盖包内引用，不能覆盖这个外部索引；不能由exists=true把E_stats_status写成PROVEN。

B. 16个D→E目标的证据其实来自E_INDEX_SIDECAR_16_LIVE.sqlite（共17行）。
其中目录记录file_id/volume_serial为空，subtree_unique_entities/subtree_content_bytes也为空，
并注明原E索引中缺失；当前却in_e_inventory=true/content_coverage_proven=true。
目录存在/计数不能替代普通文件进入复制清单。
build_ed_input_package_r3.py仅把e_index_ref写入包，没有合并这份sidecar内容；正式执行器仅按旧E索引复制会遗漏新增内容。

## 3. 完成E主索引的可靠绑定

不扫描整棵E文件树，不读全库业务文件内容hash。只处理已有元数据索引。
检查原索引是否有WAL/活动写入、实际schema/meta、扫描完成/错误记录。
- 若确为静态独立数据库，在保持只读和一致性前提下流式算完整文件SHA，并记录实际大小/时间、卷身份及哈希前后不变证据。
- 若不能保证独立一致性，使用SQLite只读源+backup在C创建一致性元数据快照，再对快照算SHA；先确认空间充足，不覆盖任何已有文件。
- 若空间不足/无法稳定绑定，直接交付具体阻塞，不删除业务文件腾空间，不伪称PROVEN。
主索引+sidecar可以继续分文件使用，不强制把8百万路径复制进一张新表；每个实际输入文件须有精确路径、字节SHA和schema。
源10月8日索引是历史基线，不能宣称今日业务内容已冻结；正式执行器逐实体核验源漂移。未证明的历史覆盖问题单列，不从目录名猜测全D缺口。

## 4. 将16个目标的真实内容补进可执行清单

只对现有40链接证据中的16个D_TO_E终端目标定点核验：
完整枚举普通目录全部子项，中文长路径安全；记录空目录；不跟随重解析点自动展开。
普通文件逐个记录实际path、source-relative-path、源卷身份+File ID、size、mtime、范围内硬链接路径。
遇重解析记录真实类型和目标，再检查其终端是否被已有E/D输入或本次delta纳入。
枚举EOF成功及无身份错误才能证明对应子树完整；错误/中断留未完成队列。
将新增/更新文件、目录、链接写C盘E delta manifest，建立明确adapter/合并视图：
base E索引 + 本次E delta + 已审D清单。
同路径更新以delta中的现场条目为准；去重依据源卷+File ID；删除/替换单列，不把目录壳当普通文件。
不能仅写sidecar JSON摘要而不让正式输入读取它。

每个16目标交出：
精确记录来源（BASE_INDEX/DELTA）、子树普通文件路径数、唯一实体数、唯一内容字节、
未解决错误数、枚举完成状态、与base差异、关联输入SHA。
零文件子树也可通过，但必须有完整枚举证据，不能用null当0。
对40条链接计算闭合：alive、终端普通内容纳入、无错误/环/未解决重解析、映射完整；
sidecar只有目录、少一个实际文件或身份失败必须不闭合。
源业务树不补写/重建链接，不修改原E索引。

## 5. 发布可以给台式机开发的输入合同

C盘新目录建议：
C:\LAN_SHARE_REPORT\R9_E_INPUT_BIND_AND_DELTA_20261013\
正式输入文件均生成后保持只读；所有meta先完成，再做一致性快照和SHA，摘要另存。
合同明确base_index_path/SHA、e_delta_snapshot_path/SHA、d_snapshot_path/SHA、package_path/SHA；
将所有外部引用及adapter规则一并绑定，新快照不能只签路径字符串。
D字节、E历史字节与本次增量/覆盖后总量分列，独立复算统计，不用旧报告数字覆盖SQL结果。
校验target相对路径映射/碰撞/逃逸；目标仍是台式机E: MarketData 806508DF，BLACKBOX及BLACKBOX_ENGINES。
INPUT_READY_FOR_DEV与COPY_AUTHORIZED分开：可审输入通过后才能ready_for_dev=true，COPY_AUTHORIZED始终false。
若部分完成，写PARTIAL并精确列剩余输入/目标/错误，不能泛称全部READY。

验证只做必要合成用例：
1. 主索引无此路径，delta含正确文件时merged输入能够枚举/去重它。
2. 只留目录壳或遗漏一个文件时，内容覆盖/闭合不得PASS。
3. 外部主索引或delta内容变化却保留旧SHA时，输入验证失败。
4. 同实体硬链接、零文件已完整枚举目录分别统计正确。
提交实际adapter及测试源码/结果，不用手工置最终true。

## 6. 时间与回传

预计完成一个最多30分钟批次；每5分钟记录进度。超预算保留完整队列/进度上传PARTIAL，恢复须接续不能从头。
若任一目标明显超出本轮预算，只完成有界元数据进度；不扩大到MIN_sandbox、全ARCHIVE或整盘扫描。
HUB新增目录：
agents/chatgpt/inbox/R9_E_INPUT_BIND_AND_DELTA_20261013/
提交SAM_REPORT.md、INPUT_CONTRACT.json、TARGET_16_COVERAGE.json、TEST_RESULTS.json、源码/diff；
大SQLite留本机，HUB只上传路径/SHA/schema/计数。报告列出下一步台式机开发所需精确参数。
同时写本任务独立回执，不覆盖鼠标键盘等其他任务报告；原迁移材料保留，不清空HUB。
完成后停止，等待ChatGPT审核，再转台式机“正式执行器开发+预演”，当前不复制业务数据。
