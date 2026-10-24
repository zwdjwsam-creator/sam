"""Independent receipt controls: actual parquet schema, data and receipt failures."""
import json
from pathlib import Path
import tempfile
import pandas as pd
import numpy as np
from r06_bundle_store import digest, write_json
from r08_receipt_audit import audit, PRICE


def main():
    with tempfile.TemporaryDirectory(prefix='r08_receipt_audit_') as tmp:
        root=Path(tmp); base=root/'parent'
        source=pd.DataFrame({'date':pd.to_datetime(['2026-08-31','2026-09-01','2026-09-01']),
                             'code':['A','A','B'],'open':[1.,2.,np.nan],'high':[1.,2.,np.nan],
                             'low':[1.,2.,np.nan],'close':[1.,2.,np.nan],
                             'volume':[10.,20.,np.nan],'money':[10.,40.,np.nan]})
        rp=base/'STOCK_DAILY_RAW_PIT_R1'/'year=2026'/'part_2026.parquet'; rp.parent.mkdir(parents=True)
        source.to_parquet(rp,index=False)
        f=source.copy(); f['r1']=[np.nan,1.,np.nan]
        f['formula_version']='TEST'; f['price_adj_tag']='RAW_NONE'
        f['pit_status']=['OBSERVED_SEGMENT_NOT_MASTER_ADMITTED']*2+['PRICE_UNOBSERVED_NOT_ZERO_NOT_NO_DATA']
        parent_f=base/'STOCK_FACTOR_DAILY_R1'/'year=2026'/'part_2026.parquet'; parent_f.parent.mkdir(parents=True)
        f.to_parquet(parent_f,index=False)
        market=pd.DataFrame({'date':pd.to_datetime(['2026-08-31','2026-09-01']),'allA_count':[1,1]})
        parent_m=base/'MARKET_STRUCTURE_DAILY_R1'/'year=2026'/'part_2026.parquet'; parent_m.parent.mkdir(parents=True)
        market.to_parquet(parent_m,index=False)
        parent=root/'R06.json'
        write_json(parent,{'generation':'R06_TWO_DAY_RECOVERY_20261024','source_pins':{},
                           'parent_cache_root':str(base),'cache_overrides':{},
                           'inherited_cache_products':['STOCK_DAILY_RAW_PIT_R1','STOCK_FACTOR_DAILY_R1','MARKET_STRUCTURE_DAILY_R1']})
        out=root/'output'; out.mkdir()
        fp=out/'f.parquet'; mp=out/'m.parquet'; ap=out/'audit.parquet'
        f.to_parquet(fp,index=False); market.to_parquet(mp,index=False)
        source[source['close'].isna()][['date','code']].to_parquet(ap,index=False)
        arts=[{'product':product,'path':str(p),'sha256':digest(p),'rows':rows}
              for product,p,rows in [('STOCK_FACTOR_DAILY_R1',fp,3),('MARKET_STRUCTURE_DAILY_R1',mp,2),('UNOBSERVED_GRID_AUDIT',ap,1)]]
        body={'generation':'R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024',
              'parent_candidate_manifest':str(parent),'r08_input_pins':{str(parent):digest(parent),str(rp):digest(rp)},
              'r08_artifacts':arts,'artifacts':arts,'production_publish_allowed':False,'engine_admission_allowed':False,
              'observation_accounting':{'input_rows':3,'observed_rows':2,'unobserved_rows':1}}
        manifest=root/'R08.json'; write_json(manifest,body)
        result=audit(manifest,digest(manifest))
        assert result['status']=='RECONCILED' and result['price_plane_row_conservation_2026']
        assert result['physical_schemas']['STOCK_FACTOR_DAILY_R1']['candidate_column_count']==12
        # A validly rehashed manifest must not conceal damaged same-key values.
        bad=f.copy(); bad.loc[0,'close']=9.; bad.to_parquet(fp,index=False)
        arts[0]['sha256']=digest(fp); write_json(manifest,body)
        result=audit(manifest,digest(manifest))
        assert '2026_price_values_and_keys_exactly_preserved' in result['failed_checks']
        # Likewise, a schema claim is tested against the actual parent and output.
        f.assign(invented=1.).to_parquet(fp,index=False)
        arts[0]['sha256']=digest(fp); write_json(manifest,body)
        assert 'schema_matches_parent:STOCK_FACTOR_DAILY_R1' in audit(manifest,digest(manifest))['failed_checks']
        f.to_parquet(fp,index=False); arts[0]['sha256']=digest(fp)
        body['observation_accounting']['input_rows']=30; write_json(manifest,body)
        assert 'full_prefix_rows_match_accounting' in audit(manifest,digest(manifest))['failed_checks']
        body['observation_accounting']['input_rows']=3; write_json(manifest,body)
        assert 'manifest_matches_reported_sha' in audit(manifest,'0'*64)['failed_checks']
    print(json.dumps({'status':'PASS','controls':6,'scope':'OFFLINE_SYNTHETIC_PHYSICAL_PARQUET',
                      'network_calls':0,'desktop_audited':False}))


if __name__=='__main__':
    main()
