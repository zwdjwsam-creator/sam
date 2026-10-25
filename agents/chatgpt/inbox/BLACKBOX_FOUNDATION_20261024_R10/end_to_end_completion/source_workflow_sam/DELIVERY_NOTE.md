# DELIVERY_NOTE — SAM 源流程交接（R10 修订项）

- handoff_id: `SAM_SOURCE_WORKFLOW_HANDOFF_R1`
- host: **SAM**（hostname=`sam`）
- counterpart task: `BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025`
- amendment answered: "Owner correction — recover and reuse the laptop workflow first (2026-10-25)"
- 交付性质：**代码/配置/证据**。无行情数据、无凭据内容、无 CURRENT 切换、无下载。

## 交付通道（两条，任取）

1. **共享直读（推荐给台式机）**
   `\\192.168.100.2\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\source_workflow_from_SAM\`
   （SAM 侧实体路径 `E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\source_workflow_from_SAM\`）
2. **HUB 只读**
   `agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/source_workflow_sam/`

## 包内容

| 文件 | bytes | SHA256 |
|---|---|---|
| `SAM_SOURCE_CODE_BUNDLE.zip` | 567589 | `bdfafc3122266eff9005215949401d685739a29503c5807f6c0477d41b41d89d` |
| `SOURCE_WORKFLOW_HANDOFF.md` | 17248 | `472b402bdaee7fe302e70c56f343aa38b05508fbcbc6a061b15369f3a5a1a9fa` |
| `DESKTOP_ADAPTATION.md` | 5386 | `d4ddb405d41e8e5393d4f342ce11de0d23107e1672043cb6c0ef9f9af84262d9` |
| `RUN_RECORDS.md` | 4398 | `f5b69f8993b45a71c9575811bcc46ec0da924483da3eae145dfd9daa7753de75` |
| `SOURCE_INDEX.json` | 39669 | `23d372575f9d6270e86308d8bb455dc5d4927fb25469064eea58ac0911fe9f8d` |
| `meta/DEPENDENCIES_PIP_FREEZE.txt` | 3944 | `3a2146ab5bb9d26701744b57c1bb45273033b5379a55d8267bc8d30266aaa643` |
| `meta/RUNTIME.txt` | 318 | `ef90f26571bf1dc7b29316dc17a261611389d1ebff0151c7340afc5d10dfd9a2` |
| `meta/PIPELINE_STRUCTURE.json` | 42714 | `09dd786d425da2ae05aecd60f9c45349c9942508375ddaafc89db1ccf927f334` |
| `meta/CODE_SEMANTICS.json` | 132502 | `48ee004ab57d95ebdad7146906f13b5412579f4b1454ba89f8acf6cd1dfe632b` |
| `meta/ADAPTATION_HARDCODES.json` | 22188 | `fd09008f2a56af3124d7da6e3ff6161e33ca322e4c4027bf9c4c17a25bb00eff` |

代码 90 个文件 / 配置 28 个文件，逐个 SHA256 见 `SOURCE_INDEX.json`。

## 三条最容易被误读的事实

1. `--mode daily_incremental` 的 Lane A **不下载**，只做 scope 刷新 + 三方 asof 对齐门。
2. `cache_stock_daily_pit_r1_reader_r1` 是 resolver **拼出来的字符串**，源机无此文件。
3. 两个 coverage 模块在源机就是 **2B/CRLF 空壳**（同 SHA `7eb7025759…61a6`），不是迁移丢失。

## 未做（边界）

- 未删除/移动任何源文件；未改 Manifest/SHA；未生成 coverage READY。
- 未执行 `R9LP_RO` 共享清理（独立尾任务，仍 pending）。
- 未上传市场 parquet、未导出任何凭据内容。
