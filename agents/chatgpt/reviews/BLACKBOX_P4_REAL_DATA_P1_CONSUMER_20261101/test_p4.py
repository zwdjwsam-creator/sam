import copy,io,json,unittest
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import p4_consumer as p
ROOT=Path(__file__).resolve().parent.parent
class ConsumerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=p.Consumer(ROOT/'p3_native_review/return/result_001',ROOT/'p1_dispatch',ROOT/'p4_offline/INPUT_PINS.json')
  cls.r=cls.c._records;cls.days=cls.c.days
 def run_internal(self,rows,**kw):return p._decision_rows(rows,self.days,kw.get('at','2026-10-27T09:00:00+08:00'),kw.get('fields',['time','code','close']),kw.get('product','stock'),kw.get('purpose',p.PURPOSE))
 def test_real_public_gate_and_all_values_and_provenance(self):
  got=self.c.select('2026-10-27T09:00:00+08:00',p.PUBLIC)
  expected=[r for r in self.r if p.available(r['time'],self.days) is not None]
  self.assertEqual(len(got),len(expected))
  for a,b in zip(got,expected):
   self.assertEqual(a['values'],{k:b[k] for k in p.PUBLIC});self.assertEqual(a['provenance'],b['provenance']);self.assertFalse(a['states']['execution_allowed']);self.assertEqual(set(a['states']),set(p.STATUS));self.assertEqual(a['availability']['historical_pit'],'NOT_ESTABLISHED')
  self.assertEqual(len({r['values']['time'] for r in got}),16)
  self.assertFalse(any(r['values']['time']=='2026-10-27' for r in got))
 def test_exact_boundary_and_preboundary(self):
  r=self.r[0];at=p.available(r['time'],self.days)
  self.assertEqual(len(self.run_internal([r],at=at)),1)
  self.assertEqual(self.run_internal([r],at=at.replace('09:00:00','08:59:59')),[])
 def test_timezone_rejections(self):
  for at in ['2026-10-27T09:00:00','2026-10-27T01:00:00+00:00']:
   with self.assertRaisesRegex(p.Rejected,'UTC_PLUS_08'):self.run_internal([],at=at)
 def test_factor_avg_pre_close_rejected(self):
  for f in ['factor','avg','pre_close']:
   with self.assertRaisesRegex(p.Rejected,'FIELD_DENIED'):self.run_internal(self.r[:1],fields=[f])
 def test_nonstock_rejected(self):
  for product in ['etf','index','STOCK']:
   with self.assertRaisesRegex(p.Rejected,'PRODUCT_DENIED'):self.c.select('2026-10-27T09:00:00+08:00',['close'],product=product)
 def test_no_backtest_or_execution_purpose(self):
  for purpose in ['BACKTEST_DAILY_T1','FACTOR_RESEARCH_T1','TRADE','LIVE']:
   with self.assertRaisesRegex(p.Rejected,'NO_BACKTEST'):self.run_internal([],purpose=purpose)
 def test_mandatory_states_even_if_not_requested(self):
  got=self.run_internal(self.r[:1],fields=['close'])[0]
  self.assertEqual(set(got['states']),set(p.STATUS));self.assertFalse(got['states']['execution_allowed'])
 def test_missing_status_input_rejected(self):
  for f in ['paused','volume','money','high_limit','low_limit']:
   r=copy.deepcopy(self.r[0]);r.pop(f)
   with self.assertRaisesRegex(p.Rejected,'MISSING_STATE'):self.run_internal([r])
 def test_null_price_and_state_rejected(self):
  for f in ['paused','volume','close','high_limit']:
   r=copy.deepcopy(self.r[0]);r[f]=None
   with self.assertRaises(p.Rejected):self.run_internal([r])
 def test_paused_stock_observations_retained_but_never_executable(self):
  r=[x for x in self.r if x['paused']==1 and p.available(x['time'],self.days)]
  got=self.run_internal(r);self.assertEqual(len(got),len(r));self.assertTrue(all(x['states']['paused']==1 and not x['states']['execution_allowed'] for x in got));self.assertEqual(len([x for x in self.r if x['paused']==1]),172);self.assertEqual(len(got),166)
 def test_forged_execution_permission_rejected(self):
  r=copy.deepcopy(self.r[0]);r['execution_allowed']=True
  with self.assertRaisesRegex(p.Rejected,'STATE_TAMPER'):self.run_internal([r])
 def test_quarantine_rejected_and_not_exposed(self):
  self.assertFalse(any(x['code']=='600621.XSHG' and x['time']=='2026-10-27' for x in self.r))
  r=copy.deepcopy(self.r[0]);r.update(time='2026-10-27',code='600621.XSHG')
  with self.assertRaisesRegex(p.Rejected,'QUARANTINE'):self.run_internal([r])
 def test_unresolved_dates_have_no_timestamp(self):
  for day in ['2026-10-27','2014-01-02','2026-10-28']:
   a=self.c.availability(day);self.assertEqual(a['status'],'UNRESOLVED');self.assertIsNone(a['presumed_available_at'])
 def test_duplicate_rejected(self):
  with self.assertRaisesRegex(p.Rejected,'DUPLICATE_KEY'):self.run_internal([self.r[0],self.r[0]])
 def test_policy_corruption_stops_original_entry(self):
  # Isolated bytes returned for one exact path; no original fixture is modified.
  from unittest.mock import patch
  original=Path.read_bytes
  def damaged(path):
   b=original(path);return b+b' ' if path==self.c.policy_root/'POLICY_BODY.txt' else b
  with patch.object(Path,'read_bytes',damaged),self.assertRaisesRegex(p.Rejected,'POLICY_OR_CALENDAR_IDENTITY'):self.c.select('2026-10-27T09:00:00+08:00',['close'])
 def test_archive_corruption_stops_original_entry(self):
  from unittest.mock import patch
  original=Path.read_bytes;target=self.c.archive_root/self.c.pins['archives'][0]['path']
  def damaged(path):
   b=original(path);return b+b' ' if path==target else b
  with patch.object(Path,'read_bytes',damaged),self.assertRaisesRegex(p.Rejected,'ARCHIVE_IDENTITY'):self.c.select('2026-10-27T09:00:00+08:00',['close'])
 def test_approval_corruption_rejected(self):
  from unittest.mock import patch
  original=Path.read_bytes
  def damaged(path):
   b=original(path);return b+b' ' if path==self.c.policy_root/'APPROVAL.json' else b
  with patch.object(Path,'read_bytes',damaged),self.assertRaisesRegex(p.Rejected,'APPROVAL_IDENTITY'):self.c.select('2026-10-27T09:00:00+08:00',['close'])
 def test_real_summary_and_calendar_plan(self):
  o=self.c.summary;self.assertEqual(o['stock_rows'],88811);self.assertEqual(o['PRESUMED_rows']+o['UNRESOLVED_rows'],88811);self.assertEqual(o['paused_by_product'],{'stock':172,'etf':20,'index':0})
  (ROOT/'p4_offline/REAL_SCOPE.json').write_text(json.dumps(o,indent=2)+'\n')
  (ROOT/'p4_offline/DATE_PLAN.json').write_text(json.dumps([{'date':d,'stock_rows':n,'status':'PRESUMED' if p.available(d,self.days) else 'UNRESOLVED','presumed_available_at':p.available(d,self.days)} for d,n in o['stock_date_counts'].items()],indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
