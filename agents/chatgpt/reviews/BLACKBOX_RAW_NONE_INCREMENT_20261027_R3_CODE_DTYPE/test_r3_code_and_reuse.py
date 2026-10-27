import base64,json,tempfile,unittest,types,sys
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pyarrow.parquet as pq
import numpy as np
import acquire_daily as a
from test_acquire_daily import bars,C,D

def obj(values=None):
    return pd.Series(C if values is None else values,dtype=object,name='code')

class CodeContract(unittest.TestCase):
    def test_explicit_object_python_string(self):
        b=obj();z,proof=a.compare_code_roundtrip(b,b.astype(pd.StringDtype(storage='python')))
        pd.testing.assert_series_equal(b,z);self.assertTrue(proof['values_exact'])
    def test_explicit_object_arrow_string(self):
        b=obj();z,proof=a.compare_code_roundtrip(b,b.astype(pd.StringDtype(storage='pyarrow')))
        pd.testing.assert_series_equal(b,z);self.assertTrue(proof['values_exact'])
    def test_explicit_object_same_dtype(self):
        b=obj();z,proof=a.compare_code_roundtrip(b,b.copy());self.assertIsNone(proof)
    def test_object_real_parquet_roundtrip(self):
        x=bars();x['code']=obj()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.parquet';x.to_parquet(p,index=None)
            proof=a.verify_parquet_roundtrip(x,pd.read_parquet(p))
            self.assertTrue(proof['values_exact'])
    def test_integer_code_rejected(self):
        with self.assertRaisesRegex(a.Blocked,'NON_STR'):a.validate_code_column(obj([1,C[1]]),set(C),'stock')
    def test_bytes_code_rejected(self):
        with self.assertRaisesRegex(a.Blocked,'NON_STR'):a.validate_code_column(obj([b'000001.XSHG',C[1]]),set(C),'stock')
    def test_all_null_kinds_rejected(self):
        for bad in [None,float('nan'),pd.NA]:
            with self.subTest(value=type(bad).__name__),self.assertRaisesRegex(a.Blocked,'CODE_NULL'):
                a.validate_code_column(obj([bad,C[1]]),set(C),'stock')
    def test_null_position_change_rejected(self):
        b=obj();after=b.astype(pd.StringDtype());after.iloc[1]=pd.NA
        with self.assertRaisesRegex(a.Blocked,'CODE_NULL'):a.compare_code_roundtrip(b,after)
    def test_row_order_change_rejected(self):
        b=obj();after=pd.Series(C[::-1],dtype=pd.StringDtype(),name='code')
        with self.assertRaisesRegex(a.Blocked,'VALUE_OR_ORDER'):a.compare_code_roundtrip(b,after)
    def test_identifier_value_change_rejected(self):
        b=obj();after=pd.Series([C[0],'000002.XSHG'],dtype=pd.StringDtype(),name='code')
        with self.assertRaisesRegex(a.Blocked,'VALUE_OR_ORDER'):a.compare_code_roundtrip(b,after)
    def test_index_change_rejected(self):
        b=obj();after=b.astype(pd.StringDtype());after.index=[1,0]
        with self.assertRaises(AssertionError):a.compare_code_roundtrip(b,after)
    def test_namespace_alias_rejected(self):
        with self.assertRaisesRegex(a.Blocked,'NAMESPACE'):a.validate_code_column(obj(['000001.SZ',C[1]]),set(C),'stock')
    def test_unrequested_code_rejected(self):
        with self.assertRaisesRegex(a.Blocked,'NOT_REQUESTED'):a.validate_code_column(obj(),{C[0]},'stock')
    def test_object_to_numeric_rejected(self):
        with self.assertRaises(a.Blocked):a.compare_code_roundtrip(obj(),pd.Series([1,2],name='code'))
    def test_reverse_string_to_object_not_admitted(self):
        with self.assertRaisesRegex(a.Blocked,'DTYPE_CHANGE'):a.compare_code_roundtrip(obj().astype(pd.StringDtype()),obj())
    def test_unrelated_object_column_not_relaxed(self):
        x=bars();x['label']=obj();y=x.copy();y['label']=y.label.astype(pd.StringDtype())
        with self.assertRaisesRegex(a.Blocked,'NON_TIMESTAMP'):a.verify_parquet_roundtrip(x,y)
    def test_retained_actual_batch_end_to_end(self):
        fixture=json.loads(Path(__file__).with_name('retained_batch_fixture.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'retained.parquet';p.write_bytes(base64.b64decode(fixture['content']))
            stored=pd.read_parquet(p);source=stored.copy();source['code']=source.code.astype(object)
            self.assertEqual(p.stat().st_size,15544)
            a.validate_code_column(source.code,set(source.code),'stock')
            # No supplier call, same actual captured80 rows through the new write/read boundary.
            n=Path(d)/'new.parquet';source.to_parquet(n,index=None)
            self.assertTrue(a.verify_parquet_roundtrip(source,pd.read_parquet(n))['values_exact'])
    def test_inherited_spend_cannot_reset_budget(self):
        class Q:
            def get_query_count(self):return {'spare':self.q.pop(0)}
        q=Q();q.q=[200000000,199300000];s=a.Supplier(q,Path('/unused'),inherited=5320);s.quota()
        with self.assertRaisesRegex(a.Blocked,'CEILING'):s.quota()
    def test_reserve_includes_inherited_spend(self):
        class Q:
            def get_query_count(self):return {'spare':200000000}
        with self.assertRaisesRegex(a.Blocked,'RESERVE'):a.Supplier(Q(),Path('/unused'),inherited=660000).call('get_price',{})
    def test_registered_new_file_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);x=root/'x.parquet';pd.DataFrame({'x':[1]}).to_parquet(x)
            record={'path':str(x),'status':'NON_PRICE_SCHEMA','columns':['x']}
            pd.DataFrame({'x':[2]}).to_parquet(root/'new.parquet')
            with patch.object(a,'require_allowed_read'),self.assertRaisesRegex(a.Blocked,'FILE_SET_DRIFT'):
                a.check_registered_freshness([{'records':[record]}])
    def test_registered_existing_price_drift_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);x=root/'x.parquet';pd.DataFrame({'x':[1]}).to_parquet(x)
            record={'path':str(x),'status':'PRICE_TIME_AXIS_READ','bytes':0,'mtime_ns':x.stat().st_mtime_ns}
            with patch.object(a,'require_allowed_read'),self.assertRaisesRegex(a.Blocked,'PRICE_FILE_DRIFT'):
                a.check_registered_freshness([{'records':[record]}])
    def test_registered_new_directory_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);x=root/'x.parquet';pd.DataFrame({'x':[1]}).to_parquet(x);(root/'unknown').mkdir()
            record={'path':str(x),'status':'NON_PRICE_SCHEMA','columns':['x']}
            with patch.object(a,'require_allowed_read'),self.assertRaisesRegex(a.Blocked,'DIRECTORY_SET_UNPROVEN'):
                a.check_registered_freshness([{'records':[record]}])
    def test_retained_input_hash_drift_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);seed=root/'STAGING/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1'
            seed.mkdir(parents=True);(seed/'BASELINE.json').write_text('tampered')
            with self.assertRaisesRegex(a.Blocked,'REUSED_SOURCE_IDENTITY_DRIFT'):
                a.reuse_inputs(root)
    def test_actual_run_reuses_prefix_and_never_refetches_metadata(self):
        # Actual run/Supplier/write/read/quality path; fake SDK and explicit host/baseline stand-ins only.
        from datetime import datetime
        codes=[f'{i:06d}.XSHE' for i in range(81)]
        fake=types.ModuleType('jqdatasdk');fake.__version__='OFFLINE_FAKE';fake.spare=200000000;calls=[]
        def get_price(security,start_date=None,end_date=None,frequency='daily',fields=None,
                      skip_paused=False,fq=None,count=None,panel=False,fill_paused=True):
            calls.append(list(security));fake.spare-=len(security)
            x=pd.DataFrame({'time':pd.Series([pd.Timestamp(start_date)]*len(security),dtype='datetime64[ns]'),
                            'code':pd.Series(security,dtype=object)})
            for f in a.FIELDS:x[f]=0.0 if f=='paused' else 1.0
            return x
        def forbidden(**kwargs):raise AssertionError('metadata unexpectedly fetched')
        fake.get_price=get_price;fake.get_all_securities=forbidden;fake.get_trade_days=forbidden
        fake.get_query_count=lambda:{'spare':fake.spare};fake.set_params=lambda **kwargs:None
        reuse={'plan':{'increment_days':{'stock':['2026-09-28'],'etf':[],'index':[]}},'stock_codes':codes,
               'retained_batch':{'path':'OLD_REFERENCE','sha256':'PINNED','rows':80}}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'new';old=root/'old.parquet';old.write_bytes(b'preserved')
            with patch.dict(sys.modules,{'jqdatasdk':fake}),patch.object(a,'check_execution_location'),\
                 patch.object(a,'pinned',return_value={}),patch.object(a,'reuse_inputs',return_value=reuse),\
                 patch.object(a,'login'),patch.object(a,'now',return_value=datetime(2026,10,27,20,tzinfo=a.CN)):
                self.assertEqual(a.run(root,out),0)
            self.assertEqual(calls,[codes[80:]])
            self.assertEqual(old.read_bytes(),b'preserved')
            r=json.loads((out/'RESULT_R3.json').read_text());self.assertEqual(r['cumulative_quota_spent'],5321)
            self.assertEqual(r['products']['stock']['daily_coverage'][0]['rows'],81)

if __name__=='__main__':unittest.main()
