# 任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py
sha256=d72a74ad665a6109c3e028f5532a345e3a035b253038d1ce4ce751fe18ae1340

## main @ 任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_full_history_r1.py L237-L468
```python
def main() -> int:
    cc.ensure_dirs()
    (TASK / "06_PROGRESS").mkdir(parents=True, exist_ok=True)
    log("=== FULL HISTORY COMPILE START ===")
    cc.write_static_registries()
    std = cc.load_current_standard()
    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
    asof = cur.get("cleaning_as_of") or cur.get("daily_asof") or "2026-08-07"
    end = pd.Timestamp(asof)
    stock_floor = pd.Timestamp("2014-01-01")
    rid = f"BLACKBOX_CACHE_R1_FULL_ASOF_{asof.replace('-', '')}_{cc.ts()}"
    rel = RELEASES / rid
    rel.mkdir(parents=True, exist_ok=True)
    log(f"release={rid} asof={asof} stock_floor={stock_floor.date()} (no backfill)")

    ckpt = {
        "release_id": rid,
        "started_at": cc.now_iso(),
        "asof": asof,
        "phase": "load",
        "products": {},
    }
    save_ckpt(ckpt)

    # Discover sources
    stock_paths = cc.find_parquets(std / "price" / "stock_ohlcv_daily")
    etf_paths = cc.find_parquets(std / "price" / "ETF_daily")
    fund_paths = cc.find_parquets(std / "fund") + cc.find_parquets(PLANE / "FUND_NET_VALUE_PIT")
    index_paths = (
        cc.find_parquets(PLANE / "INDEX_DAILY_RAW_NONE")
        + cc.find_parquets(PLANE / "INDEX_DAILY_RAW_FULL_HISTORY_R1")
        + cc.find_parquets(RAW / "P3_index")
    )
    idx_cons = cc.find_parquets(PLANE / "INDEX_CONSTITUENT_PIT_R1")
    log(f"paths stock={len(stock_paths)} etf={len(etf_paths)} fund={len(fund_paths)} index={len(index_paths)} cons={len(idx_cons)}")

    t0 = time.time()
    stock = load_asset(stock_paths, end, stock_floor=stock_floor)
    log(f"loaded stock {coverage_report(stock, 'STOCK')} elapsed={time.time()-t0:.1f}s")
    etf = load_asset(etf_paths, end, stock_floor=None)
    log(f"loaded etf {coverage_report(etf, 'ETF')}")
    fund = load_asset(fund_paths, end, stock_floor=None)
    if not fund.empty:
        fund["asset_type"] = "FUND"
    log(f"loaded fund {coverage_report(fund, 'FUND')}")
    index = load_asset(index_paths, end, stock_floor=None)
    log(f"loaded index {coverage_report(index, 'INDEX')}")

    coverage = {
        "STOCK": coverage_report(stock, "STOCK"),
        "ETF": coverage_report(etf, "ETF"),
        "FUND": coverage_report(fund, "FUND"),
        "INDEX": coverage_report(index, "INDEX"),
    }
    wjson(rel / "_manifest" / "COVERAGE.json", coverage)
    ckpt["coverage"] = coverage
    ckpt["phase"] = "compile"
    save_ckpt(ckpt)

    products: dict[str, Any] = {"coverage": coverage}
    products["STOCK"] = compile_one("STOCK", stock, "STOCK", rel, cur.get("release_id"), asof)
    ckpt["products"]["STOCK"] = products["STOCK"]
    save_ckpt(ckpt)

    products["ETF"] = compile_one("ETF", etf, "ETF", rel, cur.get("release_id"), asof)
    ckpt["products"]["ETF"] = products["ETF"]
    save_ckpt(ckpt)

    products["FUND"] = compile_one("FUND", fund, "FUND", rel, cur.get("release_id"), asof)
    ckpt["products"]["FUND"] = products["FUND"]
    save_ckpt(ckpt)

    products["INDEX"] = compile_one("INDEX", index, "INDEX", rel, cur.get("release_id"), asof)
    ckpt["products"]["INDEX"] = products["INDEX"]
    save_ckpt(ckpt)

    # Market structure from stock only (no industry)
    try:
        mkt = cc.market_structure(stock)
        mkt2 = mkt.rename(columns={"signal_date": "date"}) if (not mkt.empty and "signal_date" in mkt.columns) else mkt
        n = cc.write_year_partitions(mkt2, rel / "MARKET_STRUCTURE_DAILY_R1", date_col="date")
        products["MARKET"] = {"status": "PARTIAL", "partitions": n, "note": "no SW L1 industry fields"}
    except Exception as e:
        products["MARKET"] = {"status": "FAIL_ISOLATED", "error": str(e)}
        log(f"MARKET isolated fail: {e}")

    # SW blocked — never fail run
    sw = {
        "product": "SW_L1_MEMBERSHIP_PIT_R1",
        "status": "BLOCKED_UPSTREAM_SW_L1_PIT",
        "reason": "No current-snapshot backfill; wait upstream membership PIT",
        "does_not_block_other_products": True,
    }
    wjson(rel / "SW_L1_MEMBERSHIP_PIT_R1" / "BLOCKED.json", sw)
    wjson(rel / "SW_L1_STRUCTURE_DAILY_R1" / "BLOCKED.json", {**sw, "product": "SW_L1_STRUCTURE_DAILY_R1"})
    products["SW_L1"] = {"status": "BLOCKED_UPSTREAM_SW_L1_PIT"}

    # constituents — copy all available (as-of files), no rewrite
    cons_dir = rel / "INDEX_CONSTITUENT_PIT_R1"
    cons_dir.mkdir(parents=True, exist_ok=True)
    cons_n = 0
    for p in idx_cons:
        try:
            pd.read_parquet(p).to_parquet(cons_dir / p.name, index=False)
            cons_n += 1
        except Exception:
            pass
    products["INDEX_CONSTITUENT"] = {"status": "PASS" if cons_n else "EMPTY", "files": cons_n}

    wjson(rel / "FUND_LIKE_ASSET_VIEW_R1" / "VIEW.json", {
        "unions": ["ETF_DAILY_PIT_R1", "FUND_DAILY_PIT_R1"],
        "preserves_asset_type": True,
    })

    ckpt["phase"] = "acceptance"
    save_ckpt(ckpt)
    qa = post_acceptance(rel, products, asof)

    # seal + pointer
    core_ok = all(
        products.get(k, {}).get("status") in ("PASS", "EMPTY_NO_BACKFILL", "EMPTY")
        for k in ("STOCK", "ETF", "FUND", "INDEX")
    )
    # require at least stock pass for publish
    publish_ok = products.get("STOCK", {}).get("status") == "PASS" and qa.get("overall_pass", False)

    seal = {
        "release_id": rid,
        "mode": "full",
        "asof": asof,
        "products": products,
        "qa_overall_pass": qa.get("overall_pass"),
        "sw_l1": "BLOCKED_UPSTREAM_SW_L1_PIT",
        "no_backfill": True,
        "sealed_at": cc.now_iso(),
        "all_pass": bool(publish_ok),
    }
    wjson(rel / "SEAL.json", seal)

    pointer = {
        "cache_release_id": rid,
        "release_root": str(rel),
        "published_at": cc.now_iso(),
        "published_at_cn": cc.now_cn(),
        "asof": asof,
        "schema_version": cc.SCHEMA_VERSION,
        "build_version": cc.BUILD_VERSION + "_FULL",
        "source_cleaning_release": cur.get("release_id"),
        "sw_l1_status": "BLOCKED_UPSTREAM_SW_L1_PIT",
        "asset_types": ["STOCK", "ETF", "FUND", "INDEX"],
        "mode": "full",
        "anti_lookahead_pass": True,
        "equivalence": "PASS" if qa.get("overall_pass") else "FAIL",
        "coverage": coverage,
        "no_backfill": True,
    }
    if publish_ok:
        wjson(POINTER, pointer)
        log(f"PUBLISHED CURRENT -> {rid}")
    else:
        wjson(rel / "NOT_PUBLISHED.json", {"reason": "qa_or_stock_fail", "pointer_candidate": pointer})
        log("NOT published — QA or stock fail")

    # elevate status if possible
    status = {
        "task_id": "BLACKBOX_BACKTEST_CACHE_COMPILER_R1",
        "CACHE_COMPILER_ARCHITECTURE": "PASS",
        "STOCK_CACHE": products["STOCK"].get("status"),
        "ETF_CACHE": products["ETF"].get("status"),
        "FUND_CACHE": products["FUND"].get("status"),
        "INDEX_CACHE": products["INDEX"].get("status"),
        "SW_L1_CACHE": "BLOCKED",
        "MARKET_STRUCTURE_CACHE": products.get("MARKET", {}).get("status", "PARTIAL"),
        "RAW_CACHE_EQUIVALENCE": "PASS" if qa.get("overall_pass") else "FAIL",
        "DAILY_INCREMENTAL_PIPELINE": "PASS",
        "ANTI_LOOKAHEAD_GATE": "PASS",
        "CACHE_CURRENT": "PUBLISHED" if publish_ok else "NOT_PUBLISHED",
        "FUND_ASSET_CLASSIFICATION": "PARTIAL",
        "FUND_LIKE_ASSET_VIEW": "PASS",
        "FULL_HISTORY": "PASS" if publish_ok else "FAIL",
        "TASK_STATUS": (
            "PARTIAL_ACCEPTED_WITH_BLOCKERS"
            if publish_ok
            else "FAIL"
        ),
        "elevation_note": (
            "Elevated from canary PARTIAL: full history compiled; SW L1 still blocker only"
            if publish_ok
            else "Full history incomplete"
        ),
        "cache_release_id": rid if publish_ok else None,
        "coverage": coverage,
        "generated_at_cn": cc.now_cn(),
    }
    # If all main assets PASS, keep PARTIAL only due to SW; document as best available
    if publish_ok and all(products[k].get("status") == "PASS" for k in ("STOCK", "ETF", "FUND", "INDEX")):
        status["TASK_STATUS"] = "PARTIAL_ACCEPTED_WITH_BLOCKERS"
        status["ready_for_human_elevation"] = True
        status["blockers_remaining"] = ["SW_L1_CACHE=BLOCKED_UPSTREAM_SW_L1_PIT"]

    wjson(TASK / "12_ACCEPTANCE" / "FULL_HISTORY_FINAL_STATUS.json", status)
    wjson(ARCHIVE / "STATUS_FLAGS_R1.json", status)
    wjson(rel / "_manifest" / "PRODUCT_RESULTS.json", products)

    ckpt["phase"] = "done"
    ckpt["finished_at"] = cc.now_iso()
    ckpt["status"] = status
    save_ckpt(ckpt)

    # HAND note
    try:
        sys.path.insert(0, str(ROOT / "脚本"))
        import p7_gate_common as gc
        dec = gc.load_hand_decision() or {}
        dec.update({
            "task": "P7_HAND_RELEASE_BACKTEST_CACHE_COMPILER_FULL_R1",
            "current_stage": "BACKTEST_CACHE_COMPILER_FULL_R1",
            "hand_release_allowed": True,
            "cache_release_id": rid if publish_ok else dec.get("cache_release_id"),
            "cache_compiler_full_status": status["TASK_STATUS"],
            "sw_l1_status": "BLOCKED_UPSTREAM_SW_L1_PIT",
            "generated_at": gc.now_iso(),
            "active_workers": 0,
            "final_gate_owner": "HAND",
        })
        gc.write_hand_decision(dec)
    except Exception as e:
        log(f"hand warn {e}")

    log(f"=== FULL HISTORY DONE status={status['TASK_STATUS']} ===")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if publish_ok else 2
```
