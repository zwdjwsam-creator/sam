"""Independent R3 failure handoff audit, not source-data acceptance."""
from pathlib import Path
import json,hashlib
p=Path(__file__).parent;x=json.loads(Path('r4_source_bundle.json').read_bytes())
prefix='agents/chatgpt/inbox/BLACKBOX_A_READONLY_L1234_20261102_R3/ZHANGWEI/'
fs={r['path'][len(prefix):]:r for r in x['returns']};checks=[]
def check(v,n):
 if not v:raise AssertionError(n)
 checks.append(n)
def raw(n):return fs[n]['content'].encode()
def obj(n):return json.loads(raw(n))
def sha(b):return hashlib.sha256(b).hexdigest()
check(len(fs)==16,'RETURN_COUNT')
for n,r in fs.items():
 b=raw(n);check(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['sha'],'BLOB:'+n)
m=obj('DELIVERY_MANIFEST.json');seal=obj('control_logs/SEAL_CONTROL_MANIFEST.json');rb=obj('UPLOAD_READBACK.json')
check(len(m['files'])==9 and sum(r['bytes'] for r in m['files'])==m['bytes']==1798,'PAYLOAD_9_1798')
for r in m['files']+seal['files']:check(len(raw(r['path']))==r['bytes'] and sha(raw(r['path']))==r['sha256'],'MANIFEST:'+r['path'])
check(set(fs)=={r['path'] for r in m['files']+seal['files']}|{'DELIVERY_MANIFEST.json','control_logs/SEAL_CONTROL_MANIFEST.json','UPLOAD_READBACK.json'},'EXACT_TREE')
check(len(m['absent_conditional_members'])==len(set(m['absent_conditional_members']))==rb['conditional_members_absent']==69,'69_CONDITIONAL_ABSENCES')
check(all(n not in fs for n in m['absent_conditional_members']),'NO_FORGED_CONDITIONAL_FILES')
check(len(rb['observations'])==rb['predecessor_count']==15,'15_READBACK_PREDECESSORS')
check({r['path'] for r in rb['observations']}==set(fs)-{'UPLOAD_READBACK.json'},'READBACK_SET')
for r in rb['observations']:check(r['bytes']==r['remote_bytes']==len(raw(r['path'])) and r['sha256']==sha(raw(r['path'])) and r['blob']==fs[r['path']]['sha'] and r['readback_byte_equal'] is True,'READBACK:'+r['path'])
check(rb['all_byte_equal'] is True and not rb['unresolved_failures'],'READBACK_COMPLETE')
check(sha(x['package']['content'].encode())==m['package_sha256']==rb['package_sha256']=='89e8311c8979a4dcb7940cb46e1d63d9c2a180e1a4361dc26dd8b66dd3ca832e','R3_PACKAGE_PIN')
pm=json.loads(x['package']['content']);pins={r['path']:r for r in pm['files']}
for r in x['runtime']:
 if r['path'] not in pins:continue
 b=r['content'].encode();pin=pins[r['path']];check(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'R3_RUNTIME:'+r['path'])
check(obj('control_logs/prepare.process.json')['actual_child_exit']==4 and obj('control_logs/seal.process.json')['actual_child_exit']==0,'PHASE_EXITS_4_0')
check(raw('control_logs/prepare.stderr.txt')==b'Blocked:NATIVE_STARTUP_PROBE_FAILED\r\n','LITERAL_PREPARE_FAILURE')
d=obj('startup/STARTUP_PROCESS.json')
check(d['actual_child_exit'] is None and d['error']==dict(error_type='Safety',error='UNREVIEWED_SUBPROCESS:COMMAND_LINE_NOT_REVIEWED'),'NO_PROBE_CHILD_EXIT')
check([(r['event'],r['argv_type']) for r in d['audit_event_shapes']]==[('subprocess.Popen','str'),('_winapi.CreateProcess','str')],'ONE_POPEN_ONE_WINAPI')
check(all(n not in fs for n in ['ACK.json','ACK_UPLOAD.json']) and not any(n.startswith(('outer/','capture/')) for n in fs),'NO_ACK_NO_OBSERVER')
check(all(rb[k] is False for k in ['ack_written','bind_attempted','launch_attempted','capture_root_created','outer_root_created']),'REPORTED_NO_LATER_PHASE')
check(sum(not raw(n) for n in fs)==5,'FIVE_EMPTY_FILE_MEMBERS')
out=dict(status='R3_FAILURE_HANDOFF_VERIFIED_ZERO_DATA_OBSERVATIONS',snapshot=x['snapshot'],assertions=len(checks),checks=checks,files=16,bytes=sum(len(raw(n)) for n in fs),empty_file_members=5,conditional_absences=69,prepare_exit=4,seal_exit=0,actual_probe_child_exit=None,native_observations=0,ACK_written=False,
  inference='With the pinned hook order, Popen checking completed before the recorded WinAPI event; exact rejected command remains unmeasured.',
  local_self_correction_scope=rb['correction_of_prior_local_attribution']['scope'],base_interpreter_hypothesis='UNVERIFIED_NOT_PERMISSION',ORDER_ALLOWED=False)
(p/'R3_RETURN_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='checks'}))
