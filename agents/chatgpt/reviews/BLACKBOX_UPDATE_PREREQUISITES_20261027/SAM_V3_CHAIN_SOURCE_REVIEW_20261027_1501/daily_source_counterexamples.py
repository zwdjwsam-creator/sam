"""Reviewer AST-only Linux checks, no supplier, originals or Parquet execution."""
import ast
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import pandas as pd

source = Path(__file__).parent / 'sam/chain_source_001/bodies/0001_download_daily_r1.py'
tree = ast.parse(source.read_text())
selected = [n for n in tree.body if isinstance(n, ast.FunctionDef)
            and n.name in {'normalize_price_df', 'download_universe_daily', 'save_unit'}]
assert len(selected) == 3
namespace = {'pd': pd, 'Path': Path, 'GAP_START': '2026-09-24', 'GAP_END': '2026-09-24',
             'FIELDS_CORE': ['open','high','low','close','volume','money','paused','high_limit','low_limit','avg','pre_close','factor'],
             'log': lambda *x: None, 'time': type('NoSleep', (), {'sleep': lambda *x: None})(),
             'ts_stamp': lambda: 'fixture', 'now_iso': lambda: 'fixture',
             'sha256_file': lambda p: 'PARQUET_BYTES_NOT_EXERCISED', 'wjson': lambda *x: None}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), 'exec'), namespace)
ordinal = namespace['normalize_price_df'](pd.DataFrame({'time':[0], 'code':['A'], 'close':[1]}))
class FakeSupplier:
    def get_price(self, *args, **kwargs):
        return pd.DataFrame({'time':['2026-09-23'], 'code':['OTHER'], 'close':[1]})
frame = namespace['download_universe_daily'](FakeSupplier(), ['REQUESTED'])
units = []
with tempfile.TemporaryDirectory() as tmp, patch.object(pd.DataFrame, 'to_parquet', return_value=None):
    row = namespace['save_unit'](domain='stock_ohlcv_daily', df=frame,
            raw_path=Path(tmp)/'fixture.parquet', clean_rel='fixture', units=units)
print(json.dumps({'scope':'ISOLATED_AST_PANDAS_NO_SUPPLIER_NO_PARQUET',
    'ordinal_date_accepted_as':str(ordinal['time'].iloc[0]),
    'requested_codes':['REQUESTED'], 'returned_codes':list(frame['code']),
    'requested_date':'2026-09-24', 'returned_date':str(frame['time'].iloc[0]),
    'save_status_on_wrong_keys_and_date':row['status']},indent=2))
