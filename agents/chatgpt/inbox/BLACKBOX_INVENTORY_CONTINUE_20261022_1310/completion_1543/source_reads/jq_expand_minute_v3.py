#!/usr/bin/env python3
# P7 HARD GUARD — inserted by JQ_P7_MINUTE_RELEASE_BLOCKER_REPAIR_R1
# Date: 2026-06-14T18:59:36+00:00
# This script is BLOCKED as a P7 minute download entry.
# Use: guard/jq_p7_minute_guarded_download_entry_r1.py ONLY
#
if __name__ != "__main__":
    raise SystemExit(0)
print("=" * 60)
print("BLOCKED: P7 MINUTE DIRECT ENTRY FORBIDDEN")
print("Use guarded entry: jq_p7_minute_guarded_download_entry_r1.py")
print("This old entrypoint has been blocked.")
print("=" * 60)
raise SystemExit(1)
# END P7 HARD GUARD

# P7 HARD GUARD — inserted by JQ_P7_MINUTE_RELEASE_BLOCKER_REPAIR_R1
# Date: 2026-06-14T18:59:14+00:00
# This script is BLOCKED as a P7 minute download entry.
# Use: guard/jq_p7_minute_guarded_download_entry_r1.py ONLY
#
if __name__ != "__main__":
    raise SystemExit(0)
print("=" * 60)
print("BLOCKED: P7 MINUTE DIRECT ENTRY FORBIDDEN")
print("Use guarded entry: jq_p7_minute_guarded_download_entry_r1.py")
print("This old entrypoint has been blocked.")
print("=" * 60)
raise SystemExit(1)
# END P7 HARD GUARD

"""
全量分钟线下载 V3 — 稳定版
- batch_size=5 统一所有频率（避免挂起）
- 一次性构建文件名索引（O(1)存在性检查）
- 超时重试 + 逐只回退
- 每 5 批检查额度
- 额度降到 <=0 立即停止
"""
import sys, os, json, subprocess, tempfile, time
from pathlib import Path
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8')
sys.dont_write_bytecode = True

ROOT = Path("E:/BLACKBOX/数据/原始只读/JQData_9999_official_raw")
CRED_FILE = Path("E:/BLACKBOX/配置/secrets/已验证/聚宽账号.txt")
META_DIR = ROOT / "P0_meta" if not Path("E:/BLACKBOX/数据/原始只读/JQData_9999_official_raw/P0_meta").exists() else ROOT / "P0_meta"
OUT_DIR = ROOT / "P7_stock_minute"
BATCH_PY = Path("E:/BLACKBOX/脚本/_download_batch.py")
SCHEMA_VER = "1.0.0"
TIMEOUT = 90
RETRY_TIMEOUT = 120
YEARS = list(range(2014, 2027))
FREQS = ["1m", "30m", "60m"]
BATCH_SIZE = 5  # 全部统一 5 只

# ─── 一次性文件名索引 ──────────────────────────────────
EXISTING_FILES: dict = {}  # {freq: {year: {batch_label}}}

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

def file_exists(freq, year, batch_label):
    """O(1) 存在性检查"""
    return batch_label in EXISTING_FILES.get(freq, {}).get(year, set())

# ─── 读取凭据 ───────────────────────────────────────────
def load_cred():
    lines = CRED_FILE.read_text(encoding="utf-8").strip().split("\n")
    u = p = None
    for line in lines:
        line = line.strip()
        if not line: continue
        sep = "：" if "：" in line else ":"
        k, v = line.split(sep, 1)
        k, v = k.strip(), v.strip()
        if "账号" in k or "user" in k.lower(): u = v
        if "密码" in k or "pass" in k.lower(): p = v
    return u, p

CRED_U, CRED_P = load_cred()

# ─── 认证 + 额度（精简版）────────────────────────────────
_AUTHED = False
_QUOTA_SPARE = None
_QUOTA_CHECK_COUNT = 0

def quota_left():
    """返回剩余额度，每 5 次调用触发一次 get_query_count"""
    global _AUTHED, _QUOTA_SPARE, _QUOTA_CHECK_COUNT
    if not _AUTHED:
        import jqdatasdk as jq
        jq.auth(CRED_U, CRED_P)
        _AUTHED = True
    _QUOTA_CHECK_COUNT += 1
    if _QUOTA_CHECK_COUNT % 5 == 0:
        import jqdatasdk as jq
        try:
            q = jq.get_query_count()
            _QUOTA_SPARE = q.get("spare", 0)
        except:
            pass
    return _QUOTA_SPARE

def quota_init():
    """首次认证并获取额度"""
    global _AUTHED, _QUOTA_SPARE, _QUOTA_CHECK_COUNT
    import jqdatasdk as jq
    jq.auth(CRED_U, CRED_P)
    _AUTHED = True
    q = jq.get_query_count()
    _QUOTA_SPARE = q.get("spare", 0)
    _QUOTA_CHECK_COUNT = 0
    return _QUOTA_SPARE

def quota_ok():
    q = quota_left()
    return q is None or q > 0

# ─── 加载全部 A 股 ──────────────────────────────────────
def load_all_stocks():
    import pandas as pd
    codes = []
    for sf in sorted(META_DIR.glob("securities_stock__*.parquet")):
        codes.extend(pd.read_parquet(sf)["code"].dropna().unique().tolist())
    stocks = sorted(set(c.strip() for c in codes if c and isinstance(c, str)))
    return [s for s in stocks if s.endswith(("XSHE", "XSHG"))]

# ─── 子进程下载（超时 + kill）───────────────────────────
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

# ─── 主流程 ─────────────────────────────────────────────
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

if __name__ == "__main__":
    main()
