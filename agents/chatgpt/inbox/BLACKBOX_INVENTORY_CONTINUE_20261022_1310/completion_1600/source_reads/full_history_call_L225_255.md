# full_history call

`
225|        "etf_fund_index": "natural min_date; no pad to 2014",
226|        "sw_l1": "BLOCKED_UPSTREAM_SW_L1_PIT",
227|    }
228|    fails = [c for c in qa["checks"] if c.get("pass") is False]
229|    qa["overall_pass"] = len(fails) == 0
230|    qa["fail_count"] = len(fails)
231|    wjson(rel / "_qa" / "FULL_HISTORY_ACCEPTANCE.json", qa)
232|    wjson(TASK / "12_ACCEPTANCE" / "FULL_HISTORY_ACCEPTANCE.json", qa)
233|    wjson(ARCHIVE / "FULL_HISTORY_ACCEPTANCE.json", qa)
234|    return qa
235|
236|
237|def main() -> int:
238|    cc.ensure_dirs()
239|    (TASK / "06_PROGRESS").mkdir(parents=True, exist_ok=True)
240|    log("=== FULL HISTORY COMPILE START ===")
241|    cc.write_static_registries()
242|    std = cc.load_current_standard()
243|    cur = json.loads(CURRENT.read_text(encoding="utf-8"))
244|    asof = cur.get("cleaning_as_of") or cur.get("daily_asof") or "2026-08-07"
245|    end = pd.Timestamp(asof)
246|    stock_floor = pd.Timestamp("2014-01-01")
247|    rid = f"BLACKBOX_CACHE_R1_FULL_ASOF_{asof.replace('-', '')}_{cc.ts()}"
248|    rel = RELEASES / rid
249|    rel.mkdir(parents=True, exist_ok=True)
250|    log(f"release={rid} asof={asof} stock_floor={stock_floor.date()} (no backfill)")
251|
252|    ckpt = {
253|        "release_id": rid,
254|        "started_at": cc.now_iso(),
`
