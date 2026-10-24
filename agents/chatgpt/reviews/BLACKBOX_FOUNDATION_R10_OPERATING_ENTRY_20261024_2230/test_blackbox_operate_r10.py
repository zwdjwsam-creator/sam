"""Real Arrow fixtures and original import-child guards; no production execution."""
import copy
import json
from pathlib import Path
import tempfile
import pandas as pd
from blackbox_operate_r10 import catalogue,canonical_pin,price_query,digest,load
from engine_import_probe_r10 import launch


def reject(fn,reason):
    try:fn()
    except ValueError as e:assert reason in str(e),str(e)
    else:raise AssertionError('UNEXPECTED_PASS:'+reason)


def main():
    controls=[]
    def ok(name):controls.append(name)
    a={'rows':[{'product_id':'P','operating_state':'CURRENT_SERVES_MEASURED_WINDOW'}]}
    b={'products':[{'product_id':'P'}],'registry_sources':{},'field_ownership':{}}
    c={'bindings':[{'required_cache_product':['P'],'dataset':'D'}],'target_date_rule':{'supplier_lag':'UNKNOWN'}}
    d={'rows':[{'dataset_id':'D','source_id':'JQ_FIXTURE'}]}
    cat=catalogue(a,b,c,d)
    assert cat['products'][0]['serving_authority']=='REQUEST_NOT_EVALUATED' and not cat['FOUNDATION_ACCEPTANCE'];ok('catalogue presence and stale PASS labels do not admit data')
    assert cat['products'][0]['source_domains']==d['rows'];ok('updater/source join uses explicit product ids')
    empty=catalogue(a,b,{'bindings':[],'target_date_rule':{}},d)
    assert empty['products'][0]['update_binding_status']=='UNBOUND_IN_THIS_EVIDENCE_JOIN';ok('unknown updater stays unbound')
    reject(lambda:catalogue({'rows':a['rows']*2},b,c,d),'DUPLICATE_OR_EMPTY');ok('duplicate catalogue ids rejected')
    reject(lambda:catalogue(a,{'products':[]},c,d),'ENTITY_MISMATCH');ok('catalogue/schema entity mismatch rejected')
    assert canonical_pin({'a':1,'b':2})==canonical_pin({'b':2,'a':1});ok('semantic evidence pin independent of JSON layout')
    with tempfile.TemporaryDirectory(prefix='r10_fixture_') as td:
        root=Path(td);cal=root/'calendar.parquet'
        days=pd.to_datetime(['2026-08-28','2026-08-31','2026-09-01','2026-09-02'])
        pd.DataFrame({'trade_date':days}).to_parquet(cal,index=False)
        ptrs=[root/'CURRENT_CACHE_RELEASE.json',root/'CURRENT_CLEANING_RELEASE.json']
        for p in ptrs:p.write_bytes(b'{}')
        path=root/'price.parquet'
        data=pd.DataFrame({'date':days,'code':['000001.XSHE']*4,'close':[10.,11.,12.,13.]})
        data.to_parquet(path,index=False)
        body={'generation':'R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024','source_pins':{str(p):digest(p) for p in ptrs},
              'calendar_binding':{'path':str(cal),'sha256':digest(cal),'date_field':'trade_date'},
              'cache_overrides':{'STOCK_DAILY_RAW_PIT_R1':{'year=2026/part_2026.parquet':str(path)}},
              'artifacts':[{'path':str(path),'sha256':digest(path)}],'r08_input_pins':{}}
        query=lambda x=body:price_query(x,['000001.XSHE'],'2026-08-28','2026-09-02',['close'])
        out=query();assert out['receipt']['returned_keys']==4 and not out['ORDER_ALLOWED'];ok('actual Parquet observations served with exact key receipt')
        assert not out['SOURCE_ABSENCE_CLAIM_ALLOWED'] and out['engine_admission']=='NOT_ADMITTED';ok('diagnostic read cannot upgrade absence or engine admission')
        reject(lambda:price_query(body,['000001.XSHE'],'2026-10-01','2026-10-02',['close']),'OUTSIDE_PINNED_CALENDAR');ok('newer request rejects stale calendar')
        reject(lambda:price_query(body,['000001.XSHE'],'2026-08-28','2026-09-02',['factor']),'UNSUPPORTED_FIELD');ok('unbound fields rejected')
        reject(lambda:price_query(body,['000001'],'2026-08-28','2026-09-02',['close']),'CANONICAL_CODE');ok('code alias not guessed')
        ptrs[0].write_bytes(b'{"changed":1}');reject(query,'PINNED_PARENT');ptrs[0].write_bytes(b'{}');ok('changed CURRENT parent rejected')
        for label,frame,reason in [('missing',data.iloc[:3],'REQUEST_KEYS_NOT_COMPLETE'),
                                    ('duplicate',pd.concat([data,data.iloc[:1]]),'REVISION_CONFLICT'),
                                    ('null',data.assign(close=[10.,None,12.,13.]),'REQUEST_FIELD_UNOBSERVED'),
                                    ('zero',data.assign(close=[0.,11.,12.,13.]),'INVALID_PRICE_OBSERVATION'),
                                    ('ordinal',data.assign(date=[0,1,2,3]),'NUMERIC_PRICE_AXIS')]:
            frame.to_parquet(path,index=False);modified=copy.deepcopy(body);modified['artifacts'][0]['sha256']=digest(path)
            reject(lambda:query(modified),reason);ok(label+' data rejected at the real read boundary')
        p=root/'duplicate.json';p.write_bytes(b'{"a":1,"a":2}');reject(lambda:load(p),'DUPLICATE_JSON_KEY');ok('duplicate evidence keys rejected')
        # Import a synthetic package through the same guarded child as desktop.
        pkg=root/'engine'
        paths={'bullet_trade/core/engine.py':'class BacktestEngine:pass\n',
               'bullet_trade/data/api.py':'def get_price():return None\n',
               'bullet_trade/data/providers/base.py':'class DataProvider:pass\n'}
        for name,text in paths.items():
            p=pkg/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode())
        def pins():return {name:digest(pkg/name) for name in paths}
        out=launch(pkg,pins());assert out['status']=='MODULES_IMPORTED_NO_ENGINE_CONSTRUCTED' and not out['engine_constructed'];ok('actual child imports without constructing engine')
        (pkg/'bullet_trade/core/engine.py').write_bytes(b"open('forbidden-r10','w')\n")
        out=launch(pkg,pins());assert out['status']=='IMPORT_NOT_READY' and 'file_write' in out['blocked_events'];ok('engine import file write rejected')
        (pkg/'bullet_trade/core/engine.py').write_bytes(b"import socket\nsocket.getaddrinfo('example.test',443)\n")
        out=launch(pkg,pins());assert out['status']=='IMPORT_NOT_READY' and 'socket.getaddrinfo' in out['blocked_events'];ok('engine import network rejected')
        (pkg/'bullet_trade/core/engine.py').write_bytes(b"try:\n open('forbidden-r10','w')\nexcept PermissionError:pass\nclass BacktestEngine:pass\n")
        out=launch(pkg,pins());assert out['status']=='IMPORT_ATTEMPTED_FORBIDDEN_SIDE_EFFECT';ok('caught side effect still prevents clean import claim')
        (pkg/'bullet_trade/core/engine.py').write_bytes(b"def auth():pass\nauth()\n")
        out=launch(pkg,pins());assert out['status']=='IMPORT_NOT_READY' and any(':auth' in e for e in out['blocked_events']);ok('transitive engine authentication call denied before body')
        (pkg/'bullet_trade/core/engine.py').write_bytes(b"class BacktestEngine:\n def __init__(self):pass\nBacktestEngine()\n")
        out=launch(pkg,pins());assert out['status']=='IMPORT_NOT_READY' and any(':__init__' in e for e in out['blocked_events']);ok('import-time engine construction denied before body')
    print(json.dumps({'status':'PASS','controls_passed':len(controls),'controls':controls,'scope':'OFFLINE_SYNTHETIC_ONLY','FOUNDATION_ACCEPTANCE':False},ensure_ascii=True))


if __name__=='__main__':main()
