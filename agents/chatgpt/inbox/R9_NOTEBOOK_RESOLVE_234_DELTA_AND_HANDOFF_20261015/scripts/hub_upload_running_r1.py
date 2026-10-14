# -*- coding: utf-8 -*-
"""Upload RUNNING/final artifacts to HUB inbox; never print tokens."""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
from pathlib import Path

WORK = Path(r"C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014")
REPORT = WORK / "reports"
REPO = "zwdjwsam-creator/sam"
INBOX_DIR = "agents/chatgpt/inbox/R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014"
PTR = "agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md"


def get_token() -> str:
    t = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if t:
        return t.strip()
    try:
        out = subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL)
        if out.strip():
            return out.strip()
    except Exception:
        pass
    p = Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT")
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    raise RuntimeError("NO_GITHUB_TOKEN")


def gh_api(method: str, path: str, token: str, body: dict | None = None) -> dict:
    import urllib.request

    url = f"https://api.github.com/{path.lstrip('/')}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except Exception as e:
        # try read error body
        err_body = ""
        if hasattr(e, "read"):
            try:
                err_body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
        raise RuntimeError(f"GH_API_FAIL {method} {path}: {e} {err_body[:500]}") from e


def put_file(token: str, rel_path: str, content: bytes, message: str) -> str:
    b64 = base64.b64encode(content).decode("ascii")
    api_path = f"repos/{REPO}/contents/{rel_path}"
    sha = None
    try:
        existing = gh_api("GET", api_path, token)
        sha = existing.get("sha")
    except Exception:
        sha = None
    body = {"message": message, "content": b64, "branch": "main"}
    if sha:
        body["sha"] = sha
    res = gh_api("PUT", api_path, token, body)
    return res.get("content", {}).get("html_url") or res.get("commit", {}).get("html_url") or ""


def main() -> int:
    token = get_token()
    files = [
        REPORT / "SAM_REPORT.md",
        REPORT / "SOURCE_RECONCILE_SUMMARY.json",
        REPORT / "FILE_SHA256.json",
        REPORT / "SCRIPT_REFS.json",
    ]
    uploaded = []
    for f in files:
        if not f.exists():
            continue
        rel = f"{INBOX_DIR}/{f.name}"
        url = put_file(token, rel, f.read_bytes(), f"R9 reconcile update {f.name}")
        uploaded.append({"file": f.name, "url": url})
        print(f"uploaded {f.name}")

    # pointer
    summary = {}
    sj = REPORT / "SOURCE_RECONCILE_SUMMARY.json"
    if sj.exists():
        summary = json.loads(sj.read_text(encoding="utf-8"))
    ptr = f"""# INBOX_FOR_CHATGPT

latest_task: R9_NOTEBOOK_LOCAL_SOURCE_RECONCILE_20261014_2312
status: {summary.get('status', 'UNKNOWN')}
host: SAM
pid: {summary.get('pid')}
dirs_done: {summary.get('dirs_done')}
queue_pending: {summary.get('queue_pending')}
paths_enumerated: {summary.get('paths_enumerated')}
BASELINE_VERIFIED: {summary.get('BASELINE_VERIFIED')}
SOURCE_ENUMERATION_COMPLETE: {summary.get('SOURCE_ENUMERATION_COMPLETE')}
SOURCE_METADATA_MATCH: {summary.get('SOURCE_METADATA_MATCH')}
SOURCE_CURRENT_MATCH: {summary.get('SOURCE_CURRENT_MATCH')}
HISTORICAL_CONTENT_MATCH: UNPROVEN
inbox_dir: {INBOX_DIR}/
tree: https://github.com/{REPO}/tree/main/{INBOX_DIR}
updated_at: {summary.get('updated_at')}
ZHANGWEI: HOLD
COPY_AUTHORIZED: false
"""
    put_file(token, PTR, ptr.encode("utf-8"), "R9 reconcile INBOX pointer update")
    print("pointer_updated")
    print(json.dumps({"uploaded": uploaded, "tree": f"https://github.com/{REPO}/tree/main/{INBOX_DIR}"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
