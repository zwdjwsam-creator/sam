from pathlib import Path
import hashlib,json,urllib.request
R=Path(__file__).parent;old=Path('p3_native_review/return');spec=json.loads((R/'SOURCE_FILES.json').read_bytes());base='agents/chatgpt/inbox/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/ZHANGWEI/p3_native_candidate_20261101/';checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def ok(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
files={}
for r in spec['files']:
 name=r['path'].removeprefix(base);p=old/name
 if p.exists():b=p.read_bytes()
 else:
  b=urllib.request.urlopen('https://raw.githubusercontent.com/zwdjwsam-creator/sam/'+spec['snapshot']+'/'+r['path'],timeout=45).read();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 ok(len(b)==r['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['sha'],'git:'+name);files[name]=b
man=json.loads(files['DELIVERY_MANIFEST.json']);up=json.loads(files['UPLOAD_READBACK.json']);expected=set(files)-{'DELIVERY_MANIFEST.json','UPLOAD_READBACK.json'}
ok(len(files)==27 and len(expected)==25,'27_physical_25_payloads')
ok(set(x['path'] for x in man['files'])==set(x['path'] for x in up['files'])==expected,'both_exact_payload_sets')
for label,o in [('manifest',man),('readback',up)]:
 ok(o['declared_file_count']==len(o['files'])==25 and o['declared_total_bytes']==sum(len(files[n]) for n in expected)==39484936,label+':count_bytes')
 for row in o['files']:
  b=files[row['path']];ok(row['bytes']==len(b) and row['sha256']==sha(b),label+':body:'+row['path'])
  if label=='readback':ok(row['remote_bytes']==len(b) and row['remote_sha256']==sha(b) and row['readback_byte_equal'] is True and row['remote_git_blob']==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),'remote_identity:'+row['path'])
x=up['delivery_manifest_upload'];ok(x['bytes']==len(files['DELIVERY_MANIFEST.json']) and x['sha256']==sha(files['DELIVERY_MANIFEST.json']) and x['readback_byte_equal'],'manifest_own_readback')
empty=sorted(n for n in expected if not files[n]);ok(empty==sorted(up['zero_byte_files_preserved']) and len(empty)==4,'four_empty_streams_not_five')
prior=json.loads(Path('p3_native_review/AUDIT.json').read_bytes());ok(prior['assertions']==3734 and prior['all14_admitted_rows_compared']==117460,'prior_content_audit_retained')
result={'snapshot':spec['snapshot'],'status':'ACCEPTED_BOUNDED_NATIVE_CANDIDATE_VALUE_AND_HANDOFF_ONLY','assertions':len(checks),'checks':checks,'physical_files':27,'payload_files':25,'payload_bytes':39484936,'physical_bytes':sum(map(len,files.values())),'empty_files':empty,'prior_content_assertions':3734,'candidate_files':125,'admitted_rows':117460,'quarantined_rows':1,'task_replay_allowed':False,'backtest_admission':False,'dictionary_formal_admission':False,'p1_real_data_activation':False,'current_switch_allowed':False,'release_allowed':False,'orders_allowed':False,'limitations':['Preparation/launcher outer observations and ACK-before-launch readback are executor-reported in REPORT, not independent uploaded process traces.','Closing chat END and executor final readback of UPLOAD_READBACK itself are not independently observable in HUB. GPT independently fetched and verified that final blob.','REPORT claims five empty streams; actual returned set and structured readback contain four.','One reported unpinned raw read preceded pinned readback; read-only contract deviation retained, not source/candidate mutation.']}
(R/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
