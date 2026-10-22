# build_release

`
397|def build_release(
398|    mode: str,
399|    lookback_days: int,
400|    start: Optional[str],
401|    *,
402|    force_publish: bool = False,
403|) -> dict:
404|    ensure_dirs()
405|    write_static_registries()
406|    std = load_current_standard()
407|    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
408|    asof = cur.get("cleaning_as_of") or cur.get("daily_asof") or "2026-08-07"
409|    log(f"mode={mode} standard={std} asof={asof}")
410|
411|    # Structural hard gate (R19 incident): canary never becomes CURRENT authority.
412|    if mode == "canary" and force_publish:
413|        raise RuntimeError(
414|            "HARD_BLOCK_CANARY_CURRENT_PUBLISH: "
415|            "mode=canary has no CURRENT publish permission "
416|            f"({CANARY_CURRENT_PUBLISH}); refuse --publish/--force-publish"
417|        )
418|    pointer_before = pointer_fingerprint() if mode == "canary" else None
419|
420|    # sources
421|    stock_paths = find_parquets(std / "price" / "stock_ohlcv_daily")
422|    etf_paths = find_parquets(std / "price" / "ETF_daily")
423|    fund_price = find_parquets(std / "fund")
424|    # fund plane NAV
425|    fund_plane = find_parquets(PLANE / "FUND_NET_VALUE_PIT")
426|    etf_nav_plane = find_parquets(PLANE / "ETF_UNIT_NET_VALUE_PIT")
427|    index_plane = find_parquets(PLANE / "INDEX_DAILY_RAW_NONE") + find_parquets(
428|        PLANE / "INDEX_DAILY_RAW_FULL_HISTORY_R1"
429|    )
430|    # also P3_index raw
431|    index_raw = find_parquets(RAW / "P3_index")
432|    idx_cons = find_parquets(PLANE / "INDEX_CONSTITUENT_PIT_R1")
433|
434|    max_files = None
435|    if mode == "canary":
436|        max_files = 40
437|
438|    stock = read_price_frame(stock_paths, max_files=max_files)
439|    etf = read_price_frame(etf_paths, max_files=max_files)
440|    fund = read_price_frame(fund_price + fund_plane, max_files=max_files)
441|    if not fund.empty:
442|        fund["asset_type"] = "FUND"
443|    index = read_price_frame(index_plane + index_raw, max_files=max_files)
444|
445|    # date filter
446|    end = pd.Timestamp(asof)
447|    if mode == "canary":
448|        start_ts = end - pd.Timedelta(days=int(lookback_days * 1.7))
449|    elif start:
450|        start_ts = pd.Timestamp(start)
`
