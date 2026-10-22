# resolver excerpts

## 29-40
```
29|HAND_PATH = ROOT / "HAND.txt"
30|CACHE_CURRENT_PTR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
31|CLEANING_CURRENT_PTR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
32|CATALOG_CSV = ROOT / "数据" / "回测缓存" / "registry" / "CACHE_PRODUCT_CATALOG.csv"
33|MANIFEST_JSON = ROOT / "数据" / "回测缓存" / "registry" / "CACHE_MANIFEST_REGISTRY.json"
34|LEDGER_JSON = ROOT / "运行" / "BLACKBOX_JQ_ACCESSIBLE_DATASET_LEDGER_CURRENT.json"
35|R19_PROVENANCE = ROOT / "运行" / "BLACKBOX_CLEANING_RELEASE_PROVENANCE_R19_POST_SEAL_MUTATION.json"
36|INDEX_PATH = ROOT / "运行" / "BLACKBOX_DATA_ACCESS_INDEX_CURRENT.json"
37|SIDECAR_PRODUCTS = ROOT / "运行" / "BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json"
38|CBOND_CACHE_CURRENT_PTR = ROOT / "数据" / "回测缓存" / "可转债指针" / "CURRENT_CBOND_CACHE_RELEASE.json"
39|CBOND_PRODUCT_PREFIX = "TUSHARE_CBOND_"
40|EXTERNAL_EVIDENCE_RESOLVER_PTR = ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json"
```

## 383-443
```
383|    if CACHE_CURRENT_PTR.is_file():
384|        cache = json.loads(CACHE_CURRENT_PTR.read_text(encoding="utf-8"))
385|        result["cache_current"] = cache
386|        result["cache_release_id"] = cache.get("cache_release_id", "")
387|        # CURRENT_CACHE_RELEASE.json uses release_root; some older pointers used standard_root
388|        result["cache_release_root"] = (
389|            cache.get("release_root")
390|            or cache.get("standard_root")
391|            or cache.get("cache_root")
392|            or ""
393|        )
394|        result["cache_asof"] = cache.get("asof", "")
395|    else:
396|        errors.append("CACHE_CURRENT_POINTER MISSING")
397|        result["cache_current"] = None
398|
399|    if CBOND_CACHE_CURRENT_PTR.is_file():
400|        cbond = json.loads(CBOND_CACHE_CURRENT_PTR.read_text(encoding="utf-8"))
401|        result["cbond_cache_current"] = cbond
402|        result["cbond_cache_release_id"] = cbond.get("cache_release_id", "")
403|        result["cbond_cache_release_root"] = cbond.get("release_root", "")
404|        result["cbond_source_vendor"] = cbond.get("source_vendor", "TUSHARE_PRO")
405|        result["cbond_product_path_map"] = cbond.get("product_path_map") or {}
406|        result["cbond_parent_release_root"] = cbond.get("parent_release_root") or ""
407|    else:
408|        result["cbond_cache_current"] = None
409|        result["cbond_cache_release_root"] = ""
410|
411|    result["sidecar_product_path_map"] = {}
412|    if SIDECAR_PRODUCTS.is_file():
413|        side = json.loads(SIDECAR_PRODUCTS.read_text(encoding="utf-8"))
414|        result["sidecar_products"] = side
415|        pmap = {}
416|        for pid, meta in (side.get("products") or {}).items():
417|            if isinstance(meta, dict) and meta.get("cache_product_path"):
418|                pmap[pid] = meta["cache_product_path"]
419|        result["sidecar_product_path_map"] = pmap
420|    else:
421|        result["sidecar_products"] = None
422|
423|    # EXTERNAL EVIDENCE resolver (source-isolated; never mixes into JQ products)
424|    if EXTERNAL_EVIDENCE_RESOLVER_PTR.is_file():
425|        ext = json.loads(EXTERNAL_EVIDENCE_RESOLVER_PTR.read_text(encoding="utf-8"))
426|        result["external_evidence_resolver"] = ext
427|        emap = {}
428|        for row in ext.get("products") or []:
429|            if not isinstance(row, dict):
430|                continue
431|            pid = row.get("product_id")
432|            if pid and row.get("resolver_ready") and row.get("path"):
433|                emap[pid] = row
434|        result["external_evidence_product_map"] = emap
435|    else:
436|        result["external_evidence_resolver"] = None
437|        result["external_evidence_product_map"] = {}
438|
439|    # CLEANING CURRENT
440|    if CLEANING_CURRENT_PTR.is_file():
441|        clean = json.loads(CLEANING_CURRENT_PTR.read_text(encoding="utf-8"))
442|        result["cleaning_current"] = clean
443|        result["cleaning_release_id"] = clean.get("release_id", "")
```

## 710-755
```
710|        historical_ready = coverage_mode in ("FULL_HISTORY", "DAILY_HISTORY", "ASOF_SNAPSHOT_HISTORY") and (
711|            (coverage_distinct or 0) > 1
712|        )
713|        # start/end injected via currents optional keys
714|        start_date = currents.get("_request_start_date")
715|        end_date = currents.get("_request_end_date")
716|        if start_date and end_date and normalized in ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1"):
717|            expected = [str(d) for d in load_trade_calendar(start_date, end_date)]
718|            have = set(cov.get("dates") or [])
719|            missing_trade_days = [d for d in expected if d not in have]
720|            expected_trade_days = len(expected)
721|            available_trade_days = len(expected) - len(missing_trade_days)
722|            coverage_ready = len(missing_trade_days) == 0 and coverage_mode != "INCREMENTAL_PATCH"
723|        elif start_date and end_date:
724|            # generic: min/max containment
725|            coverage_ready = (
726|                coverage_min is not None
727|                and coverage_max is not None
728|                and coverage_min <= start_date
729|                and coverage_max >= end_date
730|                and coverage_mode != "INCREMENTAL_PATCH"
731|            )
732|        else:
733|            coverage_ready = historical_ready if normalized in (
734|                "STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "INDEX_DAILY_R1", "STOCK_FACTOR_DAILY_R1"
735|            ) else True
736|    except Exception as e:
737|        coverage_mode = "UNKNOWN_STOP"
738|        coverage_ready = False
739|        currents["_coverage_error"] = str(e)
740|
741|    # 12. Build result
742|    result = {
743|        "resolved": True,
744|        "result_status": "READY",
745|        "logical_dataset_id": dataset_raw,
746|        "product_id": normalized,
747|        "cache_release_id": currents.get("cache_release_id", ""),
748|        "cache_asof": currents.get("cache_asof", ""),
749|        "product_path": product_path,
750|        "coverage_mode": coverage_mode,
751|        "coverage_min_date": coverage_min,
752|        "coverage_max_date": coverage_max,
753|        "coverage_distinct_dates": coverage_distinct,
754|        "historical_ready": historical_ready,
755|        "coverage_ready": coverage_ready,
```
