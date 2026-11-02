"""Independent audit of the exact failed task return, never native execution."""
from pathlib import Path
from datetime import datetime
import hashlib,json

ROOT=Path(__file__).parent
bundle=json.loads(Path('l1234_r2_source_bundle.json').read_bytes())
prefix='agents/chatgpt/inbox/BLACKBOX_A_READONLY_L1234_20261102/ZHANGWEI/'
files={f['path'][len(prefix):]:f for f in bundle['returns']}
checks=[]
def check(v,n):
    if not v:raise AssertionError(n)
    checks.append(n)
def data(n):return files[n]['content'].encode('utf-8')
def obj(n):return json.loads(data(n))
def sha(b):return hashlib.sha256(b).hexdigest()
check(len(files)==27,'27_EXACT_RETURN_PATHS')
for n,r in files.items():
    b=data(n);check(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['sha'],'IMMUTABLE_BLOB:'+n)
manifest=obj('DELIVERY_MANIFEST.json');readback=obj('UPLOAD_READBACK.json');seal=obj('control_logs/SEAL_CONTROL_MANIFEST.json')
check(len(manifest['files'])==20,'20_PREDECESSOR_PAYLOADS')
check(sum(r['bytes'] for r in manifest['files'])==manifest['bytes']==5702,'PAYLOAD_BYTE_ACCOUNTING')
for r in manifest['files']+seal['files']:
    b=data(r['path']);check(len(b)==r['bytes'] and sha(b)==r['sha256'],'DECLARED_IDENTITY:'+r['path'])
declared={r['path'] for r in manifest['files']}|{'DELIVERY_MANIFEST.json'}|{r['path'] for r in seal['files']}|{'control_logs/SEAL_CONTROL_MANIFEST.json','UPLOAD_READBACK.json'}
check(set(files)==declared,'COMPLETE_DELIVERY_TREE_SET')
check(len(manifest['absent_conditional_members'])==55,'55_CONDITIONAL_MEMBERS_NOT53')
check(len(set(manifest['absent_conditional_members']))==55,'NO_DUPLICATE_ABSENT_MEMBER')
check(all(p not in files for p in manifest['absent_conditional_members']),'NO_FORGED_MISSING_MEMBERS')
check(not any(n.startswith('capture/') for n in files),'NO_CAPTURE_RESULT_OR_CAPTURE_MARKER_UPLOADED')
check(readback['conditional_members_absent']==55,'READBACK_CONDITIONAL_COUNT')
check(len(readback['observations'])==26==readback['predecessor_count'],'26_READBACK_PREDECESSORS')
check({r['path'] for r in readback['observations']}==set(files)-{'UPLOAD_READBACK.json'},'READBACK_PREDECESSOR_SET')
for r in readback['observations']:
    b=data(r['path']);check(len(b)==r['bytes']==r['remote_bytes'] and sha(b)==r['sha256'] and files[r['path']]['sha']==r['blob'] and r['readback_byte_equal'] is True,'READBACK_IDENTITY:'+r['path'])
check(readback['all_byte_equal'] is True and not readback['unresolved_failures'],'CLAIMED_BYTE_READBACK_COMPLETE')
package=bundle['package']['content'].encode();check(sha(package)==manifest['package_sha256']==readback['package_sha256'],'ORIGINAL_PACKAGE_PIN')
ack=obj('ACK.json');bound=obj('ACK_UPLOAD.json')
check(ack['package_sha256']==sha(package),'ACK_PACKAGE')
check(ack['task_id']==bound['task_id']==manifest['task_id']=='BLACKBOX_A_READONLY_L1234_20261102','ORIGINAL_TASK_IDENTITY')
check(bound['ack_sha256']==sha(data('ACK.json')) and bound['ack_bytes']==len(data('ACK.json')) and bound['ack_blob_sha']==files['ACK.json']['sha'],'ACK_IMMUTABLE_BINDING')
check(bound['git_commit']==readback['ack_commit'],'ACK_COMMIT_BINDING')
outer=obj('outer/OUTER_PROCESS.json');prepare=obj('control_logs/prepare.process.json');bind=obj('control_logs/bind.process.json');launch=obj('control_logs/launch.process.json');sealed=obj('control_logs/seal.process.json')
check([x['actual_child_exit'] for x in (prepare,bind,launch,sealed)]==[0,0,2,0],'ACTUAL_PHASE_EXITS_0_0_2_0')
check(outer['actual_child_exit'] is None,'NO_CAPTURE_CHILD_OS_EXIT')
check(outer['error']=={'error':'WRITE_OUTSIDE_CAPTURE:nul','error_type':'Safety'},'EXACT_LAUNCHER_FAILURE')
elapsed=(datetime.fromisoformat(outer['end_utc'])-datetime.fromisoformat(outer['start_utc'])).total_seconds()
check(elapsed==0.002,'TWO_MILLISECOND_EXCEPTION_WINDOW')
check(obj('FIXTURE_STATUS.json')['exists'] is False,'NATIVE_FIXTURE_ROOT_REPORTED_ABSENT')
check(readback['capture_root_created'] is False,'CAPTURE_ROOT_NOT_CREATED_REPORTED')
timing=json.loads((ROOT/'RETURN_GIT_TIMING.json').read_bytes())
check(datetime.fromisoformat(timing[bound['git_commit']]['committer'].replace('Z','+00:00'))<datetime.fromisoformat(outer['start_utc']),'ACK_GIT_COMMIT_BEFORE_LAUNCH')
check(datetime.fromisoformat(bound['bound_utc'])<datetime.fromisoformat(outer['start_utc']),'ACK_BIND_BEFORE_LAUNCH')
for r in bundle['runtime']:
    b=r['content'].encode();check(len(b)==r['bytes'] and sha(b)==r['sha256'],'REVIEWED_ORIGINAL_RUNTIME:'+r['path'])
summary=dict(status='FAILED_LAUNCH_HANDOFF_VERIFIED_NO_OBSERVATION_ACCEPTANCE',reviewed_snapshot=bundle['snapshot'],
 checks=len(checks),check_names=checks,return_files=27,return_bytes=sum(len(data(n)) for n in files),empty_streams=sum(not data(n) for n in files),
 declared_payload_files=20,declared_payload_bytes=5702,readback_predecessors=26,conditional_absences=55,
 phase_exits=[0,0,2,0],capture_child_exit=None,launcher_error=outer['error'],launcher_elapsed_seconds=elapsed,
 actual_L1_L2_L3_L4_observations=0,local_original_presence_independently_proved=False,
 wrong_bind_path_extra_invocation='Owner/local report only; no separate literal failed-invocation receipt in the27-member return. Do not rerun it.',
 ORDER_ALLOWED=False)
(ROOT/'FAILED_RETURN_AUDIT.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='check_names'}))
