L3: """FUND ETF NAV premium-plane R1: get_extras incremental → clean/anti-leak → cache → rules.
L6: - API = get_extras(unit_net_value/acc_net_value), BATCH<=5 (forbid whole-table FUND_NET_VALUE)
L37: GAP_START = "2026-07-13"  # day after year-seal batch created_at ~2026-07-12
L38: GAP_END = ASOF
L42: INC_DIR = RAW_NAV / "incremental_get_extras_r1"
L51: LEGACY_BAD_GAP = "fund_etf_nav__incremental_gap_20260713_20260730__20260729_170725.parquet"
L54: def configure_window(*, asof: str, gap_start: str | None = None) -> None:
L56: global ASOF, GAP_START, GAP_END
L58: GAP_END = ASOF
L59: if gap_start:
L60: GAP_START = str(gap_start).strip()
L63: GAP_START = ASOF
L144: trade_days = load_trade_days(GAP_START, GAP_END)
L153: out = INC_DIR / f"fund_etf_nav__ge_batch__{slug}__{GAP_START.replace('-','')}_{GAP_END.replace('-','')}__{now_ts()}.parquet"
L155: df = navc.fetch_nav_batch(batch, GAP_START, GAP_END)
L159: # get_extras long form: rows ≈ codes_with_data * trading_days — never accept ==5000 as complete
L165: # per-code day count: allow full calendar span (get_extras may include non-bday pads)
L167: cal_span = (pd.Timestamp(GAP_END) - pd.Timestamp(GAP_START)).days + 1
L192: "api_mapping": "get_extras.unit_net_value+acc_net_value",
L194: "start": GAP_START,
L195: "end": GAP_END,
L219: tip = INC_DIR / f"fund_etf_nav__ge_consolidated__{GAP_START.replace('-','')}_{GAP_END.replace('-','')}__{now_ts()}.parquet"
L231: "legacy_bad_gap_ignored": LEGACY_BAD_GAP,
L236: "gap_start": GAP_START,
L237: "gap_end": GAP_END,
L262: raise FileNotFoundError("missing consolidated get_extras tip; run --phase download")
L284: """Append prior tip parquet rows so day tip does not drop previous get_extras window."""
L378: tip_clean = tip_dir / f"ETF_NAV__incremental_get_extras__{GAP_START.replace('-','')}_{GAP_END.replace('-','')}__clean.parquet"
L380: dmin = str(tip_df["day"].min()) if len(tip_df) else GAP_START
L381: dmax = str(tip_df["day"].max()) if len(tip_df) else GAP_END
L382: tip_clean = tip_dir / f"ETF_NAV__incremental_get_extras__{dmin.replace('-','')}_{dmax.replace('-','')}__clean.parquet"
L390: "reason": "whole-table/schema-mismatch risk near 5000 silent; superseded by get_extras incremental_get_extras_r1",
L472: f"{PRODUCT_ID},L1,FUND,ACTIVE,year+incremental_tip,Fund/ETF unit_net_value PIT (get_extras); premium derived vs close\n"
L518: "legacy_gap_quarantined": LEGACY_BAD_GAP,
L535: "raw_rel": str(RAW_NAV / "incremental_get_extras_r1"),
L538: "api": "get_extras(unit_net_value)+get_extras(acc_net_value)",
L564: row["note"] = "fund_etf_nav get_extras tip ACTIVE to asof; premium DERIVED; P8 other aux still deferred"
L577: "api": "get_extras",
L604: "FUND_ETF_NAV_API=get_extras.unit_net_value+acc_net_value\n"
L626: description: FUND/ETF NAV + 溢价派生平面 — get_extras 增量；禁止 FUND_NET_VALUE 整表 5000 静默