#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在 HUB 两个 inbox 指针文件顶部插入台机复验结果指针块，正文原样保留。"""
from __future__ import annotations

import base64
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
REPO = "zwdjwsam-creator/sam"
BRANCH = "main"
TOKENS = [Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT")]
MARK = "[DESKTOP REVERIFY 20261025]"
BLOCK = f"""> **{MARK} RESULT = PASS**
> 台机 ZHANGWEI 已用本机进程跑完 `RUN_CHAIN_R1.py`（2026-10-25T19:17:59 → 19:20:24，runner exit 0），
> 证据 `LOCAL_RUN_EVIDENCE.json` 的 `identity.hostname=ZHANGWEI`；另附独立核验 `DESKTOP_INDEPENDENT_VERIFY.json` 47/47。
> 结论：`sam_led_rectification` = **DESKTOP_REVERIFY_PASS**（12/12 chain verdicts、8/8 runner verdicts、`PRODUCTION_CURRENT_WRITE=NONE`）。
> 未通过项另列：V4 仍 `BLOCKED_INPUT_INCOMPLETE`（diagnostic_only），正式回测**未通过**。
> HUB 目录: https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/sam_led_rectification
> 本块仅为交付指针；以下正文原样保留，未作删改。

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
            print(f"[SKIP] {p} already has pointer")
            continue
        new = BLOCK + txt
        raw = new.encode("utf-8")
        api(curl(p), t, "PUT",
            {"message": "desktop reverify PASS pointer", "content": base64.b64encode(raw).decode(),
             "branch": BRANCH, "sha": got["sha"]})
        back = api(curl(p) + f"?ref={BRANCH}", t)
        bt = base64.b64decode(back.get("content") or b"").decode("utf-8", "replace")
        print(f"[{'OK  ' if bt == new else 'DIFF'}] {p}  {len(raw)} B  head_ok={bt.startswith('> **' + MARK)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
