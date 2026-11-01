"""Independent artifact audit; no native helpers or vendor access."""
from pathlib import Path
from datetime import datetime,date
import ast,hashlib,json,re
BASE=Path(__file__).resolve().parent
R=BASE/'return'
checks=[]
def ck(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 if not ok:raise AssertionError(name)
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def read(n):return json.loads((R/n).read_bytes())
def dt(s):
 x=datetime.fromisoformat(s);ck('timestamp_aware:'+s,x.utcoffset() is not None);return x
j=json.loads((BASE/'RETRIEVED_BUNDLE.json').read_bytes());runtime=json.loads((BASE/'REVIEWED_RUNTIME_BUNDLE.json').read_bytes())
files={x['path']:x for x in j['files']};issued={x['path']:x for x in runtime};bodies={k:x['content'].encode() for k,x in files.items()}
expected_result={'CAPTURE_RESULT.json','LOCAL_READBACK.json','PREFLIGHT_RUN.json','RULES_AFTER.json','RULES_BEFORE.json','SOURCE_IDENTITY.json','TEST_RUN.json','TRADE_DAY_SEQUENCE.json','preflight.stderr.txt','preflight.stdout.txt','tests.stderr.txt','tests.stdout.txt'}
expected={'ACK.json','REPORT.md','DELIVERY_MANIFEST.json','UPLOAD_READBACK.json','capture/RUN_ONCE.json'}|{'capture/result_001/'+n for n in expected_result}|{'outer/'+n for n in ('RUN_ONCE.json','OUTER_RUN.json','OUTER.stdout.txt','OUTER.stderr.txt')}
ck('exact_21_return_files',set(files)==expected and len(files)==21)
ck('all_local_return_files',set(str(x.relative_to(R)).replace('\\','/') for x in R.rglob('*') if x.is_file())==expected)
for n,x in sorted(files.items()):
 b=(R/n).read_bytes();ck('immutable_blob:'+n,b==bodies[n] and len(b)==x['size'] and blob(b)==x['sha'])
zero={n for n,b in bodies.items() if not b}
ck('exact_four_empty_streams',zero=={'outer/OUTER.stdout.txt','outer/OUTER.stderr.txt','capture/result_001/preflight.stderr.txt','capture/result_001/tests.stdout.txt'})
manifest=read('DELIVERY_MANIFEST.json');upload=read('UPLOAD_READBACK.json');local=read('capture/result_001/LOCAL_READBACK.json')
ck('delivery19_predecessors',manifest['count']==len(manifest['files'])==19 and {x['path'] for x in manifest['files']}==expected-{'DELIVERY_MANIFEST.json','UPLOAD_READBACK.json'})
for x in manifest['files']:
 b=bodies[x['path']];ck('delivery_member:'+x['path'],len(b)==x['bytes']==x['remote_bytes'] and sha(b)==x['sha256'] and blob(b)==x['blob'] and x['readback_byte_equal'] is True)
ck('upload20_predecessors',upload['predecessor_count']==len(upload['predecessor_set'])==len(upload['observations'])==20 and set(upload['predecessor_set'])==expected-{'UPLOAD_READBACK.json'} and {x['path'] for x in upload['observations']}==set(upload['predecessor_set']))
for x in upload['observations']:
 b=bodies[x['path']];ck('upload_member:'+x['path'],len(b)==x['bytes']==x['remote_bytes'] and sha(b)==x['sha256'] and blob(b)==x['blob'] and x['readback_byte_equal'] is True)
ck('upload_no_self_reference',upload['all_byte_equal'] is True and 'UPLOAD_READBACK.json' not in upload['predecessor_set'])
ck('manifest_bound_in_upload',upload['delivery_manifest_blob']==blob(bodies['DELIVERY_MANIFEST.json']) and upload['delivery_manifest_bytes']==len(bodies['DELIVERY_MANIFEST.json']) and upload['delivery_manifest_sha256']==sha(bodies['DELIVERY_MANIFEST.json']))
ck('local11_predecessors',len(local['files'])==11 and {x['path'] for x in local['files']}==expected_result-{'LOCAL_READBACK.json'})
for x in local['files']:
 b=bodies['capture/result_001/'+x['path']];ck('local_member:'+x['path'],len(b)==x['bytes'] and sha(b)==x['sha256'])
package=json.loads(issued['PACKAGE.json']['content']);contract=json.loads(issued['CALENDAR_FREEZE_CONTRACT.json']['content']);pins=json.loads(issued['RULE_PINS.json']['content'])['files']
ck('issued8_runtime_files',len(issued)==8 and {x['path'] for x in package['files']}==set(issued)-{'PACKAGE.json'})
for x in runtime:
 b=x['content'].encode();ck('reviewed_runtime_git_blob:'+x['path'],blob(b)==x['sha'])
for x in package['files']:
 b=issued[x['path']]['content'].encode();ck('issued_payload:'+x['path'],len(b)==x['bytes'] and sha(b)==x['sha256'])
ack=read('ACK.json');ck('ack_package_identity',ack['package_sha256']==sha(issued['PACKAGE.json']['content'].encode())=='0c2959a70c8d2c4e6db78143dd525ec1b46e246c6fa3ac5a9fedd579519782ec')
ck('ack_host_runtime',ack['execution_host']=='ZHANGWEI' and ack['python'].startswith('3.12.10 ') and ack['executable']==r'E:\BLACKBOX\.venv\Scripts\python.exe' and ack['pyarrow']=='24.0.0' and ack['source_read'] is False)
ck('ack_six_operational_pins',ack['operational_files']==pins)
ck('six_pins_before_after',read('capture/result_001/RULES_BEFORE.json')==pins==read('capture/result_001/RULES_AFTER.json') and bodies['capture/result_001/RULES_BEFORE.json']==bodies['capture/result_001/RULES_AFTER.json'])
task=contract['task_id'];ck('all_task_ids_match',task==ack['task_id']==manifest['task_id']==upload['task_id']==read('outer/RUN_ONCE.json')['task_id']==read('capture/RUN_ONCE.json')['task'])
ck('both_markers_forbid_replay',read('outer/RUN_ONCE.json')['replay_allowed'] is False and read('capture/RUN_ONCE.json')['replay_allowed'] is False)
ck('dispatch_commit_binding',manifest['dispatch_commit']==upload['dispatch_commit']=='046bf0a8dd615f20800499918ec5d3fee9a8086e')
outer=read('outer/OUTER_RUN.json');pre=read('capture/result_001/PREFLIGHT_RUN.json');test=read('capture/result_001/TEST_RUN.json')
for name,r in [('capture',outer),('preflight',pre),('tests',test)]:ck('actual_exit_zero:'+name,r['actual_exit']==0)
exe=r'E:\BLACKBOX\.venv\Scripts\python.exe';pack=r'C:\LAN_SHARE_REPORT\BLACKBOX_HISTORICAL_CALENDAR_FREEZE_20261101_PACKAGE\package'
ck('capture_argv',outer['argv']==[exe,'-B','-X','utf8',pack+r'\freeze_calendar.py'])
ck('preflight_argv',pre['argv']==[exe,'-B','-X','utf8',r'E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py','--task-class','DATA'])
ck('test_argv',test['argv']==[exe,'-B','-X','utf8',pack+r'\test_calendar.py'])
ack_commit=j['ack_commits'][0];ck('ack_git_blob_present_before_execution',ack_commit['sha']=='5fae44cc0411a1b230465c4b229b73e01d1ba3be' and dt(ack['utc'])<=dt(ack_commit['commit']['committer']['date'])<dt(outer['start_utc']))
ck('ordered_process_intervals',dt(outer['start_utc'])<=dt(pre['start_utc'])<=dt(pre['end_utc'])<=dt(test['start_utc'])<=dt(test['end_utc'])<=dt(outer['end_utc']))
pretext=bodies['capture/result_001/preflight.stdout.txt'].decode();ck('literal_preflight_status','MUST_READ_PRECHECK = PASS' in pretext and 'TASK_CLASS = DATA' in pretext and 'HAND_READ = NOT_SUFFICIENT' in pretext)
for pin in pins[2:]:ck('literal_preflight_pin:'+pin['path'],pin['sha256'] in pretext or pin['path'].endswith('MUST_READ_MANIFEST_CURRENT.json'))
tree=ast.parse(issued['test_calendar.py']['content']);names=[]
for c in tree.body:
 if isinstance(c,ast.ClassDef):names += [(c.name,m.name) for m in c.body if isinstance(m,ast.FunctionDef) and m.name.startswith('test_')]
testtext=bodies['capture/result_001/tests.stderr.txt'].decode();actual=re.findall(r'^test_\w+ \(__main__\.(\w+)\.(test_\w+)\) \.\.\. ok\r?$',testtext,re.M)
ck('exact25_native_names_no_skip',len(names)==len(actual)==25 and set(names)==set(actual) and 'Ran 25 tests' in testtext and testtext.rstrip().endswith('OK') and 'skipped' not in testtext and 'FAIL' not in testtext and 'ERROR' not in testtext)
seq=read('capture/result_001/TRADE_DAY_SEQUENCE.json');source=read('capture/result_001/SOURCE_IDENTITY.json');result=read('capture/result_001/CAPTURE_RESULT.json')
ck('source_binding',source==seq['source']==result['source'] and source['path']==contract['source_path'] and source['bytes']==24616 and source['sha256']=='d044d628279d48c1644eb7913af9e45d27d17b04b086f6d316936e31d6eddcea' and source['sha256'].startswith(contract['known_sha256_prefix']))
ck('no_local_repin',contract['known_full_sha256']=='NOT_YET_MEASURED' and contract['known_sha256_prefix']=='d044d628279d48c1')
rawdays=seq['trade_days'];days=[date.fromisoformat(x) for x in rawdays]
ck('exact3097_ordered_unique_dates',len(days)==len(set(days))==seq['rows']==result['rows']==3097 and all(a<b for a,b in zip(days,days[1:])))
ck('strict_iso_calendar_dates',all(d.isoformat()==s and len(s)==10 for d,s in zip(days,rawdays)))
ck('exact_physical_positions',seq['physical_row_positions']==list(range(3097)))
ck('calendar_endpoints',rawdays[0]==seq['first']==result['first']=='2014-01-02' and rawdays[-1]==seq['last']==result['last']=='2026-09-24')
ck('schema_ms_and_unadjusted_local_date_axis',seq['arrow_schema']=='trade_date: timestamp[ms]' and 'timeUnit=milliseconds' in seq['parquet_footer_schema'] and 'isAdjustedToUTC=false' in seq['parquet_footer_schema'])
ck('no_calendar_availability_admission',seq['calendar_complete'] is False and seq['historical_availability_established'] is False and seq['policy_calendar_replaced'] is False and result['calendar_admission'] is False and result['orders_allowed'] is False and result['no_original_body_copy'] is True)
ck('native_reported_stability',result['source_before_after_byte_equal'] is True and result['status']=='FROZEN_OBSERVATION_AWAITING_GPT')
ck('schema_metadata_hash_shape',re.fullmatch('[0-9a-f]{64}',seq['schema_metadata_sha256']) is not None)
p1raw=(BASE.parent/'p1_dispatch/CALENDAR.json').read_bytes();p1=json.loads(p1raw);ck('P1_calendar_frozen_pin',sha(p1raw)=='ab00fa8c597c9b01977cc060a202371d2de73a6a32b8a4fe6cc533a705d056d9')
latest=p1['returned'];ck('P1_ordered_unique',latest==sorted(set(latest)))
overlap=sorted(set(rawdays)&set(latest));ck('seam_shared09_24_exact',overlap==['2026-09-24'] and rawdays[-1]==latest[0])
ck('P1_next09_28_no_weekday_inference',latest[1]=='2026-09-28' and '2026-09-25' not in latest)
union=rawdays+latest[1:];ck('review_only_union3114',len(union)==len(set(union))==3114 and union==sorted(union) and union[-1]=='2026-10-27')
ck('no10_27_successor_available',all(x<='2026-10-27' for x in union))
years={}
for d in days:years[str(d.year)]=years.get(str(d.year),0)+1
out={'acceptance':'ACCEPTED_BOUNDED_NATIVE_CALENDAR_OBSERVATION_AND_HANDOFF_ONLY','snapshot':j['snapshot'],'checks_passed':len(checks),'checks':checks,'files':len(files),'file_bytes':sum(len(b) for b in bodies.values()),'declared_payload_files':19,'declared_payload_bytes':sum(len(bodies[x['path']]) for x in manifest['files']),'upload_predecessors':20,'empty_streams':sorted(zero),'source_observation':source,'source_bytes_independently_received':False,'source_full_hash_independently_recomputed_by_GPT':False,'derived_sequence_rows':len(days),'calendar_by_year':years,'overlap':overlap,'P1_successor_of_shared_boundary':latest[1],'review_only_combined_rows':len(union),'combined_calendar_activated':False,'last_day_successor':'UNRESOLVED','capture_duration_seconds':(datetime.fromisoformat(outer['end_utc'])-datetime.fromisoformat(outer['start_utc'])).total_seconds(),'preflight_duration_seconds':(datetime.fromisoformat(pre['end_utc'])-datetime.fromisoformat(pre['start_utc'])).total_seconds(),'tests_duration_seconds':(datetime.fromisoformat(test['end_utc'])-datetime.fromisoformat(test['start_utc'])).total_seconds(),'upload_receipt_identity':{'bytes':len(bodies['UPLOAD_READBACK.json']),'sha256':sha(bodies['UPLOAD_READBACK.json']),'git_blob':blob(bodies['UPLOAD_READBACK.json'])},'backtest_admission':False,'current_switch':False,'orders_allowed':False,'documentation_findings':['Chat says22 files but actual exact set19+manifest+readback=21; no missing file or rerun required.','REPORT contains Chinese prose contrary to the English HUB prose requirement; preserve original as evidence, do not rewrite it or claim full documentation conformance. GPT review is English.','Capture interval is1.283349seconds; REPORT also quotes1440ms shell elapsed. These are different observations and cannot be presented as the same measured interval.','Original source body was intentionally not copied by task; full source SHA and stability are native code/receipt observations, not GPT direct-original-byte measurements.']}
(BASE/'INDEPENDENT_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
(BASE/'CALENDAR_SEAM_REVIEW.json').write_text(json.dumps({'status':'DESK_COMPARISON_ONLY_NOT_POLICY_EXTENSION','historical_source':source,'historical_rows':3097,'P1_calendar_sha256':sha(p1raw),'P1_rows':len(latest),'shared_dates':overlap,'shared_date_physical_position':3096,'P1_next_after_shared':'2026-09-28','combined_rows_if_separately_approved':3114,'combined_first':'2014-01-02','combined_last':'2026-10-27','no_successor_for_last_day':True,'availability_presumption_not_true_historical_availability':True,'owner_approval_required_before_extension':True,'policy_changed':False,'calendar_written_or_activated':False},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['checks','documentation_findings','empty_streams']},ensure_ascii=False))
