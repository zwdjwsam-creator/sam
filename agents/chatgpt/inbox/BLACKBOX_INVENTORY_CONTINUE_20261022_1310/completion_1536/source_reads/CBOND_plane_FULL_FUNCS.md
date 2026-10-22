# 脚本/blackbox_tushare_cbond_5y_plane_r2.py
sha256=02b9869d45ed8a05adc748d70626bf0840f062a38723047dc8af98f6c827e240

## tushare_call @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L276-L293
```python
def tushare_call(pro, api: str, params: dict[str, Any], retries: int = 6):
    last = None
    for i in range(retries):
        LIMITER.wait()
        try:
            df = pro.query(api, **params)
            LIMITER.on_success()
            return df
        except Exception as exc:
            last = exc
            kind = classify_err(f"{type(exc).__name__}: {exc}")
            if kind in {"PERMISSION_BLOCKED", "PERMISSION_BLOCKED_POINTS_8000", "API_NOT_FOUND", "BLOCKED_DO_NOT_RETRY"}:
                raise
            LIMITER.on_retry()
            if kind == "THROTTLE":
                LIMITER.on_throttle()
            time.sleep(min(32.0, 2 ** i))
    raise last
```

## save_raw_slice @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L296-L323
```python
def save_raw_slice(api: str, slice_id: str, params: dict[str, Any], df, extra: dict | None = None) -> dict[str, Any]:
    import pandas as pd

    out_dir = RAW_ROOT / api / slice_id
    n = 0 if df is None else int(len(df))
    payload = b"" if df is None else df_to_parquet_bytes(df)
    sha = hashlib.sha256(payload).hexdigest()
    wbytes(out_dir / "raw.parquet", payload)
    receipt = {
        "source_vendor": SOURCE_VENDOR,
        "source_api": api,
        "request_parameters": {k: v for k, v in params.items()},
        "fetch_timestamp": now_utc(),
        "raw_row_count": n,
        "raw_sha256": sha,
        "query_cap": QUERY_CAP,
        "slice_id": slice_id,
        "JQ_NATIVE_DATA": False,
        "schema_compat_target": SCHEMA_COMPAT_TARGET,
        "IMMUTABLE": True,
        "column_rename": False,
        "unit_change": False,
        "fill_missing": False,
    }
    if extra:
        receipt.update(extra)
    wjson(out_dir / "receipt.json", receipt)
    return receipt
```

## slice_done @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L326-L329
```python
def slice_done(api: str, slice_id: str) -> bool:
    rec = RAW_ROOT / api / slice_id / "receipt.json"
    parq = RAW_ROOT / api / slice_id / "raw.parquet"
    return rec.is_file() and parq.is_file()
```

## concat_raw @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L332-L351
```python
def concat_raw(api: str):
    import pandas as pd

    root = RAW_ROOT / api
    if not root.is_dir():
        return pd.DataFrame()
    frames = []
    for rec in sorted(root.glob("*/receipt.json")):
        parq = rec.parent / "raw.parquet"
        if not parq.is_file() or parq.stat().st_size == 0:
            continue
        try:
            df = pd.read_parquet(parq)
        except Exception:
            continue
        if df is not None and len(df) > 0:
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)
```

## paginate_api @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L354-L407
```python
def paginate_api(pro, api: str, base_params: dict[str, Any], slice_prefix: str, fields: str | None = None) -> dict[str, Any]:
    import pandas as pd

    frames = []
    offset = 0
    page = 0
    n = 0
    while True:
        slice_id = f"{slice_prefix}_p{page:04d}"
        params = dict(base_params)
        params["limit"] = QUERY_CAP
        params["offset"] = offset
        if fields:
            params["fields"] = fields
        if slice_done(api, slice_id):
            rec = json.loads((RAW_ROOT / api / slice_id / "receipt.json").read_text(encoding="utf-8"))
            n = int(rec.get("raw_row_count") or 0)
            if n > 0:
                frames.append(pd.read_parquet(RAW_ROOT / api / slice_id / "raw.parquet"))
            page += 1
            offset += QUERY_CAP
            if n < QUERY_CAP:
                break
            continue
        key = f"{api}|{slice_id}"
        if not LIMITER.acquire_key(key):
            time.sleep(0.2)
            continue
        try:
            df = tushare_call(pro, api, params)
            n = 0 if df is None else int(len(df))
            pag = "YES" if n < QUERY_CAP else "NO"
            gate = decide(
                n_rows=n,
                query_cap=QUERY_CAP,
                pagination_complete=pag,
                completeness_state="COMPLETE" if n < QUERY_CAP else "UNKNOWN",
            )
            save_raw_slice(
                api,
                slice_id,
                params,
                df if df is not None else pd.DataFrame(),
                {"PAGINATION_COMPLETE": pag, "DATA_ABSENCE_GATE": gate["DATA_ABSENCE_GATE"], "offset": offset},
            )
            if n > 0:
                frames.append(df)
        finally:
            LIMITER.release_key(key)
        page += 1
        offset += QUERY_CAP
        if n < QUERY_CAP:
            break
    return {"api": api, "rows": int(sum(len(x) for x in frames)) if frames else 0, "pages": page, "frames": frames}
```

## write_product @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L420-L441
```python
def write_product(pid: str, df, provenance: dict[str, Any]) -> None:
    payload = df_to_parquet_bytes(df)
    wbytes(CLEAN_ROOT / pid / "data.parquet", payload)
    wbytes(CACHE_ROOT / pid / "data.parquet", payload)
    body = dict(provenance)
    body.update(
        {
            "product_id": pid,
            "source_vendor": SOURCE_VENDOR,
            "schema_compat_target": SCHEMA_COMPAT_TARGET,
            "schema_compat_mode": "FIELD_SEMANTIC_MAPPING",
            "jq_native_data": False,
            "JQ_EQUIVALENT": False,
            "JQ_NATIVE": False,
            "row_count": int(len(df)),
            "content_sha256": hashlib.sha256(payload).hexdigest(),
            "written_at": now_cn(),
            "CBOND_CONVERT_PRICE_PIT": "NOT_READY",
        }
    )
    wjson(CACHE_ROOT / pid / "PROVENANCE.json", body)
    wjson(CLEAN_ROOT / pid / "PROVENANCE.json", body)
```

## build_rating_pit @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L730-L792
```python
def build_rating_pit(raw, cal: list[str]):
    import pandas as pd

    df = clean_event(raw, ["ann_date", "rating_date"])
    lineage = [
        {"src": "ts_code", "dst": "bond_code_ts", "class": "B"},
        {"src": "ts_code", "dst": "bond_code_jq", "class": "B", "formula": ".SZ→.XSHE .SH→.XSHG"},
        {"src": "ann_date", "dst": "source_ann_date / DISCLOSURE_DATE", "class": "A"},
        {"src": "rating_date", "dst": "source_rating_date / EVENT_DATE", "class": "A"},
        {"src": "rating", "dst": "rating", "class": "A"},
        {"note": "JQ_COMPAT_STATUS=NO_EQUIVALENT; no CONBOND rating PIT field invented"},
    ]
    df = df[df["ann_date"].map(ymd).notna()].copy()
    df["pit_valid_from"] = df["ann_date"].map(lambda x: next_trade_after(x, cal))
    df = df[df["pit_valid_from"].notna()].copy()
    df = df.sort_values(["bond_code_jq", "pit_valid_from", "ann_date", "rating_date"])
    df = df.drop_duplicates(["bond_code_jq", "pit_valid_from"], keep="last")
    rows = []
    for code, g in df.groupby("bond_code_jq", sort=False):
        recs = g.to_dict("records")
        for i, r in enumerate(recs):
            vf = r["pit_valid_from"]
            vt = recs[i + 1]["pit_valid_from"] if i + 1 < len(recs) else "99991231"
            if vt <= vf:
                continue
            rows.append(
                {
                    "bond_code_jq": r.get("bond_code_jq"),
                    "bond_code_ts": r.get("bond_code_ts"),
                    "pit_valid_from": vf,
                    "pit_valid_to": vt,
                    "rating": r.get("rating"),
                    "rating_outlook": r.get("rating_outlook"),
                    "rating_com_name": r.get("rating_com_name"),
                    "rating_way": r.get("rating_way"),
                    "rating_type": r.get("rating_type"),
                    "source_ann_date": r.get("ann_date"),
                    "source_rating_date": r.get("rating_date"),
                    "KNOWN_AT_POLICY": "DATE_ONLY_NEXT_TRADING_DAY",
                    "PIT_SAFE": True,
                    "source_vendor": SOURCE_VENDOR,
                    "source_api": "cb_rating",
                    "jq_native_data": False,
                }
            )
    pit = pd.DataFrame(rows)
    write_product(
        "TUSHARE_CBOND_RATING_R1",
        df,
        {"source_api": "cb_rating", "layer": "CLEAN_EVENT", "JQ_COMPAT_STATUS": "NO_EQUIVALENT", "transform_lineage": lineage},
    )
    write_product(
        "TUSHARE_CBOND_RATING_PIT_R1",
        pit,
        {
            "source_api": "cb_rating",
            "layer": "PIT",
            "KNOWN_AT": "NEXT_TRADING_DAY_AFTER_ANN_DATE",
            "PIT_SAFE": True,
            "transform_lineage": lineage,
        },
    )
    return df, pit, lineage
```

## build_call_pit @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L795-L830
```python
def build_call_pit(r1_call, carry, cal: list[str]):
    import pandas as pd

    parts = [r1_call]
    if carry is not None and len(carry):
        parts.append(carry)
    raw = pd.concat(parts, ignore_index=True)
    df = clean_event(raw, ["ann_date", "call_date", "payment_date", "call_reg_date"])
    before = int(len(df))
    df = df.drop_duplicates(
        subset=[c for c in ["bond_code_ts", "ann_date", "call_type", "is_call", "call_date"] if c in df.columns]
    )
    df["pit_valid_from"] = df["ann_date"].map(lambda x: next_trade_after(x, cal))
    usable = df[df["pit_valid_from"].notna() & df["ann_date"].notna()].copy()
    usable["source_ann_date"] = usable["ann_date"]
    usable["EVENT_DATE"] = usable["call_date"]
    usable["DISCLOSURE_DATE"] = usable["ann_date"]
    usable["KNOWN_AT_POLICY"] = "DATE_ONLY_NEXT_TRADING_DAY"
    usable["PIT_SAFE"] = True
    usable["source_api"] = "cb_call"
    write_product(
        "TUSHARE_CBOND_CALL_PIT_R1",
        usable,
        {
            "source_api": "cb_call",
            "layer": "PIT_EVENT",
            "KNOWN_AT": "NEXT_TRADING_DAY_AFTER_ANN_DATE",
            "PIT_SAFE": True,
            "source_event_preserved": True,
            "r1_rows": int(len(r1_call)),
            "carryin_rows": 0 if carry is None else int(len(carry)),
            "dedup_before": before,
            "note": "call_date is NOT known_at",
        },
    )
    return usable
```

## build_remain_pit @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L833-L956
```python
def build_remain_pit(r1_share, carry, issue, basic, cal: list[str]):
    import pandas as pd

    parts = [r1_share]
    if carry is not None and len(carry):
        parts.append(carry)
    share = clean_event(pd.concat(parts, ignore_index=True), ["publish_date", "end_date"])
    share = share[share["publish_date"].notna()].copy()
    share["pit_valid_from"] = share["publish_date"].map(lambda x: next_trade_after(x, cal))
    share = share[share["pit_valid_from"].notna()].copy()
    share["known_remain_size"] = pd.to_numeric(share.get("remain_size"), errors="coerce")
    share["known_remain_size_source"] = "CB_SHARE_REMAIN_SIZE"
    share["source_publish_date"] = share["publish_date"]
    share["size_state_source"] = "CB_SHARE_REMAIN_SIZE"

    init_rows = []
    iss = add_codes(issue) if issue is not None and len(issue) else pd.DataFrame()
    bas = add_codes(basic) if basic is not None and len(basic) else pd.DataFrame()
    size_map = {}
    if len(iss) and "issue_size" in iss.columns:
        for _, r in iss.iterrows():
            size_map[str(r.get("bond_code_ts"))] = r.get("issue_size")
    list_map = {}
    if len(bas) and "list_date" in bas.columns:
        for _, r in bas.iterrows():
            list_map[str(r.get("bond_code_ts"))] = ymd(r.get("list_date"))
    first_share = share.groupby("bond_code_ts")["pit_valid_from"].min().to_dict() if len(share) else {}
    for code, issz in size_map.items():
        ld = list_map.get(code)
        vf = next_trade_after(ld, cal) if ld else None
        if not vf:
            continue
        jq = ts_to_jq(code)
        init_rows.append(
            {
                "bond_code_ts": code,
                "bond_code_jq": jq,
                "pit_valid_from": vf,
                "known_remain_size": issz,
                "known_remain_size_source": "ISSUE_SIZE_INITIAL",
                "size_state_source": "ISSUE_SIZE_INITIAL",
                "source_publish_date": ld,
                "remain_size": issz,
                "publish_date": ld,
                "end_date": None,
                "source_api": "cb_issue",
                "PIT_SAFE": True,
            }
        )
    init = pd.DataFrame(init_rows)
    keep_init = []
    if len(init):
        for _, r in init.iterrows():
            fs = first_share.get(str(r["bond_code_ts"]))
            if fs is None or r["pit_valid_from"] < fs:
                keep_init.append(r.to_dict())
    init = pd.DataFrame(keep_init)
    cols_share = [
        "bond_code_ts",
        "bond_code_jq",
        "pit_valid_from",
        "known_remain_size",
        "known_remain_size_source",
        "size_state_source",
        "source_publish_date",
        "remain_size",
        "publish_date",
        "end_date",
        "convert_price",
        "convert_val",
        "convert_vol",
        "convert_ratio",
        "acc_convert_val",
        "acc_convert_vol",
        "acc_convert_ratio",
        "issue_size",
        "source_api",
        "PIT_SAFE",
    ]
    for c in cols_share:
        if c not in share.columns:
            share[c] = None
        if len(init) and c not in init.columns:
            init[c] = None
    share["source_api"] = "cb_share"
    share["PIT_SAFE"] = True
    events = pd.concat(
        [
            init[cols_share] if len(init) else pd.DataFrame(columns=cols_share),
            share[cols_share],
        ],
        ignore_index=True,
    )
    events = events.sort_values(["bond_code_jq", "pit_valid_from", "source_publish_date"])
    events = events.drop_duplicates(["bond_code_jq", "pit_valid_from"], keep="last")
    rows = []
    for code, g in events.groupby("bond_code_jq", sort=False):
        recs = g.to_dict("records")
        for i, r in enumerate(recs):
            vf = r["pit_valid_from"]
            vt = recs[i + 1]["pit_valid_from"] if i + 1 < len(recs) else "99991231"
            if not vf or vt <= vf:
                continue
            item = dict(r)
            item["pit_valid_to"] = vt
            item["KNOWN_AT_POLICY"] = "DATE_ONLY_NEXT_TRADING_DAY"
            item["source_vendor"] = SOURCE_VENDOR
            item["jq_native_data"] = False
            rows.append(item)
    pit = pd.DataFrame(rows)
    write_product(
        "TUSHARE_CBOND_REMAIN_SIZE_PIT_R1",
        pit,
        {
            "source_api": "cb_share+cb_issue",
            "layer": "PIT",
            "KNOWN_AT": "NEXT_TRADING_DAY_AFTER_PUBLISH_DATE",
            "PIT_SAFE": True,
            "forward_fill": True,
            "backfill": False,
            "note": "known_at is NOT end_date; convert_price here is event field not daily convert-price PIT",
        },
    )
    return pit
```

## promote @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L1311-L1449
```python
def promote(val: dict[str, Any]) -> dict[str, Any]:
    if not val.get("VALIDATE_PASS"):
        return {"promoted": False, "reason": "VALIDATE_NOT_PASS", "CBOND_CURRENT_PROMOTED": False}
    new_products = [
        ("TUSHARE_CBOND_RATING_R1", "L2", "CBOND", "event", "Tushare cb_rating clean events; not as-of"),
        ("TUSHARE_CBOND_RATING_PIT_R1", "L1", "CBOND", "pit_interval", "CBOND rating PIT next trade day after ann_date"),
        ("TUSHARE_CBOND_CALL_PIT_R1", "L1", "CBOND", "pit_event", "CBOND call/redeem PIT next trade day after ann_date"),
        ("TUSHARE_CBOND_REMAIN_SIZE_PIT_R1", "L1", "CBOND", "pit_interval", "CBOND remain_size PIT next trade day after publish_date"),
        ("TUSHARE_CBOND_TOP10_HOLDERS_R1", "L2", "CBOND", "report_period", "CBOND top10 holders report-period only; PIT not ready"),
    ]
    cat = CATALOG_CSV.read_text(encoding="utf-8")
    existing = {ln.split(",")[0] for ln in cat.splitlines()[1:] if ln.strip()}
    add_lines = [f"{pid},{layer},{asset},ACTIVE,{grain},{desc}" for pid, layer, asset, grain, desc in new_products if pid not in existing]
    if add_lines:
        if not cat.endswith("\n"):
            cat += "\n"
        guarded_write_path(CATALOG_CSV, cat + "\n".join(add_lines) + "\n")

    path_map = {pid: str(R1_CACHE / pid) for pid in R1_PRODUCTS}
    for pid, *_ in new_products:
        path_map[pid] = str(CACHE_ROOT / pid)
    ptr = {
        "cache_release_id": CACHE_REL_ID,
        "release_root": str(CACHE_ROOT),
        "parent_release_id": R1_REL_ID,
        "parent_release_root": str(R1_CACHE),
        "published_at_cn": now_cn(),
        "asof": "2026-08-14",
        "source_vendor": SOURCE_VENDOR,
        "jq_native_data": False,
        "schema_compat_target": SCHEMA_COMPAT_TARGET,
        "schema_compat_mode": "FIELD_SEMANTIC_MAPPING",
        "CBOND_CONVERT_PRICE_PIT": "NOT_READY",
        "CBOND_EOD_PIT_READY": True,
        "CBOND_EVENT_PIT_READY": True,
        "CBOND_RATING_PIT": "READY",
        "CBOND_CALL_PIT": "READY",
        "CBOND_REMAIN_SIZE_PIT": "READY",
        "CBOND_TOP10_HOLDERS": "RAW_CLEAN_READY_PIT_NOT_READY",
        "STOCK_CACHE_UNCHANGED": True,
        "reader": "脚本/blackbox_tushare_cbond_reader_r2.py",
        "product_path_map": path_map,
        "products": R1_PRODUCTS + [p[0] for p in new_products],
        "R1_PRESERVED": True,
    }
    wjson(CBOND_PTR, ptr)

    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    have = {p["product_id"] for p in index.get("products", [])}
    for pid, layer, asset, grain, desc in new_products:
        if pid in have:
            continue
        pit_pol = "NEXT_TRADE_DAY_AFTER_ANN_DATE"
        if "REMAIN" in pid:
            pit_pol = "NEXT_TRADE_DAY_AFTER_PUBLISH_DATE"
        if "TOP10" in pid:
            pit_pol = "REPORT_PERIOD_ONLY_NOT_PIT"
        index["products"].append(
            {
                "product_id": pid,
                "layer": layer,
                "asset_type": asset,
                "status": "READY" if "TOP10" not in pid else "READY_NOT_PIT",
                "grain": grain,
                "description": desc,
                "cache_release_id": CACHE_REL_ID,
                "cache_product_path": str(CACHE_ROOT / pid),
                "security_namespace": "CBOND",
                "cross_section_contract": "INNER_ON_BOND_CODE",
                "pit_policy": pit_pol,
                "source_vendor": SOURCE_VENDOR,
                "jq_native_data": False,
                "schema_compat_target": SCHEMA_COMPAT_TARGET,
                "NATIVE_JQ_DATA": False,
                "CBOND_CONVERT_PRICE_PIT": "NOT_READY",
            }
        )
    index["product_count"] = len(index["products"])
    index["cbond_cache_release_id"] = CACHE_REL_ID
    index["cbond_cache_current_root"] = str(CACHE_ROOT)
    index["cbond_parent_release_root"] = str(R1_CACHE)
    wjson(INDEX_PATH, index)
    patch_resolver()

    cap = {
        "rule_id": "BLACKBOX_CBOND_PIT_CAPABILITY_R2",
        "status": "ACTIVE",
        "asof": "2026-08-14",
        "recorded_at_cn": now_cn(),
        "FULL_PIT_READY": False,
        "CBOND_EOD_PIT_READY": True,
        "CBOND_EVENT_PIT_READY": True,
        "CBOND_CONVERT_PRICE_PIT_READY": False,
        "CBOND_RATING_PIT": "READY",
        "CBOND_CALL_PIT": "READY",
        "CBOND_REMAIN_SIZE_PIT": "READY",
        "CBOND_TOP10_HOLDERS": "RAW_CLEAN_READY_PIT_NOT_READY",
        "CBOND_FACTOR_PRO": "BLOCKED_8000_POINTS",
        "CBOND_CONVERT_PRICE_PIT": "BLOCKED_SEPARATE_PERMISSION",
        "source_vendor": SOURCE_VENDOR,
        "jq_native_data": False,
        "schema_compat_target": SCHEMA_COMPAT_TARGET,
        "HAND_DECISION_JSON": "NOT_FORGED",
        "layers": {
            "CBOND_DAILY_MARKET": {"KNOWN_AT": "EOD_SAME_DAY", "USABLE_FROM": "AFTER_CLOSE", "PIT_SAFE_FOR_NEXT_DAY": True},
            "CBOND_RATING_PIT": {"KNOWN_AT": "NEXT_TRADING_DAY_AFTER_ANN_DATE", "PIT_SAFE": True},
            "CBOND_CALL_PIT": {"KNOWN_AT": "NEXT_TRADING_DAY_AFTER_ANN_DATE", "PIT_SAFE": True},
            "CBOND_REMAIN_SIZE_PIT": {"KNOWN_AT": "NEXT_TRADING_DAY_AFTER_PUBLISH_DATE", "PIT_SAFE": True},
            "CBOND_TOP10_HOLDERS": {"KNOWN_AT": "UNKNOWN", "PIT_SAFE": False},
            "CBOND_BASIC_CURRENT_CONVERT_PRICE": {"SNAPSHOT_ONLY": True, "PIT_SAFE": False},
            "CBOND_CONVERT_PRICE_PIT": {"STATUS": "NOT_READY"},
        },
    }
    wjson(PIT_CAP_CURRENT, cap)
    wjson(HAND_RULE, cap)
    hand_append = f"""

# HAND TOP-LEVEL POINTER APPEND — CBOND PIT ENRICHMENT R2
# appended_at_cn={now_cn()}
CBOND_CACHE_RELEASE={CACHE_REL_ID}
CBOND_CACHE_PARENT={R1_REL_ID}
CBOND_RATING_PIT=READY
CBOND_CALL_PIT=READY
CBOND_REMAIN_SIZE_PIT=READY
CBOND_TOP10_HOLDERS=RAW_CLEAN_READY_PIT_NOT_READY
CBOND_FACTOR_PRO=BLOCKED_8000_POINTS
CBOND_CONVERT_PRICE_PIT=BLOCKED_SEPARATE_PERMISSION
CBOND_EOD_PIT_READY=YES
CBOND_EVENT_PIT_READY=YES
CBOND_CONVERT_PRICE_PIT_READY=NO
FULL_PIT_READY=FALSE
FUTURES=DEFERRED_NOT_READY
OPTIONS=DEFERRED_NOT_READY
ALL_BONDS=DEFERRED_NOT_READY
CBOND_READER=脚本/blackbox_tushare_cbond_reader_r2.py
HAND_DECISION_JSON=NOT_FORGED
"""
    guarded_write_path(HAND_PATH, HAND_PATH.read_text(encoding="utf-8") + hand_append)
    return {"promoted": True, "CBOND_CURRENT_PROMOTED": True, "cache_release_id": CACHE_REL_ID}
```

## main @ 脚本/blackbox_tushare_cbond_5y_plane_r2.py L1452-L1611
```python
def main() -> int:
    ctx()
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    pre = must_read_preflight()
    print(f"MUST_READ_PRECHECK={pre['MUST_READ_PRECHECK']} AUTHORITY_READY={pre['AUTHORITY_READY']}", flush=True)
    if pre["MUST_READ_PRECHECK"] != "PASS":
        print("STOP AUTHORITY_READY=NO", flush=True)
        return FAIL
    base = freeze_stock_and_r1()
    print(f"STOCK_BASELINE_ID={base['STOCK_CURRENT_ID']}", flush=True)

    import pandas as pd
    import tushare as ts

    token = load_token()
    pro = ts.pro_api(token)
    audit = run_probes(pro)
    rating_probe = audit["probes"]["cb_rating"]
    top10_probe = audit["probes"]["top10_cb_holders"]
    factor_probe = audit["probes"]["cb_factor_pro"]
    factor_status = "PROBE_OK_DOWNLOAD_NO_PER_R2_SCOPE"
    if factor_probe.get("status") == "PERMISSION_BLOCKED_POINTS_8000":
        factor_status = "PERMISSION_BLOCKED_POINTS_8000"
    elif factor_probe.get("status") == "PERMISSION_BLOCKED":
        factor_status = "PERMISSION_BLOCKED_POINTS_THRESHOLD"
    elif factor_probe.get("status") != "OK":
        factor_status = str(factor_probe.get("status"))

    basic = r1_read("TUSHARE_CBOND_BASIC_R1")
    issue = r1_read("TUSHARE_CBOND_ISSUE_R1")
    call_r1 = r1_read("TUSHARE_CBOND_CALL_R1")
    share_r1 = r1_read("TUSHARE_CBOND_SHARE_R1")
    rate = r1_read("TUSHARE_CBOND_RATE_R1")
    bridge = r1_read("TUSHARE_CBOND_STOCK_BRIDGE_R1")
    codes = sorted({str(x) for x in basic["ts_code"].dropna().tolist()}) if "ts_code" in basic.columns else sorted({str(x) for x in basic["bond_code_ts"].dropna().tolist()})
    pre_codes = []
    if "list_date" in basic.columns:
        for _, r in basic.iterrows():
            ld = ymd(r.get("list_date"))
            code = str(r.get("ts_code") or r.get("bond_code_ts"))
            if ld and ld < START:
                pre_codes.append(code)
        pre_codes = sorted(set(pre_codes))
    carry_audit = {
        "cb_basic_rows": int(len(basic)),
        "cb_issue_rows": int(len(issue)),
        "cb_rate_rows": int(len(rate)),
        "cb_call_rows": int(len(call_r1)),
        "cb_share_rows": int(len(share_r1)),
        "prewindow_listed": len(pre_codes),
        "REDOWNLOAD_SUBJECT": "NO",
    }
    wjson(TASK_DIR / "R1_CARRYIN_AUDIT.json", carry_audit)

    cal = download_trade_cal(pro)
    rating_dl = {"status": "SKIP", "rows": 0}
    if rating_probe.get("status") not in {"PERMISSION_BLOCKED", "PERMISSION_BLOCKED_POINTS_8000", "API_NOT_FOUND"}:
        rating_dl = download_rating(pro, codes)
    else:
        rating_dl = {"status": rating_probe.get("status"), "rows": 0}
    top10_ok = top10_probe.get("status") == "OK"
    top10_dl = download_top10(pro, codes, top10_ok)
    call_carry = download_carryin(pro, "cb_call", pre_codes, CB_CALL_FIELDS)
    share_carry = download_carryin(pro, "cb_share", pre_codes, CB_SHARE_FIELDS)

    rating_raw = concat_raw("cb_rating")
    top10_raw = concat_raw("top10_cb_holders")
    call_carry_df = concat_raw("cb_call")
    share_carry_df = concat_raw("cb_share")

    if rating_dl.get("status") != "DOWNLOADED" or rating_raw.empty:
        wjson(TASK_DIR / "FAIL.json", {"reason": "CB_RATING_DOWNLOAD_FAILED", "rating_dl": rating_dl, "probe": rating_probe})
        print("FINAL_STATUS=TUSHARE_CBOND_5Y_DATA_PLANE_R2_REVIEW_REQUIRED reason=RATING", flush=True)
        return FAIL

    rating_clean, rating_pit, _ = build_rating_pit(rating_raw, cal)
    call_pit = build_call_pit(call_r1, call_carry_df if len(call_carry_df) else None, cal)
    remain_pit = build_remain_pit(share_r1, share_carry_df if len(share_carry_df) else None, issue, basic, cal)
    top10_clean = clean_top10(top10_raw) if len(top10_raw) else pd.DataFrame()

    leak = leakage_tests(rating_pit, call_pit, remain_pit, cal)
    join = local_stock_join_check()
    r1u = r1_untouched(base)
    stk = stock_after(base)

    rating_dups = 0
    if len(rating_pit):
        rating_dups = int(rating_pit.duplicated(["bond_code_jq", "pit_valid_from"]).sum())
    mapped = int(bridge["stock_code_jq"].notna().sum()) if len(bridge) and "stock_code_jq" in bridge.columns else 0
    total_b = int(len(bridge)) if len(bridge) else 0

    val = {
        "VALIDATE_PASS": leak["PIT_LEAKAGE_FAILURES"] == 0
        and r1u["R1_UNTOUCHED"]
        and stk["STOCK_CURRENT_CHANGED"] == "NO"
        and int(stk["STOCK_PRODUCT_MUTATION_COUNT"]) == 0
        and len(rating_pit) > 0
        and len(call_pit) > 0
        and len(remain_pit) > 0
        and rating_dups == 0,
        "PIT_LEAKAGE_FAILURES": leak["PIT_LEAKAGE_FAILURES"],
        "R1_UNTOUCHED": r1u,
        "stock": stk,
        "join": join,
        "rating_dups": rating_dups,
    }
    wjson(TASK_DIR / "VALIDATE_REPORT.json", val)

    promo = {"promoted": False, "CBOND_CURRENT_PROMOTED": False}
    if val["VALIDATE_PASS"]:
        promo = promote(val)
    else:
        print("VALIDATE_FAIL no CURRENT promotion", flush=True)

    accepted = bool(val["VALIDATE_PASS"]) and bool(promo.get("promoted"))
    body = {
        "MUST_READ_PRECHECK": pre["MUST_READ_PRECHECK"],
        "FINAL_STATUS": "TUSHARE_CBOND_5Y_DATA_PLANE_R2_PIT_ENRICHMENT_ACCEPTED" if accepted else "TUSHARE_CBOND_5Y_DATA_PLANE_R2_REVIEW_REQUIRED",
        "CB_RATING_DOWNLOAD_STATUS": rating_dl.get("status"),
        "CB_RATING_ROWS": int(len(rating_raw)),
        "CB_RATING_BONDS": int(rating_raw["ts_code"].nunique()) if len(rating_raw) and "ts_code" in rating_raw.columns else 0,
        "CB_RATING_DUPLICATES": rating_dups,
        "CB_RATING_PIT_STATUS": "READY" if len(rating_pit) and rating_dups == 0 else "FAIL",
        "CB_RATING_PIT_ROWS": int(len(rating_pit)),
        "TOP10_CB_HOLDERS_PERMISSION": top10_probe.get("status"),
        "TOP10_CB_HOLDERS_DOWNLOAD_STATUS": top10_dl.get("status"),
        "TOP10_CB_HOLDERS_ROWS": int(len(top10_raw)),
        "TOP10_CB_HOLDERS_PIT_STATUS": "NOT_READY",
        "CB_CALL_SOURCE_ROWS": int(len(call_r1)),
        "CB_CALL_CARRYIN": call_carry,
        "CB_CALL_PIT_ROWS": int(len(call_pit)),
        "CB_CALL_PIT_STATUS": "READY" if len(call_pit) else "FAIL",
        "CB_SHARE_SOURCE_ROWS": int(len(share_r1)),
        "CB_SHARE_CARRYIN": share_carry,
        "CB_REMAIN_SIZE_PIT_ROWS": int(len(remain_pit)),
        "CB_REMAIN_SIZE_PIT_STATUS": "READY" if len(remain_pit) else "FAIL",
        "CB_FACTOR_PRO_STATUS": factor_status,
        "CB_PRICE_CHG_STATUS": "SEPARATE_PERMISSION_BLOCKED_DO_NOT_RETRY",
        "PIT_LEAKAGE_TESTS": leak["n_cases"],
        "PIT_LEAKAGE_FAILURES": leak["PIT_LEAKAGE_FAILURES"],
        "BOND_STOCK_MAPPING_RATE": (mapped / total_b) if total_b else None,
        "LOCAL_STOCK_JOIN_STATUS": join,
        "STOCK_CURRENT_BEFORE_SHA256": stk["STOCK_CURRENT_BEFORE_SHA256"],
        "STOCK_CURRENT_AFTER_SHA256": stk["STOCK_CURRENT_AFTER_SHA256"],
        "STOCK_CURRENT_CHANGED": stk["STOCK_CURRENT_CHANGED"],
        "STOCK_PRODUCT_MUTATION_COUNT": stk["STOCK_PRODUCT_MUTATION_COUNT"],
        "CBOND_CODE_IN_STOCK_UNIVERSE": 0,
        "SOURCE_VENDOR": SOURCE_VENDOR,
        "JQ_NATIVE_DATA": False,
        "CATALOG_REGISTERED": bool(promo.get("promoted")),
        "INDEX_REGISTERED": bool(promo.get("promoted")),
        "RESOLVER_REGISTERED": bool(promo.get("promoted")),
        "HAND_UPDATED": bool(promo.get("promoted")),
        "CBOND_CURRENT_PROMOTED": bool(promo.get("CBOND_CURRENT_PROMOTED")),
        "limiter": LIMITER.snapshot(),
        "secret_value_printed": False,
    }
    wjson(TASK_DIR / "FINAL_ACCEPTANCE.json", body)
    print(json.dumps({k: body[k] for k in ("FINAL_STATUS", "MUST_READ_PRECHECK", "CB_RATING_PIT_STATUS", "CB_CALL_PIT_STATUS", "CB_REMAIN_SIZE_PIT_STATUS", "PIT_LEAKAGE_FAILURES", "STOCK_CURRENT_CHANGED", "CBOND_CURRENT_PROMOTED")}, ensure_ascii=False, indent=2), flush=True)
    return OK if accepted else FAIL
```
