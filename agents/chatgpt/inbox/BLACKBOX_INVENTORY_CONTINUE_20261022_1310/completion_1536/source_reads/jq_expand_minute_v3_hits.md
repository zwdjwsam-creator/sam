# jq_expand_minute_v3.py
sha=420d1b8d638727ba8a47282826ed30ccf5b3b1b7a7ef98be2cb1f0af7b9765b7
freqs_seen=['1m', '30m', '60m']

L49: OUT_DIR = ROOT / "P7_stock_minute"
L55: FREQS = ["1m", "30m", "60m"]
L67: for f in OUT_DIR.glob(f"stock_minute_*__*.parquet"):
L69: # stock_minute_{freq}__{year}__{batch}__{ver}__{ts}
L70: # parts[0] = "stock_minute_1m", parts[1]=year, parts[2]=batch, parts[3]=ver, parts[4]=ts
L72: raw_prefix = parts[0]  # e.g. "stock_minute_1m"
L73: if raw_prefix.startswith("stock_minute_"):
L74: f_freq = raw_prefix[len("stock_minute_"):]
L140: def load_all_stocks():
L143: for sf in sorted(META_DIR.glob("securities_stock__*.parquet")):
L145: stocks = sorted(set(c.strip() for c in codes if c and isinstance(c, str)))
L146: return [s for s in stocks if s.endswith(("XSHE", "XSHG"))]
L149: def subproc_download(stocks, start_date, end_date, freq, out_path, timeout=TIMEOUT):
L153: json.dumps(stocks), start_date, end_date, freq,
L181: def try_download(stocks, start, end, freq, out_path):
L183: df = subproc_download(stocks, start, end, freq, out_path, timeout=TIMEOUT)
L187: df = subproc_download(stocks, start, end, freq, out_path, timeout=RETRY_TIMEOUT)
L194: for s in stocks:
L222: all_stocks = load_all_stocks()
L223: print(f"全部A股: {len(all_stocks)} 只")
L247: n_batches = (len(all_stocks) + BATCH_SIZE - 1) // BATCH_SIZE
L251: e = min(s + BATCH_SIZE, len(all_stocks))
L252: batch_stocks = all_stocks[s:e]
L270: out_path = OUT_DIR / f"stock_minute_{freq}__{year}__{batch_label}__{SCHEMA_VER}__{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
L272: df, skipped = try_download(batch_stocks, f"{year}-01-01", f"{year}-12-31", freq, out_path)