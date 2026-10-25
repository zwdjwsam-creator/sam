import json, re, subprocess
from pathlib import Path

R = Path(r"E:\BLACKBOX")
out = {}

# --- 1. cache 产品数（只数目录）---
cur = json.loads((R / "数据/回测缓存/CURRENT_CACHE_RELEASE.json").read_text(encoding="utf-8-sig"))
root = Path(cur["release_root"])
dirs = sorted([c.name for c in root.iterdir() if c.is_dir()])
files = sorted([c.name for c in root.iterdir() if c.is_file()])
out["cache_root"] = str(root)
out["cache_product_dirs"] = len(dirs)
out["cache_top_files"] = files
out["cache_dirs_sample_tail"] = dirs[-6:]

# --- 2. D: 盘与 ARCHIVE 常量 ---
out["D_exists"] = Path("D:\\").exists()
out["D_ARCHIVE_exists"] = Path(r"D:\CURSOR_TASK_ARCHIVE").exists()
arch_hits = []
for p in sorted(R.glob("任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/*.py")):
    t = p.read_text(encoding="utf-8", errors="ignore")
    for i, line in enumerate(t.splitlines(), 1):
        if "CURSOR_TASK_ARCHIVE" in line:
            arch_hits.append({"file": p.name, "line": i, "text": line.strip()[:150]})
out["archive_hits"] = arch_hits
out["archive_hits_n"] = len(arch_hits)

# --- 3. 日历权威 ---
import pandas as pd
cal = root / "JQ20_STK_EXCHANGE_LINK_CALENDAR_R1"
if cal.exists():
    fs = sorted(cal.rglob("*.parquet"))
    mx = None; n = 0
    for f in fs:
        df = pd.read_parquet(f)
        n += len(df)
        cols = df.columns.tolist()
        for c in ("day", "date", "calendar_date", "trade_date"):
            if c in cols:
                m = str(pd.to_datetime(df[c]).max())[:10]
                mx = m if mx is None or m > mx else mx
    out["cache_calendar"] = {"parquet": len(fs), "rows": n, "max": mx, "cols": cols[:8]}
else:
    out["cache_calendar"] = "MISSING"

# --- 4. 17 天 vs 15 天口径 ---
dr = R / "DAILY_RESEARCH"
out["daily_brief"] = sorted(p.name for p in (dr / "DAILY_BRIEF").iterdir())
out["research_trace"] = sorted(p.name for p in (dr / "RESEARCH_TRACE").iterdir())
out["daily_reports"] = sorted(p.name for p in (dr / "DAILY_REPORTS").iterdir())[:8]

# --- 5. 美股细粒度 ---
fg = R / "数据/美国市场/细粒度利润池"
out["fine_grained_root_exists"] = fg.exists()
if fg.exists():
    out["fine_grained_children"] = sorted(p.name for p in fg.iterdir())
fgcur = R / "运行/BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json"
out["fine_grained_current_exists"] = fgcur.exists()
if fgcur.exists():
    d = json.loads(fgcur.read_text(encoding="utf-8-sig"))
    out["fine_grained_current_status"] = d.get("STATUS")

# --- 6. 代码消费者：alignment_csv / alignment ---
consumers = {"alignment_csv": [], "alignment_key": []}
for p in list(R.glob("脚本/*.py")) + list(R.glob("任务/**/*.py")):
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for i, line in enumerate(t.splitlines(), 1):
        if "alignment_csv" in line:
            consumers["alignment_csv"].append(f"{p.relative_to(R)}:{i}")
        if re.search(r'\["alignment"\]|\.get\("alignment"\)', line):
            consumers["alignment_key"].append(f"{p.relative_to(R)}:{i}")
out["consumers"] = consumers

print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
Path(r"E:\BLACKBOX\任务\BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1\输出\DESKTOP_RECHECK_Q1_Q9.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
