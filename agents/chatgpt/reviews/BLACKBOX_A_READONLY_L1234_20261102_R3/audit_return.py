"""Audit exact R2 failure receipts, not a native observation acceptance."""
from pathlib import Path
from datetime import datetime
import json,hashlib
ROOT=Path(__file__).parent
x=json.loads(Path('r3_source_bundle.json').read_bytes());prefix='agents/chatgpt/inbox/BLACKBOX_A_READONLY_L1234_20261102_R2/ZHANGWEI/'
files={r['path'][len(prefix):]:r for r in x['returns']};checks=[]
def check(v,name):
    if not v:raise AssertionError(name)
    checks.append(name)
def data(n):return files[n]['content'].encode()
def obj(n):return json.loads(data(n))
def sha(b):return hashlib.sha256(b).hexdigest()
check(len(files)==27,'27_RETURN_MEMBERS')
for n,r in files.items():
 b=data(n);check(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['sha'],'BLOB:'+n)
m=obj('DELIVERY_MANIFEST.json');rb=obj('UPLOAD_READBACK.json');seal=obj('control_logs/SEAL_CONTROL_MANIFEST.json')
check(len(m['files'])==20 and sum(r['bytes'] for r in m['files'])==m['bytes']==5734,'20_PAYLOADS_5734_BYTES')
for r in m['files']+seal['files']:
 check(len(data(r['path']))==r['bytes'] and sha(data(r['path']))==r['sha256'],'MANIFEST:'+r['path'])
expected={r['path'] for r in m['files']+seal['files']}|{'DELIVERY_MANIFEST.json','control_logs/SEAL_CONTROL_MANIFEST.json','UPLOAD_READBACK.json'}
check(set(files)==expected,'RETURN_TREE_EXACT_SET')
check(len(m['absent_conditional_members'])==rb['conditional_members_absent']==55 and len(set(m['absent_conditional_members']))==55,'55_ABSENT_CONDITIONAL_MEMBERS')
check(all(p not in files for p in m['absent_conditional_members']),'NO_FORGED_CONDITIONAL_OUTPUTS')
check(not any(n.startswith('capture/') for n in files),'NO_CAPTURE_MEMBER')
check(len(rb['observations'])==rb['predecessor_count']==26,'26_READBACK_PREDECESSORS')
check({r['path'] for r in rb['observations']}==set(files)-{'UPLOAD_READBACK.json'},'READBACK_SET')
for r in rb['observations']:
 check(len(data(r['path']))==r['bytes']==r['remote_bytes'] and sha(data(r['path']))==r['sha256'] and r['blob']==files[r['path']]['sha'] and r['readback_byte_equal'] is True,'READBACK:'+r['path'])
check(rb['all_byte_equal'] is True and not rb['unresolved_failures'],'READBACK_COMPLETE_CLAIM_CORROBORATED')
package=x['package']['content'].encode();check(sha(package)==m['package_sha256']==rb['package_sha256'],'ORIGINAL_R2_PACKAGE')
a=obj('ACK.json');bind=obj('ACK_UPLOAD.json')
check(a['package_sha256']==sha(package),'ACK_PACKAGE')
check(bind['ack_bytes']==len(data('ACK.json'))==2697 and bind['ack_sha256']==sha(data('ACK.json')) and bind['ack_blob_sha']==files['ACK.json']['sha'],'ACK_BINDING')
check(bind['git_commit']==rb['ack_commit'],'ACK_COMMIT')
exits=[obj('control_logs/'+p+'.process.json')['actual_child_exit'] for p in ('prepare','bind','launch','seal')]
check(exits==[0,0,2,0],'PHASE_EXITS_0_0_2_0')
outer=obj('outer/OUTER_PROCESS.json');check(outer['actual_child_exit'] is None,'NO_OBSERVER_CHILD_EXIT')
check(outer['error']==dict(error='UNREVIEWED_SUBPROCESS',error_type='Safety'),'EXACT_FAILURE')
check(obj('FIXTURE_STATUS.json')['exists'] is False and rb['capture_root_created'] is False,'CAPTURE_NOT_CREATED_REPORTED')
t=json.loads((ROOT/'RETURN_GIT_TIMING.json').read_bytes());check(datetime.fromisoformat(t[bind['git_commit']]['committer'].replace('Z','+00:00'))<datetime.fromisoformat(outer['start_utc']),'ACK_GIT_BEFORE_LAUNCH')
for r in x['runtime']:
 b=r['content'].encode();check(len(b)==r['bytes'] and sha(b)==r['sha256'],'ORIGINAL_RUNTIME:'+r['path'])
result=dict(status='R2_FAILED_HANDOFF_IDENTITIES_VERIFIED_ZERO_OBSERVATIONS',snapshot=x['snapshot'],assertions=len(checks),checks=checks,
 return_files=27,return_bytes=sum(len(data(n)) for n in files),empty_file_members=sum(not data(n) for n in files),
 phase_exits=exits,actual_observer_child_exit=None,native_observations=0,conditional_absences=55,
 local_diagnostics_scope=rb['diagnostics'].get('scope'),
 double_Popen_attribution='Local diagnostic summary, not a supplied raw event trace. Upstream3.12.10 independently documents a string Popen event and a separate _winapi.CreateProcess event.',
 extra_wrong_bind_invocations='User/local report only; separate literal failed-invocation receipts not supplied. Do not recreate them.',ORDER_ALLOWED=False)
(ROOT/'FAILED_RETURN_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
