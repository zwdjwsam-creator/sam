"""Recompute local stock-derived candidates using original, hash-pinned functions.

No authentication, download, production registry writer or legacy publisher.
Reads the full stored prefix: EMA cannot be correctly rebuilt from 250 sessions alone.
"""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from r06_bundle_store import digest,write_json,resolve_cache

WORK=Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
COMPILER_SHA='c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336'
PRICE_COLUMNS=['date','code','open','high','low','close','volume','money']
GEN='R07_LOCAL_STOCK_DERIVED_RECOVERY_20261024'


def check(ok,code):
    if not ok:
        raise ValueError(code)


def functions(path):
    check(digest(path)==COMPILER_SHA,'COMPILER_SOURCE_CHANGED')
    text=Path(path).read_text(encoding='utf-8-sig')
    names={'compute_factors','market_structure'}
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in names]
    check({n.name for n in nodes}==names,'FUNCTION_SET_INCOMPLETE')
    ns={'pd':pd,'np':np,'FORMULA_VERSION':'univ_factor_r1_v1','PRICE_ADJ_TAG':'RAW_NONE'}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
    return ns['compute_factors'],ns['market_structure']


def frame(path,columns=None):
    return pq.ParquetFile(path).read(columns=columns).to_pandas()


def recompute(panel,compute,structure):
    data=panel[PRICE_COLUMNS].sort_values(['code','date']).copy()
    data['date']=pd.to_datetime(data['date']).dt.normalize()
    check(not data.duplicated(['date','code']).any(),'PRICE_REVISION_UNRESOLVED')
    check(not data[['date','code','close','volume']].isna().any().any(),'PRICE_INPUT_NULL')
    # All available history supplies rolling windows and the recursive EMA state.
    factors=compute(data)
    market=structure(data).rename(columns={'signal_date':'date'})
    market['signal_date']=market['date']
    return factors,market


def build(manifest,compiler,store):
    manifest,compiler,store=Path(manifest),Path(compiler),Path(store)
    parent=json.loads(manifest.read_text(encoding='utf-8'))
    check(parent['generation']=='R06_TWO_DAY_RECOVERY_20261024' and parent['build_validated'] is True,'WRONG_PARENT')
    for item in parent['artifacts']:
        check(digest(item['path'])==item['sha256'],'R06_ARTIFACT_CHANGED')
    for path,sha in parent['source_pins'].items():
        check(digest(path)==sha,'R06_SOURCE_CHANGED')
    cache_pointers=[p for p in parent['source_pins'] if p.replace('\\','/').endswith('/CURRENT_CACHE_RELEASE.json')]
    check(len(cache_pointers)==1,'PINNED_PARENT_ASOF_NOT_UNIQUE')
    parent_asof=pd.Timestamp(json.loads(Path(cache_pointers[0]).read_text(encoding='utf-8-sig'))['asof'])
    compute,structure=functions(compiler)
    dest=store/GEN
    receipt=dest/'CANDIDATE_MANIFEST.json'
    if receipt.exists():
        old=json.loads(receipt.read_text(encoding='utf-8'))
        for path,sha in old['local_recompute_input_pins'].items():
            check(digest(path)==sha,'REPLAY_INPUT_CHANGED')
        for item in old['r07_artifacts']:
            check(digest(item['path'])==item['sha256'],'REPLAY_OUTPUT_CHANGED')
        return {'status':'ALREADY_BUILT_VERIFIED','manifest':str(receipt)}
    check(not dest.exists(),'PARTIAL_CANDIDATE_REQUIRES_REVIEW')
    base=Path(parent['parent_cache_root'])
    price_root=base/'STOCK_DAILY_RAW_PIT_R1'
    physical=sorted(price_root.glob('year=*/part_*.parquet'))
    check(bool(physical),'NO_CANONICAL_PRICE_PARTITIONS')
    paths=[resolve_cache(parent,'STOCK_DAILY_RAW_PIT_R1',p.relative_to(price_root).as_posix()) for p in physical]
    check(len(paths)==len(set(map(str,paths))),'DUPLICATE_PARTITION_PATH')
    pins={str(manifest):digest(manifest),str(compiler):COMPILER_SHA}
    panels=[]
    for p in paths:
        pins[str(p)]=digest(p)
        data=frame(p,PRICE_COLUMNS)
        check(set(pd.to_datetime(data['date']).dt.year)=={int(p.parent.name.split('=')[1])},'PARTITION_YEAR_MISMATCH')
        panels.append(data)
    full=pd.concat(panels,ignore_index=True)
    latest=pd.to_datetime(full['date']).max()
    check(latest<=parent_asof,'SOURCE_ROWS_AFTER_PINNED_PARENT_ASOF')
    # This job restores local historical consumption. It does not assert latest supplier coverage.
    factors,market=recompute(full,compute,structure)
    fact=factors[pd.to_datetime(factors['date']).dt.year==2026].copy()
    core=market[pd.to_datetime(market['date']).dt.year==2026].copy()
    required={pd.Timestamp('2026-08-31'),pd.Timestamp('2026-09-01')}
    check(required.issubset(set(pd.to_datetime(fact['date']))) and required.issubset(set(pd.to_datetime(core['date']))),'RECOVERED_DATES_NOT_PROPAGATED')
    output={}
    for product,new in [('STOCK_FACTOR_DAILY_R1',fact),('MARKET_STRUCTURE_DAILY_R1',core)]:
        src=resolve_cache(parent,product,'year=2026/part_2026.parquet')
        pins[str(src)]=digest(src)
        schema=pq.ParquetFile(src).schema_arrow.remove_metadata()
        if product=='MARKET_STRUCTURE_DAILY_R1':
            # These five SW fields are outside the original pure market function.
            # Unknowns remain explicit; no stale industry breadth is promoted.
            sw={'sw_l1_n_industries','sw_l1_n_mapped','sw_l1_mapped_positive_ratio',
                'sw_l1_industry_positive_breadth','sw_l1_window'}
            unknown=set(schema.names)-set(new.columns)
            check(unknown<=sw,'UNSUPPORTED_MARKET_SCHEMA:' + ','.join(sorted(unknown-sw)))
            for c in unknown:
                new[c]=None
            new['pit_status']='PARTIAL_CORE_RECOMPUTED_SW_NOT_RECOMPUTED'
            new['known_gaps']='SW_L1_STRUCTURE_NOT_RECOMPUTED; NOT_FULL_PRODUCT_READY'
        check(set(schema.names)<=set(new.columns),'UNSUPPORTED_OUTPUT_SCHEMA')
        path=dest/product/'year=2026'/'part_2026.parquet'
        path.parent.mkdir(parents=True,exist_ok=True)
        table=pa.Table.from_pandas(new[schema.names],schema=schema,preserve_index=False,safe=True)
        pq.write_table(table,path)
        observed=frame(path)
        check(len(observed)==len(new),'OUTPUT_ROW_LOSS')
        output[product]={'path':str(path.resolve()),'sha256':digest(path),'rows':len(new),
            'status':'LOCAL_RECOMPUTED' if product.startswith('STOCK_FACTOR') else 'PARTIAL_CORE_ONLY_SW_UNVERIFIED'}
    for path,sha in pins.items():
        check(digest(path)==sha,'INPUT_CHANGED_DURING_BUILD')
    body=copy.deepcopy(parent)
    body.update(generation=GEN,scope_acceptance='LOCAL_STOCK_DERIVED_RECOMPUTE_NOT_ALL_PRODUCTS_OR_LATEST_UPDATE',
        parent_candidate_manifest=str(manifest.resolve()),local_recompute_input_pins=pins,
        r07_artifacts=list(output.values()),local_source_end=str(latest.date()),
        recursive_state_basis='ENTIRE_STORED_PRICE_PREFIX; NO_YEAR_RESET_OR_250_DAY_EMA_APPROXIMATION')
    for product,item in output.items():
        body['cache_overrides'].setdefault(product,{})['year=2026/part_2026.parquet']=item['path']
    body['artifacts']+=list(output.values())
    body['dirty_derived_products']=['MARKET_STRUCTURE_DAILY_R1: SW_FIELDS_UNVERIFIED']
    body['other_dependencies']='UNRESOLVED_UNTIL_COMPLETE_LAYER_SEARCH; NO_SOURCE_ABSENCE_CLAIM'
    write_json(receipt,body)
    return {'status':'LOCAL_CANDIDATE_RECOMPUTED','manifest':str(receipt),'products':output,
            'FOUNDATION_ACCEPTANCE':False,'network_calls':0}


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--compiler-source',required=True)
    args=ap.parse_args()
    print(json.dumps(build(WORK/'candidate_releases'/'R06'/'R06_TWO_DAY_RECOVERY_20261024'/'CANDIDATE_MANIFEST.json',
        Path(args.compiler_source),WORK/'candidate_releases'/'R07')))
