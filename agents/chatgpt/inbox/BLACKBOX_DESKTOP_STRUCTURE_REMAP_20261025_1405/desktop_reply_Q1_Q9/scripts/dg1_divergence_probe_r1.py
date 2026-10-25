import json, sys
from pathlib import Path

R = Path(r"E:\BLACKBOX")
sys.path.insert(0, str(R / "脚本"))
out = {}

# --- fine grained 产物 ---
fg = R / "数据/美国市场/细粒度利润池/CURRENT"
for n in ("US_FINE_GRAINED_SNAPSHOT_CURRENT.json", "A_SHARE_MAPPING_PRIOR_CURRENT.json"):
    p = fg / n
    ok = p.exists()
    out[n] = {"exists": ok, "bytes": p.stat().st_size if ok else 0}
    if ok:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        out[n]["keys"] = list(d.keys())[:10]
        out[n]["STATUS"] = d.get("STATUS")

p = R / "运行/BLACKBOX_US_MARKET_FINE_GRAINED_FLOW_PROFIT_POOL_CURRENT.json"
d = json.loads(p.read_text(encoding="utf-8-sig"))
out["flow_profit_pool_current"] = {"bytes": p.stat().st_size, "STATUS": d.get("STATUS"),
                                   "US_MARKET_DATE": d.get("US_MARKET_DATE"),
                                   "CN_RESEARCH_DATE": d.get("CN_RESEARCH_DATE"),
                                   "ORDER_ALLOWED": d.get("ORDER_ALLOWED")}

# --- D: 可写性 ---
try:
    t = Path(r"D:\CURSOR_TASK_ARCHIVE") / "_blackbox_write_probe.tmp"
    t.write_text("probe", encoding="utf-8")
    t.unlink()
    out["D_ARCHIVE_writable"] = True
except Exception as e:
    out["D_ARCHIVE_writable"] = f"NO: {e}"

# --- RAW 权威日历 P5 ---
import pandas as pd
p5 = R / "数据/原始只读/JQData_9999_official_raw/P5_jq20_extension/stk_exchange_link_calendar"
out["raw_p5_calendar_exists"] = p5.exists()
if p5.exists():
    fs = sorted(p5.rglob("*.parquet"))
    mx = None
    for f in fs:
        df = pd.read_parquet(f)
        if "day" in df.columns:
            m = str(pd.to_datetime(df["day"]).max())[:10]
            mx = m if mx is None or m > mx else mx
    out["raw_p5_calendar"] = {"parquet": len(fs), "max": mx}

# --- DG1 语义哈希：确认 diff 成因 ---
from blackbox_run_identity_r1 import attach_data_generation_to_manifest

src = json.loads(Path(r"\\192.168.100.2\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\source_workflow_from_SAM\config\研究系统\数据平面\CURRENT\DAILY_DATA_MANIFEST_CURRENT.json").read_text(encoding="utf-8-sig"))
cur = json.loads((R / "研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json").read_text(encoding="utf-8-sig"))

out["src_DG1"] = src.get("DATA_GENERATION_ID")
out["cur_DG1"] = cur.get("DATA_GENERATION_ID")

def dg1_of(obj):
    o = {k: v for k, v in obj.items() if k not in ("DATA_GENERATION_ID", "MANIFEST_SEMANTIC_SHA256", "DATA_GENERATION_ID_ISSUER", "BUILD_TIME")}
    return attach_data_generation_to_manifest(o).get("DATA_GENERATION_ID")

out["src_DG1_recomputed"] = dg1_of(src)
out["cur_DG1_recomputed"] = dg1_of(cur)

# 假设：把 MODE→INGEST、FINE_GRAINED→PASS、删 alignment_csv 后是否回到源机 DG1
import copy
probe = copy.deepcopy(cur)
for lane in ("JQ", "T_EXTERNAL", "GLOBAL_SELLSIDE"):
    probe[lane]["MODE"] = "INGEST"
probe["US_MARKET"]["US_FINE_GRAINED_STATUS"] = "PASS"
probe["US_MARKET"]["A_SHARE_MAPPING_PRIOR_STATUS"] = "PASS"
probe["US_MARKET"]["FIXED_PATHS"].pop("alignment_csv", None)
out["probe_semantics_equal_to_source"] = probe == {k: v for k, v in src.items() if k not in ("DATA_GENERATION_ID", "MANIFEST_SEMANTIC_SHA256", "DATA_GENERATION_ID_ISSUER", "BUILD_TIME")}
out["probe_DG1"] = dg1_of(probe)

# 逐键差异（去掉 DG1 元字段）
def flat(o, pre=""):
    r = {}
    if isinstance(o, dict):
        for k, v in o.items():
            r.update(flat(v, f"{pre}.{k}"))
    elif isinstance(o, list):
        r[pre] = json.dumps(o, ensure_ascii=False)
    else:
        r[pre] = o
    return r

fs, fc = flat(src), flat(cur)
keys = sorted(set(fs) | set(fc))
diffs = [{"key": k, "source": fs.get(k), "desktop": fc.get(k)} for k in keys if fs.get(k) != fc.get(k)]
out["diff_vs_source"] = diffs

# --- 数据平面 lane F 为何写 NOT_RUN ---
dp = (R / "脚本/run_blackbox_daily_incremental_data_plane_r1.py").read_text(encoding="utf-8", errors="ignore").splitlines()
out["lane_f_lines"] = [(i + 1, dp[i][:130]) for i in range(437, 500) if "FINE" in dp[i] or "fine" in dp[i] or "mapping" in dp[i]]

print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
Path(r"E:\BLACKBOX\任务\BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1\输出\DG1_DIVERGENCE_PROBE.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
