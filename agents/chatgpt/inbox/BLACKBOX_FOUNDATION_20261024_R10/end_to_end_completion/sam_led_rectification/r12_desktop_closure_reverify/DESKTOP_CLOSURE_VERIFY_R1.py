# -*- coding: utf-8 -*-
"""台机独立核验 R12 闭包修复后的 8 条判据 — 全部自行从产物重算，不读 runner verdict。"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re

import pandas as pd

E2E = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
RECT = E2E / "sam_led_rectification"
R3 = E2E / "candidate" / "r15_releases" / "R15_REPLAY_20260924_R3"
BB = pathlib.Path(r"E:\BLACKBOX")
DAYS = ["2026-07-03", "2026-07-06", "2026-07-07", "2026-07-08", "2026-07-09", "2026-07-10"]
EXPECT_DAILY = {"2026-07-03": 5209, "2026-07-06": 5210, "2026-07-07": 5208,
                "2026-07-08": 5208, "2026-07-09": 5208, "2026-07-10": 5207}
PROD = [
    BB / "研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json",
    BB / "研究系统/数据平面/CURRENT/DAILY_DATA_PLANE_CURRENT.json",
    BB / "研究系统/数据平面/CURRENT/DAILY_RESEARCH_INPUT_PACK_CURRENT.json",
    BB / "研究系统/数据平面/STATE/JQ_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/T_EXTERNAL_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/GLOBAL_SELLSIDE_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/DOMESTIC_RESEARCH_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/US_NEWS_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/US_MARKET_STATE_INCREMENTAL_STATE.json",
]


def sha(p):
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def main() -> int:
    R = {"schema": "DESKTOP_CLOSURE_VERIFY_R1", "checks": {}, "blockers": []}

    def chk(k, ok, detail=None):
        R["checks"][k] = {"ok": bool(ok), "detail": detail}
        if not ok:
            R["blockers"].append(k)

    # ---- #1 ----
    so = R3 / "standard" / "price" / "stock_ohlcv_daily"
    files = sorted(x.name for x in so.glob("*.parquet"))
    n_r2 = len([n for n in files if "r2_repair" in n])
    chk("c1_r15_234_12", len(files) == 234 and n_r2 == 12, {"files": len(files), "r2_repair": n_r2})

    # ---- #2 READ_CLOSURE（自己从日志抓） ----
    lg = E2E / "pipeline_runs" / "compiler_releases.log"
    txt = lg.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"READ_CLOSURE (\{.*)", txt)
    closure = json.loads(m.group(1)) if m else {}
    stock = closure.get("STOCK_DAILY_PIT_R1", {})
    etf = closure.get("ETF_DAILY_PIT_R1", {})
    chk("c2_closure_stock_234",
        stock.get("materialised") == stock.get("enumerated") == stock.get("read_ok") == 234
        and stock.get("failed") == 0 and stock.get("CLOSURE_OK") is True, stock)
    chk("c2_closure_etf_37",
        etf.get("materialised") == etf.get("enumerated") == etf.get("read_ok") == 37
        and etf.get("failed") == 0 and etf.get("CLOSURE_OK") is True, etf)

    # 交叉：日志里的 enumerated 必须等于磁盘实数
    chk("c2_enumerated_matches_disk", stock.get("enumerated") == len(files),
        {"log": stock.get("enumerated"), "disk": len(files)})

    # ---- #3 错误标记 0 ----
    pats = ["READ_FAILED", "ENUM_INCOMPLETE", "PRICE_READ_INCOMPLETE", "READ_CLOSURE_BROKEN"]
    counts = {}
    for p in (E2E / "pipeline_runs").glob("*.log"):
        t = p.read_text(encoding="utf-8", errors="replace")
        for pat in pats:
            counts[pat] = counts.get(pat, 0) + t.count(pat)
    chk("c3_no_error_markers", all(v == 0 for v in counts.values()), counts)

    # ---- #4 rows_2026 = 959896 ×3（自己数，不信 QA） ----
    rels = [d for d in (E2E / "candidate" / "cc_out" / "releases").glob("*")
            if d.is_dir() and not d.name.startswith("_prev_")]
    latest = sorted(rels, key=lambda d: d.stat().st_mtime)[-1]
    rows = {}
    for prod in ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1"):
        f = latest / prod / "year=2026" / "part_2026.parquet"
        if f.exists():
            rows[prod] = int(len(pd.read_parquet(f)))
        else:
            rows[prod] = None
    chk("c4_rows_2026_959896", all(v == 959896 for v in rows.values()), rows)

    # QA 文件应同时为 959896（两者一致才可信）
    qa = latest / "_qa" / "TIP_REBASE_QA.json"
    qa_rows = {}
    july_qa = {}
    if qa.exists():
        q = json.loads(qa.read_text(encoding="utf-8"))
        for prod in ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1"):
            qa_rows[prod] = q.get("price", {}).get("products", {}).get(prod, {}).get("rows_2026")
        july_qa = q.get("july_distinct_codes") or q.get("price", {}).get("july_distinct_codes") or {}
    chk("c4_qa_agrees_with_computed", qa_rows == rows, {"qa": qa_rows, "computed": rows})

    # ---- #5 七月六天 distinct 代码（自己从 part_2026 数） ----
    f26 = latest / "STOCK_DAILY_PIT_R1" / "year=2026" / "part_2026.parquet"
    df = pd.read_parquet(f26, columns=["date", "code"])
    ds = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    daily = {d: int(df[ds == d]["code"].nunique()) for d in DAYS}
    chk("c5_july_distinct_codes", daily == EXPECT_DAILY,
        {"actual": daily, "expected": EXPECT_DAILY})
    chk("c5_qa_july_agrees", (not july_qa) or all(str(july_qa.get(d)) == str(v) for d, v in daily.items()),
        {"qa": july_qa, "computed": daily})

    # ---- #6 production_digest_changed == {} ----
    cp = json.loads((E2E / "deliverables" / "CONNECTED_PIPELINE.json").read_text(encoding="utf-8"))
    pdc = cp.get("production_digest_changed")
    chk("c6_production_digest_changed_empty", pdc == {}, pdc)
    # 与我在跑之前抓的 _pre_digest.json 对比（独立于 runner 自带快照）
    pre = E2E / "_pre_digest.json"
    if pre.exists():
        pre_d = json.loads(pre.read_text(encoding="utf-8"))
        now_d = {p.name: (sha(p)[:16] if sha(p) else None) for p in PROD}
        chk("c6_production_unchanged_vs_pre", pre_d == now_d,
            {"changed": {k: [pre_d.get(k), now_d.get(k)] for k in now_d if pre_d.get(k) != now_d.get(k)}})

    # ---- #7 负控日志独立存在且含 exit_code: 1 ----
    nc = E2E / "pipeline_runs" / "compiler_HARD_BLOCK_negative_control.log"
    nct = nc.read_text(encoding="utf-8", errors="replace") if nc.exists() else ""
    has_exit1 = re.search(r'"exit_code"\s*:\s*1\b', nct) is not None
    chk("c7_negative_control_log", nc.exists() and has_exit1,
        {"exists": nc.exists(), "bytes": len(nct), "has_exit_code_1": has_exit1,
         "failure_mode": (re.search(r'"error":\s*"([^"]{0,90})', nct).group(1)
                          if re.search(r'"error":\s*"([^"]{0,90})', nct) else None)})

    # ---- 附加：commit 账本必须锚在本次（修后）内容，而不是旧修前树 ----
    cm = json.loads((E2E / "candidate" / "cc_commit" / "COMMIT.json").read_text(encoding="utf-8"))
    # COMMIT 记的是产品全部年份合计；这里自己把 13 个分区加总后比对（不是只比 2026）
    cm_rows = {k: int(v["rows"]) for k, v in cm.get("products", {}).items()}
    total_rows = {}
    for prod in ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1"):
        acc = 0
        for f in sorted((latest / prod).rglob("*.parquet")):
            import pyarrow.parquet as pq
            acc += int(pq.ParquetFile(f).metadata.num_rows)
        total_rows[prod] = acc
    chk("x_commit_rows_match_new_content", cm_rows == total_rows,
        {"commit_rows": cm_rows, "computed_total_rows": total_rows})
    chk("x_commit_root_is_not_archived",
        not pathlib.Path(cm.get("release_root", "")).name.startswith("_prev_"),
        cm.get("release_root"))

    # ---- 附加：硬编码 false 证据检查（production_current_untouched 不再是字面量 true） ----
    rcp = (E2E / "tools" / "run_connected_pipeline.py").read_text(encoding="utf-8", errors="replace")
    chk("x_no_hardcoded_true",
        not re.search(r'"production_current_untouched"\s*:\s*True', rcp),
        "literal True assignment absent")

    R["release"] = latest.name
    R["summary"] = {"total": len(R["checks"]),
                    "passed": sum(1 for v in R["checks"].values() if v["ok"]),
                    "failed": len(R["blockers"])}
    R["status"] = "PASS" if not R["blockers"] else "BLOCKED"
    out = RECT / "DESKTOP_CLOSURE_VERIFY.json"
    out.write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": R["status"], "summary": R["summary"],
                      "blockers": R["blockers"], "release": R["release"]},
                     ensure_ascii=False, indent=2))
    for k, v in R["checks"].items():
        print(f"  {'OK ' if v['ok'] else 'FAIL'} {k}")
    return 0 if R["status"] == "PASS" else 5


if __name__ == "__main__":
    raise SystemExit(main())
