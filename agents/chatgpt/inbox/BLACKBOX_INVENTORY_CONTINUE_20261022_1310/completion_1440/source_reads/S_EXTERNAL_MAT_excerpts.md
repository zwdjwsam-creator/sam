## main @1716
```
1716|def main() -> int:
1717|    global WORKERS, HIST_END, FORCE_TIP, FORCE_FINANCIAL_TIP
1718|    ap = argparse.ArgumentParser()
1719|    ap.add_argument("--phase", default="all", choices=[
1720|        "tushare", "exchange", "index", "canonical", "acceptance", "all",
1721|        "tushare_p0", "tushare_p1", "tushare_p2", "tushare_p3",
1722|        "asof_align",
1723|    ])
1724|    ap.add_argument("--workers", type=int, default=8, help="parallel Tushare per-code workers (default 8)")
1725|    ap.add_argument("--asof", default=None, help="YYYY-MM-DD or YYYYMMDD; default=JQ SCOPE CURRENT data_asof")
1726|    ap.add_argument("--force-tip", action="store_true", help="force tip refresh when hist_end behind asof")
1727|    ap.add_argument(
1728|        "--force-financial-tip",
1729|        action="store_true",
1730|        help="tip-refresh income/balance/cashflow/fina (slow); auto-on with --force-tip unless --skip-financial-tip",
1731|    )
1732|    ap.add_argument(
1733|        "--skip-financial-tip",
1734|        action="store_true",
1735|        help="opt-out: do not tip financials even when --force-tip (ASOF_ALIGN rule marks incomplete)",
1736|    )
1737|    args = ap.parse_args()
1738|    WORKERS = max(1, min(int(args.workers), 16))
1739|    FORCE_TIP = bool(args.force_tip)
1740|    # HAND ASOF_ALIGN_R1: --force-tip implies financial tip unless explicit skip.
1741|    FORCE_FINANCIAL_TIP = bool(args.force_financial_tip) or (FORCE_TIP and not bool(args.skip_financial_tip))
1742|    HIST_END = resolve_asof_yyyymmdd(args.asof)
1743|    print(
1744|        json.dumps(
1745|            {
1746|                "WORKERS": WORKERS,
1747|                "HIST_END": HIST_END,
1748|                "ASOF": asof_iso(HIST_END),
1749|                "FORCE_TIP": FORCE_TIP,
1750|                "FORCE_FINANCIAL_TIP": FORCE_FINANCIAL_TIP,
1751|            },
1752|            ensure_ascii=False,
1753|        ),
1754|        flush=True,
1755|    )
1756|
```