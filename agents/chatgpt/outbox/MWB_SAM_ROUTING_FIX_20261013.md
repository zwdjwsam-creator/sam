# SAM笔记本 MWB 专用路由纠偏 — 禁止调用旧BLACKBOX邮件脚本

task_id: MWB_SAM_ROUTING_FIX_20261013
target: SAM
scope: MWB_INSTALL_C_ONLY
status: READY
parent_task: MWB_INSTALL_SAM_NOTEBOOK_C_20261013
r9: HOLD
copy_authorized: false

## 症状及判定（2026-10-13用户截图）
笔记本 Cursor收到“先读HUB接个任务”后调用旧的 `外部大脑信箱_fetch_outbox.py`；
该脚本读取的是 `任务\BLACKBOX_RAW_NONE_REDOW...\外部大脑信箱\...\OUTBOX_FROM_CHATGPT.md`；
其检测到 `qmt` 后触发 `HARD_BLOCK`。
**这不是MWB任务的拦截，也不是要求关掉安全门禁。**
截图还显示旧流程把staging指向 `E:\BLACKBOX\运行\外部大脑信箱\`。E为笔记本不可写的业务源盘。这类旧流程禁止继续用于MWB通信，之前可能已经生成的文件暂不删除/移动/修改，先留证据。

## 直接执行，不再路由到旧脚本
1. 立即停止**本轮旧BLACKBOX收件尝试**，保留 `qmt` `HARD_BLOCK` 原封不动；不得给旧脚本添加 `--ignore` / `--skip-gate`、删除关键词或白名单放行任意旧业务指令。
2. 使用本机已连接GitHub工具 / GitHub仓库HTTPS只读访问 / git直接读取**明确唯一的当前任务文件**：
`agents/chatgpt/outbox/MWB_INSTALL_SAM_NOTEBOOK_C_20261013.md`
并核对 `agents/chatgpt/inbox/INBOX_FOR_NOTEBOOK.md` 顶部新的MWB优先指针。
3. 此任务完全独立于BLACKBOX邮件脚本和E盘旧staging，数据处理范围仅 `C:\LAN_SHARE_REPORT\MWB_INSTALL_SAM_20261013\` 的日志、官方PowerToys安装到C，禁止改动E/D业务源、QMT、R9、SMB现有直连/IP。
4. 根据父任务一次性安装或复用 Microsoft PowerToys / Mouse Without Borders；官方可信来源，主控设备SAM；配对SAM与ZHANGWEI仅使用本地私有安全密钥，公开HUB不能存密钥。
5. 在本机验证已经实际安装+打开MWB，目标主机未准备好时将配对状态写 `WAITING_FOR_DESKTOP`，而不是造假PASS；如果需要管理员许可/安全策略例外，先停在用户可见正规提示，不破坏安全保护。
6. 报告保存在本机 `C:\LAN_SHARE_REPORT\MWB_INSTALL_SAM_20261013\REPORT.md`，然后仅将脱敏技术结果上传 `agents/chatgpt/inbox/MWB_INSTALL_SAM_20261013/SAM_REPORT.md`。
7. **绝不**为恢复旧BLACKBOX通信而修改现有硬阻塞逻辑；如需改造旧邮件脚本将staging从E挪到C，应留待将来独立审计和授权，本轮不更改它。
8. 验收只看PowerToys/MWB真实安装与实际跨屏鼠标键盘测试；`git pull`、阅读HUB、qmt门禁通过与否不等于MWB安装成功。

### 给SAM的新对话一句话
“直接读取GitHub `agents/chatgpt/outbox/MWB_INSTALL_SAM_NOTEBOOK_C_20261013.md`，不要运行旧 `外部大脑信箱_fetch_outbox.py`。MWB仅在笔记本C盘安装/配置；E/D只读，R9 HOLD。安装后报告到指定HUB。”

本指令仅纠正路由，不扩大原有用户授权。
