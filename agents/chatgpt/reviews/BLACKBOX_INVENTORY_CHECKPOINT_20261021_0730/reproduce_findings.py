"""Independent, isolated reproductions; does not access Windows business paths."""
import ast
import hashlib
import json
import re
import sys
import types
from pathlib import Path, PureWindowsPath

BASE = Path(__file__).resolve().parent
results = {}
manifest = {
    "run_inventory_correction_0650_worker.py": "e20bfac7dc79006e62674b1bb4298476c6027f71913acc3507cfee9e49740f56",
    "run_inventory_continue_0010_worker.py": "06755ff959e29063321bda5036c9dae00ee7b47938a333425da0096656d89cbe",
    "run_inventory_advance_0712_checkpoint.py": "baae7c3010e288eeab93f1de469519bb85f0ebaa1cd28977d6c81213315bc459",
}
results["source_sha256_exact_bytes"] = {}
for name, expected in manifest.items():
    raw = (BASE / name).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    assert actual == expected, (name, actual, expected)
    results["source_sha256_exact_bytes"][name] = actual

source = (BASE / "run_inventory_correction_0650_worker.py").read_text()
tree = ast.parse(source)
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "classify_token_v4")
existing = {r"E:\BLACKBOX\.cursor\rules\gate.mdc"}

class FakeWinPath(PureWindowsPath):
    def exists(self):
        return str(self) in existing

ns = {
    "re": re, "Path": FakeWinPath, "ROOT": FakeWinPath(r"E:\BLACKBOX"),
    "PLACEHOLDER_RE": re.compile(r"<[^>]+>|\{[^}]+\}|YYYYMMDD|<asof>|YOUR_|TODO_|FIXME_|%\([^)]+\)s"),
    "RULE_ID_RE": re.compile(r"^[A-Z][A-Z0-9_]{2,}$"),
    "FORMULA_RE": re.compile(r"(<=|>=|==|!=|<|>)|KNOWN_AT|SIGNAL_TIME|FILL_TIME"),
}
exec(compile(ast.Module(body=[function], type_ignores=[]), "<isolated-classifier>", "exec"), ns)
classify = ns["classify_token_v4"]
src = FakeWinPath(r"E:\BLACKBOX\契约\x.md")
relative = classify("../脚本/foo.py", src, 1, "md_link")[0]
correct = str(FakeWinPath(r"E:\BLACKBOX\脚本\foo.py"))
assert relative["resolved"] != correct, relative
results["relative_dotdot_wrong_resolution"] = {"original": "../脚本/foo.py", "observed": relative, "correct_normalized_target": correct}
dot = classify(".cursor/rules/gate.mdc", FakeWinPath(r"E:\BLACKBOX\AGENTS.md"), 1, "md_link")[0]
no_dot = classify("cursor/rules/gate.mdc", FakeWinPath(r"E:\BLACKBOX\AGENTS.md"), 1, "md_link")[0]
assert dot["edge_status"] == no_dot["edge_status"] == "RESOLVED"
assert dot["resolved"] == no_dot["resolved"]
results["missing_dot_silently_repaired_as_resolved"] = {"actual_dot_token": dot, "distinct_no_dot_token": no_dot}

advanced = (BASE / "run_inventory_advance_0712_checkpoint.py").read_text()
advanced_tree = ast.parse(advanced)
nav_function = next(n for n in advanced_tree.body if isinstance(n, ast.FunctionDef) and n.name == "fund_nav_all_years")
seen_files = []
dataset_stub = types.ModuleType("pyarrow.dataset")
def dataset(files, **kwargs):
    seen_files.extend(files)
    return types.SimpleNamespace(schema=[types.SimpleNamespace(name=n) for n in ["day", "code", "unit_net_value", "acc_net_value"]])
dataset_stub.dataset = dataset
arrow_stub = types.ModuleType("pyarrow")
arrow_stub.__path__ = []
arrow_stub.dataset = dataset_stub
old_modules = {n: sys.modules.get(n) for n in ["pyarrow", "pyarrow.dataset"]}
sys.modules.update({"pyarrow": arrow_stub, "pyarrow.dataset": dataset_stub})
class FakeProduct:
    def rglob(self, pattern):
        return iter([
            PureWindowsPath(r"E:\product\000001\2014.parquet"),
            PureWindowsPath(r"E:\product\000001\2026.parquet"),
        ])
try:
    nav_ns = {"re": re, "Path": Path}
    exec(compile(ast.Module(body=[nav_function], type_ignores=[]), "<isolated-fund-nav>", "exec"), nav_ns)
    nav = nav_ns["fund_nav_all_years"](FakeProduct())
finally:
    for name, previous in old_modules.items():
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
assert nav["error"] == "NO_DATE_COL" and "day" in nav["columns"]
assert len(seen_files) == 1 and nav["years_read"] == ["NA"]
results["fund_nav_day_and_partition_failures"] = {"fragments_supplied": 2, "fragments_selected": seen_files, "observed": nav}

rows = [("A", None), ("B", "2026-01-02"), ("B", "2026-01-02")]
codes = [code for code, date in rows if code is not None]
dates = [date for code, date in rows if date is not None]
observed_pairs = list(zip(codes, dates[:len(codes)]))
correct_pairs = [(code, date) for code, date in rows if code is not None and date is not None]
assert len(observed_pairs) - len(set(observed_pairs)) == 0
assert len(correct_pairs) - len(set(correct_pairs)) == 1
results["null_filtered_columns_break_row_alignment"] = {
    "rows": rows, "observed_pairs": observed_pairs, "correct_pairs": correct_pairs,
    "observed_duplicates": 0, "correct_duplicates": 1,
}
results["control_flow_findings"] = {
    "0712_main_hardcodes_wait": all(s in advanced for s in ["_hub_WAIT_ACCEPTANCE.json", '"overall": "WAITING_HUB_ACCEPTANCE"']),
    "0650_main_has_no_continuation_while": not any(isinstance(n, ast.While) for n in ast.walk(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"))),
    "evidence_limit": "No production data, Windows process state, or business completeness checked here.",
}
assert results["control_flow_findings"]["0712_main_hardcodes_wait"]
assert results["control_flow_findings"]["0650_main_has_no_continuation_while"]
results["result"] = "FIVE_FAILURE_MODES_REPRODUCED_FROM_UPLOADED_SOURCE"
(BASE / "independent_reproduction.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"result": results["result"], "source_hashes": "3/3 exact GitHub byte hashes match", "production_access": False}, ensure_ascii=False))

