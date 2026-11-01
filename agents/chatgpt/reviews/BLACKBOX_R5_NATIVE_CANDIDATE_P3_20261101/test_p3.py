"""Native-portable fixtures. Never read native E: originals or invoke a supplier."""
import copy,io,json,os,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import candidate_adapter as c
import native_reader as n
from p3_common import value_hash,expected_files
import run_p3 as runner

HERE=Path(__file__).resolve().parent
B=json.loads((HERE/'bindings.json').read_bytes())

def temp():
    if os.name=='nt':
        base=HERE.parent/'fixtures_001';base.mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(prefix='p3_owned_',dir=base)
    return tempfile.TemporaryDirectory(prefix='p3_owned_')

def body(table,entry):
    sink=io.BytesIO();pq.write_table(table,sink,version='2.6')
    b=sink.getvalue();e=copy.deepcopy(entry);e['source'].update(bytes=len(b),sha256=c.sha(b));return b,e

class P3Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f=pd.DataFrame({'time':pd.to_datetime(['2026-09-28']*3).astype('datetime64[ns]'),
                        'code':['000001.XSHE','600000.XSHG','600001.XSHG']})
        for name in c.NUMERIC:f[name]=[1.,2.,3.]
        f['paused']=[0.,1.,0.]
        cls.table=pa.Table.from_pandas(f,schema=pa.schema(list(c.EXPECTED)+[pa.field('__index_level_0__',pa.int64())]),preserve_index=True)
        e={'source':{},'date':'2026-09-28','product':'stock','admitted_positions':[0,1,2],'quarantined_positions':[]}
        cls.data,cls.entry=body(cls.table,e)
    def reject_column(self,name,array,message):
        t=self.table.set_column(self.table.column_names.index(name),name,array);b,e=body(t,self.entry)
        with self.assertRaisesRegex(c.Blocked,message):c.decode(b,e)
    def test_01_partition(self):c.check_positions([0,2],[1],3)
    def test_02_duplicate_position(self):
        with self.assertRaisesRegex(c.Blocked,'REPEATED'):c.check_positions([0,0],[],2)
    def test_03_overlapping_position(self):
        with self.assertRaisesRegex(c.Blocked,'PARTITION'):c.check_positions([0,1],[1],2)
    def test_04_negative_position(self):
        with self.assertRaisesRegex(c.Blocked,'PARTITION'):c.check_positions([-1,0],[],2)
    def test_05_bool_position(self):
        with self.assertRaisesRegex(c.Blocked,'NOT_INT'):c.check_positions([False,1],[],2)
    def test_06_native_pandas_arrow_fixture(self):
        got,a=c.decode(self.data,self.entry);self.assertEqual(len(got),3);self.assertIn('nanoseconds',a['footer_schema']);self.assertFalse(a['index_used_for_admission'])
    def test_07_one_byte_corruption(self):
        with self.assertRaisesRegex(c.Blocked,'SOURCE_IDENTITY'):c.decode(self.data+b'x',self.entry)
    def test_08_saved_index_not_row_position(self):self.reject_column('__index_level_0__',pa.array([2,1,0]),'INDEX_POSITION')
    def test_09_seconds_rejected(self):self.reject_column('time',self.table['time'].cast(pa.timestamp('s')),'RAW_ARROW_SCHEMA')
    def test_10_milliseconds_rejected(self):self.reject_column('time',self.table['time'].cast(pa.timestamp('ms')),'RAW_ARROW_SCHEMA')
    def test_11_ordinal_axis_rejected(self):self.reject_column('time',pa.array([0,1,2]),'RAW_ARROW_SCHEMA')
    def test_12_non_jq_namespace(self):self.reject_column('code',pa.array(['000001.SZ']*3),'JQ_CODE_NAMESPACE')
    def test_13_null_prices_not_filled(self):self.reject_column('open',pa.array([None]*3,type=pa.float64()),'ADMITTED_NULL')
    def test_14_inf_not_hidden(self):self.reject_column('factor',pa.array([float('inf')]*3),'NONFINITE')
    def test_15_unknown_paused(self):self.reject_column('paused',pa.array([2.]*3),'UNKNOWN_PAUSED')
    def test_16_quarantine_not_general_bypass(self):
        e=copy.deepcopy(self.entry);e.update(admitted_positions=[0,2],quarantined_positions=[1])
        with self.assertRaisesRegex(c.Blocked,'QUARANTINE_EXACT_BINDING'):c.decode(self.data,e)
    def test_17_dictionary_roundtrip(self):
        t=self.table.select(c.FIELDS).replace_schema_metadata(None);self.assertTrue(c.dictionary_view(t).rename_columns(c.FIELDS).equals(t))
    def test_18_duplicates_not_suppressed(self):
        with self.assertRaisesRegex(c.Blocked,'DUPLICATE_KEY'):c.reject_duplicates(pa.concat_tables([self.table.select(c.FIELDS)]*2))
    def test_19_factor_not_adjusted(self):
        t=self.table.set_column(self.table.column_names.index('factor'),'factor',pa.array([2.5]*3));b,e=body(t,self.entry)
        got,_=c.decode(b,e);self.assertEqual(got['factor'].to_pylist(),[2.5]*3);self.assertTrue(got['close'].equals(t['close']))
    def test_20_paused_pattern_is_fact(self):
        f=self.table.select(c.FIELDS).to_pandas();f.loc[1,['open','high','low','close','pre_close']]=7.;f.loc[1,['volume','money']]=0.
        self.assertEqual(c.observations(f)['paused_1_ohlc_eq_pre_close_volume_money_zero'],1)
    def test_21_normative_semantics(self):
        r=n.semantic_bind((HERE/'domain_schema_contract.csv').read_bytes(),(HERE/'pit_schema_contract.csv').read_bytes())
        self.assertEqual(r['stock_required_fields_checked'],12);self.assertEqual(len(r['field_mapping']),14);self.assertFalse(r['dictionary_formal_admission']);self.assertEqual(r['source_supplements'],['avg','pre_close'])
    def test_22_semantic_key_drift(self):
        b=(HERE/'domain_schema_contract.csv').read_bytes().replace(b'symbol+trade_date',b'other+trade_date')
        with self.assertRaisesRegex(c.Blocked,'DICTIONARY_SEMANTICS_CHANGED'):n.semantic_bind(b,(HERE/'pit_schema_contract.csv').read_bytes())
    def test_23_no_backtest_or_same_asof_admission(self):
        for purpose in ['BACKTEST','NEXT_DAY','SAME_DAY_EOD','LIVE']:
            with self.assertRaisesRegex(c.Blocked,'USE_NOT_ADMITTED'):c.read_candidate('absent','SAME_ASOF','stock',purpose)
    def test_24_path_traversal(self):
        for bad in ['../a','/a','C:/a','a\\b','a/../b','./a','a//b']:
            with self.assertRaises(c.Blocked):c.relative(bad)
    def test_25_wrong_source_root(self):
        with self.assertRaisesRegex(c.Blocked,'SOURCE_ROOT_NOT_BOUND'):c.source_key({'source':{'path':r'E:\OTHER\raw\x'}},B)
    def test_26_changed_source_identity(self):
        with temp() as d:
            p=Path(d)/'x';p.write_bytes(b'bad')
            with self.assertRaisesRegex(c.Blocked,'SOURCE_IDENTITY'):n.exact(p,{'bytes':3,'sha256':c.sha(b'old')})
    def test_27_reparse_attribute(self):
        with temp() as d,patch.object(Path,'lstat',return_value=SimpleNamespace(st_file_attributes=0x400,st_mode=0)):
            with self.assertRaisesRegex(c.Blocked,'NATIVE_REPARSE'):n.safe(Path(d))
    def test_28_output_inside_source(self):
        with temp() as d:
            with self.assertRaisesRegex(c.Blocked,'OUTPUT_IN_SOURCE'):c.validate_output(Path(d)/'candidate',[Path(d)])
    def test_29_sibling_output_allowed(self):
        with temp() as d:c.validate_output(Path(d)/'candidate',[Path(d)/'original'])
    def test_30_existing_output_retained(self):
        with temp() as d:
            p=Path(d)/'existing';p.write_bytes(b'original')
            with self.assertRaisesRegex(c.Blocked,'OUTPUT_EXISTS'):c.validate_output(p,[])
            self.assertEqual(p.read_bytes(),b'original')
    def test_31_single_run_marker_outside_candidate(self):
        with temp() as d:
            control=Path(d)/'control';control.mkdir();output=Path(d)/'candidate'
            with patch.object(runner,'CONTROL',control),patch.object(runner,'OUTPUT',output):
                first=runner.reserve();first.rmdir()
                with self.assertRaises(FileExistsError):runner.reserve()
            self.assertTrue((control/'RUN_ONCE.json').exists());self.assertFalse(output.exists())
    def test_32_portable_hash_detects_value(self):
        t=self.table.select(c.FIELDS);other=t.set_column(2,'open',pa.array([8.]*3));self.assertNotEqual(value_hash(t),value_hash(other))
    def test_33_portable_hash_ignores_generation(self):
        self.assertEqual(value_hash(self.table),value_hash(self.table.replace_schema_metadata({b'generation':b'other'})))
    def test_34_expected_set_exactly_125(self):self.assertEqual(len(expected_files(B['expected_cells'])),125)
    def test_35_generation_bound_to_root(self):
        self.assertNotEqual(c.generation_for(HERE/'first',B),c.generation_for(HERE/'second',B))

if __name__=='__main__':unittest.main(verbosity=2)
