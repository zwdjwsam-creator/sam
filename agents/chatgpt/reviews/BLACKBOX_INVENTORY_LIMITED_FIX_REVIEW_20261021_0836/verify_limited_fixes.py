import ast, hashlib, json, ntpath, re
from pathlib import Path, PureWindowsPath
root = Path(__file__).resolve().parent
expected = {
"resolve_product_authority_v2_0815.py":"8b66cc1090c79bd352b8acbb6f94aee47301cd27004e5de5082bc0096c406bc7",
"run_inventory_authority_0815_worker.py":"4b1116745b85eefe0bc01d2cad3fd41eddc5035360c553768970f35c534e9616",
"run_inventory_authority_fix_0815b.py":"d70041fd547c21b3dd378b8bba102e0016a9c07f2f3b51d356d0ee5404b96210",
"run_inventory_resume_0730_worker.py":"93b50152c367072978d86b20081d7ded4dae1df088c4d37861b37e09ec1320b5",
}
hashes={}
for name,want in expected.items():
    digest=hashlib.sha256((root/name).read_bytes()).hexdigest()
    assert digest==want,(name,digest)
    hashes[name]=digest
std=r"E:\fixture\standard"
paths={asset+freq:std+"\\price\\"+(asset+"_"+freq) for asset in ["ETF","stock"] for freq in ["1m","5m"]}
existing={std,*paths.values(),r"E:\BLACKBOX\.cursor\rules\gate.mdc"}
patterns={
"**/ETF_1m":[paths["ETF1m"]],"**/ETF_5m":[paths["ETF5m"]],
"**/stock_1m":[paths["stock1m"]],"**/stock_5m":[paths["stock5m"]],
}
class FakePath(PureWindowsPath):
    def exists(self): return str(self) in existing
    def glob(self,pattern): return iter(FakePath(p) for p in patterns.get(pattern,[]) if p in existing)
    def resolve(self): return FakePath(ntpath.normpath(str(self)))
tree=ast.parse((root/"resolve_product_authority_v2_0815.py").read_text())
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name!="regression_fixture"]
ns={"Path":FakePath,"re":re}
exec(compile(ast.Module(body=functions,type_ignores=[]),"<isolated-v2>","exec"),ns)
rows=[]
for pid,target in [("ETF_MINUTE_1M_R1",paths["ETF1m"]),("ETF_MINUTE_5M_R1",paths["ETF5m"]),("STOCK_MINUTE_1M_R1",paths["stock1m"]),("STOCK_MINUTE_5M_R1",paths["stock5m"])]:
    row=ns["resolve_product_authority_v2"](pid,{"release_root":r"E:\cache"},{"standard_root":std},{},{},{})
    assert row["authority_path"]==target,row
    rows.append({"product":pid,"selected":row["authority_path"],"pass":True})
existing.remove(paths["ETF1m"])
row=ns["resolve_product_authority_v2"]("ETF_MINUTE_1M_R1",{"release_root":r"E:\cache"},{"standard_root":std},{},{},{})
assert row["status"]=="UNKNOWN" and not row["exists"]
rows.append({"product":"ETF_MINUTE_1M_R1","fixture":"ETF missing; stock present","status":row["status"],"pass":True})
tree=ast.parse((root/"run_inventory_resume_0730_worker.py").read_text())
selected=[]
for n in tree.body:
    if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {"PLACEHOLDER_RE","FORMULA_RE","RULE_ID_RE"} for t in n.targets): selected.append(n)
    if isinstance(n,ast.FunctionDef) and n.name=="classify_token_v5": selected.append(n)
ns={"Path":FakePath,"ROOT":FakePath(r"E:\BLACKBOX"),"re":re}
exec(compile(ast.Module(body=selected,type_ignores=[]),"<isolated-v5>","exec"),ns)
cases=[]
for token,src,want in [
("../脚本/foo.py",r"E:\BLACKBOX\任务\x.md",r"E:\BLACKBOX\脚本\foo.py"),
("cursor/rules/gate.mdc",r"E:\BLACKBOX\AGENTS.md",r"E:\BLACKBOX\cursor\rules\gate.mdc"),
(".cursor/rules/gate.mdc",r"E:\BLACKBOX\AGENTS.md",r"E:\BLACKBOX\.cursor\rules\gate.mdc")]:
    row=ns["classify_token_v5"](token,FakePath(src),1,"md_link")[0]
    assert row["resolved"]==want,row
    if token.startswith(".cursor"): assert row["edge_status"]=="RESOLVED"
    else: assert row["edge_status"]=="BROKEN_CONFIRMED"
    cases.append({"token":token,"target":row["resolved"],"status":row["edge_status"],"pass":True})
result={"source_hashes":hashes,"isolated_asset_checks":rows,"isolated_path_checks":cases,"result":"LIMITED_FIXES_REPRODUCED_SUCCESSFULLY","limits":["No production Windows paths or actual data read","No acceptance of full rule graph, coverage completeness, registry overrides, or backtest readiness"],"source_review":{"0730":"Arrow batch streaming and row-aligned candidate pairing present; main ends after fragment passes, not a full-system continuous queue","0815b":"Regression/live re-resolution/reporting helper; main ends after writing checkpoint","stage_0815_continue":"Reported mapping evidence is file stat metadata, not extracted contents"}}
(root/"independent_review.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"result":result["result"],"hashes":len(hashes),"asset_cases":len(rows),"path_cases":len(cases),"production_access":False}))
