# 脚本/jq_expand_minute_v3.py
sha256=420d1b8d638727ba8a47282826ed30ccf5b3b1b7a7ef98be2cb1f0af7b9765b7

## build_file_index L61-L80
```python
def build_file_index():
    """构建 {freq: {year: {batch_label}}} 索引"""
    for freq in FREQS:
        EXISTING_FILES[freq] = {}
        for year in YEARS:
            EXISTING_FILES[freq][year] = set()
    for f in OUT_DIR.glob(f"stock_minute_*__*.parquet"):
            parts = f.stem.split("__")
            # stock_minute_{freq}__{year}__{batch}__{ver}__{ts}
            # parts[0] = "stock_minute_1m", parts[1]=year, parts[2]=batch, parts[3]=ver, parts[4]=ts
            if len(parts) >= 5:
                raw_prefix = parts[0]  # e.g. "stock_minute_1m"
                if raw_prefix.startswith("stock_minute_"):
                    f_freq = raw_prefix[len("stock_minute_"):]
                    f_year = parts[1]
                    f_batch = parts[2]
                    if f_freq in FREQS and f_year.isdigit():
                        y = int(f_year)
                        if y in YEARS:
                            EXISTING_FILES[f_freq][y].add(f_batch)
```

## file_exists L82-L84
```python
def file_exists(freq, year, batch_label):
    """O(1) 存在性检查"""
    return batch_label in EXISTING_FILES.get(freq, {}).get(year, set())
```

## load_all_stocks L140-L146
```python
def load_all_stocks():
    import pandas as pd
    codes = []
    for sf in sorted(META_DIR.glob("securities_stock__*.parquet")):
        codes.extend(pd.read_parquet(sf)["code"].dropna().unique().tolist())
    stocks = sorted(set(c.strip() for c in codes if c and isinstance(c, str)))
    return [s for s in stocks if s.endswith(("XSHE", "XSHG"))]
```

## subproc_download L149-L179
```python
def subproc_download(stocks, start_date, end_date, freq, out_path, timeout=TIMEOUT):
    tmp = Path(tempfile.gettempdir()) / f"_jq_min_{os.getpid()}_{int(time.time()*1000)}_{freq}.parquet"
    cmd = [
        sys.executable, "-u", str(BATCH_PY),
        json.dumps(stocks), start_date, end_date, freq,
        str(tmp), str(int(time.time())), SCHEMA_VER,
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
        tmp.unlink(missing_ok=True)
        return None
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        return None
    if tmp.exists() and tmp.stat().st_size > 200:
        import pandas as pd
        try:
            df = pd.read_parquet(tmp)
            if len(df) > 0:
                df.to_parquet(out_path, index=False)
            tmp.unlink(missing_ok=True)
            return df
        except:
            tmp.unlink(missing_ok=True)
            return None
    tmp.unlink(missing_ok=True)
    return None
```

## try_download L181-L207
```python
def try_download(stocks, start, end, freq, out_path):
    """下载 + 1次重试 + 逐只回退"""
    df = subproc_download(stocks, start, end, freq, out_path, timeout=TIMEOUT)
    if df is not None and len(df) > 0:
        return df, []
    # 重试一次
    df = subproc_download(stocks, start, end, freq, out_path, timeout=RETRY_TIMEOUT)
    if df is not None and len(df) > 0:
        return df, []
    # 超时/失败 → 逐只下载
    skipped = []
    import pandas as pd
    all_parts = []
    for s in stocks:
        part_path = Path(tempfile.gettempdir()) / f"_jq_part_{s}_{int(time.time()*1000)}.parquet"
        part = subproc_download([s], start, end, freq, part_path, timeout=TIMEOUT)
        if part is not None and len(part) > 0:
            all_parts.append(part)
            part_path.unlink(missing_ok=True)
        else:
            skipped.append(s)
            part_path.unlink(missing_ok=True)
    if all_parts:
        combined = pd.concat(all_parts, ignore_index=True)
        combined.to_parquet(out_path, index=False)
        return combined, skipped
    return None, skipped
```

## main L210-L314
```python
def main():
    print("="*60)
    print("全量分钟线下载 V3 — 稳定版 (batch_size=5)")
    print(f"开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    t_start = time.time()
    build_file_index()
    for freq in FREQS:
        n_idx = sum(len(v) for v in EXISTING_FILES[freq].values())
        print(f"  [{freq}] 索引: {n_idx} 条")

    all_stocks = load_all_stocks()
    print(f"全部A股: {len(all_stocks)} 只")

    q0 = quota_init()
    print(f"初始额度: {q0:,}")
    if q0 is not None and q0 <= 0:
        print("额度已耗尽")
        return

    grand_files = 0
    grand_rows = 0
    all_skipped = []
    total_api = 0

    for freq in FREQS:
        if not quota_ok():
            break

        print(f"\n--- 频率 {freq} ---")
        local_files = 0
        local_rows = 0
        local_api = 0
        freq_skipped = []

        # 按股票索引分批 (batch_size=5, 全覆盖)
        n_batches = (len(all_stocks) + BATCH_SIZE - 1) // BATCH_SIZE

        for bi in range(n_batches):
            s = bi * BATCH_SIZE
            e = min(s + BATCH_SIZE, len(all_stocks))
            batch_stocks = all_stocks[s:e]
            batch_label = f"batch{bi:04d}"

            # 检查所有年份是否已存在
            all_exist = True
            for year in YEARS:
                if not file_exists(freq, year, batch_label):
                    all_exist = False
                    break
            if all_exist:
                continue  # 整批跳过

            for year in YEARS:
                if file_exists(freq, year, batch_label):
                    continue
                if not quota_ok():
                    break

                out_path = OUT_DIR / f"stock_minute_{freq}__{year}__{batch_label}__{SCHEMA_VER}__{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
                t0 = time.time()
                df, skipped = try_download(batch_stocks, f"{year}-01-01", f"{year}-12-31", freq, out_path)
                t = time.time() - t0
                local_api += 1 + len([s for s in skipped])  # 批量 + 逐只重试

                if df is not None and len(df) > 0:
                    local_rows += len(df)
                    local_files += 1
                freq_skipped.extend(skipped)

            # 每 5 批显示进度
            if (bi + 1) % 5 == 0 or bi == n_batches - 1:
                q = quota_left()
                elapsed = time.time() - t_start
                print(f"  [{freq}]批 {bi+1}/{n_batches}, "
                      f"文件={local_files}, 行={local_rows:,}, "
                      f"剩余额度={q}, API={local_api}, "
                      f"耗时={elapsed:.0f}s", flush=True)
                if q is not None and q <= 0:
                    print(f"\n  额度已耗尽!")
                    break

            if not quota_ok():
                break

        grand_files += local_files
        grand_rows += local_rows
        total_api += local_api
        all_skipped.extend(freq_skipped)
        print(f"  [{freq}]完成: {local_files}文件, {local_rows:,}行, 跳过{len(set(freq_skipped))}只")

    q_end = quota_left()
    elapsed = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"全部完成")
    print(f"新增: {grand_files} 文件, {grand_rows:,} 行")
    print(f"API调用: {total_api} 次")
    print(f"跳过(超时): {len(set(all_skipped))} 只")
    if all_skipped:
        print(f"  前20: {sorted(set(all_skipped))[:20]}")
    print(f"初始额度: {q0:,}")
    print(f"剩余额度: {q_end}")
    print(f"总耗时: {elapsed:.0f}s ({elapsed/60:.1f}min)")
    print(f"{'='*60}")
```
