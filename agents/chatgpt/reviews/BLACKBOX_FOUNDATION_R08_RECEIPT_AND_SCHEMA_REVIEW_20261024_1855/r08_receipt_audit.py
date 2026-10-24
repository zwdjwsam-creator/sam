"""Read-only independent reconciliation of the R08 manifest and physical artifacts.

No builder/replay, imports of production code, credentials, network or data writes.
Prints ASCII JSON. The caller may save stdout as a correction evidence file.
"""
import json
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from r06_bundle_store import digest, resolve_cache

WORK = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
MANIFEST = WORK/'candidate_releases'/'R08'/'R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024'/'CANDIDATE_MANIFEST.json'
REPORTED_SHA = '89d2a903fe01701c43c6cf8a90906c096aede74db082012fb6bc31d31735787f'
PRICE = ['date','code','open','high','low','close','volume','money']


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def physical(path, columns=None):
    return pq.ParquetFile(path).read(columns=columns).to_pandas()


def audit(manifest, expected_sha):
    manifest = Path(manifest)
    body = load(manifest)
    checks, failures = {}, []

    def check(name, ok, detail=None):
        checks[name] = {'pass':bool(ok),'detail':detail}
        if not ok:
            failures.append(name)

    check('manifest_matches_reported_sha',digest(manifest)==expected_sha,
          {'actual':digest(manifest),'expected':expected_sha})
    check('generation',body.get('generation')=='R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024')
    check('not_production_admitted',body.get('engine_admission_allowed') is False and body.get('production_publish_allowed') is False)
    parent_path = Path(body['parent_candidate_manifest'])
    parent = load(parent_path)
    check('parent_generation',parent.get('generation')=='R06_TWO_DAY_RECOVERY_20261024')
    input_pins = body['r08_input_pins']
    check('parent_manifest_pinned',input_pins.get(str(parent_path))==digest(parent_path))
    pin_groups = {'R08_inputs':input_pins,'R06_sources':parent['source_pins']}
    pin_report = {}
    for label,pins in pin_groups.items():
        result = []
        for path,expected in pins.items():
            actual = digest(path) if Path(path).is_file() else None
            result.append({'path':path,'expected':expected,'actual':actual,'match':actual==expected})
        pin_report[label] = result
        check(label+'_all_hashes',all(r['match'] for r in result))
    artifacts = []
    for item in body['artifacts']:
        p = Path(item['path'])
        actual = digest(p) if p.is_file() else None
        artifacts.append({'path':str(p),'expected':item['sha256'],'actual':actual,'match':actual==item['sha256']})
    check('all_inherited_and_new_artifact_hashes',bool(artifacts) and all(a['match'] for a in artifacts))
    input_partitions = []
    for path in input_pins:
        name = path.replace('\\','/')
        if '/STOCK_DAILY_RAW_PIT_R1/year=' in name and name.endswith('.parquet'):
            pf = pq.ParquetFile(path)
            input_partitions.append({'path':path,'rows':pf.metadata.num_rows,
                                     'schema_names':pf.schema_arrow.names})
    total = sum(p['rows'] for p in input_partitions)
    accounting = body['observation_accounting']
    check('full_prefix_rows_match_accounting',bool(input_partitions) and total==accounting['input_rows'],
          {'physical_prefix_rows':total,'manifest_prefix_rows':accounting['input_rows'],'partitions':len(input_partitions)})
    check('observed_plus_unobserved_arithmetic',accounting['observed_rows']+accounting['unobserved_rows']==total)
    r08_items = body['r08_artifacts']
    def unique(product):
        items = [i for i in r08_items if i['product']==product]
        if len(items)!=1:
            raise ValueError('PRODUCT_NOT_UNIQUE:'+product)
        return items[0]
    schemas = {}
    for product in ('STOCK_FACTOR_DAILY_R1','MARKET_STRUCTURE_DAILY_R1'):
        item = unique(product)
        p = Path(item['path'])
        old = resolve_cache(parent,product,'year=2026/part_2026.parquet')
        source_schema = pq.ParquetFile(old).schema_arrow.remove_metadata()
        candidate_schema = pq.ParquetFile(p).schema_arrow.remove_metadata()
        schemas[product] = {'candidate_path':str(p),'candidate_schema':str(candidate_schema),
                            'candidate_schema_names':candidate_schema.names,'candidate_column_count':len(candidate_schema),
                            'parent_path':str(old),'parent_schema':str(source_schema),
                            'parent_schema_names':source_schema.names,'parent_column_count':len(source_schema)}
        check('schema_matches_parent:'+product,source_schema.equals(candidate_schema))
        check('physical_rows_match_manifest:'+product,pq.ParquetFile(p).metadata.num_rows==item['rows'])
    source_path = resolve_cache(parent,'STOCK_DAILY_RAW_PIT_R1','year=2026/part_2026.parquet')
    source = physical(source_path,PRICE).sort_values(['code','date']).reset_index(drop=True)
    factor_path = unique('STOCK_FACTOR_DAILY_R1')['path']
    factors = physical(factor_path)
    candidate = factors[PRICE].sort_values(['code','date']).reset_index(drop=True)
    price_equal = True
    try:
        pd.testing.assert_frame_equal(source,candidate,check_dtype=False)
    except AssertionError:
        price_equal = False
    check('2026_price_values_and_keys_exactly_preserved',price_equal)
    check('2026_factor_grid_not_full_prefix_comparison',len(source)==len(candidate),
          {'source_2026_rows':len(source),'factor_2026_rows':len(candidate),
           'full_prefix_rows_for_formula_context':total})
    blank = source[PRICE[2:]].isna().all(axis=1)
    candidate_blank = candidate[PRICE[2:]].isna().all(axis=1)
    check('2026_unobserved_rows_conserved',int(blank.sum())==int(candidate_blank.sum())==accounting['unobserved_rows'])
    fs = factors.sort_values(['code','date']).reset_index(drop=True)
    derived = [c for c in fs if c not in PRICE+['formula_version','price_adj_tag','pit_status']]
    check('unobserved_grid_has_no_fabricated_factors',bool(derived) and fs.loc[candidate_blank,derived].isna().all().all())
    check('unobserved_grid_explicit_status',fs.loc[candidate_blank,'pit_status'].eq('PRICE_UNOBSERVED_NOT_ZERO_NOT_NO_DATA').all())
    audit_item = unique('UNOBSERVED_GRID_AUDIT')
    audit_rows = physical(audit_item['path'],['date','code'])
    wanted = source.loc[blank,['date','code']].sort_values(['code','date']).reset_index(drop=True)
    audit_keys_equal = True
    try:
        pd.testing.assert_frame_equal(wanted,audit_rows.sort_values(['code','date']).reset_index(drop=True),check_dtype=False)
    except AssertionError:
        audit_keys_equal = False
    check('grid_audit_exact_keys',audit_keys_equal)
    check('grid_audit_physical_rows',len(audit_rows)==audit_item['rows']==accounting['unobserved_rows'])
    return {'status':'RECONCILED' if not failures else 'RECONCILIATION_FAILED',
            'manifest_path':str(manifest),'manifest_sha256':digest(manifest),
            'parent_manifest_path':str(parent_path),'parent_manifest_sha256':digest(parent_path),
            'checks':checks,'failed_checks':failures,'input_partitions':input_partitions,
            'pin_report':pin_report,'artifact_hashes':artifacts,'physical_schemas':schemas,
            'observation_accounting':accounting,'price_plane_row_conservation_2026':price_equal and len(source)==len(candidate),
            'replay_semantics_from_supplied_code':'Hash validation only; replay does not reconstruct panel, rederive audit, or compare parent fingerprints.',
            'NETWORK_CALLS':0,'SOURCE_ABSENCE_CLAIMS':0,'DATA_WRITES':0,
            'FOUNDATION_ACCEPTANCE':False,'ENGINE_ADMISSION':False}


if __name__=='__main__':
    result = audit(MANIFEST,REPORTED_SHA)
    print(json.dumps(result,ensure_ascii=True,indent=2))
    raise SystemExit(0 if result['status']=='RECONCILED' else 2)
