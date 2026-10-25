#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回传 R11 复跑结论到 HUB + 补推缺失的 RERUN_AFTER_FIX.md，并逐字节回读。"""
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
BB = Path(r"E:\BLACKBOX")
RECT = BB / "_OPS" / "FOUNDATION_RECOVERY_20261024" / "end_to_end_completion" / "sam_led_rectification"
E2E = RECT.parent
REPO = "zwdjwsam-creator/sam"
BRANCH = "main"
HUB_DIR = "agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/sam_led_rectification"
SHARE = Path(r"\\192.168.100.2\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\sam_led_rectification")
TOKENS = [Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT")]

FILES = [
    (RECT / "DESKTOP_RERUN_AFTER_FIX_RESULT.json", "DESKTOP_RERUN_AFTER_FIX_RESULT.json"),
    (RECT / "DESKTOP_RERUN_AFTER_FIX.md", "DESKTOP_RERUN_AFTER_FIX.md"),
    (RECT / "probe_longpath_compiler_r1.py", "probe_longpath_compiler_r1.py"),
    (RECT / "quantify_read_gap_r1.py", "quantify_read_gap_r1.py"),
    (RECT / "RERUN_AFTER_FIX.md", "RERUN_AFTER_FIX.md"),  # 补推：SAM 未上传
    (RECT / "logs" / "RERUN1_STDOUT.log", "logs/RERUN1_STDOUT.log"),
    (E2E / "deliverables" / "CONNECTED_PIPELINE.json", "deliverables/CONNECTED_PIPELINE.json"),
]


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
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as f:
                b = f.read()
                return json.loads(b) if b else {}
        except urllib.error.HTTPError as e:
            if e.code in (409, 422) and a < 3:
                time.sleep(2 + a * 2)
                continue
            if e.code == 404:
                return {"_missing": True}
            raise SystemExit(f"HTTP {e.code} {url} :: {e.read().decode('utf-8','replace')[:200]}")
        except Exception:
            if a < 3:
                time.sleep(2 + a * 2)
                continue
            raise
    return {}


def main() -> int:
    t = tok()
    rows = []
    for src, rel in FILES:
        if not src.exists():
            print(f"WARN missing {src}", flush=True)
            continue
        raw = src.read_bytes()
        lsha = hashlib.sha256(raw).hexdigest()
        url = curl(f"{HUB_DIR}/{rel}")
        prev = api(url + f"?ref={BRANCH}", t)
        psha = None if prev.get("_missing") else prev.get("sha")
        skip = False
        if psha:
            if hashlib.sha256(base64.b64decode(prev.get("content") or b"")).hexdigest() == lsha:
                skip = True
        if not skip:
            pl = {"message": f"desktop rerun-after-fix: {rel}",
                  "content": base64.b64encode(raw).decode(), "branch": BRANCH}
            if psha:
                pl["sha"] = psha
            api(url, t, "PUT", pl)
        got = api(url + f"?ref={BRANCH}", t)
        eq = hashlib.sha256(base64.b64decode(got.get("content") or b"")).hexdigest() == lsha
        rows.append({"rel": rel, "bytes": len(raw), "local_sha256": lsha,
                     "readback_byte_equal": eq, "skipped": skip})
        print(f"[{'OK  ' if eq else 'DIFF'}] {rel:<40} {len(raw):>8} B  {lsha[:12]}", flush=True)

    man = {"schema": "BLACKBOX_DESKTOP_RERUN_AFTER_FIX_MANIFEST_R1",
           "dispatch_id": "SAM_LED_DESKTOP_RECTIFICATION_20261025",
           "rev": "R11_LONGPATH_FIX_RERUN",
           "execution_host": "ZHANGWEI",
           "delivered_at_cn": datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z"),
           "status": "BLOCKED",
           "file_count": len(rows),
           "all_byte_equal": all(r["readback_byte_equal"] for r in rows),
           "flags": {"PRODUCTION_CURRENT_WRITE": "NONE", "NEW_DATA_ACQUISITION": "NONE",
                     "ORDER_ALLOWED": False, "PUBLISH_AUTHORIZED": False},
           "files": rows}
    mf = RECT / "DESKTOP_RERUN_AFTER_FIX_MANIFEST.json"
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    raw = mf.read_bytes()
    url = curl(f"{HUB_DIR}/DESKTOP_RERUN_AFTER_FIX_MANIFEST.json")
    prev = api(url + f"?ref={BRANCH}", t)
    pl = {"message": "desktop rerun-after-fix: manifest",
          "content": base64.b64encode(raw).decode(), "branch": BRANCH}
    if not prev.get("_missing") and prev.get("sha"):
        pl["sha"] = prev["sha"]
    api(url, t, "PUT", pl)
    print(f"[OK  ] DESKTOP_RERUN_AFTER_FIX_MANIFEST.json {len(raw)} B", flush=True)

    if SHARE.parent.exists():
        SHARE.mkdir(parents=True, exist_ok=True)
        for src, rel in FILES:
            if src.exists():
                dst = SHARE / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        shutil.copy2(mf, SHARE / "DESKTOP_RERUN_AFTER_FIX_MANIFEST.json")
        print(f"[SHARE] mirrored -> {SHARE}", flush=True)
    else:
        print(f"[SHARE] unreachable", flush=True)

    print(json.dumps({"file_count": len(rows), "all_byte_equal": man["all_byte_equal"]},
                     ensure_ascii=False, indent=2), flush=True)
    return 0 if man["all_byte_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
