"""Execute the copied merge helper with pandas and one mocked prior parquet.
No real parquet, API, production data, or business module import is used.
This establishes duplicate precedence, not the business contract's desired policy.
"""
import ast
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import pandas as pd

here = Path(__file__).resolve().parent
tree = ast.parse((here / 'fund.py').read_text(encoding='utf-8'))
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_merge_prior_tips')
new = pd.DataFrame([{'code':'TEST', 'day':'2026-09-24', 'unit_net_value':2.0}])
old = pd.DataFrame([{'code':'TEST', 'day':'2026-09-24', 'unit_net_value':1.0}])
proxy = SimpleNamespace(DataFrame=pd.DataFrame, concat=pd.concat, to_datetime=pd.to_datetime,
                        read_parquet=lambda path: old.copy())
ns = {'pd':proxy, 'Path':Path}
exec(compile(ast.Module(body=[node], type_ignores=[]), 'fund.py', 'exec'), ns)
with tempfile.TemporaryDirectory(prefix='hub-nav-merge-review-') as td:
    root = Path(td)
    tip = root / 'fund' / 'ETF_NAV' / 'tip'
    tip.mkdir(parents=True)
    (tip / 'old.parquet').touch()
    result = ns['_merge_prior_tips'](new, root)
    observed = float(result.iloc[0]['unit_net_value'])
    assert observed == 1.0
report = {'production_executed':False, 'helper_executed':'_merge_prior_tips',
    'new_value':2.0, 'old_tip_value':1.0, 'observed_value':observed,
    'finding':'Prior tip overrides new input on a duplicate (code,day) key.',
    'limit':'Confirms precedence only; historical production corruption and intended revision policy not tested.'}
(here / 'NAV_RESULTS.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
