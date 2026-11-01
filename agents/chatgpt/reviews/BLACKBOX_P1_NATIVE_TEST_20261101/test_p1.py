import copy,unittest
from pathlib import Path
import p1_layer as p

ROOT=Path(__file__).parent
def sample(day='2026-10-26',paused=0):
 r={k:1.0 for k in p.SOURCE_FIELDS};r.update(time=day,code='600000.XSHG',paused=paused);return r

class Tests(unittest.TestCase):
 def setUp(self):
  self.c=p.load_contract(ROOT);self.row=sample();self.layer=p.make_layer([self.row],self.c,'stock','fixture','a'*64)
 def use(self,t='2026-10-27T09:00:00+08:00',fields=None,layer=None,purpose='BACKTEST_DAILY_T1'):
  return p.select(layer or self.layer,self.c,purpose,t,fields or ['time','code','close','paused'],'fixture','a'*64)
 def test_next_session(self):self.assertEqual(p.available_at('2026-09-30',self.c),'2026-10-08T09:00:00+08:00')
 def test_before_threshold(self):self.assertEqual(self.use('2026-10-27T08:59:59+08:00'),[])
 def test_equal_threshold(self):self.assertEqual(len(self.use()),1)
 def test_utc_equivalent(self):self.assertEqual(len(self.use('2026-10-27T01:00:00+00:00')),1)
 def test_naive_rejected(self):
  with self.assertRaisesRegex(ValueError,'NAIVE'):self.use('2026-10-27T09:00:00')
 def test_terminal_unresolved(self):self.assertIsNone(p.available_at('2026-10-27',self.c))
 def test_before_calendar(self):self.assertIsNone(p.available_at('2026-09-23',self.c))
 def test_non_session(self):self.assertIsNone(p.available_at('2026-10-01',self.c))
 def test_factor_denied(self):
  with self.assertRaisesRegex(ValueError,'FIELD'):self.use(fields=['factor'])
 def test_original_unchanged(self):self.assertEqual(self.row,sample());self.assertNotIn('factor',self.layer[0]['values'])
 def test_paused_preserved(self):
  x=p.make_layer([sample(paused=1)],self.c,'stock','fixture','a'*64);self.assertEqual(self.use(layer=x)[0]['paused'],1)
 def test_zero_volume_not_filled(self):
  r=sample();r['volume']=0;r['money']=0;x=p.make_layer([r],self.c,'stock','fixture','a'*64)
  self.assertEqual(self.use(layer=x,fields=['volume','money']),[{'volume':0,'money':0}])
 def test_forbidden_uses(self):
  for use in ['LIVE','SAME_DAY_EOD','BACKTEST','NEXT_DAY']:
   with self.assertRaises(ValueError):self.use(purpose=use)
 def test_product_scope(self):
  for product in ['etf','index']:
   with self.assertRaisesRegex(ValueError,'PRODUCT'):p.make_layer([self.row],self.c,product,'fixture','a'*64)
 def test_duplicate(self):
  with self.assertRaisesRegex(ValueError,'DUPLICATE'):p.make_layer([self.row,self.row],self.c,'stock','fixture','a'*64)
 def test_quarantine(self):
  r=sample('2026-10-27');r['code']='600621.XSHG'
  with self.assertRaisesRegex(ValueError,'QUARANTINED'):p.make_layer([r],self.c,'stock','fixture','a'*64)
 def test_timestamp_not_date(self):
  with self.assertRaises(ValueError):p.make_layer([sample('2026-10-26T00:00:00')],self.c,'stock','fixture','a'*64)
 def test_future_date_tamper(self):
  x=copy.deepcopy(self.layer);x[0]['availability']['presumed_available_at']='2026-10-26T09:00:00+08:00'
  with self.assertRaisesRegex(ValueError,'TAMPER'):self.use(layer=x)
 def test_generation_tamper(self):
  x=copy.deepcopy(self.layer);x[0]['availability']['source_generation']='different'
  with self.assertRaisesRegex(ValueError,'SOURCE_BINDING'):self.use(layer=x)
 def test_sixteen_resolved_one_unresolved(self):
  days=self.c['days'][1:];self.assertEqual(sum(p.available_at(d,self.c) is not None for d in days),16)

if __name__=='__main__':unittest.main(verbosity=2)
