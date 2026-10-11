# 给台式机 AI（ZHANGWEI）｜只修长路径验收，复验现有1GiB副本

任务ID：R9_DESKTOP_LONGPATH_ACCEPTANCE_20261011_1301
取代：R9_DESKTOP_FINISH_STALE_QUERY_20261011_1227（停止及复制阶段已完成）
唯一执行方：台式机 Cursor。笔记本 SAM 待命，不承担本轮开发或扫描。
状态：待执行。

## 1. 已审证据 / 不得倒退重做

ChatGPT已读取最新主报告、原始复制日志、copy-record及原验收JSON：
- 挂起findstr定点停止，cmd自然退出；无需再次处理旧PID或诊断UAC。
- 普通预检PASS；COPY_OK，662实体，22998路径，唯一字节1064950668。
- 本次唯一run_id：2026-10-11T1230430800。
- copy-record：C:\LAN_SHARE_REPORT\PILOT_COPY_RECORD_2026-10-11T1230430800.json。
- 验收失败：HASH_COVERAGE=650，PATH_IDENTITY_COVERAGE=22082，MISSING_DEST_PATHS。
- 原验收的1064153681目标唯一内容字节、1065459712分配空间只是未完整覆盖的统计，不作为全样本最终结果。
- 报告称 GetFileAttributesW + 长路径对22998路径复核无真实缺失，支持Path.exists误判，但还不能据此判整体PASS。

禁止重新运行复制器；禁止清空/覆盖/重建/改名实验目录；禁止改清单与本次copy-record；禁止源E/D写入、全量迁移或重扫。

## 2. 只修验收路径访问层

在C:\LAN_SHARE_REPORT保留验收器现版备份并记录SHA。
优先仅修改 acceptance_script_r9_1g.py；如确需共用函数，局限新增长路径辅助函数，保持复制器及既有安全逻辑不变。

问题定位：
- 当前 dest_paths[0].exists() 和 dp.exists() 使用未扩展路径，先于已有长路径句柄打开而误判缺失。
- 不能只修exists而遗漏os.walk目录枚举、相对路径计算、重解析点检查。

实现要求：
1. 所有目标文件/目录的真实I/O统一用现有 to_win_long_path 转换后的路径，或等效可靠Win32宽字符API。
   本地 E:\ 转为 \\?\E:\；已有前缀不重复，UNC规则保持正确。
2. 存在性优先使用现有GetFileAttributesW/get_attrs辅助逻辑，或直接稳定句柄打开并分类错误。
   只有实际“文件/路径不存在”可记MISSING；权限/路径/API其他错误独立记deficit，不得吞掉或视作存在。
   注意get_attrs构造的OSError可能在errno中携带Win32码；按实际实现读取，不假设只在winerror中。
3. 目录遍历也用扩展长路径根，保留onerror及不跟随重解析点规则。
   用相同表示形式计算relative_path后再与清单相对路径比较，
   不得因多一个\\?\前缀而把合法文件算EXTRA，不得用粗暴字符串替换绕过目标边界检查。
4. 保留目标根/祖先及遍历遇到的重解析点检查；额外文件、枚举失败、真正缺失仍必须FAIL。
5. 不降低662实体/22998路径完整覆盖，不跳过SHA、不从缺失名单中直接删除长路径项；
   空清单/局部验收/复制记录不完整不能PASS。
6. 内容SHA按实体比较本次稳定源句柄复制记录，链接身份检查覆盖全部路径。
   唯一内容字节、分配空间按目标卷+File ID去重。
   覆盖不足时空间可列为PARTIAL统计，但不得将其当完整防膨胀通过。
7. 不改系统LongPathsEnabled注册表，不要求重启，不提升权限来掩盖API问题。

## 3. 小型回归：在C盘，不动真实目标

创建少量中文长目录/长文件名（路径超过260、300字符，单段合法）及硬链接合成样本：
- 长路径真实存在，内容与链接正确：完整验收主流程可PASS；
- 真正删除一个合成样本路径：FAIL；
- 同长度改坏合成文件内容：FAIL；
- 注入目录枚举错误：FAIL；
- 清单外长路径文件：FAIL；
- 同组链接分裂/跨组错误合并继续被拒绝。
测试数据只在C盘新建专用临时目录；不重用或自动删除未知旧目录。
提交测试源码与逐项结果，不只测试helper；正常用例不能靠删deficit或mock最终verdict通过。
不重复其他无关历史实验。

## 4. 在现有副本上完整只读复验一次

小型回归通过后，允许直接运行修订验收器：
python acceptance_script_r9_1g.py
  --copy-record C:\LAN_SHARE_REPORT\PILOT_COPY_RECORD_2026-10-11T1230430800.json
  --dest E:\BLACKBOX_MANIFEST_PILOT_R9_1G
  --log C:\LAN_SHARE_REPORT\ACCEPTANCE_R9_PILOT_ZHANGWEI_LONGPATH.json

不带 --limit-entities 或 --dry-structure-only。
先核验主机ZHANGWEI、目标卷serial806508DF与既有GUID、清单SHA
cfb831ecc0a85fec0137b74a12162e169828d708ff57961df906deffb185c041
及本次copy-record绑定。
不要重跑要求“目标不存在”的复制预检；现在目标存在是正确状态。
真实目标只读，不补文件、不重建链接、不重拷，不重复全量源UNC哈希探测。

PASS必须具备：662实体哈希、22998路径身份全部完成；
目标唯一内容字节1064950668，组内链接一致、跨组无误合并；
无真正缺失/额外文件/异常重解析点/枚举错误；所有必要证据完整。
否则保留FAIL并列出真实异常，不自行修目标。

## 5. 回传HUB并结束

原包 agents/chatgpt/inbox/R9_PILOT_FIX_20261011/ 内更新：
- 验收器完整源码（以及确实改动的common），代码差异、修改前后SHA。
- 小型测试源码及结果。
- ACCEPTANCE_R9_PILOT_ZHANGWEI_LONGPATH.json。
- R9_ZHANGWEI_LONGPATH_ACCEPTANCE_REPORT.md。
- 补交上一轮“22998路径长路径复核0缺失”的实际脚本/JSON（如存在）；没有独立材料就说明是报告层结果，不伪造。
简报列出最终覆盖计数、内容/链接结果、去重内容字节、分配空间、原复制前后空闲差及当前空闲、复验耗时。
原ACCEPTANCE_R9_PILOT_ZHANGWEI.json保留，不覆盖失败证据。
更新INBOX_FOR_CHATGPT.md。完成后等待审核，不自动开始全量迁移。
D完整性未证实仍保留；本次PASS仅证明该样本的复制和链接方法，不证明全库完成。
当前运行/失败/诊断证据有价值，本轮不再删除；不重传已清理的冗余测试输出。
