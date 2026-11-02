"""GPT desk-only retained-index review; no local drive scan or network calls."""
import json,hashlib,re,csv,io
from pathlib import Path
R=Path(__file__).resolve().parent
BASE=R.parent
checks=[]
def ck(n,b):
 if not b: raise AssertionError(n)
 checks.append(n)
def read(p): return json.loads(p.read_bytes())
def blob(p):
 b=p.read_bytes();return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def out(n,d): (R/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
src=read(R/'retained_source_bodies.json')
for item in src:
 b=item['content'].encode('utf-8')
 ck('reviewed retained source blob:'+item['path'],hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==item['sha'])
inv=next(json.loads(x['content']) for x in src if x['path'].endswith('/RAW_STATUS_FIELD_INVENTORY.json'))
rest=next(json.loads(x['content']) for x in src if x['path'].endswith('/TRADEABILITY_RESTORE.json'))
history=BASE/'calendar_acceptance/return/capture/result_001/TRADE_DAY_SEQUENCE.json'
cal=BASE/'p1_dispatch/CALENDAR.json';planpath=BASE/'evidence/RAW_TRANSFER_PLAN.json'
ck('historical sequence blob pinned',blob(history)=='bef3159080fda7f7ffc96d58737c867d804a13a1')
ck('P1 calendar blob pinned',blob(cal)=='f880832566d4175d61b2e93107f27876ad049441')
ck('RAW transfer plan blob pinned',blob(planpath)=='fdb67ee619abfb9424344f07bff57dbc616fc02a')
h=read(history)['trade_days'];c=read(cal)['returned'];plan=read(planpath)['rows']
days=sorted(set(x for x in h+c if '2026-09-04'<=x<='2026-10-28'))
ck('32 observed listed dates',len(days)==32)
rows=[]
for day in days:
 batches=[b for b in inv['batches'] if day in b['distinct_dates']]
 source_files=[]
 for b in batches:
  reports=[s for s in rest['sources'] if s['file']==b['file']]
  ck('exact historical name and content date:'+b['file'],b['date_matches_name'] and b['distinct_dates']==[day])
  for s in reports:
   ck('historical fullsha:'+s['file'],len(s.get('sha256',''))==64)
   source_files.append({'path':inv['raw_root']+'\\'+b['file'],'sha256':s['sha256'],'reported_rows':b['rows'],'field_completeness_reported':all(b[k].get('present') and b[k].get('null')==0 for k in ['paused','high_limit','low_limit']),'evidence_level':'RETAINED_NATIVE_OBSERVATION_NOT_NEW_GPT_SOURCE_BYTE_READ'})
 positions=[i for i,p in enumerate(plan) if p['relative_path'].startswith('raw/stock/'+day+'_')]
 rows.append({'trade_date':day,'calendar_basis':'RETAINED_B_SEQUENCE' if day in h else 'FROZEN_P1_CALENDAR', 'raw_status_related_files_identified':bool(source_files or positions),'historical_exact_sources':source_files,'p3_transfer_plan_zero_based_row_indices':positions,'p3_stock_batch_count':len(positions),'p3_reference':'RAW_TRANSFER_PLAN.json blob fdb67ee619abfb9424344f07bff57dbc616fc02a; each referenced row preserves root/relative_path/bytes/fullSHA','independent_regime_bound':False,'source_absent':None,'download_required':None})
old=[r for r in rows if r['historical_exact_sources']];new=[r for r in rows if r['p3_stock_batch_count']]
ck('15 historical dates and17 P3dates',len(old)==15 and len(new)==17)
ck('all32 dates have indexed status-related RAW',all(r['raw_status_related_files_identified'] for r in rows))
ck('no regime inference from caps',not any(r['independent_regime_bound'] for r in rows))
ck('duplicates preserved on09-10and09-24',all(len(r['historical_exact_sources'])==2 for r in old if r['trade_date'] in ['2026-09-10','2026-09-24']))
ck('inventory summary counts batches not unique dates',len(inv['dates_with_complete_status_and_limits'])>len(set(inv['dates_with_complete_status_and_limits'])))
ck('unbound ST explicitly recorded','is_st' in rest['fields_not_restored'])
ck('prior13writecount',read(R/'PRIOR_13_FILES.json')['total']==len(read(R/'PRIOR_13_FILES.json')['files'])==13)
out('DAILY_EVIDENCE_MATRIX.json',{'requested_review_interval':['2026-09-04','2026-10-28'],'calendar_policy_extended':False,'dates':rows,'extra_requested_endpoint':{'date':'2026-10-28','calendar_status':'UNRESOLVED_IN_PINNED_INPUTS','raw_file_status':'NOT_IDENTIFIED_IN_SELECTED_RETAINED_INDICES_NOT_SOURCE_ABSENCE','download_required':None},'identified_dates':len(rows),'regime_admitted_dates':0,'supplier_calls':0,'orders_allowed':False})
buf=io.StringIO();w=csv.writer(buf);w.writerow(['trade_date','historical_raw_members','P3_stock_batch_members','independent_regime_bound','download_required'])
for r in rows:w.writerow([r['trade_date'],len(r['historical_exact_sources']),r['p3_stock_batch_count'],'false','UNDETERMINED'])
w.writerow(['2026-10-28','NOT_IDENTIFIED','NOT_IDENTIFIED','false','UNDETERMINED_CALENDAR'])
(R/'DAILY_EVIDENCE_MATRIX.csv').write_text(buf.getvalue())
out('DESK_CHECKS.json',{'assertions':len(checks),'checks':checks,'scope':'RETAINED_INDEX_AND_DATE_JOIN_ONLY_NO_ENGINE_TEST','source_bodies_executed':False,'backtest_admission':False,'units_established':False,'regime_bound':False})
print(json.dumps({'assertions':len(checks),'observed_dates':len(rows),'historical_dates':len(old),'P3_dates':len(new),'historical_source_references':sum(len(r['historical_exact_sources']) for r in old),'P3_batch_references':sum(r['p3_stock_batch_count'] for r in new),'10-28':'UNRESOLVED','actual_scope':'GPT_DESK_ONLY'}))
