import json, tempfile, types, sys
from pathlib import Path
from unittest.mock import patch
import blackbox_data_coverage_common_r1 as c
import blackbox_cache_coverage_non_regression_gate_r1 as g

out={}
def cov(n, exists=True, status="OK"):
    return {"exists":exists,"distinct_dates":n,"min_date":"2026-01-01" if n else None,
            "max_date":"2026-09-30" if n else None,"coverage_extract_status":status,
            "coverage_mode":"FULL_HISTORY" if n>1 else ("UNKNOWN_STOP" if exists else "EMPTY_OR_MISSING")}
for label,parent,child in [
    ("lost_40_percent_allowed",cov(100),cov(60)),
    ("same_count_changed_dates_allowed",cov(100),cov(100)),
    ("unknown_parent_allowed",cov(0,False,"MISSING_PRODUCT"),cov(100)),
    ("missing_both_allowed",cov(0,False,"MISSING_PRODUCT"),cov(0,False,"MISSING_PRODUCT"))]:
    with patch.object(g,"_product_cov",side_effect=[parent,child]):
        res=g.gate("parent","child",["STOCK_DAILY_PIT_R1"])
    out[label]={"publishable":res["CACHE_RELEASE_PUBLISHABLE"],"details":res["details"]}
out["two_dates_full_history"]=c.infer_mode_for_product("STOCK_DAILY_PIT_R1",cov(2))
with tempfile.TemporaryDirectory() as td:
    p=Path(td); y=p/"year=2026"; y.mkdir()
    (y/"good.parquet").touch(); (y/"bad.parquet").touch()
    pq=types.ModuleType("pyarrow.parquet")
    def pf(fp):
        if Path(fp).name=="bad.parquet": raise OSError("unreadable partition")
        return types.SimpleNamespace(metadata=types.SimpleNamespace(num_rows=2),
                                     schema_arrow=types.SimpleNamespace(names=["date"]))
    pq.ParquetFile=pf
    pa=types.ModuleType("pyarrow"); pa.parquet=pq
    with patch.dict(sys.modules,{"pyarrow":pa,"pyarrow.parquet":pq}), patch.object(c,"_unique_dates_from_parquet",return_value={"2026-09-01","2026-09-02"}):
        res=c.product_date_coverage(p)
    out["partial_partition_failure"]={"result":res,"mode":c.infer_mode_for_product("STOCK_DAILY_PIT_R1",res)}
with patch.object(c,"load_trade_calendar",return_value=[__import__("datetime").date(2026,9,1)]),patch.object(c,"raw_stock_daily_dates",return_value={"raw_gap_count":1,"raw_missing_trade_days":["2026-09-01"]}),patch.object(c,"cleaning_stock_daily_dates",return_value={"gap_count":1,"missing_trade_days":["2026-09-01"]}),patch.object(c,"cache_stock_daily_dates",return_value={"gap_count":1,"missing_trade_days":["2026-09-01"]}):
    res=c.classify_stock_daily("2026-09-01","2026-09-01")
    out["classifier_contract"]={"root_cause":res["root_cause"],"download_required":res["download_required"],"has_cache_key":"cache" in res,"has_coverage_mode":"coverage_mode" in res}
print(json.dumps(out,ensure_ascii=False,indent=2))

