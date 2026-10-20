import json, tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import blackbox_data_coverage_common_r1 as c
import blackbox_cache_coverage_non_regression_gate_r1 as g
import blackbox_data_access_resolver_r1 as r
out={}
with tempfile.TemporaryDirectory() as td:
 root=Path(td); pid="STOCK_DAILY_PIT_R1";(root/pid).mkdir()
 bad={"exists":True,"coverage_extract_status":"UNVERIFIABLE","errors":["bad"],"dates":["2026-09-01","2026-09-02"],"distinct_dates":2,"min_date":"2026-09-01","max_date":"2026-09-02","year_slices":["year=2026"],"supported_product":True}
 curr={"catalog":pd.DataFrame([{"product_id":pid,"asset_type":"STOCK"}]),"cache_release_root":str(root),"_request_start_date":"2026-09-01","_request_end_date":"2026-09-02"}
 with patch.object(c,"product_date_coverage",return_value=bad),patch.object(c,"load_trade_calendar",return_value=[date(2026,9,1),date(2026,9,2)]):
  x=r.resolve_product(pid,None,None,curr)
 out["previous_unverifiable_repro"]={"mode":x["coverage_mode"],"coverage_ready":x["coverage_ready"]}
 good={**bad,"coverage_extract_status":"OK","errors":[]}
 with patch.object(c,"load_trade_calendar",return_value=[date(2026,9,1),date(2026,9,2)]):
  out["two_days_with_own_range"]=c.infer_mode_for_product(pid,good)
  out["existing_self_test"]=g.self_test()
 curr.pop("_request_start_date");curr.pop("_request_end_date")
 with patch.object(c,"product_date_coverage",return_value=good),patch.object(c,"load_trade_calendar",side_effect=OSError("calendar unavailable")):
  x=r.resolve_product(pid,None,None,curr)
 out["calendar_failure_without_window"]={"mode":x["coverage_mode"],"coverage_ready":x["coverage_ready"],"historical_ready":x["historical_ready"],"coverage_error":curr.get("_coverage_error")}
print(json.dumps(out,ensure_ascii=False,indent=2))
