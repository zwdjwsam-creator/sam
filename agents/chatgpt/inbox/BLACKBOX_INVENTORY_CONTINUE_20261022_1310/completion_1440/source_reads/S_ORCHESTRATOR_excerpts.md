## main @26
```
26|def main() -> int:
27|    ap = argparse.ArgumentParser()
28|    ap.add_argument("--run-target-date", required=True)
29|    ap.add_argument("--cleaning-json", help="Cleaning candidate RELEASE.json; default live CURRENT")
30|    ap.add_argument("--no-publish", action="store_true")
31|    ap.add_argument("--out-root")
32|    ap.add_argument("--parent-root")
33|    args = ap.parse_args()
34|    tgt = resolve_run_target_trade_date(cli_date=args.run_target_date)
35|    check_cmd = [
36|        str(PY), "-u", str(INDEX_WEIGHT_CHECK),
37|        "--run-target-date", tgt["RUN_TARGET_TRADE_DATE"],
38|    ]
39|    if args.no_publish:
40|        check_cmd.append("--dry-run")
41|    print(json.dumps({"step": "INDEX_WEIGHT_MANAGED_CHECK", "dry_run": bool(args.no_publish)}, ensure_ascii=False))
42|    rc_w = subprocess.call(check_cmd)
43|    if rc_w != 0:
44|        return rc_w
45|    etf_min_check = ROOT / "脚本" / "blackbox_etf_minute_daily_increment_check_r1.py"
46|    etf_cmd = [
47|        str(PY), "-u", str(etf_min_check),
48|        "--run-target-date", tgt["RUN_TARGET_TRADE_DATE"],
49|    ]
50|    if args.no_publish:
51|        etf_cmd.append("--dry-run")
52|    print(json.dumps({"step": "ETF_MINUTE_1M_MANAGED_CHECK", "dry_run": bool(args.no_publish)}, ensure_ascii=False))
53|    rc_m = subprocess.call(etf_cmd)
54|    if rc_m != 0:
55|        return rc_m
56|    cmd = [
57|        str(PY), "-u", str(TIP),
58|        "--run-target-date", tgt["RUN_TARGET_TRADE_DATE"],
59|    ]
60|    if args.cleaning_json:
61|        cmd.extend(["--cleaning-json", args.cleaning_json])
62|    if args.parent_root:
63|        cmd.extend(["--parent-root", args.parent_root])
64|    if args.out_root:
65|        cmd.extend(["--out-root", args.out_root])
66|    if args.no_publish:
```