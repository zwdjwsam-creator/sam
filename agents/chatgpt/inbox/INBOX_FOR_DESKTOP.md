# ZHANGWEI 台式机｜剩余批次、核验恢复及全计划验收

task_id: R9_DESKTOP_FINISH_BATCHES_AND_VERIFIED_RESUME_20261013_1902
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
instruction: agents/chatgpt/outbox/R9_DESKTOP_FINISH_BATCHES_AND_VERIFIED_RESUME_20261013_1902.md
supersedes: R9_DESKTOP_BATCH_RESUME_ACCEPTANCE_20261013_1852

仍由台式机执行，SAM=HOLD。
path映射、虚拟alias实际存在、missing观察及正常二次零写入已独立复跑PASS，成果保留。
恢复尚未成立：ChatGPT模拟篡改代表文件内容/FileId和alias卷/FileId后，production_run仍直接复用done并按PRESENT跳过无关alias。
本轮完成目录/重解析批次、真实完整观察器、三中断点的核验恢复、绑定全计划验收；先封住模拟合同误接真实后端的路径。
完整交付源码/依赖/CLI/测试及逐项输出，不仅增量PY。不重扫/重建已有计划。
IMPLEMENTATION_READY=false
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
本轮仍准备期，不格式化、不真实复制/链接试验、不在E写入。
回执：agents/chatgpt/inbox/R9_DESKTOP_FINISH_BATCHES_AND_VERIFIED_RESUME_20261013/ZHANGWEI_REPORT.md
