"""GPT-owned two-day candidate recovery. No network, legacy publish or source writes.

Uses the actual CURRENT pair as parent, full parent daily-file inheritance and two
exact hash-pinned vendor units. Cache mappings must reproduce the adjacent control.
The output is a sparse candidate view, not a new formal full release.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from r06_bundle_store import digest, write_json, relative_key, resolve_cache, resolve_clean

WORK = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
BB = Path(r'E:\BLACKBOX')
GENERATION = 'R06_TWO_DAY_RECOVERY_20261024'
DATES = ['2026-08-31', '2026-09-01']
RAW_HASHES = {'2026-08-31':'553bad1973f6834506989b15a8298746bc07490534834cde25790b957720b063',
              '2026-09-01':'25e695dd9de457b24cd0d087064d5d68709908c72a53d8c49ca477d818d4ded7'}
PRODUCTS = ['STOCK_DAILY_PIT_R1', 'STOCK_DAILY_RAW_PIT_R1']


def checked(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def file_frame(path):
    # Read physical columns, not a virtual Hive year column.
    return pq.ParquetFile(path).read().to_pandas()


def normalized(frame):
    return frame.sort_values(['date', 'code'], kind='mergesort').reset_index(drop=True)


def map_cache(raw, product, schema, source_version):
    date = pd.to_datetime(raw['time']).dt.normalize()
    mapped = raw.rename(columns={'time':'date'}).copy()
    mapped['date'] = date
    mapped['signal_date'] = date
    mapped['data_date'] = date
    mapped['asset_type'] = 'STOCK'
    mapped['price_adj_tag'] = 'RAW_NONE'
    mapped['asof_rule'] = 'SAME_DAY_KNOWN_EOD'
    mapped['pit_status'] = 'OK'
    mapped['source_version'] = source_version
    mapped['known_at'] = date + pd.Timedelta(hours=15) if product == 'STOCK_DAILY_RAW_PIT_R1' else pd.NaT
    missing = [c for c in schema.names if c not in mapped]
    checked(not missing, 'UNSUPPORTED_CACHE_COLUMNS:' + ','.join(missing))
    # Exact schema and safe conversion: no fabricated unknown columns.
    table = pa.Table.from_pandas(mapped[schema.names], schema=schema, preserve_index=False, safe=True)
    return table.to_pandas()


def same_frame(a, b, exclude=()):
    cols = [c for c in a.columns if c not in exclude]
    pd.testing.assert_frame_equal(normalized(a[cols]), normalized(b[cols]), check_dtype=False)


def inherit_file(source, target):
    checked(not target.exists(), 'CANDIDATE_TARGET_EXISTS')
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(source, target)
        checked(os.path.samefile(source, target), 'HARDLINK_IDENTITY_FAILED')
        return 'HARDLINK_READ_ONLY'
    except OSError:
        shutil.copy2(source, target)
        checked(digest(source) == digest(target), 'INHERIT_COPY_MISMATCH')
        return 'COPY_VERIFIED'


def build(gap, bb, store, *, live=True, registry_path=None):
    bb, store = Path(bb), Path(store)
    clean_ptr = bb/'数据'/'清洗成品'/'CURRENT_CLEANING_RELEASE.json'
    cache_ptr = bb/'数据'/'回测缓存'/'CURRENT_CACHE_RELEASE.json'
    clean_bytes, cache_bytes = clean_ptr.read_bytes(), cache_ptr.read_bytes()
    clean, cache = json.loads(clean_bytes.decode('utf-8-sig')), json.loads(cache_bytes.decode('utf-8-sig'))
    checked(clean['release_id'] == cache['source_cleaning_release'], 'SOURCE_CURRENT_PAIR_MISMATCH')
    std = Path(clean['standard_root'])
    cache_root = Path(cache['release_root'])
    daily = std/'price'/'stock_ohlcv_daily'
    checked(daily.is_dir() and cache_root.is_dir(), 'PARENT_MISSING')
    checked('canary' not in cache['cache_release_id'].lower(), 'THIN_CANARY_PARENT_FORBIDDEN')
    candidate = store/GENERATION
    manifest_path = candidate/'CANDIDATE_MANIFEST.json'
    if manifest_path.exists():
        body = read_json(manifest_path)
        for p, expected in body['source_pins'].items():
            checked(digest(p) == expected, 'IDEMPOTENT_SOURCE_CHANGED')
        for item in body['artifacts']:
            checked(digest(item['path']) == item['sha256'], 'IDEMPOTENT_OUTPUT_CHANGED')
        checked(sorted(p.name for p in daily.iterdir()) == body['parent_daily_names'], 'IDEMPOTENT_PARENT_FILES_CHANGED')
        checked({p.name:[p.stat().st_size, p.stat().st_mtime_ns] for p in daily.iterdir()} == body['parent_daily_fingerprints'], 'IDEMPOTENT_PARENT_CHANGED')
        for name in body['parent_daily_names']:
            a, b = daily/name, Path(body['cleaning_daily_root'])/name
            checked(b.is_file() and (os.path.samefile(a,b) or digest(a)==digest(b)), 'IDEMPOTENT_INHERITANCE_CHANGED')
        return {'status':'ALREADY_BUILT_VERIFIED', 'manifest':str(manifest_path), 'generation':GENERATION}
    checked(not candidate.exists(), 'PARTIAL_CANDIDATE_REQUIRES_REVIEW')
    raw_by_day = gap['raw_inputs']
    source_pins = {str(clean_ptr):hashlib.sha256(clean_bytes).hexdigest(), str(cache_ptr):hashlib.sha256(cache_bytes).hexdigest()}
    registry = None
    if registry_path is not None:
        registry_path = Path(registry_path)
        registry = read_json(registry_path)
        source_pins[str(registry_path)] = digest(registry_path)
        records = [r for r in registry['datasets'] if r['dataset_id']=='PRICE_STOCK_DAILY']
        checked(len(records)==1, 'REGISTRY_DATASET_NOT_UNIQUE')
        checked(Path(records[0]['layers']['CLEAN']['root']).resolve()==daily.resolve(), 'REGISTRY_NOT_BOUND_TO_LIVE_CURRENT')
    frames, raw_paths = {}, {}
    for day in DATES:
        item = raw_by_day[day]
        source = Path(item['path'])
        expected = RAW_HASHES[day] if live else item['sha256']
        checked(digest(source) == expected == item['sha256'], 'RAW_HASH_MISMATCH:' + day)
        sc = gap['raw_sidecar_provenance'][day]
        side = Path(sc['sidecar_path'])
        checked(digest(side) == sc['sidecar_sha256'], 'SIDECAR_HASH_MISMATCH')
        rel = str(relative_key(sc['declared_clean_rel']))
        checked(rel.startswith('price/stock_ohlcv_daily/') and rel.count('/') == 2, 'UNPLANNED_CLEAN_TARGET')
        # Content-addressed sidecar and mapping evidence are preserved; no staging is needed.
        raw = file_frame(source)
        checked(len(raw) == item['rows'], 'RAW_ROW_COUNT_CHANGED')
        checked(not raw.duplicated(['time','code']).any(), 'RAW_DUPLICATE_KEYS')
        checked(sorted(pd.to_datetime(raw['time']).dt.strftime('%Y-%m-%d').unique()) == [day], 'RAW_DATE_MISMATCH')
        checked(raw['code'].notna().all(), 'RAW_NULL_CODE')
        for field, nulls in item['null_counts'].items():
            checked(int(raw[field].isna().sum()) == nulls == 0, 'RAW_NULLS_CHANGED:' + field)
        checked(raw['fq'].isna().all(), 'RAW_ADJUSTMENT_NOT_NONE')
        frames[day], raw_paths[day] = raw, source
        source_pins[str(source)], source_pins[str(side)] = expected, sc['sidecar_sha256']
    control = gap['adjacent_unit_mapping_proof']
    control_raw = Path(control['raw_path'])
    checked(digest(control_raw) == control['raw_sha256'], 'ADJACENT_RAW_CHANGED')
    adjacent = file_frame(control_raw)
    adjacent_day = str(pd.to_datetime(adjacent['time']).dt.date.iloc[0])
    clean_control = daily/Path(control['clean_path']).name
    checked(clean_control.is_file() and digest(clean_control) == control['raw_sha256'], 'ACTIVE_CLEAN_CONTROL_NOT_IDENTICAL')
    source_pins[str(control_raw)] = control['raw_sha256']
    parent_files = sorted(daily.iterdir())
    checked(all(p.is_file() and not p.is_symlink() for p in parent_files), 'UNPLANNED_DAILY_DIRECTORY_ENTRY')
    parents = {p.name:(p.stat().st_size, p.stat().st_mtime_ns) for p in parent_files}
    cached = {}
    for product in PRODUCTS:
        p = cache_root/product/'year=2026'/'part_2026.parquet'
        schema = pq.ParquetFile(p).schema_arrow.remove_metadata()
        old = file_frame(p)
        checked(not old.duplicated(['date','code']).any(), 'PARENT_CACHE_DUPLICATE_KEYS:' + product)
        mask = pd.to_datetime(old['date']).dt.strftime('%Y-%m-%d').isin(DATES)
        checked(not mask.any(), 'TARGET_ALREADY_IN_PARENT_CACHE')
        old_control = old[pd.to_datetime(old['date']).dt.strftime('%Y-%m-%d') == adjacent_day]
        checked(len(old_control) == len(adjacent), 'ADJACENT_CACHE_CONTROL_COUNT')
        mapped_control = map_cache(adjacent, product, schema, 'CONTROL_ONLY')
        same_frame(old_control, mapped_control, exclude=('source_version',))
        source_pins[str(p)] = digest(p)
        cached[product] = (old, schema)
    candidate.mkdir(parents=True)
    new_daily = candidate/'cleaning'/'price'/'stock_ohlcv_daily'
    modes = {}
    for p in parent_files:
        modes[p.name] = inherit_file(p, new_daily/p.name)
    artifacts = []
    def record(path):
        artifacts.append({'path':str(path.resolve()), 'sha256':digest(path), 'bytes':path.stat().st_size})
    for day in DATES:
        rel = relative_key(gap['raw_sidecar_provenance'][day]['declared_clean_rel'])
        target = new_daily/rel.name
        inherit_file(raw_paths[day], target)
        record(target)
    checked(sorted(p.name for p in new_daily.iterdir()) == sorted(list(parents) + [relative_key(gap['raw_sidecar_provenance'][d]['declared_clean_rel']).name for d in DATES]), 'PARENT_INHERITANCE_LOSS')
    overrides, results = {}, {}
    for product, (old, schema) in cached.items():
        additions = [map_cache(frames[d], product, schema, GENERATION) for d in DATES]
        merged = pd.concat([old]+additions, ignore_index=True)
        checked(not merged.duplicated(['date','code']).any(), 'OUTPUT_DUPLICATE_KEYS')
        merged = normalized(merged)
        path = candidate/'cache'/product/'year=2026'/'part_2026.parquet'
        path.parent.mkdir(parents=True)
        pq.write_table(pa.Table.from_pandas(merged, schema=schema, preserve_index=False, safe=True), path)
        observed = file_frame(path)
        dates = pd.to_datetime(observed['date']).dt.strftime('%Y-%m-%d')
        same_frame(old, observed[~dates.isin(DATES)])
        for day, mapped in zip(DATES, additions):
            same_frame(mapped, observed[dates == day])
        checked(len(observed) == len(old) + sum(len(frames[d]) for d in DATES), 'ROW_CONSERVATION_FAILED')
        record(path)
        overrides[product] = {'year=2026/part_2026.parquet':str(path.resolve())}
        results[product] = {'parent_rows':len(old), 'candidate_rows':len(observed), 'added_by_date':{d:len(frames[d]) for d in DATES}, 'all_non_target_rows_preserved':True}
    for p, expected in source_pins.items():
        checked(digest(p) == expected, 'SOURCE_CHANGED_DURING_BUILD')
    checked({p.name:(p.stat().st_size, p.stat().st_mtime_ns) for p in daily.iterdir()} == parents, 'PARENT_DAILY_CHANGED_DURING_BUILD')
    entries = list(cache_root.iterdir())
    for p in entries:
        is_link = p.is_symlink() or bool(getattr(p, 'is_junction', lambda:False)())
        checked(not is_link or p.exists(), 'BROKEN_PARENT_PRODUCT_LINK:' + p.name)
    products = sorted(p.name for p in entries if p.is_dir() and not p.name.startswith('_'))
    registry_output = None
    if registry is not None:
        rec = next(r for r in registry['datasets'] if r['dataset_id']=='PRICE_STOCK_DAILY')
        rec['layers']['CLEAN'].update(root=str(new_daily.resolve()), release_id=GENERATION,
            candidate_only=True, scope_acceptance='TWO_DAY_REPAIR_WITH_PARENT_INHERITANCE_NOT_FULL_ENGINE_ADMISSION')
        registry['R06_NOTE']='Diagnostic candidate view; no production pointer changed; inherited claims are not newly certified.'
        registry_output = candidate/'ECOLOGY_REGISTRY_R06_DIAGNOSTIC.json'
        write_json(registry_output,registry)
        record(registry_output)
    body = {'generation':GENERATION, 'candidate_only':True, 'build_validated':True,
        'scope_acceptance':'EXACT_TWO_DATES_TWO_PRICE_PRODUCTS_ONLY', 'FOUNDATION_ACCEPTANCE':False,
        'production_publish_allowed':False, 'engine_admission_allowed':False,
        'parent_cleaning_id':clean['release_id'], 'parent_cleaning_standard_root':str(std),
        'parent_cache_id':cache['cache_release_id'], 'parent_cache_root':str(cache_root),
        'cleaning_daily_root':str(new_daily.resolve()), 'cache_overrides':overrides,
        'candidate_registry_path':str(registry_output.resolve()) if registry_output else None,
        'inherited_cache_products':products, 'parent_daily_names':sorted(parents),
        'parent_daily_fingerprints':{n:list(v) for n,v in parents.items()},
        'parent_daily_count':len(parents), 'candidate_daily_count':len(parents)+2,
        'inherited_status':'PRESERVED_REFERENCE_NOT_REVERIFIED_OR_PROMOTED',
        'catalog_reconciliation_status':'PHYSICAL_PARENT_PRODUCT_ROOTS_ONLY; registry and sidecars remain a separate gate',
        'dirty_derived_products':['STOCK_FACTOR_DAILY_R1','MARKET_STRUCTURE_DAILY_R1'],
        'other_dependencies':'UNVERIFIED_UNTIL_DEPENDENCY_REGISTRY_RECONCILED',
        'source_pins':source_pins, 'artifacts':artifacts, 'cache_results':results,
        'parent_realpaths':{'cleaning_standard':os.path.realpath(std), 'stock_daily':os.path.realpath(daily), 'cache':os.path.realpath(cache_root)}}
    # Verify the sparse resolver selects new targets and retains untouched product roots.
    for day in DATES:
        rel = gap['raw_sidecar_provenance'][day]['declared_clean_rel']
        checked(digest(resolve_clean(body, rel)) == raw_by_day[day]['sha256'], 'CLEAN_VIEW_RESOLUTION_FAILED')
    for product in PRODUCTS:
        checked(resolve_cache(body, product, 'year=2026/part_2026.parquet').is_file(), 'CACHE_VIEW_RESOLUTION_FAILED')
    write_json(manifest_path, body)
    return {'status':'CANDIDATE_BUILT', 'generation':GENERATION, 'manifest':str(manifest_path), 'scope':body['scope_acceptance'], 'cache_results':results, 'FOUNDATION_ACCEPTANCE':False}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--gap-inputs', required=True)
    args = ap.parse_args()
    result = build(read_json(args.gap_inputs), BB, WORK/'candidate_releases'/'R06', registry_path=WORK/'ECOLOGY_REGISTRY_R3.json')
    print(json.dumps(result))
