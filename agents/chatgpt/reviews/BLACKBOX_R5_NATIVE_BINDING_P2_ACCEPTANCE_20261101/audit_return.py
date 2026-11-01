from pathlib import Path,PureWindowsPath
import json,hashlib,base64,importlib.util,csv,io
p=Path(__file__).parent
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda n:(p/n).read_bytes()
js=lambda n:json.loads(read(n))
checks=[]
def check(x,n):
 if not x:raise AssertionError(n)
 checks.append(n)
tree=js('tree_rows.json');actual={r['path']:r for r in tree}
check(len(actual)==14,'exact_return_file_count_14')
for n,r in actual.items():
 b=read(n);check(len(b)==r['size'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['sha'],'git_body_identity:'+n)
for name,prefix,expected in [('DELIVERY_MANIFEST.json','',12),('UPLOAD_READBACK.json','',13),('capture_001/LOCAL_READBACK.json','capture_001/',4)]:
 d=js(name);rows=d['files'];check(len(rows)==expected and len({r['path'] for r in rows})==expected,'receipt_set:'+name)
 for r in rows:
  b=read(prefix+r['path']);check(len(b)==r['bytes'] and sha(b)==r['sha256'],'receipt_hash:'+prefix+r['path'])
  if 'remote_git_blob' in r:check(r['remote_git_blob']==actual[r['path']]['sha'],'remote_blob:'+r['path'])
 if name=='DELIVERY_MANIFEST.json':
  check(sum(r['bytes'] for r in rows)==d['declared_total_bytes']==108249,'declared_delivery_bytes')
  check({r['path'] for r in rows}|{'DELIVERY_MANIFEST.json','UPLOAD_READBACK.json'}==set(actual),'closed_return_set')
check(len(read('UPLOAD_READBACK.json'))==4879 and sha(read('UPLOAD_READBACK.json'))=='aa409a932dc1a6fa6a0aa2b5fa780c8cac9d42ee8b6a0e271d55fe6ed5b4ff36','readback_self_observed_by_GPT')
check([n for n in actual if len(read(n))==0]==['OUTER.stderr.txt','OUTER.stdout.txt','capture_001/preflight.stderr.txt'],'three_literal_empty_streams')
a=js('ACK.json');pv=js('PACKAGE_VERIFY.json');pkg=js('issued_PACKAGE.json')
check(sha(read('issued_PACKAGE.json'))==a['package']['package_json_sha256']==pv['package_json_sha256'],'package_external_identity')
for r in pkg['files']:
 matches=[v for v in pv['files'] if v['path']==r['path']];check(len(matches)==1 and matches[0]['bytes']==r['bytes'] and matches[0]['sha256']==r['sha256'],'package_payload:'+r['path'])
check(sha(read('issued_collector.py'))==next(r['sha256'] for r in pkg['files'] if r['path']=='capture_environment.py'),'executed_collector_source_pin')
spec=importlib.util.spec_from_file_location('reviewed_p2',p/'issued_collector.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
e=js('capture_001/ENVIRONMENT_AND_BODIES.json');files=e['files'];check(len(files)==17 and not e['problems'] and e['status']=='COMPLETE_HANDOFF_ONLY','17_body_completion')
expected={str(PureWindowsPath(str(c.ROOT))/r) for r in c.INPUTS};check({r['path'] for r in files}==expected,'exact_source_allowlist')
decoded={};bodies=[]
for r in files:
 b=base64.b64decode(r['body_base64'],validate=True);check(len(b)==r['bytes'] and sha(b)==r['sha256'],'decoded_body:'+r['path']);decoded[r['path']]=b;bodies.append({k:r[k] for k in ('path','bytes','sha256')})
for rel,pin in c.PINS.items():check(sha(decoded[str(PureWindowsPath(str(c.ROOT))/rel)])==pin,'embedded_pin:'+rel)
check(sum(len(b) for b in decoded.values())==57240,'source_body_bytes_57240')
outer=js('OUTER_RUN.json');inner=js('capture_001/PREFLIGHT_RUN.json');stdout=read('capture_001/preflight.stdout.txt').decode()
check(outer['actual_os_exit']==inner['actual_exit_code']==0 and outer['run_count']==1 and not outer['retry'] and outer['attached_and_waited'],'actual_returned_process_receipts')
check(outer['started_utc']<=inner['started_utc']<inner['ended_utc']<=outer['ended_utc'] and a['acked_at_utc']<outer['started_utc'],'receipt_time_order')
check(inner['argv']==[c.EXE,'-X','utf8',str(PureWindowsPath(str(c.ROOT))/c.PREFLIGHT),'--task-class','DATA'],'exact_preflight_argv')
check('MUST_READ_PRECHECK = PASS' in stdout and 'HAND_READ = NOT_SUFFICIENT' in stdout and 'status = VERIFIED' in stdout,'literal_gate_output_preserved')
source=decoded[str(PureWindowsPath(str(c.ROOT))/c.PREFLIGHT)].decode()
check('HAND_READ = NOT_SUFFICIENT' in source and 'AUTHORITY_READY' in source,'HAND_READ_annotation_source_present')
calendar_path=next(k for k in decoded if k.endswith('CALENDAR.json'));cal=json.loads(decoded[calendar_path]);print('CALENDAR',cal)
ptrs=[]
for rel in c.POINTERS:
 path=str(PureWindowsPath(str(c.ROOT))/rel);v=json.loads(decoded[path]);ptrs.append({'path':path,'sha256':sha(decoded[path]),'declared_dates':{k:v[k] for k in ['cleaning_as_of','daily_asof','asof','CN_RESEARCH_DATE'] if k in v}})
domain=next(k for k in decoded if k.endswith('domain_schema_contract.csv'));pit=next(k for k in decoded if k.endswith('pit_schema_contract.csv'))
rows=list(csv.DictReader(io.StringIO(decoded[domain].decode('utf-8-sig'))));pitrows=list(csv.DictReader(io.StringIO(decoded[pit].decode('utf-8-sig'))))
price=next(r for r in rows if r['domain']=='price_fq_factor');pitprice=next(r for r in pitrows if r['domain']=='price_fq_factor')
report={'task_id':c.TASK,'verdict':'ACCEPTED_BOUNDED_NATIVE_BINDING_HANDOFF_ONLY','checks_passed':len(checks),'checks':checks,'files':tree,'source_bodies':bodies,'native_runtime':{k:e[k] for k in ['host','python','executable','platform','packages']},'current_pointer_observations':ptrs,'calendar':cal,'dictionary_price_row':price,'pit_price_row':pitprice,'literal_outer_exit':0,'literal_preflight_exit':0,'native_unit_tests':'NOT_RUN_BY_CONTRACT','pre_post_original_identity':'REPORTED_AND_EXECUTED_REVIEWED_CODE_PATH; second reads not separately uploaded','process_inventory_audit':'NOT_PERFORMED','chat_END':'OWNER_SUPPLIED_CLOSING_CHAT; not inferred from repository fields','cleaning_authorized':False,'p1_activated':False,'orders_allowed':False,'next':'GPT-native-adapter repairs and separately approved presumed-availability policy; no new local task issued'}
(p/'AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('PASSED',len(checks));print('POINTERS',ptrs);print('PIT',pitprice)
