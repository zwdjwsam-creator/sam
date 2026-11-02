"""Collect literal isolated regression outcomes; no native roots or data opened."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,subprocess,sys,tempfile

ROOT=Path(__file__).parent
results=[]
with tempfile.TemporaryDirectory() as tmp:
    base=Path(tmp);env=dict(os.environ,BLACKBOX_STDIO_FIXTURE_ROOT=str(base))
    for mode in ('old','fixed','real'):
        (base/mode).mkdir()
        argv=[sys.executable,'-B','-X','utf8',str(ROOT/'stdio_regression.py'),mode,str(base/mode)]
        start=datetime.now(timezone.utc).isoformat();p=subprocess.run(argv,env=env,capture_output=True)
        result=dict(mode=mode,argv=argv,actual_exit=p.returncode,start_utc=start,end_utc=datetime.now(timezone.utc).isoformat(),stdout=p.stdout.decode(),stderr=p.stderr.decode())
        results.append(result);assert p.returncode==0,result
json_result=dict(scope='GPT host actual child-process regression; Windows native outcome still pending',results=results,actual_native_execution=False)
(ROOT/'STDIO_REGRESSION_RESULTS.json').write_text(json.dumps(json_result,indent=2)+'\n')
print(json.dumps({r['mode']:json.loads(r['stdout']) for r in results}))
