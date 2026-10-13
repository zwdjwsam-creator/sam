# 给笔记本 AI（SAM）｜向HUB交付桌面缺失的迁移元数据

task_id: R9_SAM_METADATA_HANDOFF_20261013_1524
target: SAM
status: READY
COPY_AUTHORIZED: false
FULL_MIGRATION: false

唯一执行方：笔记本SAM。桌面ZHANGWEI本轮停止开发待命，下一轮再接收材料。
用户要求继续迁移准备；由用户本人将来格式化台式机E盘。本任务不格式化、不复制业务文件、不做E盘写入试验。
仅在笔记本C生成/读取迁移元数据并上传HUB；源E/D只读，不改网络、SMB共享、MWB、账号或轮询器。

## 1. 解决明确缺口，不从头扫描

桌面最新报告：
agents/chatgpt/inbox/R9_DESKTOP_EXECUTOR_DEV_20261013/ZHANGWEI_REPORT.md
桌面E base快照与delta SHA已对上；D修复DB缺失，现有\\192.168.100.2\E_DRIVE不可读，故42文件未核验Win32身份。
不再让桌面重复尝试一个不可读共享。本轮由源端直接提供元数据，经HUB交付。
当前桌面已具备9.38GB E快照，因此无需再次上传/传输E base。

## 2. 导出D修复清单的实际一致性快照

源C：
C:\LAN_SHARE_REPORT\BLACKBOX_R9_SELECTED_MANIFEST\SELECTED_D_MANIFEST_REPAIRED.sqlite
不能拿原未修复DB的787b14...来验证修复DB。

使用源只读连接+SQLite backup在新C目录生成独立D快照，不覆盖旧DB。
先写完必要meta，再冻结，不为自身摘要后写而改变已hash快照。
保留供后续adapter使用的实际schema（nodes/dir_enum/queue/meta等已有表），而非仅统计JSON。
只保留迁移元数据，检查无凭据/业务文件内容；不要把日志/凭据树打进交付。

复算：
- 普通文件路径34745，唯一普通文件实体34744，
  unique_content_bytes8163480337，普通目录10637，重解析16；
- 有效源卷+File ID、普通文件size/mtime一致，无未解决身份/枚举错误；
- 记录schema、每表计数、源主机/源卷，integrity_check。
实际与基线不一致则准确列差异，不用报告数字覆盖SQL。
快照实际文件名/路径/SHA、字节大小必须配对。
旧snapshot e3e0f...只能与它对应文件配对，不假定工作库当前hash等于它。

## 3. 在源端核对42条delta身份并提供规范输入

使用已有E delta的42个实际路径，不扫描其他源文件。
调用已审r9_pilot_common_r9fix.py的稳定只读句柄及handle_identity，或同等Win32API，
取得32-bit volume serial和统一64-bit file index、size、mtime、nlinks；不要仅对st_dev截低32位猜测身份。
同句柄观察值前后稳定；源文件变化/不在声明根内/重解析/读属性或身份失败即具体阻塞。
源只读，不读取业务内容hash，也不修改源文件。

原delta SHA 9f1a37...保留历史。
导出新E_DELTA_CANONICAL.sqlite，保留42文件/16目标/空目录/必要普通目录记录及原Python身份供比对。
canonical实体键按Win32源卷+File ID，size不作为实体键；同键size/mtime冲突必须失败。
完成16目标的实际文件记录覆盖复算；null身份/None字符串/遗漏/额外不明重解析不能通过。
若42中某条已变，明确记录，不能静默改元数据再宣称原输入未变。
为新delta记录真实路径/SHA/大小、canonical字段口径、核验时间及错误数。

## 4. 实际经HUB交付：压缩的是元数据，不是业务数据

桌面无法读取笔记本C路径，仅交本机path没有解决阻塞。
本轮特别允许把约50MB D元数据快照压缩后上传HUB；
新规范delta也一起交付。不是打包355GB BLACKBOX业务数据，不上传9.38GB E索引副本。

新目录：
agents/chatgpt/inbox/R9_SAM_METADATA_HANDOFF_20261013/
提交：
- D_REPAIRED_SNAPSHOT.sqlite.gz
- E_DELTA_CANONICAL.sqlite（或.sqlite.gz）
- HANDOFF_CONTRACT.json
- SAM_REPORT.md
- schema/统计SQL及导出程序
合同列每个HUB确切artifact路径、压缩文件SHA、解压后SQLite字节SHA/大小、schema/计数、生成来源。
压缩包仅含一个明确元数据文件；桌面解压到C新目录，不按包内任意路径写出。
若单件过大，可固定命名分片，每片SHA/序号/大小和重组后SHA全列；不上传业务内容或凭据，不force-push。
通过已存在GitHub凭据上传，远端GET/文件字节或blob确认提交；没实际上传则HANDOFF_READY=false，不能只声明“本机留档即完成”。
保留旧材料，不删除HUB其他目录。

最小验证：
本机C新路径解压并核验实际SHA/integrity/表计数与冻结输入一致；
新delta规范Win32身份都有值，42条与16目标计数一致，错误时不ready。
记录实际结果，不用“hash长度64”或统计存在当真正validator拒绝测试。
可同时指出现有共享存在/不存在的只读状态，但不改共享权限/网卡或反复修网络。

## 5. 回报与下一执行方

HANDOFF_READY = 两份完整元数据都实际在HUB、路径/SHA成对、结构统计验证通过、42身份规范完成。
COPY_AUTHORIZED=false、FULL_MIGRATION=false始终保持；不启用交易或后台业务。
本轮最多30分钟，通常只需元数据备份/42次定点核验/压缩上传；
预算到交PARTIAL及可续接状态，不从头重扫。

更新INBOX_FOR_CHATGPT.md，指向SAM_REPORT和HANDOFF_CONTRACT。
完成后SAM停止待命，等待ChatGPT发桌面接收+继续开发令。

审核提示：桌面现有r9_formal_executor.py还不是完成的正式执行器：
validate-input/preflight-readonly目前仅打印说明，plan只统计E与overlay、未合并D，
即使给了D路径也未导入。下一轮由桌面修成真实validator和统一计划。
SAM不要为此另造桌面执行器，不重复原1GiB实验。
