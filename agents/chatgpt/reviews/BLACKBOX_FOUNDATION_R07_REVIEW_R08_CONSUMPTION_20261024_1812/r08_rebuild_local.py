"""GPT-owned R08 candidate repair. Preserve price rows, never fabricate prices.

All-null OHLCV rows are retained as explicitly unobserved factor rows. Original
functions run on observed segments only; an internal all-null run resets rolling
and EMA state. This does not infer listing, delisting, suspension, or source loss.
No imports of production compiler top-level code and no supplier calls.
"""
import argparse
import copy
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from r06_bundle_store import digest, write_json, resolve_cache
from r07_rebuild_local import functions, frame, COMPILER_SHA, PRICE_COLUMNS
from r08_coverage_gate import require, normalize_dates, keys, compare, diagnose_observed_layers

WORK = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
GEN = 'R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024'
CALENDAR = Path(r'E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P0_meta\calendar_cn_exchange\calendar_cn_exchange_v2_asof_20260924\CALENDAR_TRADE_DAYS.parquet')
CALENDAR_PREFIX = 'd044d628279d48c1'
OHLCVM = ['open','high','low','close','volume','money']
FORMULA = 'univ_factor_r1_v1.R08_OBSERVED_SEGMENTS'
TARGETS = {pd.Timestamp('2026-08-31'), pd.Timestamp('2026-09-01')}
RAW_TWO_DAY_HASHES = {
    '2026-08-31':'553bad1973f6834506989b15a8298746bc07490534834cde25790b957720b063',
    '2026-09-01':'25e695dd9de457b24cd0d087064d5d68709908c72a53d8c49ca477d818d4ded7'}


def diagnose_two_days(parent, raw_hashes=RAW_TWO_DAY_HASHES):
    raw_frames, clean_frames = [], []
    for day, sha in raw_hashes.items():
        raw_paths = [p for p,h in parent['source_pins'].items() if h==sha]
        clean_paths = [a['path'] for a in parent['artifacts'] if a['sha256']==sha]
        require(len(raw_paths)==len(clean_paths)==1, 'TWO_DAY_SOURCE_NOT_UNIQUE')
        for path, dest in ((raw_paths[0],raw_frames),(clean_paths[0],clean_frames)):
            require(digest(path)==sha, 'TWO_DAY_SOURCE_CHANGED')
            data=frame(path,['time','code','close']).rename(columns={'time':'date'})
            data['date']=normalize_dates(data['date'])
            require(set(data['date'])=={pd.Timestamp(day)}, 'TWO_DAY_DATE_MISMATCH')
            dest.append(data)
    raw=pd.concat(raw_frames,ignore_index=True)
    clean=pd.concat(clean_frames,ignore_index=True)
    expected=raw[['date','code']]
    result={}
    for product in ('STOCK_DAILY_PIT_R1','STOCK_DAILY_RAW_PIT_R1'):
        path=resolve_cache(parent,product,'year=2026/part_2026.parquet')
        child=frame(path,['date','code','close'])
        child=child[pd.to_datetime(child['date']).isin(TARGETS)].copy()
        published=frame(Path(parent['parent_cache_root'])/product/'year=2026'/'part_2026.parquet',['date','code','close'])
        published=published[pd.to_datetime(published['date']).isin(TARGETS)].copy()
        for actual in (clean,child):
            pd.testing.assert_frame_equal(raw.sort_values(['date','code']).reset_index(drop=True),
                                          actual.sort_values(['date','code']).reset_index(drop=True),check_dtype=False)
        result[product]={
            'published':diagnose_observed_layers({'RAW':raw,'CLEAN':clean,'CACHE':published,'READER':published},expected),
            'candidate':diagnose_observed_layers({'RAW':raw,'CLEAN':clean,'CACHE':child,'READER':child},expected),
            'reader':'R08 explicit candidate Arrow date/code/close read; NOT engine/Master admission',
            'all_two_day_close_values_equal_raw':True}
    return result


def observed_recompute(panel, compute, structure):
    data = panel[PRICE_COLUMNS].copy()
    data['date'] = normalize_dates(data['date'])
    require(data['code'].notna().all(), 'NULL_SECURITY_CODE')
    data = data.sort_values(['code','date'], kind='mergesort').reset_index(drop=True)
    keys(data, ('date','code'))
    blank = data[OHLCVM].isna().all(axis=1)
    partial = data[OHLCVM].isna().any(axis=1) & ~blank
    require(not partial.any(), 'PARTIAL_PRICE_OBSERVATION_REQUIRES_REVIEW')
    numeric = data.loc[~blank, OHLCVM].to_numpy(dtype=float)
    require(np.isfinite(numeric).all(), 'NONFINITE_OBSERVED_PRICE')
    require((data.loc[~blank,'close'] > 0).all(), 'NONPOSITIVE_CLOSE')
    require((data.loc[~blank,['volume','money']] >= 0).all().all(), 'NEGATIVE_VOLUME_OR_MONEY')
    require((~blank).any(), 'NO_OBSERVED_PRICE')
    # A blank run interrupts the observable series. Do not bridge it or fill it.
    segment = blank.groupby(data['code'], sort=False).cumsum()
    group = pd.MultiIndex.from_arrays([data['code'],segment])
    tokens = pd.factorize(group, sort=False)[0].astype(str)
    original_codes = dict(zip(tokens, data['code']))
    observed = data.loc[~blank].copy()
    observed['code'] = tokens[~blank]
    factors = compute(observed)
    factors['code'] = factors['code'].map(original_codes)
    factors['formula_version'] = FORMULA
    factors['pit_status'] = 'OBSERVED_SEGMENT_NOT_MASTER_ADMITTED'
    empty = data.loc[blank].copy()
    for col in factors.columns:
        if col not in empty:
            empty[col] = None if factors[col].dtype == object else np.nan
    empty['formula_version'] = FORMULA
    empty['price_adj_tag'] = 'RAW_NONE'
    empty['pit_status'] = 'PRICE_UNOBSERVED_NOT_ZERO_NOT_NO_DATA'
    result = pd.concat([factors, empty[factors.columns]], ignore_index=True)
    result = result.sort_values(['code','date'], kind='mergesort').reset_index(drop=True)
    require(len(result) == len(data) and keys(data,('date','code')).difference(keys(result,('date','code'))).empty,
            'FACTOR_GRID_ROW_CONSERVATION_FAILED')
    pd.testing.assert_frame_equal(result[PRICE_COLUMNS], data[PRICE_COLUMNS], check_dtype=False)
    market = structure(observed).rename(columns={'signal_date':'date'})
    market['signal_date'] = market['date']
    audit = data.loc[blank,['date','code']].copy()
    audit['observation_state'] = 'ALL_SIX_PRICE_FIELDS_NULL'
    audit['interpretation'] = 'UNOBSERVED_GRID_ROW_NO_IDENTITY_OR_SOURCE_ABSENCE_INFERENCE'
    stats = {'input_rows':len(data), 'observed_rows':int((~blank).sum()), 'unobserved_rows':int(blank.sum()),
             'unobserved_codes':int(data.loc[blank,'code'].nunique()),
             'unobserved_dates':int(data.loc[blank,'date'].nunique()),
             'all_price_keys_preserved':True, 'null_to_zero_fills':0,
             'state_policy':'CONTIGUOUS_OBSERVED_SEGMENTS; NO_BRIDGING_EXPLICIT_NULL_RUNS',
             'listing_or_delisting_inferred':False}
    return result, market, audit, stats


def bind_calendar(path, *, live=True):
    path = Path(path)
    sha = digest(path)
    if live:
        require(sha.startswith(CALENDAR_PREFIX), 'CALENDAR_R07_PREFIX_CHANGED')
    data = frame(path, ['trade_date'])
    dates = normalize_dates(data['trade_date'])
    require(not dates.duplicated().any(), 'CALENDAR_DUPLICATES')
    if live:
        require(len(dates)==3097 and dates.min()==pd.Timestamp('2014-01-02') and dates.max()==pd.Timestamp('2026-09-24'), 'CALENDAR_SCOPE_CHANGED')
        require(TARGETS <= set(dates), 'RECOVERY_TARGET_NOT_A_SESSION')
    return {'path':str(path.resolve()), 'sha256':sha, 'date_field':'trade_date',
            'rows':len(dates), 'min':str(dates.min().date()), 'max':str(dates.max().date()),
            'selection':'EXPLICIT_REVIEWED_VERSION; NO_GLOB_LATEST; NO_ADJUST_FACTOR_PROXY'}, set(dates)


def build(manifest, compiler, store, calendar, *, live=True):
    manifest, compiler, store = Path(manifest), Path(compiler), Path(store)
    parent = json.loads(manifest.read_text(encoding='utf-8'))
    require(parent['generation']=='R06_TWO_DAY_RECOVERY_20261024' and parent['build_validated'] is True, 'WRONG_PARENT')
    for item in parent['artifacts']:
        require(digest(item['path'])==item['sha256'], 'R06_ARTIFACT_CHANGED')
    for path, sha in parent['source_pins'].items():
        require(digest(path)==sha, 'R06_SOURCE_CHANGED')
    compute, structure = functions(compiler)
    dest, receipt = store/GEN, store/GEN/'CANDIDATE_MANIFEST.json'
    if receipt.exists():
        old = json.loads(receipt.read_text(encoding='utf-8'))
        for path, sha in old['r08_input_pins'].items():
            require(digest(path)==sha, 'REPLAY_INPUT_CHANGED')
        for item in old['artifacts']:
            require(digest(item['path'])==item['sha256'], 'REPLAY_OUTPUT_CHANGED')
        return {'status':'ALREADY_BUILT_VERIFIED','manifest':str(receipt)}
    require(not dest.exists(), 'PARTIAL_CANDIDATE_REQUIRES_REVIEW')
    binding, sessions = bind_calendar(calendar, live=live)
    ptrs = [p for p in parent['source_pins'] if p.replace('\\','/').endswith('/CURRENT_CACHE_RELEASE.json')]
    require(len(ptrs)==1, 'PARENT_ASOF_NOT_UNIQUE')
    asof = pd.Timestamp(json.loads(Path(ptrs[0]).read_text(encoding='utf-8-sig'))['asof'])
    require(binding['max']==str(asof.date()), 'CALENDAR_PARENT_ASOF_MISMATCH')
    root = Path(parent['parent_cache_root'])/'STOCK_DAILY_RAW_PIT_R1'
    physical = sorted(root.glob('year=*/part_*.parquet'))
    require(bool(physical), 'NO_CANONICAL_PRICE_PARTITIONS')
    paths = [resolve_cache(parent,'STOCK_DAILY_RAW_PIT_R1',p.relative_to(root).as_posix()) for p in physical]
    require(len(paths)==len(set(map(str, paths))), 'DUPLICATE_PARTITION_PATH')
    pins = {str(manifest.resolve()):digest(manifest),str(compiler.resolve()):COMPILER_SHA,
            binding['path']:binding['sha256']}
    for module in (Path(__file__), Path(__file__).with_name('r08_coverage_gate.py'), Path(__file__).with_name('r07_rebuild_local.py'), Path(__file__).with_name('r06_bundle_store.py')):
        pins[str(module.resolve())] = digest(module)
    panels = []
    for path in paths:
        pins[str(path)] = digest(path)
        data = frame(path, PRICE_COLUMNS)
        dates = normalize_dates(data['date'])
        require(set(dates.dt.year)=={int(path.parent.name.split('=')[1])}, 'PARTITION_YEAR_MISMATCH')
        require(set(dates) <= sessions, 'PRICE_DATE_OUTSIDE_PINNED_CALENDAR')
        panels.append(data)
    full = pd.concat(panels, ignore_index=True)
    require(pd.to_datetime(full['date']).max()<=asof, 'SOURCE_ROWS_AFTER_PARENT_ASOF')
    factors, market, audit, stats = observed_recompute(full, compute, structure)
    if live:
        require((stats['unobserved_rows'],stats['unobserved_codes'],stats['unobserved_dates'])==(34477,344,143), 'R07_NULL_FAMILY_CHANGED')
    diagnoses = diagnose_two_days(parent) if live else {'status':'OFFLINE_FIXTURE_WITHOUT_VENDOR_UNITS'}
    fact = factors[factors['date'].dt.year==2026].copy()
    core = market[market['date'].dt.year==2026].copy()
    require(TARGETS<=set(fact['date']) and TARGETS<=set(core['date']), 'RECOVERY_DATES_NOT_PROPAGATED')
    prepared, gates = {}, {}
    for product, new, grain, fields in [('STOCK_FACTOR_DAILY_R1',fact,('date','code'),('close',)),
                                       ('MARKET_STRUCTURE_DAILY_R1',core,('date',),('allA_count','allA_money'))]:
        source = resolve_cache(parent,product,'year=2026/part_2026.parquet')
        pins[str(source)] = digest(source)
        schema = pq.ParquetFile(source).schema_arrow.remove_metadata()
        if product=='MARKET_STRUCTURE_DAILY_R1':
            sw = {'sw_l1_n_industries','sw_l1_n_mapped','sw_l1_mapped_positive_ratio','sw_l1_industry_positive_breadth','sw_l1_window'}
            require(set(schema.names)-set(new.columns)<=sw, 'UNSUPPORTED_MARKET_SCHEMA')
            for col in set(schema.names)-set(new.columns):
                new[col] = None
            new['pit_status'] = 'PARTIAL_OBSERVED_CORE_SW_UNVERIFIED'
            new['known_gaps'] = 'SW_NOT_RECOMPUTED; OBSERVED_QUOTES_NOT_PIT_UNIVERSE; NOT_MASTER_ADMITTED'
        require(set(schema.names)<=set(new.columns), 'UNSUPPORTED_OUTPUT_SCHEMA')
        table = pa.Table.from_pandas(new[schema.names],schema=schema,preserve_index=False,safe=True)
        old = frame(source, list(set(grain)|set(fields)))
        gates[product] = compare(old, table.to_pandas(),grain,fields)
        require(gates[product]['coverage_non_regression_pass'], 'COVERAGE_REGRESSION:' + product)
        prepared[product] = table
    # All semantic guards precede the first candidate write.
    dest.mkdir(parents=True)
    artifacts = []
    for product, table in prepared.items():
        out = dest/product/'year=2026'/'part_2026.parquet'
        out.parent.mkdir(parents=True)
        pq.write_table(table,out)
        require(pq.ParquetFile(out).metadata.num_rows==table.num_rows, 'OUTPUT_ROW_LOSS')
        artifacts.append({'product':product,'path':str(out.resolve()),'sha256':digest(out),'rows':table.num_rows})
    audit_path = dest/'UNOBSERVED_GRID_ROWS.parquet'
    audit.to_parquet(audit_path,index=False)
    artifacts.append({'product':'UNOBSERVED_GRID_AUDIT','path':str(audit_path.resolve()),'sha256':digest(audit_path),'rows':len(audit)})
    for path,sha in pins.items():
        require(digest(path)==sha, 'INPUT_CHANGED_DURING_BUILD')
    body = copy.deepcopy(parent)
    body.update(generation=GEN,r08_input_pins=pins,r08_artifacts=artifacts,
                parent_candidate_manifest=str(manifest.resolve()), observation_accounting=stats,
                calendar_binding=binding, coverage_gates=gates,
                bounded_two_day_layer_diagnoses=diagnoses,
                scope_acceptance='OBSERVED_STOCK_DERIVED_CANDIDATE; NOT_FULL_PRODUCT_OR_ENGINE_ADMISSION',
                all_products_ready=False, production_publish_allowed=False,engine_admission_allowed=False,
                dirty_derived_products=['MARKET_STRUCTURE_DAILY_R1: SW_UNVERIFIED; PIT_UNIVERSE_UNRESOLVED'],
                other_dependencies='UNRESOLVED; NO_SOURCE_ABSENCE_OR_MIGRATION_LOSS_INFERENCE')
    for item in artifacts:
        if item['product']!='UNOBSERVED_GRID_AUDIT':
            body['cache_overrides'].setdefault(item['product'],{})['year=2026/part_2026.parquet']=item['path']
    body['artifacts'] += artifacts
    write_json(receipt,body)
    return {'status':'CANDIDATE_BUILT_WITH_EXPLICIT_UNOBSERVED_ROWS','manifest':str(receipt),
            'observation_accounting':stats,'coverage_gates':gates,'network_calls':0,
            'SOURCE_ABSENCE_CLAIM_ALLOWED':False,'FOUNDATION_ACCEPTANCE':False}


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--compiler-source',required=True)
    args=ap.parse_args()
    print(json.dumps(build(WORK/'candidate_releases'/'R06'/'R06_TWO_DAY_RECOVERY_20261024'/'CANDIDATE_MANIFEST.json',
                           args.compiler_source,WORK/'candidate_releases'/'R08',CALENDAR),ensure_ascii=False,default=str))
