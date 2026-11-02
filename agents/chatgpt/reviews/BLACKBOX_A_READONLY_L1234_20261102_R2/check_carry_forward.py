"""Prove that the repair changes stdio, never the data or admission contracts."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).parent
OLD=Path('l1234_r1_original')
A='BLACKBOX_A_READONLY_L1234_20261102'
B=A+'_R2'
unchanged=[]
for name in ['observe.py','guard.py','prepare_ack.py','bind_ack_upload.py','preflight_worker.py','seal_delivery.py',
             'INPUTS.json','RULE_PINS.json','PREFLIGHT_AUX_RULES.json','L4_PREREGISTRATION.json']:
    old=(OLD/name).read_bytes();new=(ROOT/name).read_bytes()
    assert new.decode().replace(B,A).encode()==old,name
    unchanged.append(dict(path=name,original_sha256=hashlib.sha256(old).hexdigest(),repair_sha256=hashlib.sha256(new).hexdigest(),only_task_namespace_changed=old!=new))
for name in ['launch.py','run_capture.py','control.py']:
    old=(OLD/name).read_text();new=(ROOT/name).read_text().replace(B,A)
    expected=old.replace('import observe as o\n','import observe as o\nfrom subprocess_io import run_readonly_stdin\n') if name!='control.py' else old.replace('import hashlib,json,os,re,socket,subprocess,sys\n','import hashlib,json,os,re,socket,subprocess,sys\nfrom subprocess_io import run_readonly_stdin\n')
    expected=expected.replace('subprocess.run(argv,cwd=', 'run_readonly_stdin(argv,cwd=').replace('stdin=subprocess.DEVNULL,','')
    assert new==expected,name
tree=ast.parse((ROOT/'test_observe.py').read_bytes())
tests=[x.name for x in ast.walk(tree) if isinstance(x,ast.FunctionDef) and x.name.startswith('test_')]
assert len(tests)==57 and len(set(tests))==57
log=(ROOT/'OFFLINE_TEST.stderr.txt').read_text();assert 'Ran 57 tests' in log and log.rstrip().endswith('OK') and all(n+' (' in log for n in tests)
assert json.loads((ROOT/'OFFLINE_TEST_PROCESS.json').read_bytes())['actual_exit']==0
inputs=json.loads((ROOT/'INPUTS.json').read_bytes())
assert len(inputs['historical'])==17 and len(inputs['universes'])==17 and len(inputs['stock'])==1122
assert len(set(r['path'] for k in ['historical','universes','stock'] for r in inputs[k]))==1156
for p in ROOT.glob('*.py'):compile(p.read_bytes(),str(p),'exec')
result=dict(status='PASS_STDIO_ONLY_REPAIR_SCOPE',unchanged_business_and_guard_files=unchanged,
            modified_callers=['launch.py','run_capture.py','control.py'],native_tests=57,
            source_paths=1156,observation_semantics_changed=False,guard_device_write_exemption_added=False,
            data_acquisition_or_admission_added=False,actual_native_execution=False)
(ROOT/'CARRY_FORWARD_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print('PASS:1156 source paths, all field/classification/scale rules and audit restrictions unchanged;57 actual fixture tests exit0.')
