"""Isolated control-flow counterexamples from pinned deployed source. No module import."""
import ast
import json
from pathlib import Path
import sys
import tempfile
import time
import types

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "bodies" / "commit_audit_20261026" / "deployed_source"
def load_function(path, name, env):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), node], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(path), "exec"), env)
    return env[name]

daily = SOURCE / "3_compiler" / "cache_compiler_daily_incremental_r1.py"
runner = SOURCE / "2_runner" / "run_connected_pipeline.py"
env={"READ_REPORT":[],"_norm":lambda p:str(p),"json":json}
closure=load_function(daily,"assert_read_closure",env)
empty=closure(product="STOCK_DAILY_PIT_R1", expected_files=[],enumerated_files=[],read_files=[],report=[])
result={"empty_required_source_accepted":empty["CLOSURE_OK"]}

old_pd=sys.modules.get("pandas")
sys.modules["pandas"]=types.ModuleType("pandas")
try:
    fn=load_function(daily,"expected_keys_from_frames",{})
    try:fn([None])
    except Exception as e:result["empty_frame_exception"]=type(e).__name__+": "+str(e)
finally:
    if old_pd is None:sys.modules.pop("pandas",None)
    else:sys.modules["pandas"]=old_pd

with tempfile.TemporaryDirectory() as td:
    root=Path(td);acc=root/"acceptance";acc.mkdir()
    external=root/"external"/"DECLARED";external.mkdir(parents=True)
    (external/"SEAL.json").write_text(json.dumps({"release_id":"DECLARED","all_pass":True}))
    (external/"RELEASE.json").write_text(json.dumps({"cache_release_id":"DECLARED"}))
    cleaning=root/"clean.json";cleaning.write_text(json.dumps({"release_id":"CLEAN"}))
    def fake_compiler(cmd, log):
        (acc/"TIP_REBASE_LAST.json").write_text(json.dumps({"pointer":{
            "cache_release_id":"DECLARED","release_root":str(external),"asof":"2026-09-24",
            "source_cleaning_release":"CLEAN"},"seal":{"all_pass":True}}))
        return {"exit_code":0}
    class Stop(Exception):
        def __init__(self,*args):super().__init__(*args)
    env={"Path":Path,"json":json,"os":__import__("os"),"time":time,
         "PY":sys.executable,"TASK":root,"SEALED_PARENT":root/"parent",
         "RUN_LOG_DIR":root/"logs","ASOF":"2026-09-24","run":fake_compiler,"PipelineStop":Stop}
    fn=load_function(runner,"compile_release",env)
    actual=fn(cleaning,root/"authorized"/"releases",acc,root/"no_receipt.json")
    result["outside_declared_root_accepted"]=actual["bound_release_root"]==str(external)
assert result["empty_required_source_accepted"] is True
assert result["empty_frame_exception"].startswith("NameError")
assert result["outside_declared_root_accepted"] is True
result["scope"]="Extracted source control flow; metadata stubs; no Parquet, supplier, NTFS or actual compiler execution."
print(json.dumps(result,indent=2))

