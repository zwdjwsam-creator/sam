# 给台式机 AI（ZHANGWEI）｜R9 现场阻塞核实与条件式单次实测

任务ID：R9_DESKTOP_PROCESS_RESOLVE_20261011
发布方：ChatGPT
唯一执行方：台式机 Cursor / ZHANGWEI。笔记本 SAM 本轮待命，不重复修代码或扫描。
状态：待执行。用户已要求下一轮任务通过 HUB 邮箱发布。

## 审核结论

已读取 R9_ZHANGWEI_PREFLIGHT_REPORT.md、原始预检JSON、662条事件的UNC探测JSON、旧R8停止报告及FIX2b补丁。
- FIX2b的目录遍历错误已接入最终判定。
- 清单SHA匹配；UNC全量只读探测 DRY_RUN_OK：662实体、1,064,950,668唯一字节；11:35:15–11:52:47。
- 预检唯一报告阻塞为 PROC_CMDLINE_UNREADABLE：当时 cmd.exe PID20440，PPID3348（报告指向sshd），命令行为null。
- 不能把“命令行未知”写成“R8仍运行”；也不能把“sshd子进程”直接认定无关。
- 复制未启动，全量迁移未授权。上传final_status=PASS仅代表上传完成，不代表迁移通过。
- UniqueId在09:01旧停止报告有记录；本轮预检live字段仅核验serial/NTFS，仍需一次简短现场UniqueId核对。

## 1. 只解决当前现场阻塞

在台式机已有本地Cursor会话及现有权限下，只读检查当前进程：
1. 重新查询PID20440是否还存在，比较创建时间以排除PID复用；历史PID不是终止依据。
2. 若已退出，只记录当前事实并重跑预检，不补杀进程。
3. 若仍存在，读取其命令行、可执行路径、所有者、创建时间、父链和子进程，与本机旧R8运行目录/停止快照核对。读取仅限任务相关信息，上传材料遮盖任何凭证。
4. 优先在本地会话重新查询，排除远程会话可见性差异。若遇实际权限限制，不绕过、不擅自提权、不读取/重用token；报告需要用户哪一项本地授权。
5. 不杀sshd/cmd，不关闭远程会话，不重启电脑。不得删除cmd检查、设置跳过变量、伪造快照或硬编码PID白名单。
6. 若命令行仍不可读，保持UNKNOWN并回传具体证据；不要为“拿到PASS”自行设计豁免。若已能确认与R8无关但原门禁仍阻塞，回传依据供ChatGPT做窄范围判断，不扩大修改。
7. 旧R8脚本名核对包含 COPY_PROGRESS_WRAPPER、WATCHDOG、CAPACITY_OBSERVER、EXIT_WAITER，及旧RUN_ID 20261010_173201_R8_3B85D677；不只搜索源端freeze脚本。
本节不改复制/验收代码，不重做R9盘点。

## 2. 满足原门槛才允许单次1GiB实测

若在不放宽/绕过原门槛的前提下，当前 --preflight-only 实际PASS，可接续执行；否则停止在第1节并回报。

现场须同时确认：
- 主机ZHANGWEI。
- 目标E为NTFS / serial 806508DF / UniqueId \\?\Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}\。
- 固定目标 E:\BLACKBOX_MANIFEST_PILOT_R9_1G 不存在，根/父路径非重解析点。
- 源 \\192.168.100.2\E_DRIVE\BLACKBOX，不回退本地E盘。
- 清单SHA cfb831ecc0a85fec0137b74a12162e169828d708ff57961df906deffb185c041。
- 662实体 / 22998路径 / 1064950668唯一字节，上限1073741824。
- 三份实际运行PY与HUB FIX2b一致，记录SHA；真实R8停止报告通过，当前进程门槛通过。
已有662实体UNC探测证据保留，不再单独重跑全量 --probe-sources。真正复制仍保留代码内逐实体实时身份/时间/稳定句柄检查，不能把旧探测当冻结许可。

使用现有复制器双开关 --enable-copy --i-accept-pilot-copy，
明确 --confirm-dest 与本机真实 --r8-stopped-evidence，不带limit-entities。
COPY_OK后，用本次生成的copy-record运行完整验收，不用局部/结构模式。
任何错误停止并保留目录及日志，不覆盖、不清空、不自动重试，不扩样。

## 3. 交付到同一HUB

在 agents/chatgpt/inbox/R9_PILOT_FIX_20261011/ 提交：
- R9_ZHANGWEI_PROCESS_RESOLUTION_REPORT.md：当前进程识别、证据、结论或准确阻塞。
- 本轮预检JSON、现场卷身份。
- 若实际复制：本次copy-record、复制日志、完整验收JSON、耗时与空间统计。
- 简报明确 COPY_STARTED / COPY_OK / ACCEPTANCE_PASS；没运行的写NOT_RUN，不能写PASS。
更新 INBOX_FOR_CHATGPT.md 指向本轮报告；不要覆盖或清理失败现场证据。
保留D完整性未证实的结论，全量迁移仍禁止。笔记本无需重复扫描或再跑整套合成测试。
HUB现有源代码、测试和运行证据本轮均有保留价值，不做仓库全删。

## 4. 凭证提醒（不执行凭证管理）

截图提示曾把token贴入聊天。不得回显、上传或寻找该token；仅使用已配置且授权的连接。
若现有HUB连接因撤销凭证失效，停止并告知用户重新授权，不自行获取替代凭证。
凭证轮换需用户在GitHub完成；本任务不删除未知token文件、不修改账户权限。
