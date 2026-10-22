# 任务/BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1/p4_etf_nav_share_common_r1.py
sha256=8ef7374dfa3d26cbfd1b69f233beed33453394810db5852b7bf79d6102c92ac3
size=10780
## fetch_nav_batch L238-L251 (14 lines)
`python
def fetch_nav_batch(codes: list[str], start: str, end: str) -> pd.DataFrame:
    import jqdatasdk as jq

    u = jq.get_extras("unit_net_value", codes, start_date=start, end_date=end, df=True)
    a = jq.get_extras("acc_net_value", codes, start_date=start, end_date=end, df=True)
    if u is None or len(u) == 0:
        return pd.DataFrame(columns=["code", "day", "unit_net_value", "acc_net_value"])
    du = extras_to_long(u, "unit_net_value")
    if a is None or len(a) == 0:
        da = pd.DataFrame(columns=["code", "day", "acc_net_value"])
    else:
        da = extras_to_long(a, "acc_net_value")
    m = du.merge(da, on=["code", "day"], how="outer")
    return m.sort_values(["code", "day"]).reset_index(drop=True)
`
## validate_nav_df L271-L285 (15 lines)
`python
def validate_nav_df(df: pd.DataFrame) -> list[str]:
    errs: list[str] = []
    if len(df) == 0:
        return errs
    need = {"code", "day", "unit_net_value", "acc_net_value"}
    if not need.issubset(set(df.columns)):
        errs.append("missing_columns")
        return errs
    if len(df) == 0:
        return errs
    if df.duplicated(subset=["code", "day"]).any():
        errs.append("duplicate_code_day")
    if not df["day"].is_monotonic_increasing:
        pass
    return errs
`