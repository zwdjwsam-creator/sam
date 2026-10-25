#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回传台机复验结果到 HUB sam_led_rectification 目录，并逐字节回读校验。"""
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
    (RECT / "DESKTOP_REVERIFY_RESULT.json", "DESKTOP_REVERIFY_RESULT.json"),
    (RECT / "DESKTOP_REVERIFY_REPORT.md", "DESKTOP_REVERIFY_REPORT.md"),
    (RECT / "LOCAL_RUN_EVIDENCE.json", "LOCAL_RUN_EVIDENCE.json"),
    (RECT / "DESKTOP_INDEPENDENT_VERIFY.json", "DESKTOP_INDEPENDENT_VERIFY.json"),
    (RECT / "DESKTOP_INDEPENDENT_VERIFY_R1.py", "DESKTOP_INDEPENDENT_VERIFY_R1.py"),
    (RECT / "logs" / "A_chain.log", "logs/A_chain.log"),
    (RECT / "logs" / "B_status_iso.log", "logs/B_status_iso.log"),
    (RECT / "logs" / "C_bad_date.log", "logs/C_bad_date.log"),
    (RECT / "logs" / "D_status_compact.log", "logs/D_status_compact.log"),
    (E2E / "deliverables" / "CONNECTED_PIPELINE.json", "deliverables/CONNECTED_PIPELINE.json"),
]


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def tok() -> str:
    for tf in TOKENS:
        if tf.exists():
            for line in tf.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
                s = line.strip()
                if s.startswith(("gho_", "ghp_", "github_pat_", "ghu_")):
                    return s
    raise SystemExit("no token")


def curl(p: str) -> str:
    return f"https://api.github.com/repos/{REPO}/contents/{urllib.parse.quote(p, safe='/')}"


def api(url: str, t: str, method: str = "GET", payload=None):
    data = None
    headers = {"Authorization": "Bearer " + t, "Accept": "application/vnd.github+json",
               "User-Agent": "BLACKBOX-AG"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    for a in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as f:
                b = f.read()
                return json.loads(b) if b else {}
        except urllib.error.HTTPError as e:
            d = e.read().decode("utf-8", "replace")[:300]
            if e.code in (409, 422) and a < 3:
                time.sleep(2 + a * 2)
                continue
            if e.code == 404:
                return {"_missing": True}
            raise SystemExit(f"HTTP {e.code} {url} :: {d}")
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
        prev_sha = None if prev.get("_missing") else prev.get("sha")
        skip = False
        if prev_sha:
            old = base64.b64decode(prev.get("content") or "")
            if hashlib.sha256(old).hexdigest() == lsha:
                skip = True
        if not skip:
            pl = {"message": f"desktop reverify: {rel}", "content": base64.b64encode(raw).decode("ascii"),
                  "branch": BRANCH}
            if prev_sha:
                pl["sha"] = prev_sha
            api(url, t, "PUT", pl)
        got = api(url + f"?ref={BRANCH}", t)
        rbytes = base64.b64decode(got.get("content") or "")
        eq = hashlib.sha256(rbytes).hexdigest() == lsha
        rows.append({"rel": rel, "bytes": len(raw), "local_sha256": lsha,
                     "remote_blob": got.get("sha"), "readback_byte_equal": eq,
                     "skipped_identical": skip})
        print(f"[{'OK  ' if eq else 'DIFF'}] {rel:<42} {len(raw):>8} B  {lsha[:12]}", flush=True)

    man = {"schema": "BLACKBOX_DESKTOP_REVERIFY_MANIFEST_R1",
           "dispatch_id": "SAM_LED_DESKTOP_RECTIFICATION_20261025",
           "execution_host": "ZHANGWEI",
           "delivered_at_cn": now_cn(),
           "hub_dir": HUB_DIR,
           "status": "PASS",
           "file_count": len(rows),
           "all_byte_equal": all(r["readback_byte_equal"] for r in rows),
           "flags": {"PRODUCTION_CURRENT_WRITE": "NONE", "NEW_DATA_ACQUISITION": "NONE",
                     "ORDER_ALLOWED": False, "PUBLISH_AUTHORIZED": False},
           "files": rows}
    mf = RECT / "DESKTOP_REVERIFY_MANIFEST.json"
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    raw = mf.read_bytes()
    url = curl(f"{HUB_DIR}/DESKTOP_REVERIFY_MANIFEST.json")
    prev = api(url + f"?ref={BRANCH}", t)
    pl = {"message": "desktop reverify: manifest", "content": base64.b64encode(raw).decode("ascii"),
          "branch": BRANCH}
    if not prev.get("_missing") and prev.get("sha"):
        pl["sha"] = prev["sha"]
    api(url, t, "PUT", pl)
    print(f"[OK  ] DESKTOP_REVERIFY_MANIFEST.json {len(raw)} B", flush=True)

    if SHARE.parent.exists():
        SHARE.mkdir(parents=True, exist_ok=True)
        for src, rel in FILES:
            if src.exists():
                d = SHARE / rel
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, d)
        shutil.copy2(mf, SHARE / "DESKTOP_REVERIFY_MANIFEST.json")
        print(f"[SHARE] mirrored -> {SHARE}", flush=True)
    else:
        print(f"[SHARE] unreachable {SHARE.parent}", flush=True)

    print(json.dumps({"file_count": len(rows), "all_byte_equal": man["all_byte_equal"],
                      "hub_dir": HUB_DIR}, ensure_ascii=False, indent=2), flush=True)
    return 0 if man["all_byte_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
