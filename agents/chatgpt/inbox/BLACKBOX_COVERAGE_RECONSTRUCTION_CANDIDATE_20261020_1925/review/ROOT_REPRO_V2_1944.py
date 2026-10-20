import json, tempfile
from pathlib import Path
from datetime import date
from unittest.mock import patch
import pandas as pd
import blackbox_data_coverage_common_r1 as common
import blackbox_data_access_resolver_r1 as resolver
import blackbox_cache_coverage_non_regression_gate_r1 as gate

out={}
with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    pid="STOCK_DAILY_PIT_R1"; (root/pid).mkdir()
    cov={"exists":True,"coverage_extract_status":"UNVERIFIABLE","errors":["bad.parquet:OSError"],
         "dates":["2026-09-01","2026-09-02"],"distinct_dates":2,"min_date":"2026-09-01","max_date":"2026-09-02","year_slices":["year=2026"]}
    currents={"catalog":pd.DataFrame([{"product_id":pid,"asset_type":"STOCK"}]),"cache_release_root":str(root),"_request_start_date":"2026-09-01","_request_end_date":"2026-09-02"}
    with patch.object(common,"product_date_coverage",return_value=cov),patch.object(common,"load_trade_calendar",return_value=[date(2026,9,1),date(2026,9,2)]):
        r=resolver.resolve_product(pid,None,None,currents)
    out["bad_partition_actual_resolver"]={k:r.get(k) for k in ["coverage_mode","coverage_ready","historical_ready","result_status"]}
    pid="CORP_SHAREHOLDER_TOP10_PIT_R1"; (root/pid).mkdir()
    currents={"catalog":pd.DataFrame([{"product_id":pid,"asset_type":"STOCK"}]),"cache_release_root":str(root)}
    r=resolver.resolve_product(pid,None,None,currents)
    out["unsupported_actual_resolver_no_window"]={k:r.get(k) for k in ["coverage_mode","coverage_ready","historical_ready","result_status"]}
cov={"exists":True,"coverage_extract_status":"OK","errors":[],"distinct_dates":100,"min_date":"2014-01-02","max_date":"2026-09-24","year_slices":["year=2014","year=2026"]}
out["100_sparse_dates_without_contract"]=common.infer_mode_for_product("STOCK_DAILY_PIT_R1",cov)
def facts(ds):
 return {"exists":True,"coverage_extract_status":"OK","errors":[],"dates":ds,"distinct_dates":len(ds),"min_date":min(ds),"max_date":max(ds),"year_slices":["year=2026"]}
with patch.object(gate,"product_date_coverage",side_effect=[facts(["2026-09-01","2026-09-02"]),facts(["2026-09-01"])]):
 r=gate.gate("parent","child",["STOCK_DAILY_PIT_R1"])
out["previous_date_loss_now_rejected"]=r["CACHE_RELEASE_PUBLISHABLE"] is False
print(json.dumps(out,ensure_ascii=False,indent=2))
