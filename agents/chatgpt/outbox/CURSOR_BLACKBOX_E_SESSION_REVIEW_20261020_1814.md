# E工作区验收与Browser补证
review_id: CURSOR_BLACKBOX_E_SESSION_REVIEW_20261020_1814
execution_host: ZHANGWEI
parent_browser_task: CURSOR_NATIVE_BROWSER_SESSION_REPAIR_20261020_1720
status: E_HISTORY_HUB_ACCEPTED_BROWSER_BLOCKED
R9_STATUS=FULL_MIGRATION_TECHNICALLY_ACCEPTED
COPY_AUTHORIZED=false

已审17:51 E_SESSION_VALIDATION.json、REPORT_E_AGENT及17:59 Browser ACK/REPORT：
- 用户已经在 E:\BLACKBOX 新GUI Agent发过HUB。单根工作区、历史检索、HUB收发接受通过；不得再要求重复开E窗口/搬136文件/重做这些验收。
- Browser live失败属实；扩展激活和脚本注入不等于Agent MCP已挂载。旧D成功不算本E通过。
- REPORT的“Cursor Settings → Tools & MCP → Browser Automation → Browser Tab，确认Connected”未附本版本实际控件证据、当前值或观察来源。不能确定这是3.24.12现有菜单，也不能仅照10/12旧报告要求用户操作。“会话未附着”是症状层判断，底层原因尚未定位。

接续原1720任务，仅补缺项，不另开平行修复：
1. 优先从本机本版本实际设置/公开命令注册与相关窗口日志，核实上述控件是否存在、当前值和来源。可只读查看本机公开命令/设置定义；不要读取秘密或完整聊天，不用浏览器绕过失效的官方MCP。
2. 若已有可调用的受支持官方机制能完成最小可逆恢复，仍按原授权执行；重载前保存接续材料并确认未保存编辑安全，最多一次，不强杀、不循环重试。没有实际入口则标不可代操作。
3. 若最终确需用户UI，只提供本版本已核的最小动作及依据；不能确认具体菜单就明确“未验证”，不要继续沿用猜测菜单。不要把四步流程称为一次点击，也不要把新开Agent保证为必修复。
4. 恢复后按原1720 A/B/C测live tabs、无业务页可撤销输入、GPT页可见性；不向GPT发送测试消息。未恢复继续BLOCKED，不影响已通过的HUB与历史使用。
5. 本轮不碰LiteLLM独立故障，不复制profile/cookie/state.vscdb，不重跑R9。

在原CURSOR_NATIVE_BROWSER_SESSION_REPAIR_20261020目录提交FOLLOWUP_EVIDENCE.md，列实际观察、做过的动作、结果和最小剩余操作。若可得证据已穷尽，直接说明工具边界，不反复生成同类任务。
