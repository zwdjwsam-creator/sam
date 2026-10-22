# aux_billboard_adjust_index_minute_r15.py

sha=daf65eb17dc1e7e59c1cb5cb888e69c997dba8d6b2e73efde920c6629ea8052b
funcs=['now_iso', 'ts', 'log', 'wjson', 'hand_ok', 'download_billboard', 'download_adjust_factor_day', 'load_codes', 'download_index_minute_day', 'merge_staging', 'main']

L2: """R15 aux download: billboard + adjust_factor + index_minute for asof day."""
L19: RAW = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw")
L22: P5_BB = RAW / "P5_attributes_events" / "billboard"
L31: LOG = TASK / "11_LOGS" / "aux_download.log"
L47: f.write(line + "\n")
L53: tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
L66: def download_billboard(jq, start: str, end: str) -> dict:
L71: df = jq.get_billboard_list(stock_list=None, end_date=d, count=1)
L73: log(f"billboard empty {d}")
L80: log(f"billboard {d} rows={len(df)}")
L82: log(f"billboard FAIL {d}: {e}")
L87: P5_BB.mkdir(parents=True, exist_ok=True)
L88: fp = P5_BB / f"billboard__incremental__{start.replace('-','')}_{end.replace('-','')}__{stamp}.parquet"
L96: "clean_rel": f"events/billboard/{fp.name}",
L102: def download_adjust_factor_day(jq, day: str) -> dict:
L160: def download_index_minute_day(jq, day: str) -> dict:
L240: import jq_download_base as jdb
L248: # billboard: from day after last known through ASOF
L251: results["billboard"] = download_billboard(jq, bb_start, ASOF)
L253: results["billboard"] = {"status": "FAIL", "error": str(e), "tb": traceback.format_exc()}
L254: log(f"billboard FAIL {e}")
L257: results["adjust_factor"] = download_adjust_factor_day(jq, ASOF)
L263: results["index_minute"] = download_index_minute_day(jq, ASOF)
L269: if results.get("billboard", {}).get("status") == "PASS":
L270: merge_items.append(results["billboard"])
L284: for k in ("billboard", "adjust_factor")