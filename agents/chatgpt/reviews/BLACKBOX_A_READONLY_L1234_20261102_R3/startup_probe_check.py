"""GPT-only actual audited child launch using the exact prepare-time probe."""
from pathlib import Path
import os,sys,json
import startup_probe
out=Path('l1234_r3_startup_probe');out.mkdir(exist_ok=False)
result=startup_probe.run(out,sys.executable,os.getcwd())
assert result['actual_child_exit']==0 and result['error'] is None
print(json.dumps(result))
