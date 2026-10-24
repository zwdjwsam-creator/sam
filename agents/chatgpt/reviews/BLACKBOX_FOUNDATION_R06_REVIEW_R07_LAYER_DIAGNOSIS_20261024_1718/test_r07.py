"""Offline behavioral controls; no live BLACKBOX data or remote supplier use."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from r07_claim_guard import decide,assert_download_allowed
from r07_rebuild_local import functions,recompute,build,GEN
from r06_bundle_store import write_json,digest


def test_claims():
    assert decide({'scope':'one cache window','cache_rows':0})['classification']=='UNKNOWN_STOP'
    found={'scope':'two exact days','source_rows_found':100,'raw_scope_complete':True,'clean_serves_request':False}
    assert decide(found)['classification']=='RAW_COMPLETE_CLEANING_MISSING'
    assert not decide(found)['SOURCE_ABSENCE_CLAIM_ALLOWED']
    assert decide({'source_file_hash_verified':True,'clean_scope_complete':True,'cache_serves_request':False})['classification']=='CLEANING_COMPLETE_CACHE_MISSING'
    assert not decide({'r9_content_verified_for_entity':True})['MIGRATION_LOSS_PROVEN']
    purported={'existing_diagnoser':{'classification':'SOURCE_MISSING','completed':True,'receipt_path':'invented','receipt_sha256':'invented'}}
    assert not decide(purported)['SOURCE_ABSENCE_CLAIM_ALLOWED']
    try:
        assert_download_allowed(found)
    except ValueError:
        pass
    else:
        raise AssertionError('DOWNLOAD_ALLOWED_FOR_EXISTING_SOURCE')


def sample():
    dates=pd.bdate_range('2025-01-02','2026-09-24')
    parts=[]
    for i,code in enumerate(['A','B']):
        n=len(dates)
        close=np.arange(n,dtype=float)+10+i
        parts.append(pd.DataFrame({'date':dates,'code':code,'open':close-.1,'high':close+.2,
            'low':close-.2,'close':close,'volume':np.arange(n,dtype=float)+100.,'money':close*100.}))
    return pd.concat(parts,ignore_index=True)


def main(compiler):
    test_claims()
    compute,structure=functions(compiler)
    panel=sample()
    factors,market=recompute(panel,compute,structure)
    code=factors[factors['code']=='A'].sort_values('date')
    assert np.isclose(code['r1'].iloc[-1],code['close'].iloc[-1]/code['close'].iloc[-2]-1)
    assert np.isclose(code['ma250'].iloc[-1],code['close'].tail(250).mean())
    assert np.isclose(code['ema12'].iloc[-1],code['close'].ewm(span=12,adjust=False).mean().iloc[-1])
    old_panel=panel[~panel['date'].isin(pd.to_datetime(['2026-08-31','2026-09-01']))]
    old_f,_=recompute(old_panel,compute,structure)
    before=pd.Timestamp('2026-08-31')
    pd.testing.assert_frame_equal(factors[factors['date']<before].reset_index(drop=True),old_f[old_f['date']<before].reset_index(drop=True))
    a=old_f[(old_f['code']=='A')&(old_f['date']==pd.Timestamp('2026-09-02'))]['r1'].iloc[0]
    b=factors[(factors['code']=='A')&(factors['date']==pd.Timestamp('2026-09-02'))]['r1'].iloc[0]
    assert not np.isclose(a,b)
    try:
        recompute(pd.concat([panel,panel.iloc[[0]]]),compute,structure)
    except ValueError:
        pass
    else:
        raise AssertionError('CONFLICTING_OR_DUPLICATE_INPUT_ACCEPTED')
    with tempfile.TemporaryDirectory(prefix='r07_offline_') as tmp:
        root=Path(tmp)
        base=root/'parent'
        price=base/'STOCK_DAILY_RAW_PIT_R1'
        for y,g in panel.groupby(panel['date'].dt.year):
            p=price/f'year={y}'/f'part_{y}.parquet'
            p.parent.mkdir(parents=True)
            g.to_parquet(p,index=False)
        factor_path=base/'STOCK_FACTOR_DAILY_R1'/'year=2026'/'part_2026.parquet'
        factor_path.parent.mkdir(parents=True)
        old_f[old_f['date'].dt.year==2026].to_parquet(factor_path,index=False)
        market_path=base/'MARKET_STRUCTURE_DAILY_R1'/'year=2026'/'part_2026.parquet'
        market_path.parent.mkdir(parents=True)
        parent_market=market[market['date'].dt.year==2026].copy()
        for c in ['sw_l1_n_industries','sw_l1_n_mapped','sw_l1_mapped_positive_ratio','sw_l1_industry_positive_breadth']:
            parent_market[c]=np.nan
        parent_market['sw_l1_window']='OLD_UNKNOWN'
        parent_market.to_parquet(market_path,index=False)
        manifest=root/'R06.json'
        cache_pointer=root/'CURRENT_CACHE_RELEASE.json'
        write_json(cache_pointer,{'asof':'2026-09-24'})
        body={'generation':'R06_TWO_DAY_RECOVERY_20261024','build_validated':True,'candidate_only':True,
              'artifacts':[],'source_pins':{str(cache_pointer):digest(cache_pointer)},'parent_cache_root':str(base),'cache_overrides':{},
              'inherited_cache_products':['STOCK_DAILY_RAW_PIT_R1','STOCK_FACTOR_DAILY_R1','MARKET_STRUCTURE_DAILY_R1']}
        write_json(manifest,body)
        inputs={str(p):digest(p) for p in base.rglob('*.parquet')}
        result=build(manifest,compiler,root/'store')
        assert result['status']=='LOCAL_CANDIDATE_RECOMPUTED'
        child=json.loads(Path(result['manifest']).read_text(encoding='utf-8'))
        assert child['generation']==GEN
        new_market=pd.read_parquet(child['cache_overrides']['MARKET_STRUCTURE_DAILY_R1']['year=2026/part_2026.parquet'])
        assert new_market['sw_l1_n_mapped'].isna().all()
        assert new_market['pit_status'].eq('PARTIAL_CORE_RECOMPUTED_SW_NOT_RECOMPUTED').all()
        assert build(manifest,compiler,root/'store')['status']=='ALREADY_BUILT_VERIFIED'
        assert all(digest(p)==h for p,h in inputs.items())
    print(json.dumps({'status':'PASS','scope':'offline synthetic full-prefix formulas, candidate files and absence-claim guard',
        'controls':['cache miss not source absence','RAW presence blocks redownload','CLEAN/CACHE distinction',
                    'R9 historical success not migration-loss proof','unreviewed absence receipt blocked',
                    'r1 arithmetic','250-session rolling arithmetic','recursive EMA prefix','past values unchanged',
                    'later returns change after restored sessions','duplicate keys rejected','candidate file build',
                    'SW unknowns remain explicitly partial','idempotent replay','parent files unchanged'],
        'network_calls':0,'source_absence_claims_authorized':0}))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
