import importlib.util, json, sys, types
from unittest.mock import patch
spec=importlib.util.spec_from_file_location("entry","query_stock_daily_bounded_r1.py")
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
checks={}
def snap(sha="same",ready=True):
 return {"authority_ready":ready,"cache_release_id":"release","cache_release_root":"root","cache_asof":"2026-09-24","pointer_sha256":sha,"errors":[],"currents":{}}
read={"row_count":1,"rows":[{"date":"2026-09-02","code":"000001.XSHE","known_at":None}],"dates":["2026-09-02"],"projected_columns":["date","code"],"filter_expression":"code+date","date_column_type":"timestamp[ns]","query_elapsed_ms":1,"materialization":"filtered","files_used":[]}
res=types.SimpleNamespace(resolve_product=lambda *a:{"coverage_ready":True,"coverage_scope":"BOUNDED_WINDOW_VERIFIED","product_path":"fixture","full_history_status":"UNPROVEN"})
common=types.SimpleNamespace(set_expected_range_authority=lambda *a:None)
meta={"modules":{"resolver":res,"common":common},"interpreter":"controlled"}
def call(argv,snaps):
 capture=[]
 with patch.object(sys,"argv",["entry"]+argv),patch.object(e,"_configure_stdio_utf8"),patch.object(e,"_verify_runtime",return_value=meta),patch.object(e,"_snapshot_current",side_effect=snaps),patch.object(e,"_read_rows",return_value=read) as reader,patch.object(e,"_emit",side_effect=lambda body,rc:(capture.append((body,rc)) or rc)):
  rc=e.main()
 return rc,capture[-1][0],reader.call_count
argv=["--code","000001.XSHE","--start-date","2026-09-02","--end-date","2026-09-10"]
rc,b,n=call(argv,[snap(),snap(),snap("changed")])
checks["actual_main_post_read_change_rejects"]=rc==2 and b["error"]=="CURRENT_CHANGED_DURING_ROW_READ" and n==1
rc,b,n=call(argv,[snap(),snap(),snap()])
checks["unchanged_main_returns_rows"]=rc==0 and b["row_count"]==1 and n==1
rc,b,n=call(argv,[snap(),snap(),snap(ready=False)])
checks["post_read_authority_failure_rejects"]=rc==2 and b["error"]=="CURRENT_CHANGED_DURING_ROW_READ"
rc,b,n=call(["--code","x","--start-date","2026-09-10","--end-date","2026-09-02"],[])
checks["reversed_date_before_data_access"]=rc==2 and b["error"]=="END_DATE_BEFORE_START_DATE" and n==0
rc,b,n=call(["--code","x","--start-date","2026-09-02"],[])
checks["single_endpoint_before_data_access"]=rc==2 and n==0
print(json.dumps({"all_pass":all(checks.values()),"checks":checks,"scope":"entry main with controlled runtime/row inputs; not Windows Parquet reread"},indent=2))
assert all(checks.values())
