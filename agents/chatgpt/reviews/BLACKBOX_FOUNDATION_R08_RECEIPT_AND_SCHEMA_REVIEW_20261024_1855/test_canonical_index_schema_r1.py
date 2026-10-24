"""Reproduce old canonical-code skip without importing production compiler."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Optional
import numpy as np
import pandas as pd
from canonical_index_schema_r1 import normalize_canonical_index


def main(compiler):
    source=Path(compiler).read_bytes()
    assert hashlib.sha256(source).hexdigest()=='c8ddf805a6ddc998cda507f2aa5c92f27b13a43b5445e5bfed21477c5822f336'
    nodes=[n for n in ast.parse(source.decode('utf-8-sig')).body if isinstance(n,ast.FunctionDef) and n.name=='read_price_frame']
    assert len(nodes)==1
    ns={'Path':Path,'Optional':Optional,'pd':pd,'log':lambda _:None}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'original_read_price_frame','exec'),ns)
    original=pd.DataFrame({'canonical_index_id':['CSI2000','CSI2000'],'canonical_code':['399303.XSHE']*2,
                           'provider_native_code':['399303.XSHE']*2,
                           'trade_date':pd.to_datetime(['2026-01-05','2026-01-06']),
                           'open':[np.nan,2000.],'high':[np.nan,2010.],'low':[np.nan,1990.],
                           'close':[np.nan,2005.],'pre_close':[np.nan,2000.],
                           'volume':[np.nan,100.],'amount':[np.nan,200500.],
                           'price_variant':['PRICE_INDEX']*2,'return_variant':['PRICE']*2,
                           'source_fq':['NOT_APPLICABLE']*2,'source_provider':['original_provider']*2})
    before=original.copy(deep=True)
    with tempfile.TemporaryDirectory(prefix='canonical_index_schema_') as tmp:
        path=Path(tmp)/'canonical.parquet'; original.to_parquet(path,index=False)
        legacy=ns['read_price_frame']([path])
        assert legacy.empty
        fixed=normalize_canonical_index(pd.read_parquet(path))
        assert len(fixed)==2 and fixed['close'].notna().sum()==1
        assert fixed.loc[1,'code']=='399303.XSHE' and fixed.loc[1,'money']==200500.
        assert fixed.loc[0,['open','high','low','close','pre_close','volume','money']].isna().all()
        pd.testing.assert_series_equal(fixed['source_provider'],original['source_provider'])
        assert 'known_at' not in fixed and 'pit_status' not in fixed
    pd.testing.assert_frame_equal(original,before)
    bad=original.copy(); bad['trade_date']=[0,1]
    try:
        normalize_canonical_index(bad)
    except ValueError as e:
        assert str(e)=='ORDINAL_NOT_A_TRADE_DATE'
    else:
        raise AssertionError('ORDINAL_ACCEPTED')
    try:
        normalize_canonical_index(pd.concat([original,original.iloc[[0]]]))
    except ValueError as e:
        assert str(e).startswith('DUPLICATE_CANONICAL_KEYS')
    else:
        raise AssertionError('DUPLICATE_ACCEPTED')
    bad=original.copy(); bad['source_fq']='pre'
    try:
        normalize_canonical_index(bad)
    except ValueError as e:
        assert str(e).startswith('UNSUPPORTED_PRICE_SEMANTICS')
    else:
        raise AssertionError('SEMANTIC_MISMATCH_ACCEPTED')
    print(json.dumps({'status':'PASS','controls':9,'legacy_canonical_rows_returned':0,
                      'successor_rows_preserved':2,'scope':'OFFLINE_SYNTHETIC_NOT_PRODUCTION_INTEGRATION',
                      'production_compiler_imported':False,'network_calls':0}))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
