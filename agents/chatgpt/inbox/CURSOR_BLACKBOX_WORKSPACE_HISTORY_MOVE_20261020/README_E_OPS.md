# Cursor 维护工作区（迁入 BLACKBOX）

task_id: CURSOR_BLACKBOX_WORKSPACE_HISTORY_MOVE_20261020_1728  
host: ZHANGWEI  
维护主目录: `E:\BLACKBOX\_OPS\CURSOR_WORKSPACE`  
Cursor 主根（应打开）: `E:\BLACKBOX`（不是只打开本子目录）

## 来源与回退

- 真实 D 源（保留回退，未删除）: `D:\CursorDualRouteConfig`
- 本目录为上述项目工具/配置/可读历史的复制件；密钥目录 `secrets` 未迁入
- R9 冻结 plan/state/8GB 库仍在 `C:\LAN_SHARE_REPORT\...` 原位，见 `MIGRATION_HISTORY_INDEX.md`

## 新 Agent 必读

1. 本文件  
2. `MIGRATION_HISTORY_INDEX.md`  
3. `E:\BLACKBOX\AGENTS.md`（业务内核入口；含指向本目录的短入口）  
4. 历史副本: `migration_history_copies\`

## 通信现状（实测见任务 REPORT）

- HUB 文件通道: 可用（本机 token 文件，不上传 token）  
- 官方 Browser / GPT 页: 见 REPORT 实测栏（搬目录 ≠ 聊天/登录自动跟随）  
- LiteLLM/API 链: 本任务不启动

## 边界

- R9 FULL 技术验收已通过；**禁止**再 execute / 全量 hash / 改已验收业务数据  
- 后续增量维护须单独明确数据范围
