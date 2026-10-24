"""Meaningful end-to-end fixture and process-failure controls for the R06 candidate."""
import json
from pathlib import Path
import tempfile
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from r06_bundle_store import digest, write_json, publish_candidate, read_generation, resolve_cache
from r06_gap_repair import build, map_cache, DATES, PRODUCTS


def frame(day):
    return pd.DataFrame({'time':pd.to_datetime([day,day]), 'code':['A','B'],
        'open':[1.,2.], 'high':[2.,3.], 'low':[.5,1.], 'close':[1.5,2.5],
        'volume':[100.,200.], 'money':[150.,500.], 'factor':[1.,1.],
        'pre_close':[1.,2.], 'paused':[0.,0.], 'high_limit':[3.,4.],
        'low_limit':[.1,.2], 'avg':[1.5,2.5], 'fq':[None,None]})


def fixture(root):
    bb = root/'bb'
    std = bb/'clean_parent'/'standard'
    daily = std/'price'/'stock_ohlcv_daily'
    daily.mkdir(parents=True)
    rawroot=bb/'raw'
    rawroot.mkdir()
    raw_inputs, sidecars={},{}
    for day in DATES:
        path=rawroot/(day+'.parquet')
        raw=frame(day)
        raw.to_parquet(path,index=False)
        rel='price/stock_ohlcv_daily/'+day+'.parquet'
        side=path.with_suffix('.sidecar.json')
        write_json(side,{'clean_rel':rel,'file_sha256':digest(path)})
        raw_inputs[day]={'path':str(path),'sha256':digest(path),'rows':2,
            'null_counts':{c:0 for c in raw.columns if c not in ('time','code','fq')}}
        sidecars[day]={'sidecar_path':str(side),'sidecar_sha256':digest(side),'declared_clean_rel':rel}
    adjacent=rawroot/'control.parquet'
    frame('2026-09-02').to_parquet(adjacent,index=False)
    (daily/adjacent.name).write_bytes(adjacent.read_bytes())
    frame('2026-09-03').to_parquet(daily/'next.parquet',index=False)
    cache=bb/'cache_parent'
    cache.mkdir()
    (cache/'FUND_NAV_PIT_R1').mkdir()
    (cache/'FUND_NAV_PIT_R1'/'UNTOUCHED.txt').write_text('preserve-exactly')
    # Both price schema variants come from existing compiler tag functions.
    base=frame('2026-09-02').rename(columns={'time':'date'})
    for key in ('signal_date','data_date'):
        base[key]=base['date']
    base['asset_type']='STOCK'
    base['price_adj_tag']='RAW_NONE'
    base['asof_rule']='SAME_DAY_KNOWN_EOD'
    base['pit_status']='OK'
    base['source_version']='PARENT'
    base['known_at']=pd.NaT
    for prod in PRODUCTS:
        if prod=='STOCK_DAILY_RAW_PIT_R1':
            base['known_at']=base['date']+pd.Timedelta(hours=15)
        schema=pa.Table.from_pandas(base,preserve_index=False).schema.remove_metadata()
        old=pd.concat([map_cache(frame(d),prod,schema,'PARENT') for d in ['2026-09-02','2026-09-03']],ignore_index=True)
        p=cache/prod/'year=2026'/'part_2026.parquet'
        p.parent.mkdir(parents=True)
        pq.write_table(pa.Table.from_pandas(old,schema=schema,preserve_index=False),p)
    write_json(bb/'数据'/'清洗成品'/'CURRENT_CLEANING_RELEASE.json',{'release_id':'CLEAN','standard_root':str(std)})
    write_json(bb/'数据'/'回测缓存'/'CURRENT_CACHE_RELEASE.json',{'cache_release_id':'CACHE','source_cleaning_release':'CLEAN','release_root':str(cache)})
    gap={'raw_inputs':raw_inputs,'raw_sidecar_provenance':sidecars,
         'adjacent_unit_mapping_proof':{'raw_path':str(adjacent),'raw_sha256':digest(adjacent),'clean_path':str(daily/adjacent.name)}}
    return bb,gap


def main():
    with tempfile.TemporaryDirectory(prefix='blackbox_r06_fixture_') as temp:
        root=Path(temp)
        bb,gap=fixture(root)
        store=root/'candidate'
        registry=root/'registry.json'
        standard=json.loads((bb/'数据'/'清洗成品'/'CURRENT_CLEANING_RELEASE.json').read_text())['standard_root']
        write_json(registry,{'datasets':[{'dataset_id':'PRICE_STOCK_DAILY','layers':{'CLEAN':{'root':str(Path(standard)/'price'/'stock_ohlcv_daily')}}},
                                       {'dataset_id':'UNCHANGED_REFERENCE','layers':{}}]})
        registry_hash=digest(registry)
        inputs={str(p):digest(p) for p in bb.rglob('*') if p.is_file()}
        result=build(gap,bb,store,live=False,registry_path=registry)
        assert result['status']=='CANDIDATE_BUILT'
        manifest=Path(result['manifest'])
        body=json.loads(manifest.read_text())
        assert body['parent_daily_count']==2 and body['candidate_daily_count']==4
        assert digest(registry)==registry_hash
        new_registry=json.loads(Path(body['candidate_registry_path']).read_text())
        assert new_registry['datasets'][0]['layers']['CLEAN']['root']==body['cleaning_daily_root']
        assert new_registry['datasets'][1]['dataset_id']=='UNCHANGED_REFERENCE'
        assert set(body['inherited_cache_products'])==set(PRODUCTS+['FUND_NAV_PIT_R1'])
        for prod in PRODUCTS:
            assert body['cache_results'][prod]['candidate_rows']==8
            assert body['cache_results'][prod]['all_non_target_rows_preserved']
            path=resolve_cache(body,prod,'year=2026/part_2026.parquet')
            assert len(pd.read_parquet(path))==8
        assert resolve_cache(body,'FUND_NAV_PIT_R1','UNTOUCHED.txt').read_text()=='preserve-exactly'
        assert build(gap,bb,store,live=False)['status']=='ALREADY_BUILT_VERIFIED'
        assert all(digest(p)==h for p,h in inputs.items())
        # A failed publication exposes no partial generation.
        try:
            publish_candidate(store,manifest,None,fault='before_commit')
        except RuntimeError:
            pass
        assert not (store/'CANDIDATE_CURRENT.json').exists()
        try:
            publish_candidate(store,manifest,None,fault='after_commit')
        except RuntimeError:
            pass
        assert read_generation(store)['generation']==body['generation']
        assert publish_candidate(store,manifest,None)=='ALREADY_CURRENT'
        second=store/'SECOND'/'CANDIDATE_MANIFEST.json'
        next_body={**body,'generation':'SECOND'}
        write_json(second,next_body)
        previous=digest(store/'CANDIDATE_CURRENT.json')
        try:
            publish_candidate(store,second,None)
        except ValueError as exc:
            assert str(exc)=='STALE_CANDIDATE_PARENT'
        else:
            raise AssertionError('STALE_PARENT_ACCEPTED')
        assert digest(store/'CANDIDATE_CURRENT.json')==previous
        assert publish_candidate(store,second,previous)=='COMMITTED_CANDIDATE_ONLY'
        assert read_generation(store)['generation']=='SECOND'
        # Candidate corruption fails rather than being treated as idempotent success.
        Path(body['artifacts'][0]['path']).write_bytes(b'corruption')
        # Artifact is a hardlink to a fixture RAW, never real business data.
        try:
            build(gap,bb,store,live=False)
        except ValueError:
            pass
        else:
            raise AssertionError('CHANGED_SOURCE_OR_OUTPUT_ACCEPTED')
    print(json.dumps({'status':'PASS','scope':'end-to-end synthetic Arrow/parquet and candidate publication fixtures',
        'checks':['two-day clean and cache recovery','all parent daily files retained','other product retained',
                  'all non-target rows unchanged','candidate registry binding','idempotent replay','original inputs unchanged before injected corruption',
                  'before-commit failure','after-commit complete generation','stale parent rejected','corruption rejected'],
        'production_publish_tested':False}))


if __name__=='__main__':
    main()
