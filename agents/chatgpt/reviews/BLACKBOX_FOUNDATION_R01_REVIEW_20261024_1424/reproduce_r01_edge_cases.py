import ast, json, os, re, sys
from datetime import date, datetime
from typing import Any, Optional, Sequence, Dict
from types import SimpleNamespace
source = open(sys.argv[1], encoding="utf-8").read()
tree = ast.parse(source)
helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {"_d", "_ymd"}]
original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LocalPlaneProvider")
methods = [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in {"_select_files", "_dedupe_versions", "get_split_dividend"}]
probe_class = ast.ClassDef(name="Probe", bases=[], keywords=[], body=methods, decorator_list=[])
module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *helpers, probe_class], type_ignores=[])
ast.fix_missing_locations(module)
ns = dict(globals(), STATUS_OK="OK", STATUS_PARTIAL="PARTIAL", STATUS_REJECTED="REJECTED")
exec(compile(module, "exact_R01_method_probe", "exec"), ns)
p = ns["Probe"]()
picked = p._select_files(["/fixture/bars__2014__20260612_090000.parquet"], date(2026,6,1), date(2026,6,30))
class Rows:
    num_rows = 1
    column_names = ["code", "a_xr_date"]
    def column(self, name): return ["000001.XSHE"]
    def filter(self, mask): return self
    def to_pylist(self): return [{"code":"000001.XSHE", "a_xr_date":"2026-07-01"}]
ns["pa"] = SimpleNamespace(array=lambda value: value)
ns["pc"] = SimpleNamespace(is_in=lambda *a, **kw: True)
p._plane = lambda name: {"root":"/fixture", "layer":"RAW"}
p._glob_parquet = lambda root: ["/fixture/events__2026.parquet"]
p._read = lambda files: Rows()
p.max_rows = 100
event = p.get_split_dividend("000001.XSHE", "2026-01-01", "2026-09-30", asof="2026-06-01")
result = {
 "scope":"Exact R01 methods in an isolated standard-library harness; source discovery and Arrow row filtering are stubbed. No Windows, real dataset, network or engine execution.",
 "build_timestamp_misused_as_coverage":{"coverage_year":2014,"build_timestamp":"20260612_090000","requested_year":2026,"selected":bool(picked),"files":picked},
 "unknown_announcement_admitted":{"asof":"2026-06-01","announcement_fields_present":False,"status":event["status"],"returned_rows":event["row_count"],"knowable_at":event["data"][0]["knowable_at"]}
}
assert result["build_timestamp_misused_as_coverage"]["selected"]
assert result["unknown_announcement_admitted"]["status"] == "OK"
print(json.dumps(result, indent=2))

