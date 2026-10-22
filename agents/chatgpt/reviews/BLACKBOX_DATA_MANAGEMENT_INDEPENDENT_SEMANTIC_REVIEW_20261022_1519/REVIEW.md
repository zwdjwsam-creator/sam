# 1507包独立语义复核（非生产验收）

依据：completion_1507/source_reads 中已上传的函数正文。
生产数据/业务API/下载/发布均未执行。本包不是修复部署。

## 确认的发布失败窗口
publish_gate blob c064ba1765d523058cd0822cdbd98e83aed9af4a 中 publish_atomic 顺序：
备份CACHE/CLEAN → wjson(CLEAN_PTR) → wjson(CACHE_PTR) → wjson(FACTS) → LEDGER → refresh。
common blob d55a5d6b39287505012f71c81bbe521edc0b7cbe 的 wjson 使用临时文件+os.replace，仅保证单文件替换，不能使三个文件整体原子。
函数内没有写失败时的回滚处理/恢复事务。
reproduce.py仅从源码AST提取publish_atomic和wjson，用临时目录、PASS矩阵stub到达写入阶段：
- 正常：三文件均NEW；
- CACHE写失败：CLEAN=NEW，CACHE/FACTS=OLD；
- FACTS写失败：CLEAN/CACHE=NEW，FACTS=OLD。
3个预期断言通过。备份存在，但实际函数未自动恢复。此为源码可复现的故障窗口，不说明生产发生过该故障。未测试真实矩阵、Windows进程中断、全局读者一致性。

## 确认的NAV同键优先级
fund blob 69d00f36ed4307d78b0912243204f21823fc8de1 中 _merge_prior_tips：
frames=[新输入]，随后追加旧tip，再(code,day) drop_duplicates(keep="last")。
reproduce_nav.py实际执行该函数，仅mock旧parquet读取：新值2、旧值1，同键输出1。
这确认“旧tip覆盖新输入”的现实现象；若新批次是同日净值修订，会保留旧值。是否违背正式修订策略仍需合同依据，不能擅自换优先级。未证明历史生产已出现错误净值。

## ADJUST静态结论（未运行）
incremental_backward_refresh_r1_EXTRACTS.md完整函数可知：
- date/code为合并键；fetch过滤非法/非正factor，并按code/date去重keep last；
- overlap取缓存<=update_date的最后OVERLAP_DAYS个已有日期，abs_diff>1e-8标dirty；
- dirty代码从FULL_HISTORY_START重取并替换旧代码历史；无dirty时已有目标日则跳过，否则取目标日追加去重；
- publish_successor直接写RELEASE.json和CACHE_PTR，未调用通用publish_atomic，也未在该函数更新FACTS；旧release保留不等于自动回滚；
- 空或不完整接口结果是否阻止新世代发布，在所读main/fetch路径未看到完整标的×日期覆盖门，应作为明确待核项，不推断已导致数据丢失。
恢复语义应据上述控制流说明，不以是否含“state”关键词判定。

## 可重复方式
在一个全新的隔离目录放本包4文件，从HUB既有路径复制以下源码为本地别名：
completion_1507/source_reads/blackbox_daily_increment_publish_gate_r1.py → gate.py
completion_1507/source_reads/blackbox_daily_increment_common_r1.py → common.py
completion_1507/source_reads/blackbox_fund_etf_nav_premium_plane_r1.py → fund.py
执行python reproduce.py、python reproduce_nav.py。后者需已有pandas。
本次已在Linux临时环境完成，无需为回执在台式机重复跑相同用例。脚本不import这些业务模块，只编译指定函数AST；矩阵与旧parquet输入替换为fixture。
结果见RESULTS.json、NAV_RESULTS.json。所有生产就绪、完整度和系统整体验收仍未通过。
