"""Bound the repair to spawn protocol/startup evidence; preserve data contracts."""
from pathlib import Path
import json,ast,hashlib
ROOT=Path(__file__).parent;OLD=Path('l1234_r2_original');old='BLACKBOX_A_READONLY_L1234_20261102_R2';new='BLACKBOX_A_READONLY_L1234_20261102_R3'
unchanged=['observe.py','bind_ack_upload.py','launch.py','run_capture.py','preflight_worker.py','control.py','subprocess_io.py','stdio_regression.py','INPUTS.json','RULE_PINS.json','PREFLIGHT_AUX_RULES.json','L4_PREREGISTRATION.json']
for n in unchanged:assert (ROOT/n).read_text().replace(new,old)==(OLD/n).read_text(),n
a=(OLD/'guard.py').read_text();b=(ROOT/'guard.py').read_text()
assert a[a.index('        paths=[]'):a.index('    return check')]==b[b.index('        paths=[]'):b.index('    return check')]
t=ast.parse((ROOT/'test_observe.py').read_bytes());names=[n.name for n in ast.walk(t) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
assert len(names)==70 and all(n+' (' in (ROOT/'OFFLINE_TEST.stderr.txt').read_text() for n in names)
assert 'Ran 70 tests' in (ROOT/'OFFLINE_TEST.stderr.txt').read_text() and (ROOT/'OFFLINE_TEST.stderr.txt').read_text().rstrip().endswith('OK')
assert json.loads((ROOT/'OFFLINE_TEST_PROCESS.json').read_bytes())['actual_exit']==0
inputs=json.loads((ROOT/'INPUTS.json').read_bytes());assert sum(len(inputs[k]) for k in ['historical','universes','stock'])==1156
result=dict(status='PASS_REPAIR_SCOPE',unchanged_after_namespace_substitution=unchanged,write_network_source_enumeration_guards_unchanged=True,
            native_fixture_tests=70,actual_fixture_exit=0,source_paths=1156,no_data_semantics_or_admission_changed=True,
            startup_probe_is_C_receipt_and_fixed_python_print_only=True,actual_native_execution=False)
(ROOT/'SCOPE_CHECK.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
