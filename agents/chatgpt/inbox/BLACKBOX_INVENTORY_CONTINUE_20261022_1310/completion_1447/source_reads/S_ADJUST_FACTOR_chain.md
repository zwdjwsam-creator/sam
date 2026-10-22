## wrapper_main
```
1|# -*- coding: utf-8 -*-
2|"""Permanent entry for ADJUST_FACTOR_PIT_R1 backward-dirty incremental refresh."""
3|from _base import *  # noqa: F401,F403
4|
5|import sys
6|from pathlib import Path
7|
8|TASK_SCRIPT = ROOT / "任务" / "BLACKBOX_ADJUST_FACTOR_PIT_R1_FULL_REBUILD_AND_BACKWARD_REFRESH_R1" / "incremental_backward_refresh_r1.py"
9|PY = ROOT / ".venv" / "Scripts" / "python.exe"
10|
11|
12|def main() -> int:
13|    if not TASK_SCRIPT.is_file():
14|        print("HARD_BLOCK: incremental engine missing", TASK_SCRIPT)
15|        return FAIL
16|    cmd = [str(PY), "-u", str(TASK_SCRIPT), *sys.argv[1:]]
17|    r = guarded_run(cmd, cwd=str(ROOT))
18|    return int(r.returncode)
19|
20|
21|if __name__ == "__main__":
22|    raise SystemExit(main())
```

## task_main
```
188|def main() -> int:
189|    ap = argparse.ArgumentParser()
190|    ap.add_argument("--update-date", default="2026-08-14")
191|    ap.add_argument("--overlap-days", type=int, default=OVERLAP_DAYS)
192|    ap.add_argument("--selftest", action="store_true")
193|    args = ap.parse_args()
194|    auth()
195|    import jqdatasdk as jq
196|
197|    cur = json.loads(CACHE_PTR.read_text(encoding="utf-8"))
198|    cache = load_cache_factor()
199|    ud = pd.Timestamp(args.update_date)
200|    cache_dates = sorted(cache.loc[cache["date"] <= ud, "date"].unique())
201|    overlap = cache_dates[-int(args.overlap_days) :]
202|    codes = sorted(cache["code"].unique())
203|    live = fetch_factor(jq, codes, str(overlap[0].date()), str(ud.date()))
204|    merged = cache.merge(live, on=["date", "code"], how="inner", suffixes=("_cache", "_live"))
205|    merged["abs_diff"] = (merged["factor_cache"] - merged["factor_live"]).abs()
206|    dirty = merged.loc[merged["abs_diff"] > 1e-8, "code"].drop_duplicates().tolist()
207|    xr_aux = aux_xr_codes(Path(cur["release_root"]), overlap[0], ud)
208|    receipt = {
209|        "update_date": args.update_date,
210|        "new_date_appended": None,
211|        "overlap_dates_checked": [str(x.date()) for x in overlap],
212|        "overlap_codes_checked": int(merged["code"].nunique()),
213|        "backward_dirty_count": int(len(dirty)),
214|        "backward_dirty_codes": dirty[:50],
215|        "xr_xd_aux_codes_in_overlap": xr_aux[:50],
216|        "xr_xd_aux_count": int(len(xr_aux)),
217|        "xr_xd_is_sole_trigger": False,
218|        "full_history_refreshed_count": 0,
219|        "factor_revision_rows": int((merged["abs_diff"] > 1e-8).sum()),
220|        "source_max_date": str(live["date"].max().date()) if len(live) else None,
221|        "cache_max_date": str(cache["date"].max().date()),
222|        "resolver_release": cur["cache_release_id"],
223|        "raw_fallback_used": False,
224|        "silent_factor_one_used": False,
225|        "fq": FQ,
226|        "FULL_HISTORY_START": FULL_HISTORY_START,
227|        "AUTHORITY_READY": False,
```

## publish_successor
```
134|def publish_successor(new_factor: pd.DataFrame, reason: str) -> dict:
135|    cur = json.loads(CACHE_PTR.read_text(encoding="utf-8"))
136|    parent = Path(cur["release_root"])
137|    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
138|    rid = f"BLACKBOX_CACHE_R1_ADJFACTOR_PIT_INCR_{stamp}"
139|    dst = CACHE_ROOT / "releases" / rid
140|    dst.mkdir(parents=True, exist_ok=True)
141|    inherited = 0
142|    for child in parent.iterdir():
143|        if child.name == PRODUCT:
144|            continue
145|        mode = inherit_tree(child, dst / child.name)
146|        if mode in ("JUNCTION", "COPYTREE", "EXISTS", "COPYFILE"):
147|            inherited += 1
148|    write_factor_years(dst / PRODUCT, new_factor)
149|    cov = {
150|        "product_id": PRODUCT,
151|        "date_min": str(new_factor["date"].min().date()),
152|        "date_max": str(new_factor["date"].max().date()),
153|        "n_codes": int(new_factor["code"].nunique()),
154|        "n_rows": int(len(new_factor)),
155|        "fq": FQ,
156|        "reason": reason,
157|    }
158|    wjson(dst / PRODUCT / "COVERAGE.json", cov)
159|    pointer = {
160|        "cache_release_id": rid,
161|        "release_root": str(dst),
162|        "published_at_cn": now_cn(),
163|        "asof": str(new_factor["date"].max().date()),
```