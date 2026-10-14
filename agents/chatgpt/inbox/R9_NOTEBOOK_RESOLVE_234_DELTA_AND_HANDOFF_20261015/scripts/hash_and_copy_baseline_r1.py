# -*- coding: utf-8 -*-
"""Stream-hash UNC baseline; optional clean local copy; never mutate source."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

EXPECT = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"
EXPECT_BYTES = 6025072640
UNC = Path(r"\\192.168.100.1\R9_SOURCE_BASELINE_20261014\SOURCE_BASELINE.sqlite")
LOCAL = Path(r"C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\baseline\SOURCE_BASELINE.sqlite")
OUT = Path(r"C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\reports\BASELINE_VERIFY.json")


def sha256_stream(path: Path, label: str) -> dict:
    h = hashlib.sha256()
    size = path.stat().st_size
    done = 0
    t0 = time.time()
    with open(path, "rb", buffering=8 * 1024 * 1024) as f:
        while True:
            chunk = f.read(8 * 1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            done += len(chunk)
            if done % (256 * 1024 * 1024) < 8 * 1024 * 1024:
                elapsed = max(time.time() - t0, 1e-6)
                mbps = (done / (1024 * 1024)) / elapsed
                print(f"{label} {done}/{size} ({100.0 * done / size:.1f}%) {mbps:.1f} MiB/s", flush=True)
    digest = h.hexdigest()
    return {
        "path": str(path),
        "bytes": size,
        "sha256": digest,
        "match_expect": digest == EXPECT and size == EXPECT_BYTES,
        "seconds": round(time.time() - t0, 3),
    }


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "hash-unc"
    result: dict = {
        "expect_sha256": EXPECT,
        "expect_bytes": EXPECT_BYTES,
        "mode": mode,
    }
    if mode == "hash-unc":
        print("HASH_UNC_START", flush=True)
        result["unc"] = sha256_stream(UNC, "UNC")
        print("UNC_DONE", result["unc"]["sha256"], result["unc"]["match_expect"], flush=True)
    elif mode in ("clean-copy", "copy-hash"):
        LOCAL.parent.mkdir(parents=True, exist_ok=True)
        if LOCAL.exists():
            try:
                LOCAL.unlink()
                print("LOCAL_REMOVED", flush=True)
            except OSError as e:
                alt = LOCAL.with_suffix(".sqlite.bad")
                print("LOCAL_UNLINK_FAIL", e, "rename_to", alt, flush=True)
                if alt.exists():
                    alt.unlink()
                LOCAL.rename(alt)
        print("COPY_HASH_START", flush=True)
        h = hashlib.sha256()
        done = 0
        t0 = time.time()
        unc_size = UNC.stat().st_size
        with open(UNC, "rb", buffering=8 * 1024 * 1024) as src, open(
            LOCAL, "wb", buffering=8 * 1024 * 1024
        ) as dst:
            while True:
                chunk = src.read(8 * 1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
                h.update(chunk)
                done += len(chunk)
                if done % (256 * 1024 * 1024) < 8 * 1024 * 1024:
                    elapsed = max(time.time() - t0, 1e-6)
                    mbps = (done / (1024 * 1024)) / elapsed
                    print(
                        f"COPY_HASH {done}/{unc_size} ({100.0 * done / unc_size:.1f}%) {mbps:.1f} MiB/s",
                        flush=True,
                    )
        digest = h.hexdigest()
        local_size = LOCAL.stat().st_size
        result["transfer"] = {
            "bytes_written": done,
            "local_bytes": local_size,
            "unc_bytes": unc_size,
            "sha256": digest,
            "match_expect": digest == EXPECT and local_size == EXPECT_BYTES,
            "seconds": round(time.time() - t0, 3),
        }
        print("COPY_HASH_DONE", digest, result["transfer"]["match_expect"], flush=True)
        sides = {}
        for suf in ("-wal", "-journal", "-shm"):
            p = Path(str(LOCAL) + suf)
            sides[suf] = {"exists": p.exists(), "bytes": (p.stat().st_size if p.exists() else None)}
        result["side_files"] = sides
        qc = None
        try:
            con = sqlite3.connect(f"file:{LOCAL.as_posix()}?mode=ro", uri=True)
            qc = con.execute("pragma quick_check").fetchone()[0]
            con.close()
        except Exception as e:
            qc = f"ERROR:{type(e).__name__}:{e}"
        result["quick_check"] = qc
        result["BASELINE_VERIFIED"] = bool(
            result["transfer"]["match_expect"]
            and qc == "ok"
            and not any((sides[s]["exists"] and (sides[s]["bytes"] or 0) > 0) for s in ("-wal", "-journal"))
        )
        print("BASELINE_VERIFIED", result["BASELINE_VERIFIED"], flush=True)
    else:
        raise SystemExit(f"unknown mode {mode}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", OUT, flush=True)
    return 0 if result.get("BASELINE_VERIFIED") or (result.get("unc") or {}).get("match_expect") else 2


if __name__ == "__main__":
    raise SystemExit(main())
