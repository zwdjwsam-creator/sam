#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 HUB 两个 inbox 指针顶部插入 R11 复跑 BLOCKED 结论块（幂等）。"""
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from pathlib import Path

REPO = "zwdjwsam-creator/sam"
BRANCH = "main"
TOKENS = [Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT")]
MARK = "[DESKTOP RERUN AFTER FIX R11 20261025]"
BLOCK = f"""> **{MARK} RESULT = BLOCKED（A 过 / B 不过）**
> 台机 ZHANGWEI 本机跑 `tools\\run_connected_pipeline.py --r15-rid R15_REPLAY_20260924_R3`：exit 0、12/12 verdicts true，
> **但 `rows_2026 = 928,760 ≠ 959,896`（差 31,136），6 个交易日仍是每天 19 个代码。**
> **A 已修好**：R15 `stock_ohlcv_daily` = 234 文件 / 12 个 r2_repair ✅
> **B 未修好**：编译器 `find_parquets` 仍用 `p.is_file()`，台机 `LongPathsEnabled=0`、
> R3 全路径 271 字符 → `find_parquets()` 只返回 **222**，静默丢同一批 12 个文件。
> 台机实测：`is_file` 可见 222 / `\\?\` 前缀 stat 234 全通过 / 被丢文件可正常读 2,890 行。
> 需 SAM 改 `find_parquets`（`_lp` + 显式 stat）+ 加"编译读到文件数/行数"硬门；台机不擅改业务代码。
> 另：`run_r15_cleaning_replay.py.bak_sam_led_r11` 与当前文件字节相同（回滚链断）；`RERUN_AFTER_FIX.md` 原先未推 HUB，本次已补。
> HUB 目录: https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/sam_led_rectification
> 指针块，以下正文原样保留。

---

"""

TARGETS = ["agents/chatgpt/inbox/INBOX_FOR_NOTEBOOK.md", "agents/chatgpt/inbox/INBOX_FOR_DESKTOP.md"]


def tok() -> str:
    for tf in TOKENS:
        for line in tf.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            s = line.strip()
            if s.startswith(("gho_", "ghp_", "github_pat_", "ghu_")):
                return s
    raise SystemExit("no token")


def curl(p: str) -> str:
    return f"https://api.github.com/repos/{REPO}/contents/{urllib.parse.quote(p, safe='/')}"


def api(url: str, t: str, method: str = "GET", payload=None):
    data = None
    h = {"Authorization": "Bearer " + t, "Accept": "application/vnd.github+json", "User-Agent": "BB"}
    if payload is not None:
        data = json.dumps(payload).encode()
        h["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=180) as f:
        b = f.read()
        return json.loads(b) if b else {}


def main() -> int:
    t = tok()
    for p in TARGETS:
        got = api(curl(p) + f"?ref={BRANCH}", t)
        txt = base64.b64decode(got.get("content") or b"").decode("utf-8", "replace")
        if MARK in txt:
            print(f"[SKIP] {p} already has R11 pointer")
            continue
        new = BLOCK + txt
        raw = new.encode()
        api(curl(p), t, "PUT", {"message": "desktop rerun-after-fix BLOCKED pointer",
                                "content": base64.b64encode(raw).decode(),
                                "branch": BRANCH, "sha": got["sha"]})
        back = base64.b64decode(api(curl(p) + f"?ref={BRANCH}", t).get("content") or b"").decode("utf-8", "replace")
        print(f"[{'OK  ' if back == new else 'DIFF'}] {p}  {len(raw)} B  head={back.startswith('> **' + MARK)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
