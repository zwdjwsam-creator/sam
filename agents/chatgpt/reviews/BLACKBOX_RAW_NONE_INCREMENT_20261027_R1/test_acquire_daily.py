import json
import tempfile
import unittest
from pathlib import Path
from datetime import date,datetime,timedelta
from unittest.mock import patch
import pandas as pd
import numpy as np
import acquire_daily as a

D=date(2026,10,9)
C=['000001.XSHG','399001.XSHE']
def bars():
    x=pd.DataFrame({'time':[pd.Timestamp(D)]*2,'code':C})
    for f in a.FIELDS:x[f]=[1.,2.]
    x['paused']=[0.,1.]
    return x

class Keys(unittest.TestCase):
    def test_valid_exact_keys(self):
        x,q=a.normalize(bars(),C,D);self.assertEqual(q['keys']['missing'],[]);self.assertEqual(q['rows'],2)
    def test_missing_key_blocks(self):
        with self.assertRaisesRegex(a.Blocked,'MISSING_KEY'):a.normalize(bars().iloc[:1],C,D)
    def test_extra_key_blocks(self):
        with self.assertRaisesRegex(a.Blocked,'OUT_OF_UNIVERSE'):a.normalize(bars(),C[:1],D)
    def test_duplicate_blocks(self):
        x=pd.concat([bars(),bars().iloc[:1]])
        with self.assertRaisesRegex(a.Blocked,'DUPLICATE_RESPONSE'):a.normalize(x,C,D)
    def test_two_times_same_day_blocks(self):
        x=pd.concat([bars(),bars().iloc[:1]]).reset_index(drop=True);x.loc[2,'time']+=timedelta(hours=1)
        with self.assertRaisesRegex(a.Blocked,'NORMALIZED'):a.normalize(x,C,D)
    def test_ordinal_blocks(self):
        x=bars();x['time']=[0,1]
        with self.assertRaisesRegex(a.Blocked,'NUMERIC_DATE'):a.normalize(x,C,D)
    def test_wrong_day_blocks(self):
        x=bars();x['time']+=timedelta(days=1)
        with self.assertRaisesRegex(a.Blocked,'OUT_OF_RANGE_DATE'):a.normalize(x,C,D)
    def test_null_key_blocks(self):
        x=bars();x.loc[0,'code']=None
        with self.assertRaisesRegex(a.Blocked,'NULL_STABLE_KEY'):a.normalize(x,C,D)
    def test_missing_field_blocks(self):
        with self.assertRaisesRegex(a.Blocked,'SCHEMA_MISSING'):a.normalize(bars().drop(columns=['factor']),C,D)
    def test_live_null_blocks(self):
        x=bars();x.loc[0,'close']=np.nan
        with self.assertRaisesRegex(a.Blocked,'LIVE_BAR_NULL'):a.normalize(x,C,D)
    def test_paused_null_preserved(self):
        x=bars();x.loc[1,'close']=np.nan;y,q=a.normalize(x,C,D)
        self.assertTrue(pd.isna(y.loc[1,'close']));self.assertFalse(q['local_price_fill'])
    def test_unknown_paused_blocks(self):
        x=bars();x.loc[0,'paused']=np.nan
        with self.assertRaisesRegex(a.Blocked,'UNKNOWN_PAUSED'):a.normalize(x,C,D)
    def test_universe_lifecycle_blocks(self):
        x=pd.DataFrame({'start_date':[date(2027,1,1)],'end_date':[date(2200,1,1)]},index=[C[0]])
        with self.assertRaisesRegex(a.Blocked,'LIFECYCLE_MISMATCH'):a.universe(x,D,8000)
    def test_universe_no_namespace_invention(self):
        x=pd.DataFrame({'start_date':[D],'end_date':[D]},index=['000001.OTHER'])
        with self.assertRaisesRegex(a.Blocked,'NAMESPACE'):a.universe(x,D,8000)
    def test_calendar_exact_holidays_and_completion(self):
        values=[date(2026,9,24),date(2026,9,25),date(2026,10,27)]
        self.assertEqual(a.sessions(values,datetime(2026,10,27,14,0,tzinfo=a.CN)),[date(2026,9,25)])
        self.assertEqual(a.sessions(values,datetime(2026,10,27,16,0,tzinfo=a.CN))[-1],date(2026,10,27))
    def test_no_integer_epoch(self):
        for x in [0,1,np.int64(2),2.0,False]:
            with self.assertRaisesRegex(a.Blocked,'NUMERIC'):a.checked_day(x)
    def test_no_replay_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.json';a.put(p,{'a':1})
            with self.assertRaises(FileExistsError):a.put(p,{'a':2})
            self.assertEqual(json.loads(p.read_text()),{'a':1})
    def test_real_parquet_and_footer(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'p';p.mkdir();x=bars();x.to_parquet(p/'one.parquet',index=True)
            pd.testing.assert_frame_equal(x,pd.read_parquet(p/'one.parquet'))
            # Explicit path-policy stand-in for OS temporary fixtures, not native production-path proof.
            with patch.object(a,'require_allowed_read'):
                maximum=a.coverage([p],root/'coverage.json')
            self.assertEqual(maximum,D)
    def test_integer_footer_not_relabelled(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'p';p.mkdir();x=bars();x['time']=[0,1];x.to_parquet(p/'x.parquet')
            with patch.object(a,'require_allowed_read'),self.assertRaisesRegex(a.Blocked,'NUMERIC_REGISTERED'):
                a.coverage([p],root/'coverage.json')
    def test_unhandled_file_not_absence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'p';p.mkdir();(p/'new.csv').write_text('time,code\n')
            with patch.object(a,'require_allowed_read'),self.assertRaisesRegex(a.Blocked,'UNHANDLED'):
                a.coverage([p],root/'coverage.json')
    def test_file_cap_is_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'p';p.mkdir();bars().to_parquet(p/'x.parquet')
            with patch.object(a,'require_allowed_read'),self.assertRaisesRegex(a.Blocked,'FILE_CAP'):
                a.coverage([p],root/'coverage.json',max_files=0)
    def test_wrong_host_before_output(self):
        with patch.object(a.platform,'system',return_value='Linux'):
            with self.assertRaisesRegex(a.Blocked,'WRONG_HOST'):a.run(Path('/unused'),Path('/unused/output'))
    def test_quota_reset_not_ignored(self):
        class Q:
            def get_query_count(self):return {'spare':self.q.pop(0)}
        q=Q();q.q=[100,101];s=a.Supplier(q,Path('/unused'));s.quota()
        with self.assertRaisesRegex(a.Blocked,'QUOTA_RESET'):s.quota()
    def test_quota_unmeasured_blocks(self):
        class Q:
            def get_query_count(self):return {'spare':None}
        with self.assertRaisesRegex(a.Blocked,'QUOTA_UNMEASURED'):a.Supplier(Q(),Path('/unused')).quota()
    def test_endpoint_whitelist(self):
        with self.assertRaisesRegex(a.Blocked,'ENDPOINT_NOT_ALLOWED'):a.Supplier(None,Path('/unused')).call('order',{})
    def test_windows_source_root_boundary(self):
        self.assertTrue(a.allowed_windows_path('E:\\BLACKBOX\\数据\\x.parquet'))
        self.assertFalse(a.allowed_windows_path('E:\\BLACKBOX_other\\x.parquet'))
        self.assertFalse(a.allowed_windows_path('C:\\temp\\secret.parquet'))
    def test_windows_extended_source_root(self):
        self.assertTrue(a.allowed_windows_path('\\\\?\\E:\\BLACKBOX_ENGINES\\x.parquet'))

if __name__=='__main__':unittest.main()
