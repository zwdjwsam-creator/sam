# ZHANGWEI_REPORT — R9_DESKTOP_BIND_SOURCE_FACTS_AND_FINAL_PREP_20261013_2016

host: ZHANGWEI
SAM: HOLD
status: SIMULATED_COMPLETE_PENDING_REVIEW
IMPLEMENTATION_READY=false
CODE_SIMULATED_REVIEW_READY=true
PLAN_BINDING_VALID=true
LINK_TYPES_BOUND=true
SOURCE_INPUT_CONTRACT_VALID=true
SOURCE_ACCESS_VALID=false
SOURCE_LIVE_PREFLIGHT_PENDING=true
WRITE_TESTS_NOT_RUN=true
FORMAT_DONE=false
COPY_AUTHORIZED=false
FULL_MIGRATION=false
WINDOWS_IO_EXECUTED=false

两份事实文件按原始字节核对：D_REPARSE_TYPE_OVERLAY.json SHA 1f6d3bf2… 39583 字节；SOURCE_SHARE_FACTS.json SHA 4355f966… 3608 字节。选用的共享是 shares_relevant 里的 E_DRIVE=E:\ 和 D_DRIVE=D:\。E_DRIVE_share 字段实际指向名为 BLACKBOX 的共享，合同没有采用它，也没有采用 D$。

16 条 D 链接按 source_path 对上计划，数字 tag 都是 2684354563 / 0xA0000003。E 的 4809 条按基线 entries.path 查到同一个 mount point tag。计划 links 现在 4825 条都有 reparse_tag，空 tag 为 0。普通统计没有改：files 8715067，entities 1223721，unique_content_bytes 365007198749，logical_path_bytes 5085136765894，dirs 233660，links 4825。旧计划备份在 plan_v2\MERGED_PLAN.before_tag_bind.sqlite。没有重建计划，没有重算 9GB 输入。

计划身份改为冻结后的 SQLite 文件 SHA256，不再只用行数。摘要 94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba，6025072640 字节，耗时 3.462 秒，没有 WAL。这个摘要没有写回计划文件。同计数下修改 mtime，摘要会变，旧 run 绑定被验收拒绝。

孤立实体查询带上 is_dir=0 和 is_reparse=0 后，实际 EXPLAIN 是 SEARCH paths USING COVERING INDEX ix_entity。不带这两列时仍是 SCAN paths。

桌面只读预检只试了一次 \\192.168.100.2\E_DRIVE\BLACKBOX，WinError 1326，随后没有再试 D 或 16 条链接。SOURCE_ACCESS_VALID=false。源访问失败不构成复制授权。

40 项纯测试通过。A/B/C 和严格验收反例仍在。实盘 NOT_RUN。
