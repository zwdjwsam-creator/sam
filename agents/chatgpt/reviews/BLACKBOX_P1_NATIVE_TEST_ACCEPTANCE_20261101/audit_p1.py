from pathlib import Path
import json,hashlib,re,ast
from datetime import datetime,date,time,timedelta,timezone
p=Path(__file__).parent;q=p/'return';issued=p/'issued'
sha=lambda b:hashlib.sha256(b).hexdigest()
load=lambda n:json.loads((q/n).read_bytes())
checks=[]
def ck(ok,name):
 if not ok:raise AssertionError(name)
 checks.append(name)
rows=json.loads((p/'tree.json').read_bytes());lookup={r['path']:r for r in rows}
ck(len(lookup)==18,'exact_18_return_files')
for name,r in lookup.items():
 b=(q/name).read_bytes();ck(len(b)==r['size'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['sha'],'actual_git_blob:'+name)
for name,prefix,n in [('DELIVERY_MANIFEST.json','',16),('UPLOAD_READBACK.json','',17),('result_001/LOCAL_READBACK.json','result_001/',8)]:
 d=load(name);items=d['files'];ck(len(items)==n and len({x['path'] for x in items})==n,'receipt_set:'+name)
 for x in items:
  b=(q/(prefix+x['path'])).read_bytes();ck(len(b)==x['bytes'] and sha(b)==x['sha256'],'receipt_identity:'+prefix+x['path'])
  if 'remote_git_blob' in x:ck(x['remote_git_blob']==lookup[x['path']]['sha'],'remote_blob:'+x['path'])
 if name=='DELIVERY_MANIFEST.json':
  ck({x['path'] for x in items}|{'DELIVERY_MANIFEST.json','UPLOAD_READBACK.json'}==set(lookup),'closed_delivery_set')
  ck(sum(x['bytes'] for x in items)==d['declared_total_bytes'],'declared_payload_bytes')
up=(q/'UPLOAD_READBACK.json').read_bytes();ck(len(up)==6133 and sha(up)=='b1dd1319305812e078ca2284d4302eec787e392e918bd64d4af7782f2de504ce','GPT_upload_readback_self_observation')
ck(sum(len((q/n).read_bytes())==0 for n in lookup)==4,'four_literal_zero_byte_streams')
pkg=json.loads((issued/'PACKAGE.json').read_bytes());ack=load('ACK.json');pv=load('PACKAGE_VERIFY.json')
ck(sha((issued/'PACKAGE.json').read_bytes())==pv['package_json_sha256'],'package_external_digest')
ck(len(pkg['files'])==9,'nine_payloads')
for x in pkg['files']:
 b=(issued/x['path']).read_bytes();ck(len(b)==x['bytes'] and sha(b)==x['sha256'],'issued_payload:'+x['path'])
 received=next(r for r in pv['files'] if r['path']==x['path']);ck(received['bytes']==x['bytes'] and received['sha256']==x['sha256'],'native_payload_receipt:'+x['path'])
policy_sha=sha((issued/'POLICY_BODY.txt').read_bytes());cal_sha=sha((issued/'CALENDAR.json').read_bytes());approval=json.loads((issued/'APPROVAL.json').read_bytes())
ck(policy_sha==approval['policy_body_sha256']=='31dee3a67f7674db25b0ba4d56c169c941e28f857b8656454b6006401938f884','approved_policy_body')
ck(cal_sha==approval['calendar_sha256']=='ab00fa8c597c9b01977cc060a202371d2de73a6a32b8a4fe6cc533a705d056d9','frozen_calendar')
# Independent datetime reconstruction; do not call p1_layer.available_at or native DATE_PLAN code.
cal=json.loads((issued/'CALENDAR.json').read_bytes());days=cal['returned'];plan=load('result_001/DATE_PLAN.json');expected=[]
for day in cal['completed_session_candidates']:
 successor=next((d for d in days if d>day),None)
 at=None if successor is None else datetime.combine(date.fromisoformat(successor),time(9),timezone(timedelta(hours=8))).isoformat()
 expected.append({'data_date':day,'presumed_available_at':at,'status':'PRESUMED' if at else 'UNRESOLVED'})
ck(plan['dates']==expected,'all_17_date_rows_independent_exact')
ck(sum(x['status']=='PRESUMED' for x in expected)==16 and expected[-1]=={'data_date':'2026-10-27','presumed_available_at':None,'status':'UNRESOLVED'},'16_presumed_1_unresolved')
ck(plan['policy_body_sha256']==policy_sha and plan['calendar_sha256']==cal_sha,'plan_policy_calendar_identity')
outer=load('OUTER_RUN.json');pre=load('result_001/preflight.json');tests=load('result_001/tests.json');result=load('result_001/RESULT.json')
ck(outer['actual_os_exit']==pre['actual_exit']==tests['actual_exit']==0,'three_distinct_zero_exit_receipts')
ck(outer['run_count']==1 and outer['retry'] is False and outer['attached_and_waited'],'one_attached_run_receipt')
ck(outer['started_utc']<=pre['start_utc']<pre['end_utc']<=tests['start_utc']<tests['end_utc']<=outer['ended_utc'],'native_stage_order')
ck(ack['acked_at_utc']<outer['started_utc'],'ACK_before_execution')
prelog=(q/'result_001/preflight.stdout.txt').read_text();log=(q/'result_001/tests.stderr.txt').read_text()
ck('MUST_READ_PRECHECK = PASS' in prelog and 'HAND_READ = NOT_SUFFICIENT' in prelog,'literal_preflight_annotations')
actual_names=re.findall(r'^(test_\w+) \(test_p1.Tests\.\1\) \.\.\. ok$',log,re.M)
methods=[n.name for n in ast.walk(ast.parse((issued/'test_p1.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
ck(len(actual_names)==len(set(actual_names))==20 and set(actual_names)==set(methods),'20_exact_native_test_names_no_omission')
ck('Ran 20 tests' in log and log.rstrip().endswith('OK') and 'skipped' not in log,'literal_unittest_OK_no_skips')
ck(result['status']=='NATIVE_FIXTURE_CONFORMANCE_ONLY' and result['native_price_rows_read']==0 and result['cleaning_run'] is False and result['backtest_admission'] is False and result['orders_allowed'] is False,'bounded_native_result')
ck('result_001/FAILED.json' not in lookup,'no_failed_receipt_on_success')
report={'task_id':'BLACKBOX_P1_NATIVE_TEST_20261101','source_snapshot':'89152d8b42839cebf7a9bd9763faef0d277de787','verdict':'ACCEPTED_NATIVE_FIXTURE_CONFORMANCE_ONLY','assertions_passed':len(checks),'checks':checks,'return_files':rows,'total_return_bytes':sum(r['size'] for r in rows),'date_plan_independently_recomputed':expected,'outer_actual_exit':0,'preflight_actual_exit':0,'native_tests_actual_exit':0,'native_fixture_tests':20,'policy_body_sha256':policy_sha,'calendar_sha256':cal_sha,'policy_approved':True,'real_data_admission':False,'native_cleaning_executed':False,'orders_allowed':False,'local_extra_verification':'Owner reports one corrected index error in an auxiliary date check. That helper/source/failure output is not in the prescribed 18-file delivery; no independent acceptance of that auxiliary result. GPT date recomputation is separate.','E_source_pre_post':'Supported by pinned runner and its result; no independent second-read bodies or OS-wide trace uploaded.','P2_count_correction':{'delivery_payload_count':12,'delivery_payload_bytes':108249,'total_return_count':14,'total_return_bytes':115660}}
(p/'AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('PASS',len(checks),'return_bytes',report['total_return_bytes'])
