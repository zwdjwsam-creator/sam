# 自动化漏检根因与修复（2026-10-21）

## 原因
1. 只监视 `agents/chatgpt/outbox`，未监视 `agents/chatgpt/reviews`（GPT 网页发布的复现附件在此）
2. 只比较文件名时间戳是否 `> arm tip`；tip 已到 0730 后同 tip/同目录增量显示为 NO_NEWER_OUTBOX
3. 未用 GitHub `path+sha` 检测内容变更

## 修复（已写入自动化）
- 每 3 分钟查收：outbox + reviews
- `_hub_SEEN_HUB_OBJECTS.json` 做 sha 基线与增量
- 增量写入 `_hub_NEW_FROM_GPT.json` + `_hub_patrol_ACTION_REQUIRED.json`
- ACCEPT/RESUME/reviews 增量可解除 WAIT

## 本次查实
- GitHub 最新 BLACKBOX tip 仍是 0730（已被 CLAIM/EXECUTING）
- GPT 同时发布了 `reviews/BLACKBOX_INVENTORY_CHECKPOINT_20261021_0730/`（旧逻辑看不见）