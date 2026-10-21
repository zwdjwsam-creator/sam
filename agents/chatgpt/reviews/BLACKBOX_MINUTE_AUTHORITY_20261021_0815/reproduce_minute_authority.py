"""Synthetic reproduction of inventory-only minute authority routing."""
import ast, hashlib, json, sys
from pathlib import Path, PureWindowsPath
source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("run_inventory_continue_0010_worker.py")
raw = source_path.read_bytes()
expected = "06755ff959e29063321bda5036c9dae00ee7b47938a333425da0096656d89cbe"
assert hashlib.sha256(raw).hexdigest() == expected
standard = r"E:\synthetic_clean\standard"
stock1 = standard + r"\finance\A股_stock_1m"
etf1 = standard + r"\finance\ETF_1m"
stock5 = standard + r"\finance\A股_stock_5m"
etf5 = standard + r"\finance\ETF_5m"
existing = {standard, stock1, etf1, stock5, etf5}
by_pattern = {
    "**/A股_stock_1m": [stock1], "**/ETF_1m": [etf1],
    "**/A股_stock_5m": [stock5], "**/ETF_5m": [etf5],
}
class FakePath(PureWindowsPath):
    def exists(self): return str(self) in existing
    def glob(self, pattern): return iter(FakePath(p) for p in by_pattern.get(pattern, []))
fn = next(n for n in ast.parse(raw.decode("utf-8")).body if isinstance(n, ast.FunctionDef) and n.name == "resolve_product_authority")
ns = {"Path": FakePath, "ROOT": FakePath(r"E:\BLACKBOX")}
exec(compile(ast.Module(body=[fn], type_ignores=[]), "<isolated-inventory-resolver>", "exec"), ns)
resolve = ns["resolve_product_authority"]
rows = []
for product, expected_path in [
    ("ETF_MINUTE_1M_R1", etf1), ("ETF_MINUTE_5M_R1", etf5),
    ("STOCK_MINUTE_1M_R1", stock1), ("STOCK_MINUTE_5M_R1", stock5),
]:
    row = resolve(product, {"release_root": r"E:\synthetic_cache"}, {"standard_root": standard}, {}, {}, {})
    rows.append({"product_id": product, "selected": row["authority_path"], "intended_fixture_target": expected_path, "matches_fixture_target": row["authority_path"] == expected_path})
assert rows[0]["selected"] == rows[2]["selected"] == stock1
assert rows[1]["selected"] == rows[3]["selected"] == stock5
assert [r["matches_fixture_target"] for r in rows] == [False, False, True, True]
result = {
    "result": "INVENTORY_ROUTER_SELECTS_STOCK_FOR_ETF_WHILE_BOTH_ASSET_DIRECTORIES_EXIST",
    "source_sha256": expected, "fixture_rows": rows,
    "production_access": False,
    "limits": "Confirms a bug in the uploaded inventory helper only; does not establish the actual instruments held in production files or a defect in the accepted bounded query runtime.",
}
print(json.dumps(result, ensure_ascii=False, indent=2))
