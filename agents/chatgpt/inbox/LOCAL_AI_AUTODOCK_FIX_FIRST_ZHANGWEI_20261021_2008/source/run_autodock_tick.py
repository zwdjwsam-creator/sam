# -*- coding: utf-8 -*-
"""Wrapper: set git auth from known token file, then run autodock once."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

TOKEN_CANDIDATES = [
    Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT"),
    Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_pat.TXT"),
]
HERE = Path(__file__).resolve().parent
REPO = Path(r"D:\LOCAL_AI\HUB_sam")


def load_token() -> str:
    for p in TOKEN_CANDIDATES:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip().replace("\ufeff", "")
            if line.startswith(("gho_", "ghp_", "github_pat_", "ghu_")):
                return "".join(ch for ch in line if 32 <= ord(ch) < 127)
    raise SystemExit("NO_TOKEN")


def main() -> int:
    token = load_token()
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GITHUB_TOKEN"] = token
    env["OLLAMA_MODELS"] = r"D:\LOCAL_AI\Models"
    args = sys.argv[1:]
    if "--repo" not in args:
        args = ["--repo", str(REPO), *args]
    cmd = [sys.executable, "-u", str(HERE / "run_autodock_once.py"), *args]
    return subprocess.call(cmd, cwd=str(HERE), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
