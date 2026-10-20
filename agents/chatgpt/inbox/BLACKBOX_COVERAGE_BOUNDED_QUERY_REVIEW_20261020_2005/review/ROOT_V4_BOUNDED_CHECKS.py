import json,tempfile
from pathlib import Path
from datetime import date
from unittest.mock import patch
import pandas as pd
import blackbox_data_coverage_common_r1 as c
import blackbox_data_access_resolver_r1 as r
import blackbox_cache_coverage_non_regression_gate_r1 as g
checks={}
cov={"exists":True,"coverage_extract_status":"OK","errors":[],"dates":["2026-09-01","2026-09-02"],"distinct_dates":2,"min_date":"2026-09-01","max_date":"2026-09-02","year_slices":["year=2026"],"supported_product":True}
with patch.object(c,"load_trade_calendar",return_value=[date(2026,9,1),date(2026,9,2)]):
 checks["two_days_not_full"]=c.infer_mode_for_product("STOCK_DAILY_PIT_R1",dict(cov))!="FULL_HISTORY"
checks["all_existing_self_tests"]=all(v["PASS"] for v in g.self_test().values())
with tempfile.TemporaryDirectory() as td:
 root=Path(td); pid="STOCK_DAILY_PIT_R1";(root/pid).mkdir()
 def currents(start=None,end=None):
  x={"catalog":pd.DataFrame([{"product_id":pid,"asset_type":"STOCK"}]),"cache_release_root":str(root)}
  if start:x["_request_start_date"]=start
  if end:x["_request_end_date"]=end
  return x
 def resolve(cov0,cu,calendar=None,error=None):
  with patch.object(c,"product_date_coverage",return_value=dict(cov0)),patch.object(c,"load_trade_calendar",side_effect=error,return_value=calendar or [date(2026,9,1),date(2026,9,2)]):
   return r.resolve_product(pid,None,None,cu)
 x=resolve(cov,currents("2026-09-01","2026-09-02"))
 checks["complete_bounded_ready"]=x["coverage_ready"] is True and x["coverage_scope"]=="BOUNDED_WINDOW_VERIFIED" and x["historical_ready"] is False
 x=resolve({**cov,"dates":["2026-09-02"]},currents("2026-09-01","2026-09-02"))
 checks["missing_day_blocked"]=x["coverage_ready"] is False
 x=resolve({**cov,"coverage_extract_status":"UNVERIFIABLE","errors":["bad"]},currents("2026-09-01","2026-09-02"))
 checks["partial_read_blocked"]=x["coverage_ready"] is False and x["coverage_mode"]=="UNKNOWN_STOP"
 x=resolve(cov,currents())
 checks["no_window_unproven_blocked"]=x["coverage_ready"] is False and x["historical_ready"] is False
 x=resolve(cov,currents("2026-09-01"))
 checks["single_endpoint_blocked"]=x["coverage_ready"] is False
 x=resolve(cov,currents("2026-09-01","2026-09-02"),error=OSError("calendar down"))
 checks["calendar_failure_bounded_blocked"]=x["coverage_ready"] is False
 x=resolve(cov,currents(),error=OSError("calendar down"))
 checks["calendar_failure_unbounded_not_allowed"]=x["coverage_ready"] is False
 for ds in [[],["2026-09-01"]]:
  with patch.object(g,"product_date_coverage",side_effect=[dict(cov),{**cov,"dates":ds,"distinct_dates":len(ds)}]):
   x=g.gate("p","c",[pid])
  checks["date_loss_"+str(len(ds))]=x["CACHE_RELEASE_PUBLISHABLE"] is False
 with patch.object(g,"product_date_coverage",side_effect=[dict(cov),dict(cov)]):
  x=g.gate("p","c",[pid])
 checks["retention_not_publishability"]=x["SET_RETENTION_OK"] is True and x["CACHE_RELEASE_PUBLISHABLE"] is False
print(json.dumps({"checks":checks,"all_pass":all(checks.values()),"scope":"controlled extraction/calendar inputs; real candidate logic; not Windows parquet execution"},ensure_ascii=False,indent=2))
assert all(checks.values()),checks
