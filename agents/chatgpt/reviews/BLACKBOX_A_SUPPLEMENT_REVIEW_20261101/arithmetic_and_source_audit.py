"""GPT-only source and arithmetic illustration; no fills, engine or native entry."""
from pathlib import Path
from decimal import Decimal as D,ROUND_CEILING,ROUND_FLOOR,ROUND_HALF_UP
import hashlib,io,json
import pyarrow.parquet as pq
import candidate_adapter as old
import p4_consumer as p
ROOT=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
checks=[]
def ck(n,b):
 checks.append({'name':n,'passed':bool(b)})
 if not b:raise AssertionError(n)
reader=old.BodyReader(ROOT/'evidence',json.loads((ROOT/'p3_dispatch/bindings.json').read_bytes()))
pairs=[(e,k) for e,k in zip(reader.admission['entries'],reader.entry_keys) if e['source']['path'].endswith('2026-10-15_00720_R4.parquet')]
ck('one_exact_source_file',len(pairs)==1)
e,k=pairs[0];body=reader.read(e,k);ck('original15545bytes_sha',len(body)==15545 and hashlib.sha256(body).hexdigest()=='158937b474c53184087ef5a05968ba36e5b81a4348f49ed66cf5cad77fa6763f')
t=pq.ParquetFile(io.BytesIO(body)).read();raw=t.slice(68,1).to_pylist()[0]
ck('physical_row68_admitted',68 in e['admitted_positions'] and 68 not in e['quarantined_positions'])
ck('target_key',raw['code']=='002270.XSHE' and raw['time'].date().isoformat()=='2026-10-15')
c=p.Consumer(ROOT/'p3_native_review/return/result_001',ROOT/'p1_dispatch',ROOT/'p4_offline/INPUT_PINS.json')
r=next(x for x in c._records if x['code']=='002270.XSHE' and x['time']=='2026-10-15');prior=next(x for x in c._records if x['code']=='002270.XSHE' and x['time']=='2026-10-14')
fields=['open','high','low','close','volume','money','high_limit','low_limit','paused'];ck('raw_to_candidate_fields_exact',all(raw[f]==r[f] for f in fields))
ck('raw_to_candidate_provenance',r['provenance']['physical_row_position']==68 and r['provenance']['source_sha256']==hashlib.sha256(body).hexdigest())
ck('literal_volume_money_values',r['volume']==14076869.0 and r['money']==254286654.36)
anchor={'status':'OFFICIAL_EXCHANGE_REFERENCE_NOT_RETRIEVED','comparison_status':'NOT_COMPLETED','absolute_units_established':False,'stock':'002270.XSHE','date':'2026-10-15','source':e['source'],'physical_row_position':68,'source_row_fields':{f:str(raw[f]) for f in fields},'candidate_generation':p.GEN,'candidate_manifest_sha256':p.MAN,'provenance':r['provenance'],'official_reference':None,'permitted_after_binding_scope':'Same identified stock/fq=None endpoint/product/version only; not all suppliers,CDRs,indices or funds','hypothetical_display_conversions_only':{'IF_volume_is_shares_to_hands':str(D(str(r['volume']))/D('100')),'IF_volume_is_shares_to_10000_shares':str(D(str(r['volume']))/D('10000')),'IF_money_is_CNY_to_10000_CNY':str(D(str(r['money']))/D('10000')),'IF_money_is_CNY_to_100000000_CNY':str(D(str(r['money']))/D('100000000'))},'orders_allowed':False}
(OUT/'002270_QUOTE_ANCHOR_REVIEW.json').write_text(json.dumps(anchor,ensure_ascii=False,indent=2)+'\n')
# Pure Decimal illustrations of the approved convention, not a fill implementation.
examples=[]
for price,wantbuy,wantsell,wantbp in [('20','20.01','19.99','5'),('5','5.01','4.99','20'),('2','2.01','1.99','50'),('17.87','17.88','17.86',None)]:
 q=D(price);unrounded_buy=q*D('1.0005');unrounded_sell=q*D('.9995');buy=unrounded_buy.quantize(D('.01'),rounding=ROUND_CEILING);sell=unrounded_sell.quantize(D('.01'),rounding=ROUND_FLOOR)
 ck('outward_buy:'+price,buy==D(wantbuy) and buy>=unrounded_buy)
 ck('outward_sell:'+price,sell==D(wantsell) and sell<=unrounded_sell)
 bps=(buy-q)/q*D('10000');sbps=(q-sell)/q*D('10000');ck('actual_slippage_at_least5bp:'+price,bps>=D('5') and sbps>=D('5'))
 if wantbp:ck('exact_bps:'+price,bps==sbps==D(wantbp))
 examples.append({'quote_CNY':str(q),'unrounded_buy':str(unrounded_buy),'unrounded_sell':str(unrounded_sell),'rounded_buy':str(buy),'rounded_sell':str(sell),'effective_buy_bps':str(bps),'effective_sell_bps':str(sbps)})
ck('issuer_gross_dividend_total',D('896225431')*D('2.60')/D('10')==D('233018612.06'))
# A diagnostic only: never manufacture a band or write it into quote/source data.
ref=D(str(prior['close']))-D('.26');up=(ref*D('1.10')).quantize(D('.01'),rounding=ROUND_HALF_UP);low=(ref*D('.90')).quantize(D('.01'),rounding=ROUND_HALF_UP)
ck('002270_actual_cap_diagnostic',str(prior['close'])=='18.28' and ref==D('18.02') and up==D(str(r['high_limit'])) and low==D(str(r['low_limit'])))
illustration={'purpose':'DECIMAL_DESK_ILLUSTRATION_ONLY_NO_FILL_MODEL','configured_bps':'5','tick_CNY':'.01','examples':examples,'price_bucket_proposal':['0<price<=2','2<price<=5','5<price<=20','price>20'],'dividend_total_CNY':'233018612.06','limit_diagnostic_only':{'previous_close':'18.28','gross_dividend':'0.26','reference_after_dividend':'18.02','actual_reported_high_limit':str(r['high_limit']),'actual_reported_low_limit':str(r['low_limit']),'may_generate_or_replace_bands':False},'volume_cap_illustration_only':{'IF_units_bound_and_signal_date':'2026-10-15','prospective_execution_date':'2026-10-16','0.5_percent_of_that_prior_day_volume':str(D(str(r['volume']))*D('.005')),'separate_smoke_order_cap':10000,'uses_execution_day_full_volume_for_sizing':False},'backtest_run':False,'orders_allowed':False}
(OUT/'ROUNDING_AND_FIELD_ILLUSTRATIONS.json').write_text(json.dumps(illustration,indent=2)+'\n')
result={'checks_passed':len(checks),'checks':checks,'raw_source_bytes_verified':True,'raw_to_candidate_target_row_equal':True,'official_exchange_anchor_verified':False,'fill_model_implemented':False,'native_execution':False,'backtest_run':False,'orders_allowed':False}
(OUT/'DESK_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
