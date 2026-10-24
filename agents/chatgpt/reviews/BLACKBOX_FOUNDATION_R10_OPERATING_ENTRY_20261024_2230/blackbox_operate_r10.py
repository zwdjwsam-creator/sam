"""Bounded BLACKBOX operations: evidence catalogue, diagnostic price reads, import probe.

No publisher, download, strategy, provider factory registration or trading entry.
Catalogue declarations remain separate from measured request usability.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

WORK=Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
RUNTIME=WORK/'reviews/R09/control_2100/r09_control_runtime_preflight_fixed.py'
RUNTIME_SHA='f52236648c37eb91944fd7e03e545f18ed887dc0e2c7ec12f2dcdeb6895d9d24'
MANIFEST=WORK/'candidate_releases/R08/R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024/CANDIDATE_MANIFEST.json'
MANIFEST_SHA='89d2a903fe01701c43c6cf8a90906c096aede74db082012fb6bc31d31735787f'
PRODUCT='STOCK_DAILY_RAW_PIT_R1'
FIELDS=('open','high','low','close','volume','money')
FLAGS={'FOUNDATION_ACCEPTANCE':False,'formal_backtest_active':False,'ORDER_ALLOWED':False,
       'CURRENT_SWITCH_ALLOWED':False,'NEW_DATA_ACQUISITION_AUTHORIZED':False}


def need(ok,reason):
    if not ok:raise ValueError(reason)


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def no_duplicates(pairs):
    result={}
    for k,v in pairs:
        need(k not in result,'DUPLICATE_JSON_KEY:'+k);result[k]=v
    return result


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=no_duplicates)


def canonical_pin(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('ascii')).hexdigest()


def catalogue(matrix,dependency,bindings,acquisition):
    rows=matrix['rows'];products=dependency['products']
    ids=[r['product_id'] for r in rows];pids=[r['product_id'] for r in products]
    need(bool(ids) and len(set(ids))==len(ids),'DUPLICATE_OR_EMPTY_CATALOG')
    need(len(set(pids))==len(pids) and set(ids)==set(pids),'CATALOG_DEPENDENCY_ENTITY_MISMATCH')
    pd={r['product_id']:r for r in products}
    result=[]
    for binding in bindings['bindings']:
        targets=binding.get('required_cache_product') or []
        need(isinstance(targets,list) and all(isinstance(t,str) for t in targets),'INVALID_EXPLICIT_PRODUCT_ROUTE')
    for row in rows:
        pid=row['product_id'];updaters=[b for b in bindings['bindings'] if pid in (b.get('required_cache_product') or [])]
        domains=[a for a in acquisition['rows'] if a.get('dataset_id') in {b.get('dataset') for b in updaters}]
        result.append({'product_id':pid,'historical_catalog_and_measurement':row,'schema_and_physical_binding':pd[pid],
                       'update_bindings':updaters,'source_domains':domains,
                       'update_binding_status':'DECLARED_ROUTE_NOT_EXECUTED' if updaters else 'UNBOUND_IN_THIS_EVIDENCE_JOIN',
                       'serving_authority':'REQUEST_NOT_EVALUATED',
                       'use_for_formal_backtest':False,'source_absence_claim_allowed':False})
    return {'schema':'BLACKBOX_OPERATING_CATALOG_R10','products':result,'source_domains':acquisition['rows'],
            'target_date_contract':bindings['target_date_rule'],'registry_sources':dependency['registry_sources'],
            'field_ownership':dependency.get('field_ownership'),'dependency_edges':dependency.get('dependency_edges'),
            'canonical_input_pins':{k:canonical_pin(v) for k,v in [('matrix',matrix),('dependency',dependency),('bindings',bindings),('acquisition',acquisition)]},
            'historical_labels_are_not_current_admission':True,
            'review_corrections':{
                'INDEX_DAILY_R1':'Canonical full-history source already proven present in R08. The old H1 minute-derivation instruction is superseded; do not redownload or derive from minutes to replace it.',
                'MARKET_UNIVERSE_PIT_R1':'A historical measured window ending 2026-07-20 does not serve later requests and does not itself prove regression.',
                'ADJUST_FACTOR_PIT_R1':'Date union and COVERAGE sidecar are not symbol/field completeness or supplier acquisition receipts; 83503-row sidecar difference remains unresolved.'},
            'catalog_count':len(result),'scope':'EVIDENCE_JOIN; NO_NEW_BUSINESS_POLICY_OR_COMPLETENESS_CERTIFICATE',**FLAGS}


def read_input_bundle(here):
    package=load(Path(here)/'R10_INPUT_SPEC.json')
    result={}
    for key,item in package['inputs'].items():
        obj=load(Path(here)/item['file'])
        need(canonical_pin(obj)==item['canonical_json_sha256'],'EVIDENCE_INPUT_CHANGED:'+key)
        result[key]=obj
    return result


def price_query(body,codes,start,end,fields):
    """Read actual keys for an exact bounded request; never emit source absence."""
    import numpy as np
    import pandas as pd
    import pyarrow.parquet as pq
    need(1<=len(codes)<=5 and len(set(codes))==len(codes),'INVALID_CODE_COUNT')
    need(all(isinstance(c,str) and re.fullmatch(r'\d{6}\.(XSHG|XSHE)',c) for c in codes),'CANONICAL_CODE_REQUIRED')
    need(bool(fields) and len(set(fields))==len(fields) and set(fields)<=set(FIELDS),'UNSUPPORTED_FIELD')
    need(isinstance(start,str) and isinstance(end,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',start) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',end),'EXPLICIT_DAILY_DATES_REQUIRED')
    a,b=pd.Timestamp(start),pd.Timestamp(end)
    need(0<=(b-a).days<=31,'REQUEST_WINDOW_LIMIT_31_DAYS')
    need(body.get('generation')=='R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024','WRONG_CANDIDATE_GENERATION')
    heads={p:s for p,s in body['source_pins'].items() if Path(p).name in ('CURRENT_CACHE_RELEASE.json','CURRENT_CLEANING_RELEASE.json')}
    need(len(heads)==2,'PARENT_CURRENT_PAIR_UNBOUND')
    pins=dict(heads)
    cal=body['calendar_binding'];pins[cal['path']]=cal['sha256']
    for p,s in pins.items():need(digest(p)==s,'PINNED_PARENT_OR_CALENDAR_CHANGED')
    days=pq.ParquetFile(cal['path']).read(columns=[cal['date_field']]).to_pandas()[cal['date_field']]
    need(not pd.api.types.is_numeric_dtype(days),'NUMERIC_CALENDAR_AXIS_REJECTED')
    days=pd.to_datetime(days,errors='raise')
    need(days.notna().all() and days.dt.tz is None and not days.duplicated().any(),'INVALID_CALENDAR')
    need(a>=days.min() and b<=days.max(),'REQUEST_OUTSIDE_PINNED_CALENDAR; NO_SOURCE_ABSENCE_CLAIM')
    wanted_days=days[(days>=a)&(days<=b)]
    need(len(wanted_days)>0,'NO_SESSION_IN_REQUEST')
    expected=pd.MultiIndex.from_product([wanted_days,codes],names=['date','code'])
    artifacts={i['path']:i['sha256'] for i in body['artifacts']}
    authorized={**body['r08_input_pins'],**artifacts}
    frames=[]
    for year in sorted(set(wanted_days.dt.year)):
        key=f'year={year}/part_{year}.parquet'
        path=body['cache_overrides'].get(PRODUCT,{}).get(key)
        if path is None:path=str(Path(body['parent_cache_root'])/PRODUCT/key)
        need(path in authorized,'PARTITION_NOT_PINNED')
        pins[path]=authorized[path];need(digest(path)==pins[path],'PRICE_PARTITION_CHANGED')
        pf=pq.ParquetFile(path);need(pf.metadata.num_rows<=2500000,'PARTITION_ROW_LIMIT')
        need({'date','code',*fields}<=set(pf.schema_arrow.names),'SCHEMA_NOT_SUPPORTED')
        f=pf.read(columns=['date','code',*fields]).to_pandas()
        need(not pd.api.types.is_numeric_dtype(f['date']),'NUMERIC_PRICE_AXIS_REJECTED')
        f['date']=pd.to_datetime(f['date'],errors='raise')
        need(f['date'].dt.tz is None and f['date'].notna().all() and f['date'].eq(f['date'].dt.normalize()).all(),'INVALID_PRICE_AXIS')
        f=f[(f['date']>=a)&(f['date']<=b)&f['code'].isin(codes)]
        frames.append(f)
    out=pd.concat(frames,ignore_index=True)
    need(not out.duplicated(['date','code']).any(),'REVISION_CONFLICT_REQUIRES_CONTRACT')
    keys=pd.MultiIndex.from_frame(out[['date','code']])
    need(len(keys.difference(expected))==0 and len(expected.difference(keys))==0,'REQUEST_KEYS_NOT_COMPLETE; NO_SOURCE_ABSENCE_CLAIM')
    for name in fields:
        need(pd.api.types.is_numeric_dtype(out[name]) and np.isfinite(out[name].to_numpy(dtype=float,na_value=np.nan)).all(),'REQUEST_FIELD_UNOBSERVED:'+name)
        need(bool((out[name]>=0).all()) if name in ('volume','money') else bool((out[name]>0).all()),'INVALID_PRICE_OBSERVATION:'+name)
    for p,s in pins.items():need(digest(p)==s,'SOURCE_CHANGED_DURING_QUERY')
    out=out.sort_values(['date','code']).reset_index(drop=True)
    out['date']=out['date'].dt.strftime('%Y-%m-%d')
    return {'status':'BOUNDED_OBSERVATIONS_SERVED','product_id':PRODUCT,'generation':body['generation'],
            'request':{'codes':codes,'start':start,'end':end,'fields':fields,'fq':None},'rows':out.to_dict('records'),
            'receipt':{'expected_keys':len(expected),'returned_keys':len(out),'source_pins':pins},
            'SOURCE_ABSENCE_CLAIM_ALLOWED':False,'engine_admission':'NOT_ADMITTED',
            'scope':'RAW_NONE_CANDIDATE_OBSERVATIONS; NO_PIT_OR_TRADING_ELIGIBILITY_CLAIM',**FLAGS}


def reviewed_runtime():
    need(digest(RUNTIME)==RUNTIME_SHA,'FIXED_RUNTIME_CHANGED')
    need(digest(RUNTIME.with_name('build_r09_control_successor.py'))=='0b11552b87cf98bd21d19f04ef32813faaa3c617e7d6f19a4a688dae9f5cd1fd','R09_BUILDER_CHANGED')
    sys.path.insert(0,str(RUNTIME.parent))
    spec=importlib.util.spec_from_file_location('r10_reviewed_runtime',RUNTIME)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def main():
    ap=argparse.ArgumentParser();ap.add_argument('operation',choices=['catalog','describe','query','update-plan'])
    ap.add_argument('--product');ap.add_argument('--codes');ap.add_argument('--start');ap.add_argument('--end');ap.add_argument('--fields',default='close')
    args=ap.parse_args();here=Path(__file__).resolve().parent
    def no_network(event,args):
        if event in ('socket.connect','socket.connect_ex','socket.getaddrinfo'):raise PermissionError('R10_NETWORK_FORBIDDEN')
    sys.addaudithook(no_network)
    runtime=reviewed_runtime()
    preflight=runtime.run_preflight(WORK/'candidate/r09/control_successor')
    need(preflight.get('ok') is True,'REAL_MUST_READ_NOT_PASS')
    inputs=read_input_bundle(here);cat=catalogue(**inputs)
    if args.operation=='catalog':return {**cat,'real_preflight':preflight}
    product=next((p for p in cat['products'] if p['product_id']==args.product),None)
    need(product is not None,'PRODUCT_NOT_IN_REVIEWED_CATALOG')
    if args.operation=='describe':return {**product,'review_correction':cat['review_corrections'].get(args.product),'real_preflight':preflight}
    if args.operation=='update-plan':
        return {'product':product,'review_correction':cat['review_corrections'].get(args.product),'target_date_contract':cat['target_date_contract'],
                'status':'CONTRACT_PLAN_ONLY; NO_SUPPLIER_CALL_OR_WRITER',
                'execution_order':['MUST_READ_ACQUISITION','CHECKPOINT_AND_EXCLUSION','REGISTERED_LAYER_SEARCH',
                  'REQUEST_AND_STABLE_PAGINATION_CONTRACT','APPEND_ONLY_RAW_RECEIPTS','CLEAN_ALIGN_PIT',
                  'CACHE_EXACT_KEY_AND_FIELD_NON_REGRESSION','GENERATION_BOUND_ADMISSION','PUBLICATION_AND_FRESHNESS'],'real_preflight':preflight,**FLAGS}
    need(args.product==PRODUCT,'PRODUCT_READER_NOT_ACTIVATED; NO_RAW_FALLBACK')
    need(digest(MANIFEST)==MANIFEST_SHA,'R08_MANIFEST_CHANGED')
    result=price_query(load(MANIFEST),(args.codes or '').split(','),args.start,args.end,args.fields.split(','))
    result['real_preflight']=preflight;result['candidate_manifest_sha256']=MANIFEST_SHA
    return result


if __name__=='__main__':
    sys.dont_write_bytecode=True
    try:print(json.dumps(main(),ensure_ascii=True,allow_nan=False,default=str))
    except Exception as exc:
        print(json.dumps({'status':'STOP','reason':str(exc),'SOURCE_ABSENCE_CLAIM_ALLOWED':False,**FLAGS},ensure_ascii=True))
        raise SystemExit(3)
