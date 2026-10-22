# direct_download_billboard_r1.py

sha=807d0cd8f234dfe94acd933ad8af54081dda5ef4bb7622c78f068e449c0e72f7
funcs=['trade_days', 'run_canary', 'run_full', 'run_seal', 'main']

L2: """billboard — get_billboard_list 正式全量。"""
L11: import direct_download_common_r1 as c
L13: DOMAIN = "billboard"
L14: OUT = Path("E:/BLACKBOX/数据/原始只读/JQData_9999_official_raw/P5_attributes_events/billboard")
L27: df = jq.get_billboard_list(stock_list=None, end_date=dt, count=500)
L33: manifest = {"task": f"{DOMAIN}_canary", "generated_at": c.now_iso(), "final_status": "PASS" if ok else "REVIEW_REQUIRED", "api": "get_billboard_list"}
L36: (d / "SAMPLE_EVIDENCE.json").write_text(json.dumps({"samples": evidence}, ensure_ascii=False, indent=2), encoding="utf-8")
L37: (d / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
L48: op = OUT / f"billboard__{yr}__v1__{ts}.parquet"
L49: if op.exists() or any(OUT.glob(f"billboard__{yr}__*.parquet")):
L54: df = jq.get_billboard_list(stock_list=None, end_date=ed, start_date=sd, count=None)
L66: df = jq.get_billboard_list(stock_list=None, end_date=ed, count=10000)
L83: "landed": landed, "still_downloadable": 0, "api_error": full.get("fail", 0), "run_stats": full,
L86: c.write_seal(DOMAIN, manifest, f"# billboard\n\n- landed: {landed}\n")
L96: c.write_blocking(blocks[0].upper(), {"domain": DOMAIN, "blocks": blocks})
L99: c.write_receipt(DOMAIN)
L107: c.append_daily(DOMAIN, seal["final_status"], f"billboard {seal['final_status']}", jdb.quota_left(force=True))