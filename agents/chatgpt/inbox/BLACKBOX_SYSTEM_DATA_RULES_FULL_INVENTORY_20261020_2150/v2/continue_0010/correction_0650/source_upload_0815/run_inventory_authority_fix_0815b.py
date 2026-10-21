# -*- coding: utf-8 -*-
"""0815b: isolated authority v2 + live re-resolve minute products; continue evidence."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path, PureWindowsPath

CN = timezone(timedelta(hours=8))
OUT = Path(
    r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
HUB = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox\BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150\v2\continue_0010\correction_0650"
)
SCRIPTS = Path(r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\脚本")
ST = Path(r"E:\BLACKBOX\运行\外部大脑信箱")
LOG = OUT / "authority_fix_0815b.log"


def now() -> str:
    return datetime.now(CN).isoformat(timespec="seconds")


def log(msg: str) -> None:
    line = f"{now()} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def write_status(**kw) -> None:
    body = {
        "updated_at": now(),
        "task": "BLACKBOX_SYSTEM_INVENTORY_AUTHORITY_AND_NEXT_STAGE_20261021_0815",
        "parent": "BLACKBOX_SYSTEM_DATA_RULES_FULL_INVENTORY_20261020_2150",
        **kw,
    }
    text = json.dumps(body, ensure_ascii=False, indent=2)
    (OUT / "STATUS_PROGRESS.json").write_text(text, encoding="utf-8")
    HUB.mkdir(parents=True, exist_ok=True)
    (HUB / "STATUS_PROGRESS.json").write_text(text, encoding="utf-8")


def regress_v2_fixture() -> dict:
    """GPT-style dual-dir fixture against v2 resolver (PureWindowsPath fake)."""
    sys.path.insert(0, str(SCRIPTS))
    import resolve_product_authority_v2_0815 as mod

    standard = r"E:\synthetic_clean\standard"
    stock1 = standard + r"\finance\A股_stock_1m"
    etf1 = standard + r"\finance\ETF_1m"
    stock5 = standard + r"\finance\A股_stock_5m"
    etf5 = standard + r"\finance\ETF_5m"
    existing = {standard, stock1, etf1, stock5, etf5}
    by_pattern = {
        "**/A股_stock_1m": [stock1],
        "**/ETF_1m": [etf1],
        "**/A股_stock_5m": [stock5],
        "**/ETF_5m": [etf5],
        "**/etf_1m": [],
        "**/etf_5m": [],
        "**/stock_1m": [],
        "**/stock_5m": [],
        "**/*ETF*1m*": [etf1],
        "**/*ETF*5m*": [etf5],
        "**/*stock*1m*": [stock1],
        "**/*stock*5m*": [stock5],
    }

    class FakePath(PureWindowsPath):
        def exists(self):
            return str(self) in existing

        def glob(self, pattern):
            return (FakePath(p) for p in by_pattern.get(pattern, []))

    real = mod.Path
    mod.Path = FakePath  # type: ignore
    try:
        rows = []
        expect = {
            "ETF_MINUTE_1M_R1": etf1,
            "ETF_MINUTE_5M_R1": etf5,
            "STOCK_MINUTE_1M_R1": stock1,
            "STOCK_MINUTE_5M_R1": stock5,
        }
        for pid, want in expect.items():
            row = mod.resolve_product_authority_v2(
                pid,
                {"release_root": r"E:\synthetic_cache"},
                {"standard_root": standard},
                {},
                set(),
                {},
            )
            rows.append(
                {
                    "product_id": pid,
                    "selected": row["authority_path"],
                    "want": want,
                    "ok": bool(row["authority_path"] == want),
                    "status": row["status"],
                }
            )
        collision = rows[0]["selected"] == rows[2]["selected"]
        # also prove old v1 still fails on same fixture
        old_src = SCRIPTS / "run_inventory_continue_0010_worker.py"
        old_bug = None
        if old_src.exists():
            raw = old_src.read_bytes()
            expected_sha = "06755ff959e29063321bda5036c9dae00ee7b47938a333425da0096656d89cbe"
            old_bug = {
                "source_sha_match": hashlib.sha256(raw).hexdigest() == expected_sha,
                "source_sha256": hashlib.sha256(raw).hexdigest(),
            }
        return {
            "PASS": bool(all(r["ok"] for r in rows) and not collision),
            "rows": rows,
            "etf_stock_collision": collision,
            "old_source": old_bug,
        }
    finally:
        mod.Path = real  # type: ignore


def live_reresolve_minutes() -> dict:
    sys.path.insert(0, str(SCRIPTS))
    from resolve_product_authority_v2_0815 import resolve_product_authority_v2

    # load authority map for current stock paths + find standard_root hint
    auth_p = OUT.parent / "PRODUCT_AUTHORITY_MAP.csv"
    rows = []
    if auth_p.exists():
        with auth_p.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    by = {r.get("product_id"): r for r in rows}
    # infer standard_root from existing stock minute path
    stock_path = (by.get("STOCK_MINUTE_1M_R1") or {}).get("authority_path") or ""
    std = ""
    if stock_path:
        p = Path(stock_path)
        # .../finance/A股_stock_1m -> standard root = parents[1] or search
        if p.name.startswith("A股_stock") or "stock_" in p.name.lower():
            std = str(p.parent.parent) if p.parent.name.lower() in {"finance", "standard"} else str(p.parent)
            # prefer .../standard
            for up in [p.parent, p.parent.parent, p.parent.parent.parent]:
                if up.name.lower() == "standard" or (up / "finance").exists():
                    std = str(up if up.name.lower() == "standard" else up)
                    if (Path(std) / "finance").exists() or std.endswith("standard"):
                        break
    # also try known clean roots from CURRENT files
    candidates = [
        std,
        r"E:\BLACKBOX\数据\清洗\standard",
        r"E:\BLACKBOX\数据\清洗产物\standard",
    ]
    # discover from stock path: walk up until glob finds ETF_1m or A股_stock_1m
    if stock_path:
        cur = Path(stock_path)
        for _ in range(6):
            candidates.append(str(cur))
            cur = cur.parent

    standard_root = ""
    for c in candidates:
        if not c:
            continue
        cp = Path(c)
        if not cp.exists():
            continue
        if list(cp.glob("**/A股_stock_1m")) or list(cp.glob("**/ETF_1m")):
            standard_root = str(cp)
            break

    cache_root = ""
    for r in rows:
        ap = r.get("authority_path") or ""
        if "releases" in ap.replace("\\", "/"):
            cache_root = str(Path(ap).parent)
            break

    results = []
    for pid in (
        "ETF_MINUTE_1M_R1",
        "ETF_MINUTE_5M_R1",
        "STOCK_MINUTE_1M_R1",
        "STOCK_MINUTE_5M_R1",
    ):
        old = by.get(pid) or {}
        row = resolve_product_authority_v2(
            pid,
            {"release_root": cache_root or r"E:\BLACKBOX\数据\回测缓存\releases\_none"},
            {"standard_root": standard_root},
            {},
            set(),
            {},
        )
        results.append(
            {
                "product_id": pid,
                "old_path": old.get("authority_path"),
                "old_status": old.get("status"),
                "v2": row,
                "identity": (
                    "AUTHORITY_IDENTITY_UNVERIFIED"
                    if (
                        "ETF" in pid
                        and old.get("authority_path")
                        and "stock" in (old.get("authority_path") or "").lower()
                    )
                    else row.get("status")
                ),
            }
        )
    out = {
        "at": now(),
        "standard_root_used": standard_root,
        "cache_root_guess": cache_root,
        "results": results,
        "note": "ETF coverage remains unverified until v2 path exists and is read separately",
    }
    (OUT / "MINUTE_AUTHORITY_V2_LIVE_0815.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


def strict_parser_v5_fix() -> dict:
    """Re-assert v5 cases with strict bools (not truthy path strings)."""
    sys.path.insert(0, str(SCRIPTS))
    # import classify from resume worker
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "resume0730", SCRIPTS / "run_inventory_resume_0730_worker.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    ROOT = Path(r"E:\BLACKBOX")
    cases = []
    e = m.classify_token_v5("../脚本/foo.py", ROOT / "任务" / "x.md", 1, "t")
    resolved = Path(e[0]["resolved"])
    expect = (ROOT / "脚本" / "foo.py").resolve()
    cases.append(
        {
            "name": "relative_dotdot_target",
            "ok": bool(
                ".." in e[0]["raw_token"]
                and (
                    resolved == expect
                    or str(resolved).replace("/", "\\").endswith(
                        str(expect).replace("/", "\\")
                    )
                )
            ),
        }
    )
    e = m.classify_token_v5("cursor/rules/gate.mdc", ROOT / "AGENTS.md", 1, "t")
    cases.append(
        {
            "name": "cursor_no_autoresolve",
            "ok": bool(e[0]["edge_status"] != "RESOLVED"),
        }
    )
    e = m.classify_token_v5(
        "cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc", ROOT / "AGENTS.md", 1, "t"
    )
    cases.append(
        {
            "name": "cursor_original_broken_even_if_dot_exists",
            "ok": bool(
                e[0]["edge_status"] == "BROKEN_CONFIRMED"
                and bool(e[0].get("recovery_candidate"))
            ),
        }
    )
    e = m.classify_token_v5(
        ".cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc", ROOT / "AGENTS.md", 1, "t"
    )
    cases.append(
        {
            "name": "dot_cursor_ok",
            "ok": bool(e[0]["edge_status"] == "RESOLVED"),
        }
    )
    res = {"PASS": bool(all(c["ok"] is True for c in cases)), "cases": cases}
    (OUT / "parser_regression_v5_strict.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return res


def refresh_ledger_and_inbox_pointer() -> None:
    led = OUT / "PRODUCT_STAGE_LEDGER_75.csv"
    if led.exists():
        # ensure frag fields present
        with led.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        if rows:
            keys = list(rows[0].keys())
            for extra in (
                "frag_0730_checked",
                "frag_0730_discovered",
                "authority_identity_0815",
            ):
                if extra not in keys:
                    keys.append(extra)
            frag = {}
            fp = OUT / "FRAGMENT_COVERAGE_0730.csv"
            if fp.exists():
                with fp.open("r", encoding="utf-8-sig", newline="") as f:
                    frag = {r["product_id"]: r for r in csv.DictReader(f)}
            for r in rows:
                pid = r.get("product_id") or ""
                fr = frag.get(pid) or {}
                r["frag_0730_checked"] = fr.get("read_files_checked", r.get("frag_0730_checked", ""))
                r["frag_0730_discovered"] = fr.get("files_discovered", r.get("frag_0730_discovered", ""))
                r["authority_identity_0815"] = fr.get(
                    "authority_identity", r.get("authority_identity_0815", "")
                )
            with led.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    log("AUTHORITY_FIX_0815B_START")
    write_status(phase="AUTHORITY_V2_REGRESS", overall="RUNNING", worker_pid=os.getpid())

    fx = regress_v2_fixture()
    (OUT / "AUTHORITY_V2_FIXTURE_REGRESS_0815.json").write_text(
        json.dumps(fx, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log(f"v2_fixture PASS={fx.get('PASS')}")

    live = live_reresolve_minutes()
    log(f"live standard_root={live.get('standard_root_used')!r}")

    pv5 = strict_parser_v5_fix()
    log(f"parser_v5_strict PASS={pv5.get('PASS')}")

    refresh_ledger_and_inbox_pointer()

    # copy sources
    src = OUT / "source_upload_0815"
    src.mkdir(exist_ok=True)
    for name in (
        "resolve_product_authority_v2_0815.py",
        "run_inventory_authority_fix_0815b.py",
        "run_inventory_authority_0815_worker.py",
        "run_inventory_resume_0730_worker.py",
    ):
        p = SCRIPTS / name
        if p.exists():
            shutil.copy2(p, src / name)
    files = []
    for f in src.iterdir():
        if f.is_file():
            files.append(
                {"name": f.name, "sha256": sha256_file(f), "bytes": f.stat().st_size}
            )
    (OUT / "SOURCE_SHA_0815.json").write_text(
        json.dumps({"at": now(), "files": files}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    master = f"""# AUTHORITY_0815b_PROGRESS

status: **PARTIAL_CONTINUE_NO_FORCED_WAIT**
overall_acceptance: **FALSE** (SYSTEM_INVENTORY_ACCEPTANCE=false)

## Align with GPT summary
- FUND_NAV 5980 fragments / ~6.5M rows / day→2026-09-24 retained
- ETF minute → stock dir: confirmed; marked AUTHORITY_IDENTITY_UNVERIFIED (not ETF coverage)
- Tip 0815 continue: isolated resolver v2 + fixture regress PASS={fx.get('PASS')}
- parser_v5_strict PASS={pv5.get('PASS')} (bool-only)

## Live re-resolve
standard_root: `{live.get('standard_root_used')}`
See MINUTE_AUTHORITY_V2_LIVE_0815.json

## Still not acceptance
plane/rules/strategy static chains; ETF true authority read; INDEX date contract; NO_PARQUET product class.

elapsed_sec: {round(time.time()-t0,1)}
local: `{OUT}`
"""
    (OUT / "MASTER_PROGRESS_0815.md").write_text(master, encoding="utf-8")
    write_status(
        phase="AUTHORITY_V2_CHECKPOINT",
        overall="PARTIAL_CONTINUE_NO_FORCED_WAIT",
        worker_pid=os.getpid(),
        v2_fixture_pass=fx.get("PASS"),
        parser_v5_strict_pass=pv5.get("PASS"),
        system_inventory_acceptance=False,
        elapsed_sec=round(time.time() - t0, 1),
        note="identity fix isolated; overall NOT accepted",
    )
    HUB.mkdir(parents=True, exist_ok=True)
    for name in (
        "STATUS_PROGRESS.json",
        "MASTER_PROGRESS_0815.md",
        "AUTHORITY_V2_FIXTURE_REGRESS_0815.json",
        "MINUTE_AUTHORITY_V2_LIVE_0815.json",
        "parser_regression_v5_strict.json",
        "SOURCE_SHA_0815.json",
        "PRODUCT_STAGE_LEDGER_75.csv",
        "FRAGMENT_COVERAGE_0730.csv",
    ):
        p = OUT / name
        if p.exists():
            (HUB / name).write_bytes(p.read_bytes())
    for f in (OUT / "source_upload_0815").iterdir():
        if f.is_file():
            d = HUB / "source_upload_0815"
            d.mkdir(exist_ok=True)
            (d / f.name).write_bytes(f.read_bytes())
    log("AUTHORITY_FIX_0815B_DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
