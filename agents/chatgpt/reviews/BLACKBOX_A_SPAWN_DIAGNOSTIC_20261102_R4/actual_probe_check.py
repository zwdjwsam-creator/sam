"""GPT-only actual print-child check of the exact diagnostic collector."""
from pathlib import Path
import sys,os,json
from diagnostic_probe import capture
p=Path('r4_GPT_probe_001');p.mkdir(exist_ok=False)
r=capture(p,sys.executable,os.getcwd())
assert r['actual_child_exit']==0 and r['exact_success_token'] and r['audit_events']
assert r['audit_events'][0]['command_literal']==r['argv']  # POSIX GPT host only.
assert r['audit_events'][0]['decision']=='APPROVED'
print(json.dumps(dict(actual_child_exit=r['actual_child_exit'],exact_success_token=True,literal_events_captured=True,actual_native_execution=False)))
