"""Offline controls using real Arrow files and original hash-pinned formulas."""
import json
from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
from r06_bundle_store import write_json, digest
from r07_rebuild_local import functions, frame
from r08_rebuild_local import observed_recompute, build, diagnose_two_days, GEN, FORMULA
from r08_coverage_gate import normalize_dates, compare, diagnose_observed_layers, require_union_members, MISSING_ENUM


def rejected(fn, prefix):
    try:
        fn()
    except ValueError as exc:
        assert str(exc).startswith(prefix), str(exc)
    else:
        raise AssertionError('UNEXPECTED_ACCEPTANCE:' + prefix)


def main(compiler):
    compute, structure = functions(compiler)
    dates = pd.bdate_range('2025-01-02','2026-09-24')
    chunks=[]
    for i,code in enumerate(['A','B','C']):
        close=np.arange(len(dates),dtype=float)+10+i
        chunks.append(pd.DataFrame({'date':dates,'code':code,'open':close,'high':close+1,
                                   'low':close-1,'close':close,'volume':100.,'money':close*100}))
    source=pd.concat(chunks,ignore_index=True)
    ohlcvm=['open','high','low','close','volume','money']
    # A leading null grid, an internal unknown interval and an all-null code.
    source.loc[(source['code']=='B') & (source['date']<pd.Timestamp('2025-02-01')),ohlcvm]=np.nan
    source.loc[(source['code']=='A') & source['date'].between('2026-06-01','2026-06-05'),ohlcvm]=np.nan
    source.loc[source['code']=='C',ohlcvm]=np.nan
    original=source.copy(deep=True)
    factors,market,audit,stats=observed_recompute(source,compute,structure)
    assert len(factors)==len(source) and stats['input_rows']==stats['observed_rows']+stats['unobserved_rows']
    pd.testing.assert_frame_equal(source,original)
    assert factors[factors['code']=='C'].drop(columns=['date','code','formula_version','price_adj_tag','pit_status']).isna().all().all()
    assert not factors['close'].eq(0).any()
    after=factors[(factors['code']=='A') & (factors['date']==pd.Timestamp('2026-06-08'))].iloc[0]
    assert pd.isna(after['r1']) and after['ema12']==after['close'] and pd.isna(after['ma250'])
    end=factors[(factors['code']=='B') & (factors['date']==dates[-1])].iloc[0]
    vals=source[(source['code']=='B') & source['close'].notna()]['close']
    assert np.isclose(end['ema12'], vals.ewm(span=12,adjust=False).mean().iloc[-1])
    assert factors['formula_version'].eq(FORMULA).all()
    assert market['allA_count'].max()==2
    short=source[source['date']<'2026-08-01']
    past,_,_,_=observed_recompute(short,compute,structure)
    pd.testing.assert_frame_equal(past.reset_index(drop=True), factors[factors['date']<'2026-08-01'].reset_index(drop=True))
    partial=source.copy()
    partial.loc[0,'close']=np.nan
    rejected(lambda: observed_recompute(partial,compute,structure), 'PARTIAL_PRICE_OBSERVATION')
    rejected(lambda: observed_recompute(pd.concat([source,source.iloc[[0]]]),compute,structure), 'DUPLICATE_KEYS')
    rejected(lambda: normalize_dates(pd.Series([0,1,2])), 'NUMERIC_DATE_AXIS')
    # Exact date sets are insufficient when a symbol disappears on the same date.
    tiny=source[(source['code'].isin(['A','B'])) & (source['date']==dates[-1])]
    assert not compare(tiny,tiny.iloc[:1])['coverage_non_regression_pass']
    hollow=tiny.copy(); hollow.loc[hollow.index[0],'close']=np.nan
    assert not compare(tiny,hollow)['coverage_non_regression_pass']
    assert compare(tiny,tiny)['coverage_non_regression_pass']
    assert compare(tiny,tiny)['PUBLISH_ALLOWED'] is False
    diagnosed=diagnose_observed_layers({'RAW':tiny,'CLEAN':tiny,'CACHE':tiny.iloc[:0]},tiny[['date','code']])
    assert diagnosed['root_cause']=='CLEANING_COMPLETE_CACHE_MISSING' and not diagnosed['DOWNLOAD_REQUIRED']
    assert diagnosed['root_cause'] in MISSING_ENUM
    unknown=diagnose_observed_layers({'RAW':tiny.iloc[:0]},tiny[['date','code']])
    assert unknown['root_cause']=='UNKNOWN_STOP' and not unknown['SOURCE_ABSENCE_CLAIM_ALLOWED']
    rejected(lambda: require_union_members({'ETF':tiny,'FUND':tiny.iloc[:0]},['ETF','FUND']), 'CACHE_PRODUCT_UNAVAILABLE')
    with tempfile.TemporaryDirectory(prefix='r08_offline_') as tmp:
        root=Path(tmp); parent=root/'parent'; price=parent/'STOCK_DAILY_RAW_PIT_R1'
        for year,g in source.groupby(source['date'].dt.year):
            out=price/f'year={year}'/f'part_{year}.parquet'; out.parent.mkdir(parents=True)
            g.to_parquet(out,index=False)
        oldf=factors[(factors['date'].dt.year==2026)&~factors['date'].isin(pd.to_datetime(['2026-08-31','2026-09-01']))]
        fp=parent/'STOCK_FACTOR_DAILY_R1'/'year=2026'/'part_2026.parquet'; fp.parent.mkdir(parents=True)
        oldf.to_parquet(fp,index=False)
        mp=parent/'MARKET_STRUCTURE_DAILY_R1'/'year=2026'/'part_2026.parquet'; mp.parent.mkdir(parents=True)
        oldm=market[(market['date'].dt.year==2026)&~market['date'].isin(pd.to_datetime(['2026-08-31','2026-09-01']))].copy()
        for col in ['sw_l1_n_industries','sw_l1_n_mapped','sw_l1_mapped_positive_ratio','sw_l1_industry_positive_breadth']:
            oldm[col]=np.nan
        oldm['sw_l1_window']='UNVERIFIED'; oldm.to_parquet(mp,index=False)
        ptr=root/'CURRENT_CACHE_RELEASE.json'; write_json(ptr,{'asof':'2026-09-24'})
        manifest=root/'R06.json'
        write_json(manifest,{'generation':'R06_TWO_DAY_RECOVERY_20261024','build_validated':True,'candidate_only':True,
                           'artifacts':[],'source_pins':{str(ptr):digest(ptr)},'parent_cache_root':str(parent),
                           'cache_overrides':{},'inherited_cache_products':['STOCK_DAILY_RAW_PIT_R1','STOCK_FACTOR_DAILY_R1','MARKET_STRUCTURE_DAILY_R1']})
        calendar=root/'calendar.parquet'; pd.DataFrame({'trade_date':dates}).to_parquet(calendar,index=False)
        inputs={str(p):digest(p) for p in parent.rglob('*.parquet')}
        result=build(manifest,compiler,root/'store',calendar,live=False)
        assert result['status']=='CANDIDATE_BUILT_WITH_EXPLICIT_UNOBSERVED_ROWS'
        body=json.loads(Path(result['manifest']).read_text(encoding='utf-8'))
        assert body['generation']==GEN and not body['engine_admission_allowed']
        new=frame(body['cache_overrides']['STOCK_FACTOR_DAILY_R1']['year=2026/part_2026.parquet'])
        assert len(new)==len(source[source['date'].dt.year==2026])
        assert len(frame(body['r08_artifacts'][2]['path']))==stats['unobserved_rows']
        assert build(manifest,compiler,root/'store',calendar,live=False)['status']=='ALREADY_BUILT_VERIFIED'
        assert all(digest(p)==sha for p,sha in inputs.items())
        artifact=Path(body['r08_artifacts'][0]['path']); saved=artifact.read_bytes(); artifact.write_bytes(saved+b'x')
        rejected(lambda: build(manifest,compiler,root/'store',calendar,live=False), 'REPLAY_OUTPUT_CHANGED')
        artifact.write_bytes(saved)
        dp={'source_pins':{},'artifacts':[],'parent_cache_root':str(root/'old_cache'),'cache_overrides':{}}
        raw_hashes={}
        two=[]
        for day in ['2026-08-31','2026-09-01']:
            raw=tiny.copy(); raw['date']=pd.Timestamp(day)
            raw=raw.rename(columns={'date':'time'})[['time','code','close']]
            rp=root/('raw_'+day+'.parquet'); cp=root/('clean_'+day+'.parquet')
            raw.to_parquet(rp,index=False); cp.write_bytes(rp.read_bytes())
            sha=digest(rp); raw_hashes[day]=sha
            dp['source_pins'][str(rp)]=sha
            dp['artifacts'].append({'path':str(cp),'sha256':sha})
            two.append(raw.rename(columns={'time':'date'}))
        both=pd.concat(two,ignore_index=True)
        for product in ['STOCK_DAILY_PIT_R1','STOCK_DAILY_RAW_PIT_R1']:
            old=root/'old_cache'/product/'year=2026'/'part_2026.parquet'; old.parent.mkdir(parents=True)
            both.iloc[:0].to_parquet(old,index=False)
            new=root/(product+'.parquet'); both.to_parquet(new,index=False)
            dp['cache_overrides'][product]={'year=2026/part_2026.parquet':str(new)}
        diagnosis=diagnose_two_days(dp,raw_hashes)
        for body in diagnosis.values():
            assert body['published']['root_cause']=='CLEANING_COMPLETE_CACHE_MISSING'
            assert body['candidate']['diagnosis_status']=='AVAILABLE_FOR_EXACT_REQUEST'
            assert body['all_two_day_close_values_equal_raw']
        bad=both.copy(); bad.loc[0,'close']+=1
        bad.to_parquet(new,index=False)
        try:
            diagnose_two_days(dp,raw_hashes)
        except AssertionError:
            pass
        else:
            raise AssertionError('CANDIDATE_CLOSE_DRIFT_ACCEPTED')
    controls=['price/grid conservation','source input unchanged','all-null rows preserved without factors or zero fills',
              'internal gap resets recursive and rolling state','full observed prefix EMA arithmetic',
              'explicit semantic formula version','observed-only market count','future append cannot rewrite earlier results',
              'partial quote rejected','duplicate keys rejected','ordinal date rejected',
              'same-date symbol loss rejected','same-key valued field loss rejected','bounded success cannot authorize publication',
              'RAW presence classifies cache miss without download','unproven empty source remains unknown',
              'empty union member rejected','actual candidate parquet and audit build','candidate replay',
              'parent byte conservation','tampered candidate replay rejected',
              'actual RAW/CLEAN/CACHE two-day diagnosis','same-key close value drift rejected']
    print(json.dumps({'status':'PASS','controls':controls,'controls_passed':len(controls),'network_calls':0,
                      'scope':'OFFLINE_SYNTHETIC_ONLY; NOT_DESKTOP_REBUILD_OR_MASTER_ADMISSION'}))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
