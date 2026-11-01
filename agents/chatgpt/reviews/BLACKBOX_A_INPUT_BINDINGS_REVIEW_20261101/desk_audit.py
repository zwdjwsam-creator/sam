"""GPT desk evidence checks only. No fill model, native command or activation."""
from pathlib import Path
from collections import Counter
from datetime import date
import hashlib,io,json
import p4_consumer as p
ROOT=Path(__file__).resolve().parent.parent
OUT=Path(__file__).resolve().parent
checks=[]
def ck(n,b):
 checks.append({'name':n,'passed':bool(b)})
 if not b:raise AssertionError(n)
sources=json.loads((ROOT/'a_inputs_source_bundle.json').read_bytes())
for r in sources:
 b=(OUT/Path(r['path']).name).read_bytes();ck('source_identity:'+Path(r['path']).name,hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['sha'])
can=json.loads((OUT/'jq_official_canonical_field_dictionary.json').read_bytes())
units=[r for r in can['fields'] if r['jq_field_name'] in ['volume','money'] and r['official_asset_scope']=='stock']
ck('four_stock_unit_rows_blank',len(units)==4 and all(r['official_unit']=='' for r in units))
ck('original_field_dictionary_already_available',hashlib.sha256((OUT/'jqdata_official_field_dictionary_CURRENT.csv').read_bytes()).hexdigest()=='7599640e56e1701ce6a6abb952e567174a6fde77ce02ed57bbf055b7dfadddd8')
consumer=p.Consumer(ROOT/'p3_native_review/return/result_001',ROOT/'p1_dispatch',ROOT/'p4_offline/INPUT_PINS.json')
records=consumer._records
ck('all_stock_rows_88811',len(records)==88811)
allowed=json.loads((ROOT/'p4_offline/REAL_SCOPE.json').read_bytes())['resolved_dates']
ck('sixteen_prior_P1_dates',len(allowed)==16 and allowed[0]=='2026-09-28' and allowed[-1]=='2026-10-26')
ck('public002270_event_joins_supplied_scope',any(r['code']=='002270.XSHE' for r in records))
ck('public002270_ex_date_inside16_data_dates','2026-10-15' in allowed)
selected=[r for r in records if r['time'] in allowed];codes=sorted({r['code'] for r in records});smoke_codes=sorted({r['code'] for r in selected})
ck('83588_rows_for16_dates',len(selected)==83588)
ck('only_two_admitted_namespaces',{x.split('.')[-1] for x in codes}=={'XSHG','XSHE'})
ck('all_numeric_first_digits_036',{x[0] for x in codes}=={'0','3','6'})
# This is proposed model routing, not a verified security-by-date board master.
def route(code):
 if code=='689009.XSHG':return 'HOLD_CDR_UNIT_AND_POLICY_SCOPE'
 if code=='302132.XSHE':return 'SMOKE_CHINEXT' # exact proposed exception, never rewrite the source identifier
 n,s=code.split('.')
 if s=='XSHG' and n[:3] in ('600','601','603','605'):return 'SMOKE_SSE_MAIN'
 if s=='XSHG' and n[:3] in ('688','689'):return 'SMOKE_STAR'
 if s=='XSHE' and n[:3] in ('000','001','002','003'):return 'SMOKE_SZSE_MAIN'
 if s=='XSHE' and n[:3] in ('300','301'):return 'SMOKE_CHINEXT'
 return 'BLOCKED_UNMAPPED'
ck('exact302132_exception_proposed',route('302132.XSHE')=='SMOKE_CHINEXT' and any(r['code']=='302132.XSHE' for r in records))
ck('all_codes_have_proposed_profile',all(route(x)!='BLOCKED_UNMAPPED' for x in codes))
ck('CDR_not_silently_admitted_as_ordinary_shares',route('689009.XSHG')=='HOLD_CDR_UNIT_AND_POLICY_SCOPE' and '689009.XSHG' in codes)
positive=[r for r in selected if r['volume']>0 and r['money']>0 and r['low']>0 and r['high']>=r['low']]
scales={}
for name,vm,mm in [('proposed_share_CNY',1,1),('lot100_CNY',100,1),('share_thousand_CNY',1,1000),('both_scaled100',100,100)]:
 count=sum(r['low']-1e-6 <= r['money']*mm/(r['volume']*vm) <= r['high']+1e-6 for r in positive)
 scales[name]={'volume_multiplier':vm,'money_multiplier':mm,'rows_mean_inside_daily_range':count,'rows_tested':len(positive)}
ck('ratio_cannot_prove_absolute_common_scale',scales['proposed_share_CNY']['rows_mean_inside_daily_range']==scales['both_scaled100']['rows_mean_inside_daily_range'])
reg={'status':'EVENT_IDENTITIES_UNRESOLVED_NOT_EMPTY_EVENT_LIST','source_generation':p.GEN,'source_manifest_sha256':p.MAN,'data_window':{'dates':allowed,'stock_rows':len(selected),'distinct_symbols':len(smoke_codes)},'execution_or_valuation_event_window_to_review':{'first':'2026-09-28','last':'2026-10-27','reason':'T+1 fills/positions may need next-day events even though last-day bar is unavailable to decisions'},'confirmed_affected_symbols':None,'confirmed_event_count':None,'unresolved_symbols':smoke_codes,'unknown_is_not_no_event':True,'not_a_download_determination':True,'source_policy':'Use existing registered RAW/Clean/cache/event records and exact body identities before any acquisition proposal. Do not treat report_date as ex-date.','backtest_admission':False,'orders_allowed':False}
(OUT/'CORPORATE_ACTION_SCOPE_REGISTER.json').write_text(json.dumps(reg,indent=2)+'\n')
rules=json.loads((OUT/'cn_a_exchange_trading_hard_rules_20260706_R1.json').read_bytes())
ck('legacy_rules_not_dated_lot_table',len(rules['rules'])==9 and not any(x['rule_category'] in ['lot','order_lot','lot_size'] for x in rules['rules']))
ds=json.loads((OUT/'DATASET_STATE.json').read_bytes());xr=next(x for x in ds['datasets'] if x['dataset_id']=='XR_XD')
ck('registered_XR_layers_exist',xr['layers']['RAW']['measurement']['n_files_total']==64 and xr['layers']['CLEAN']['measurement']['n_files_total']==62)
ck('raw_axis_is_report_period',xr['layers']['RAW']['measurement']['time_role']=='REPORT_PERIOD' and xr['layers']['RAW']['measurement']['time_column']=='report_date')
ck('cache_effective_axis_registered',xr['cache_products'][0]['product']=='CORP_XR_XD_EVENT_PIT_R1' and xr['cache_products'][0]['measurement']['time_column']=='effective_date')
result={'scope':'GPT_DESK_ONLY_NO_NATIVE_TASK_OR_FILL_IMPLEMENTATION','checks':checks,'checks_passed':len(checks),'stock_rows':len(records),'stock_distinct_codes':len(codes),'stock_suffix_rows':dict(Counter(r['code'].split('.')[-1] for r in records)),'smoke_rows':len(selected),'smoke_distinct_codes':len(smoke_codes),'proposed_profile_rows17dates':dict(Counter(route(r['code']) for r in records)),'proposed_profile_unique_codes17dates':dict(Counter(route(x) for x in codes)),'proposed_profile_rows16dates':dict(Counter(route(r['code']) for r in selected)),'unmapped_codes':sorted(x for x in codes if route(x)=='BLOCKED_UNMAPPED'),'prefix_routing_is_proposal_not_master_fact':True,'volume_money_binding_status':'NOT_ESTABLISHED','ratio_diagnostic':scales,'ratio_diagnostic_is_unit_certificate':False,'event_identities_established':False,'event_symbol_register_count':len(smoke_codes),'native_command':None,'calendar_extended':False,'orders_allowed':False}
(OUT/'DESK_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','ratio_diagnostic']},ensure_ascii=False))
