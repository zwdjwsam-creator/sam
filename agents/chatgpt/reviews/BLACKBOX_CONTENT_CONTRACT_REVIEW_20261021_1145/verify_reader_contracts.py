"""Isolated behavioral probes of uploaded original function bodies.

AST allowlist only: no original imports/main, no production paths or parquet I/O.
Fake Arrow Table supports pandas-backed contract probes, NOT a real Arrow test.
"""
from __future__ import annotations
import ast
import hashlib
import json
import re
import tempfile
from collections import defaultdict
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import pandas as pd

HERE = Path(__file__).resolve().parent
SOURCES = {
    'unified': ('blackbox_unified_market_data_plane_r1.py', '6826c1cf7c0e2d227f6e639f88897bd896bc380fb323ec5a1d9ccd400aefd9ce'),
    'etf': ('blackbox_etf_minute_1m_plane_r1.py', 'cadddb88549b36ee971fd5463d90a71cf40f90d35969bed15ccb6745f14ab316'),
}

class Table:
    def __init__(self, df): self.df = df.copy()
    @property
    def num_rows(self): return len(self.df)
    @property
    def column_names(self): return list(self.df.columns)
    def to_pandas(self): return self.df.copy()
    @staticmethod
    def from_pandas(df, preserve_index=False): return Table(df.reset_index(drop=True))

class FakeArrow:
    Table = Table
    @staticmethod
    def string(): return str
    @staticmethod
    def array(values, type=None): return list(values)
    @staticmethod
    def table(columns): return Table(pd.DataFrame(columns))
    @staticmethod
    def concat_tables(tables, promote_options=None):
        return Table(pd.concat([t.df for t in tables], ignore_index=True))

def load_functions(key, names):
    filename, expected = SOURCES[key]
    path = HERE / filename
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    tree = ast.parse(path.read_bytes().decode('utf-8'), filename=filename)
    body = [ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)]
    body += [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    assert {n.name for n in body if isinstance(n, ast.FunctionDef)} == set(names)
    module = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    env = dict(globals(), pa=FakeArrow, CN_TZ=timezone(timedelta(hours=8)))
    exec(compile(module, str(path), 'exec'), env)
    return env

def main():
    u = load_functions('unified', [
        '_load_json', 'normalize_product_id', '_daterange', '_scan_cleaning_dir',
        '_scan_raw_year_envelope', 'resolve_product', '_date_in_envelope',
        'classify_date', 'coverage_window', 'list_files_for_window',
    ])
    e = load_functions('etf', [
        'load_json', 'classify_name', 'parse_range', 'code_in_range', 'code_matches_daily',
        'envelope_from_name', 'sidecar_envelope', 'window_overlap', 'scan_root',
        'overlapping_shards', 'read_overlapping', 'dedupe_canonical', 'anti_lookahead_test',
    ])
    e.update(DAY_RE=re.compile(r'__1m__(?P<date>\d{4}-\d{2}-\d{2})__'),
             YEAR_RE=re.compile(r'__(?P<year>\d{4})__1m__'),
             RANGE_RE=re.compile(r'fund_etf_price_1m__(?P<a>\d{6}\.[A-Z]+)_(?P<b>\d{6}\.[A-Z]+)'),
             EX_RE=re.compile(r'__(XSHE|XSHG)__'))
    results = []
    def check(name, actual, expected, meaning):
        assert actual == expected, (name, actual, expected)
        results.append(dict(name=name, actual=actual, expected=expected, assertion_pass=True, interpretation=meaning))
    with tempfile.TemporaryDirectory(prefix='blackbox_contract_fixture_') as tmp:
        root = Path(tmp); raw = root/'raw'; raw.mkdir(); clean = root/'standard'/'price'/'ETF_1m'; clean.mkdir(parents=True)
        u['ROOT'] = root; e['RAW_1M'] = raw
        registry = {'pointers': {'raw_root': 'raw'}, 'products': {'ETF_MINUTE_1M_R1': {
            'asset':'ETF','freq':'1m','planes': {
                'CLEANING_CURRENT': {'relative_under_standard':'price/ETF_1m', 'day_name_regex':r'__1m__(?P<date>\d{4}-\d{2}-\d{2})__', 'year_batch_regex':r'__(?P<year>\d{4})__1m__'},
                'RAW_REPLACEMENT': {'relative_under_raw_root':'.', 'year_batch_glob':'*__{year}__*.parquet'},
            }}}}
        u['load_cleaning_pointer'] = lambda: {'standard_root':str(root/'standard'), 'release_id':'fixture_clean'}
        raw_file = raw/'fund_etf_price_1m__510000.XSHG_519999.XSHG__2026__1m__fixture.parquet'
        raw_file.write_bytes(b'NOT_PARQUET_SYNTHETIC_PLACEHOLDER')
        side = Path(str(raw_file)+'.sidecar.json'); side.write_text('{}')
        env = u['_scan_raw_year_envelope'](raw,'2026','*__{year}__*.parquet','start_date','end_date')
        check('undated_sidecar_widens_full_year', [env['start_min'],env['end_max']], ['2026-01-01','2026-12-31'], 'Metadata envelope only; no parquet content was read')
        cov = u['coverage_window']('ETF_MINUTE_1M_R1','2026-01-05','2026-01-05',registry)
        check('empty_sidecar_can_declare_data_plane_ready', [cov['n_present'],cov['DATA_PLANE_READY']], [1,'YES'], 'PRESENT/YES is not actual row/calendar/symbol completeness')
        side.write_text('{malformed')
        bad = u['_scan_raw_year_envelope'](raw,'2026','*__{year}__*.parquet','start_date','end_date')
        check('malformed_sidecar_still_widens', [bad['n_sidecars'],bad['start_min'],bad['end_max']], [1,'2026-01-01','2026-12-31'], 'Counter increments before parse; malformed metadata can become broad declaration')
        old = clean/'fund_etf_price_1m__510000.XSHG_519999.XSHG__2025__1m__fixture.parquet'; old.touch()
        resolved = u['resolve_product']('ETF_MINUTE_1M_R1',registry)
        check('cleaning_year_prevents_discovery_other_raw_year', sorted(resolved['planes']['P2_RAW_REPLACEMENT']['year_envelope']), ['2025'], 'RAW 2026 is not discovered when a CLEANING 2025 year batch exists')
        old.unlink()
        mat = clean.with_name(clean.name+'.__mat_fixture'); mat.mkdir()
        (mat/'fund_etf_price_1m__510000.XSHG_519999.XSHG__2025__1m__fixture.parquet').touch()
        tip_name='fund_etf_price_1m__XSHG__1m__2026-09-24__fixture.parquet'
        (clean/tip_name).touch()
        scanned = e['scan_root'](clean,'fixture_clean')
        check('current_scan_excludes_sibling_materialization', [s['file_name'] for s in scanned], [tip_name], 'Exact root glob does not traverse sibling .__mat directories')
        def shard(path, generation, a, b, kind, name):
            return {'path':path,'source_generation':generation,'date_min':a,'date_max':b,'shard_type':kind,'file_name':name,'sidecar_codes':['510300.XSHG']}
        tip = shard('fixture_tip','fixture_clean','2026-09-24','2026-09-24','DAILY_SLICE',tip_name)
        hist = shard('fixture_raw','P4_fund_etf_raw_none/fund_etf_price_1m','2026-01-01','2026-12-31','YEAR_BATCH',raw_file.name)
        manifest={'shards':[tip,hist]}
        select = lambda a,b,plane='CLEANING': e['overlapping_shards'](manifest,a,b,['510300.XSHG'],plane=plane,cleaning_release_id='fixture_clean')
        check('cleaning_selection_tip_only',[s['path'] for s in select('2026-09-24','2026-09-24')],['fixture_tip'],'CLEANING selector accepts TIP')
        check('cleaning_selection_history_empty',[s['path'] for s in select('2026-09-23','2026-09-23')],[],'RAW candidate is present but CLEANING selector excludes it')
        check('raw_selection_history_explicit_only',[s['path'] for s in select('2026-09-23','2026-09-23','RAW')],['fixture_raw'],'Explicit RAW selection differs from default reader path')
        calls=[]
        def fake_read(path):
            calls.append(str(path)); return Table(pd.DataFrame({'security_code':['510300.XSHG'],'datetime':[pd.Timestamp('2026-09-24 15:00')],'trade_date':['2026-09-24'],'open':[1.0],'high':[1.0],'low':[1.0],'close':[1.0],'volume':[1.0],'amount':[1.0]}))
        e['_read_table']=fake_read
        e['normalize_table']=lambda table,path: table
        def fake_filter(table,symbols,start,end):
            df=table.to_pandas(); return Table(df[df.security_code.isin(symbols)&df.trade_date.between(start,end)])
        e['filter_request']=fake_filter
        body=e['read_overlapping'](['510300.XSHG'],'2026-09-23','2026-09-24',manifest=manifest,cleaning_release_id='fixture_clean')
        check('default_reader_does_not_fallback_raw',calls,['fixture_tip'],'Original read_overlapping body uses CLEANING only; read/normalization/filter were fake test adapters')
        check('partial_window_can_have_dedupe_pass',[body['ROWS_AFTER_DEDUPE'],body['DEDUPE_QA']],[1,'PASS'],'DEDUPE_QA is not coverage acceptance; one date is absent')
        df=fake_read(Path('synthetic')).to_pandas(); other=df.copy();other['close']=2.0
        dd=e['dedupe_canonical'](Table(pd.concat([df,other],ignore_index=True)))
        check('conflicting_key_is_removed_not_priority_selected',[dd['conflicts'],dd['after']],[1,0],'Original dedupe detects conflict and removes conflicting key; no day/year precedence is applied here')
        nat=Table(pd.DataFrame({'datetime':[pd.Timestamp('2026-09-24 15:00')],'bar_available_at':[pd.NaT]}))
        look=e['anti_lookahead_test'](nat)
        check('anti_lookahead_nan_availability_passes',look['status'],'PASS','Existing test does not reject NaT and has no request_time argument; PASS cannot prove no lookahead')
    report={'schema':1,'source_sha256':{k:v[1] for k,v in SOURCES.items()},'n_probes':len(results),'all_assertions_pass':True,'probes':results,'scope':'Original AST-allowlisted function bodies; synthetic files and pandas-backed FakeArrow; production/real parquet/real Arrow NOT_RUN. Passing assertions reproduce observed behavior, NOT production readiness.','system_inventory_acceptance':False}
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
