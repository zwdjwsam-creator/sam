# resolver catalog reject
path=E:\BLACKBOX\脚本\blackbox_data_access_resolver_r1.py
sha256=88ec468f5b18bf7eec2002d605e7922d7ff085f6bbf9fb69d0d57d6d3716f6f5

```
583|    # 3. Look up in catalog
584|    catalog = currents.get("catalog")
585|    if catalog is None:
586|        return {"resolved": False, "result_status": "CATALOG_MISSING"}
587|
588|    if normalized in ("FUND_PORTFOLIO_STOCK_PIT_R1", "FUND_PORTFOLIO_STOCK", "fund_portfolio_stock"):
589|        return {
590|            "resolved": False,
591|            "result_status": "SOURCE_PRESENT_AUTHORITY_NOT_PRODUCTIZED",
592|            "product_id": "FUND_PORTFOLIO_STOCK_PIT_R1",
593|            "SOURCE_API_AVAILABLE": True,
594|            "LOCAL_RAW_PRESENT": False,
595|            "FORMAL_PRODUCT_AVAILABLE": False,
596|            "CACHE_PRODUCT_AVAILABLE": False,
597|            "OLD_LEDGER_POINTER_STATUS": "MISCLASSIFIED_NAV_SOURCE",
598|            "must_not_return": "NAV",
599|            "WEIGHT_PROXY_FORBIDDEN": True,
600|            "download_required": False,
601|            "error": "finance.FUND_PORTFOLIO_STOCK API exists; local holdings RAW/formal product absent. P4b_fund_expand is NAV, not holdings.",
602|        }
603|
604|    product_rows = catalog[catalog["product_id"] == normalized]
605|    if len(product_rows) == 0:
606|        # Formal coverage classification — do not say "maybe missing download"
607|        related = None
608|        if normalized == "VALUATION_PIT_R1":
609|            related = "STOCK_FACTOR_DAILY_R1"
610|        return {
611|            "resolved": False,
612|            "result_status": "CACHE_PRODUCT_UNAVAILABLE",
613|            "root_cause": "CACHE_PRODUCT_UNAVAILABLE",
614|            "download_required": False,
615|            "error": f"Product '{normalized}' not in CACHE catalog. Requested as '{dataset_raw}'.",
616|            "related_product_hint": related,
617|            "note": (
618|                "Do not claim BLACKBOX has no valuation source; RAW may exist. "
619|                "Dedicated VALUATION_PIT cache product is unavailable — use formal diagnosis."
620|            ),
621|        }
622|    product_info = product_rows.iloc[0].to_dict()
623|
624|    # 4. Check R19 superseded guard for FUND_MF
625|    if "FUND_MF" in normalized and "R19" in str(currents.get("cache_release_id", "")):
626|        return {
627|            "resolved": False,
```
