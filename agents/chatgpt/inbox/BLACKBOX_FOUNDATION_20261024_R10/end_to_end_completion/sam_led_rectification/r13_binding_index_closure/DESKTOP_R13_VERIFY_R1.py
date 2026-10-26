# -*- coding: utf-8 -*-
"""台机独立核验 R13（release binding + file-set closure + index canonical_code）。

全部从产物/日志/文件系统重算，不采信 runner 的 verdict。
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

import pandas as pd
import pyarrow.parquet as pq

E2E = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
RECT = E2E / "sam_led_rectification"
BB = pathlib.Path(r"E:\BLACKBOX")
ARCH = E2E / "candidate" / "cc_out" / "_archive_r12_round_20261026_181002"
PRODUCTS = ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1")
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


def rows_of(p: pathlib.Path) -> int | None:
    return pq.ParquetFile(p).metadata.num_rows if p.exists() else None


def keys_of(p: pathlib.Path) -> set:
    df = pd.read_parquet(p, columns=["date", "code"])
    return set(zip(pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d"),
                   df["code"].astype(str).str.upper()))


def main() -> int:
    R = {"schema": "DESKTOP_R13_CLOSURE_VERIFY", "checks": {}, "blockers": [], "findings": []}

    def chk(k, ok, detail=None, severity="BLOCKER"):
        R["checks"][k] = {"ok": bool(ok), "detail": detail}
        if not ok:
            R["blockers"].append({"id": k, "severity": severity, "detail": detail})

    deliverable = json.loads((E2E / "deliverables" / "CONNECTED_PIPELINE.json").read_text(encoding="utf-8"))
    comp = deliverable["stages"]["compiler"]
    rel = pathlib.Path(comp["bound_release_root"])

    # ---- 1 R15 ----
    so = E2E / "candidate" / "r15_releases" / "R15_REPLAY_20260924_R3" / "standard" / "price" / "stock_ohlcv_daily"
    if not so.exists():
        cands = sorted([d for d in (E2E / "candidate" / "r15_releases").iterdir()
                        if d.is_dir() and "_r13_passA_R3" in d.name], key=lambda d: d.name)
        so = cands[-1] / "standard" / "price" / "stock_ohlcv_daily"
    files = sorted(x.name for x in so.glob("*.parquet"))
    chk("c1_r15_234_12", len(files) == 234 and len([n for n in files if "r2_repair" in n]) == 12,
        {"files": len(files), "r2_repair": len([n for n in files if "r2_repair" in n])})

    # ---- 2 closure：从 QA 与日志双取 ----
    qa = json.loads((rel / "_qa" / "TIP_REBASE_QA.json").read_text(encoding="utf-8"))
    rc = qa["price"]["read_closure"]
    for pid, exp in (("STOCK_DAILY_PIT_R1", 234), ("ETF_DAILY_PIT_R1", 37), ("INDEX_DAILY_R1", 1501)):
        d = rc.get(pid, {})
        chk(f"c2_closure_{pid}",
            d.get("expected") == exp and d.get("enumerated") == exp and d.get("read_ok") == exp
            and d.get("missing_read") == 0 and d.get("failed") == 0
            and d.get("CLOSURE_OK") is True and d.get("semantics") == "FILE_SET_IDENTITY", d)
    chk("c2_index_sources", rc["INDEX_DAILY_R1"].get("sources") ==
        {"RAW_FULL_HISTORY": {"files": 1464}, "CLEANING_CURRENT_INDEX_DAILY": {"files": 37}},
        rc["INDEX_DAILY_R1"].get("sources"))

    # ---- 3 错误标记 0 ----
    lg = (E2E / "pipeline_runs" / "compiler_releases.log").read_text(encoding="utf-8", errors="replace")
    counts = {p: lg.count(p) for p in
              ("READ_FAILED", "ENUM_INCOMPLETE", "PRICE_READ_INCOMPLETE",
               "READ_CLOSURE_BROKEN", "KEY_SET_MISMATCH")}
    chk("c3_no_error_markers", all(v == 0 for v in counts.values()), counts)

    # ---- 4 行数 ----
    got_rows = {p: rows_of(rel / p / "year=2026" / "part_2026.parquet") for p in PRODUCTS}
    chk("c4_stock_rows_959896", all(v == 959896 for v in got_rows.values()), got_rows)
    chk("c4_etf_rows_63204", rows_of(rel / "ETF_DAILY_PIT_R1" / "year=2026" / "part_2026.parquet") == 63204,
        rows_of(rel / "ETF_DAILY_PIT_R1" / "year=2026" / "part_2026.parquet"))
    chk("c4_index_rows_106822", rows_of(rel / "INDEX_DAILY_R1" / "year=2026" / "part_2026.parquet") == 106822,
        rows_of(rel / "INDEX_DAILY_R1" / "year=2026" / "part_2026.parquet"))

    # ---- 5 键集合对账（自己算） ----
    kc = qa["price"].get("key_check", {})
    own = {}
    for p in PRODUCTS + ("INDEX_DAILY_R1",):
        k = keys_of(rel / p / "year=2026" / "part_2026.parquet")
        own[p] = {"keys": len(k), "qa_status": (kc.get(p) or {}).get("status"),
                  "qa_expected": (kc.get(p) or {}).get("expected_keys"),
                  "qa_written": (kc.get(p) or {}).get("written_keys")}
    chk("c5_keycheck_match", all(v["qa_status"] == "MATCH" and v["qa_written"] == v["keys"]
                                 and v["qa_expected"] == v["keys"] for v in own.values()), own)

    # ---- 6 七月六天不变 ----
    d26 = pd.read_parquet(rel / "STOCK_DAILY_PIT_R1" / "year=2026" / "part_2026.parquet",
                          columns=["date", "code"])
    ds = pd.to_datetime(d26["date"]).dt.strftime("%Y-%m-%d")
    daily = {d: int(d26[ds == d]["code"].nunique()) for d in DAYS}
    chk("c6_july_distinct_unchanged", daily == EXPECT_DAILY, {"actual": daily, "expected": EXPECT_DAILY})

    # ---- 7 指数是补充而非替换 ----
    old_rel = sorted([d for d in ARCH.iterdir() if d.is_dir()
                      and (d / "INDEX_DAILY_R1" / "year=2026" / "part_2026.parquet").exists()],
                     key=lambda d: d.name)[0]
    ko = keys_of(old_rel / "INDEX_DAILY_R1" / "year=2026" / "part_2026.parquet")
    kn = keys_of(rel / "INDEX_DAILY_R1" / "year=2026" / "part_2026.parquet")
    idx = pd.read_parquet(rel / "INDEX_DAILY_R1" / "year=2026" / "part_2026.parquet", columns=["date", "code"])
    chk("c7_index_additive", ko <= kn and len(ko - kn) == 0 and len(kn) - len(ko) == 106549,
        {"old_keys": len(ko), "new_keys": len(kn), "removed": len(ko - kn),
         "added": len(kn) - len(ko), "old_is_subset": ko <= kn})
    chk("c7_index_shape", int(idx["code"].nunique()) == 732 and
        int(pd.to_datetime(idx["date"]).dt.date.nunique()) == 176,
        {"codes": int(idx["code"].nunique()),
         "dates": int(pd.to_datetime(idx["date"]).dt.date.nunique())})

    # ---- 8 发布绑定 ----
    last = pathlib.Path(comp["binding_source"])
    # TIP_REBASE_LAST.json 是单槽文件，run 内的 replay 会再次覆盖它；因此只能校验
    # (a) 绑定确实来自该文件 (b) 运行时快照(declared) 与 bound 一致 (c) 旧值被移位。
    chk("c8_binding_from_declaration",
        last.name == "TIP_REBASE_LAST.json"
        and comp["declared"]["cache_release_id"] == comp["bound_release_id"] == rel.name
        and pathlib.Path(comp["declared"]["release_root"]).name == rel.name,
        {"binding_source": last.name, "bound": comp["bound_release_id"],
         "declared_at_run": comp["declared"]["cache_release_id"],
         "slot_now_points_to": json.loads(last.read_text(encoding="utf-8"))["pointer"]["cache_release_id"]
         if last.exists() else None})
    if last.exists() and json.loads(last.read_text(encoding="utf-8"))["pointer"]["cache_release_id"] != rel.name:
        R["findings"].append({
            "id": "DECLARATION_SLOT_IS_MUTABLE", "severity": "LOW",
            "detail": "acceptance/TIP_REBASE_LAST.json 是单槽文件：本轮 run 内的 same-input replay "
                      "第二次编译会把它覆盖成第二个 release。事后读该文件不等于当时的绑定证据；"
                      "本次可核性依赖 deliverable 里复制的 declared 快照。建议编译时另写一份"
                      "TIP_REBASE_BIND_<run_id>.json 作为不可变证据，或保留 prev_* 链并登记。",
            "evidence": {"bound": comp["bound_release_id"],
                         "slot_after_run": json.loads(last.read_text(encoding="utf-8"))
                         ["pointer"]["cache_release_id"]}})
    chk("c8_stale_declaration_moved", bool(comp.get("stale_moved_to"))
        and pathlib.Path(comp["stale_moved_to"]).name.startswith("TIP_REBASE_LAST.prev_"),
        comp.get("stale_moved_to"))
    srcs = ["".join(p.read_text(encoding="utf-8", errors="replace") for p in
                    [E2E / "tools" / "run_connected_pipeline.py"]
                    + sorted((E2E.parent.parent / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1").glob("*.py")))]
    calls = sum(len(re.findall(r"newest_release\s*\(", s)) for s in srcs)
    defs = sum(1 for s in srcs if "def newest_release" in s)
    chk("c8_newest_release_no_call_sites", calls - defs == 0, {"calls": calls, "defs": defs})

    # ---- 9 幂等 ----
    rp = deliverable["stages"]["same_input_replay"]
    cm = deliverable["stages"]["commit"]["commit"]
    chk("c9_idempotent", rp.get("status") == "PASS" and rp["commit"]["status"] == "IDEMPOTENT_NOOP"
        and rp["commit"]["commit_id"] == cm["commit_id"],
        {"replay": rp.get("status"), "replay_commit": rp["commit"]["status"],
         "commit_id": cm["commit_id"][:16], "second_release": rp.get("second_release_id")})

    # ---- 10 生产未动 ----
    pre = json.loads((E2E / "_pre_digest_r13.json").read_text(encoding="utf-8"))
    now = {p.name: (hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else None) for p in PROD}
    chk("c10_production_unchanged", pre == now and deliverable.get("production_digest_changed") == {},
        {"changed": {k: [pre.get(k), now.get(k)] for k in now if pre.get(k) != now.get(k)}})

    # ---- 11 负控（只判非零，同时记录真实失败类别） ----
    ncl = E2E / "pipeline_runs" / "compiler_HARD_BLOCK_negative_control.log"
    nct = ncl.read_text(encoding="utf-8", errors="replace") if ncl.exists() else ""
    exit_m = re.search(r'"exit_code"\s*:\s*(-?\d+)', nct)
    fail_lines = re.findall(r"\] FAIL (.{0,120})", nct)
    chk("c11_negative_control_nonzero", bool(exit_m) and int(exit_m.group(1)) != 0,
        {"exit_code": exit_m.group(1) if exit_m else None,
         "read_gate_markers": {k: nct.count(k) for k in
                              ("READ_CLOSURE_BROKEN", "MATERIALISED_UNREADABLE")},
         "fail_lines": fail_lines[:3]})

    # ---- 12 fixture 负控结果（另由 DESKTOP_FILE_SET_IDENTITY_FIXTURE_R1.py 产出） ----
    fx = RECT / "DESKTOP_FILE_SET_IDENTITY_FIXTURE.json"
    if fx.exists():
        v = json.loads(fx.read_text(encoding="utf-8"))["verdict"]
        chk("c12_fixture_swapped_key_blocked", v["detects_swapped_key"] and v["detects_missing_one"]
            and v["healthy_passes"] and v["read_failed_blocks"], v)
        # 这两个是"应当拦但没有拦/报错类型不对"的观察项，单列 findings
        if v.get("empty_root_is_blind"):
            R["findings"].append({
                "id": "EMPTY_EXPECTED_SET_IS_BLIND", "severity": "HIGH",
                "detail": "expected_files=[]（源根不存在）时 expected=enumerated=read_ok=0 且 CLOSURE_OK=true。"
                          "scan_parquet_independent 对不存在路径返回 []，assert_read_closure 没有 expected==0 的守卫，"
                          "于是'一个文件都没有'与'全部读完'不可区分。本轮负控正是走这条：它没有在读门被拦，"
                          "而是跑到最后因 missing=['VALUATION_PIT_R1'] 才 exit 2。",
                "evidence": "HARD_BLOCK 负控日志 2870 行 FAIL missing=['VALUATION_PIT_R1']；"
                            "fixture case empty_source_root -> NO_RAISE"})
        if v.get("empty_frame_bug"):
            R["findings"].append({
                "id": "EMPTY_FRAME_NAMEERROR", "severity": "MEDIUM",
                "detail": "expected_keys_from_frames 内一段从 read_price_frame 复制的分支引用未定义变量 p/report，"
                          "任何空 frame 都会抛 NameError，导致本可继续的键对账变成 KEY_SET_UNVERIFIABLE 假失败。",
                "evidence": "fixture case empty_frame_in_expected_keys -> NameError: name 'report' is not defined"})

    # ---- 13 commit 身份范围（新增，本轮实测） ----
    sys.path.insert(0, str(E2E / "tools"))
    import candidate_commit as cc  # noqa: E402
    archived_with_index = [d for d in ARCH.iterdir() if d.is_dir()
                           and (d / "INDEX_DAILY_R1" / "year=2026" / "part_2026.parquet").exists()]
    old_ids = {cc.build_identity(d)["commit_id"] for d in archived_with_index}
    new_id = cc.build_identity(rel)["commit_id"]
    old_idx_rows = {rows_of(d / "INDEX_DAILY_R1" / "year=2026" / "part_2026.parquet")
                    for d in archived_with_index}
    chk("c13_commit_covers_index", new_id not in old_ids,
        {"new_commit_id": new_id[:16], "archived_commit_ids": sorted(x[:16] for x in old_ids),
         "archived_index_rows": sorted(old_idx_rows),
         "new_index_rows": rows_of(rel / "INDEX_DAILY_R1" / "year=2026" / "part_2026.parquet"),
         "required_products": list(cc.REQUIRED_PRODUCTS)})
    if new_id in old_ids:
        R["findings"].append({
            "id": "COMMIT_IDENTITY_EXCLUDES_ETF_AND_INDEX", "severity": "HIGH",
            "detail": "candidate_commit.REQUIRED_PRODUCTS 只含 3 个股票产品。指数从 273 行补到 106,822 行后，"
                      "commit_id 与归档的 273 行版本完全相同，提交状态为 REBOUND_SAME_CONTENT_NEW_ROOT。"
                      "因此 commit_consistent / IDEMPOTENT_NOOP 无法发现指数或 ETF 平面的回归——"
                      "正是我们这两轮一直在抓的'身份没覆盖真正变了的那部分'。",
            "evidence": {"new": new_id[:16], "archived": sorted(x[:16] for x in old_ids),
                         "index_rows_archived": sorted(old_idx_rows), "index_rows_new": 106822}})

    R["release"] = rel.name
    R["summary"] = {"checks": len(R["checks"]),
                    "passed": sum(1 for v in R["checks"].values() if v["ok"]),
                    "blockers": len(R["blockers"]), "findings": len(R["findings"])}
    # c13 是本轮新增的"身份是否覆盖指数"判据：它不成立属真缺陷，但与 SAM 本轮声明的
    # 9 条功能判据相互独立，故单列状态，避免把两者混成一句"全过"或"全废"。
    only_identity = all(b["id"].startswith("c13_") for b in R["blockers"])
    if not R["blockers"]:
        R["status"] = "PASS"
    elif only_identity:
        R["status"] = "PASS_FUNCTIONAL_BLOCKED_ON_COMMIT_IDENTITY_SCOPE"
    else:
        R["status"] = "BLOCKED"
    R["stated_criteria"] = {
        "all_hold": all(v["ok"] for k, v in R["checks"].items() if not k.startswith(("c12_", "c13_"))),
        "note": "c12/c13 为台机自行增加的判据，不计入 SAM 本轮 9 条声明",
    }
    (RECT / "DESKTOP_R13_VERIFY.json").write_text(json.dumps(R, ensure_ascii=False, indent=2),
                                                  encoding="utf-8")
    print(json.dumps({"status": R["status"], "summary": R["summary"], "release": R["release"]},
                     ensure_ascii=False, indent=2))
    for k, v in R["checks"].items():
        print(f"  {'OK  ' if v['ok'] else 'FAIL'} {k}")
    print("findings:", [f["id"] for f in R["findings"]])
    return 0 if R["status"] == "PASS" else 5


if __name__ == "__main__":
    raise SystemExit(main())
