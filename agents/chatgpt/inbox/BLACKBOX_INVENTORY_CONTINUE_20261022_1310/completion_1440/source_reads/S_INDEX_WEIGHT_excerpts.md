## main @19
```
19|def main() -> int:
20|    ap = argparse.ArgumentParser()
21|    ap.add_argument("--run-target-date", required=True)
22|    ap.add_argument("--dry-run", action="store_true")
23|    ap.add_argument("--live", action="store_true")
24|    args = ap.parse_args()
25|    probe = {}
26|    qa = {}
27|    p3 = TASK / "03_SOURCE_CADENCE_PROBE.json"
28|    p2 = TASK / "02_RAW_QA.json"
29|    if p3.is_file():
30|        probe = load_json(p3)
31|    if p2.is_file():
32|        qa = load_json(p2)
33|    out = daily_check(args.run_target_date, probe=probe, qa=qa, live=args.live)
34|    out["dry_run"] = bool(args.dry_run)
35|    out["apply_download"] = False
36|    print(json.dumps(out, ensure_ascii=False, indent=2))
37|    return 0
38|
39|
40|if __name__ == "__main__":
41|    raise SystemExit(main())
```