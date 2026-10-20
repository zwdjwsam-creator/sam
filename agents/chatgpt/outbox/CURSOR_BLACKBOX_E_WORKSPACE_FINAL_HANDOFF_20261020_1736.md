# ZHANGWEI｜1728资料迁移通过，补E工作区真正启用与路径衔接

task_id: CURSOR_BLACKBOX_WORKSPACE_HISTORY_MOVE_20261020_1728
followup_id: CURSOR_BLACKBOX_E_WORKSPACE_FINAL_HANDOFF_20261020_1736
execution_host: ZHANGWEI
status: FILE_HISTORY_ACCEPTED_E_SESSION_VALIDATION_PENDING

ChatGPT已核REPORT/ACK/BROWSER_PROBE/复制清单。136普通文件初次复制hash相同、历史检索4项和C冻结保留可接受。
ACK明确当前Agent仍D:\CursorDualRouteConfig；BROWSER_PROBE亦明确existing session。因此HUB/Browser成功仅算D旧会话，不能作为新E Agent验收。
本followup补实际启用，避免又要求用户重做项目迁移。

1. 发布完整脱敏BLACKBOX.code-workspace和AGENTS新增段落，核主根确为E:\BLACKBOX。当前workspace folders同时含"."与其子目录_OPS/CURSOR_WORKSPACE，根已包含子目录；若没有必要的独立设置，简化为单一BLACKBOX根，避免重复遍历/索引（新改动须记diff）。
2. CONFIG_DIFF说paths.ps1已把DualAIRoot改到E，而COPY_HASH_MANIFEST说136全匹配。分清“复制当时hash”和“有意修改后的最终hash”；提供最终changed-files清单/确切diff，不把预修改hash当当前文件证明。
3. secrets未迁是事实，但E脚本仍指向本目录cursor_ai_stack\secrets会缺文件。明确只需HUB通道的实际入口和凭据加载路径：优先复用本机已有认证；必要时只读引用D现有受保护凭据路径（D已保留），写清这一剩余依赖，不上传/打印secret，不用缺凭据的E入口称可用。禁止复制浏览器cookie/全局state.vscdb，LiteLLM/API仍不启动。
4. 当前D窗口保留回退。检查本机已安装Cursor官方CLI/help支持的打开工作区方式，直接打开E:\BLACKBOX\BLACKBOX.code-workspace新窗口（用受支持new-window而不是关闭D；若该E窗口已存在就复用，不重复开）。这是用户已授权切换，不需要再问是否可以打开。不要伪造此步执行结果。
5. 新E窗口内Agent才做最终验证：
   - 当前workspace URI/主根证据为E；
   - 真正读取根AGENTS→README/历史索引，引用真实历史；
   - 从E维护入口发唯一HUB ACK并读回；
   - live官方Browser标签页/快照，无业务测试页可撤销输入，及GPT页可见性；不发网页测试消息。
   D Agent不能替新E Agent认领这项，CLI/headless不能假装附着GUI Browser。
6. 如果当前工具只能打开新窗口、无法在E GUI启动新Agent/输入任务，就先完成1-4，把精确接续提示写入E项目README和NEW_E_AGENT_HANDOFF.md，并将提示复制到本机剪贴板（可用时）。回NEEDS_ONE_UI_ACTION，只要求用户在已打开的E窗口新对话发送“HUB”，不要再要求用户找配置开关/重复复制。必须说明已打开哪窗口、为什么当前D会话不能代替E会话，以及是否仍有原GPT登录需要本机正常处理。
7. 报告文件迁移完成/E会话已打开/E Agent检索/HUB/Browser各项实际状态，未跑的不标PASS。不重新搬136文件/全盘扫描/R9验收。此前R9 FULL技术验收保持通过。

所有回执回原1728目录，新增FINAL_CONFIG_DIFF.md、E_WORKSPACE_CONTENT.json（脱敏）、E_SESSION_VALIDATION.json或NEW_E_AGENT_HANDOFF.md，更新INBOX_FOR_CHATGPT。
D原目录/C冻结资料/已验收业务数据不删不改，除本用户工作区迁移授权的E管理文件/入口最小更改。
