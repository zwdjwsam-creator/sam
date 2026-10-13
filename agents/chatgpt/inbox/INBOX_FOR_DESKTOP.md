# ZHANGWEI台式机｜严格验收与真实Win32包装修复

task_id: R9_DESKTOP_STRICT_ACCEPTANCE_WIN32_FIX_20261013_1934
target: ZHANGWEI
status: READY
phase: PREPARATION_ONLY
instruction: agents/chatgpt/outbox/R9_DESKTOP_STRICT_ACCEPTANCE_WIN32_FIX_20261013_1934.md
supersedes: R9_DESKTOP_CLOSE_REPARSE_RESUME_ACCEPTANCE_20261013_1910

仍由台式机执行，SAM=HOLD。
完整包20个文件SHA/大小匹配，33项纯测试独立复跑通过；A/B/C与目录/重解析模拟成果保留。
新反例：缺目标FileId/volume、缺type、缺reparse_target、plan孤立entity，full_acceptance仍true。修NULL/必需字段及完整计划key核验。
真实identity返回mtime_ft而reader返回ISO，copy仍读mtime，须接正确转换/比较；补真实Win32包装的创建模式、64位声明、reparse原始buffer解析及no-follow错误处理。
验收每唯一实体hash一次、合理复制块及磁盘SQLite暂存；不重扫/重建已有计划。
IMPLEMENTATION_READY=false
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
本轮仍准备期，不格式化、不真实复制/链接试验、不在E写入。
回执：agents/chatgpt/inbox/R9_DESKTOP_STRICT_ACCEPTANCE_WIN32_FIX_20261013/ZHANGWEI_REPORT.md
