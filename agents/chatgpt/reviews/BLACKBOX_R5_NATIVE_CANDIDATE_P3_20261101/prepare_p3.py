"""Read package and native runtime only; prepare fixed pre-execution ACK."""
import json,os,socket,sys
from pathlib import Path
from datetime import datetime,timezone
import candidate_adapter as c
from native_reader import safe
ROOT=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101')
EXE=r'E:\BLACKBOX\.venv\Scripts\python.exe'
def main():
    c.require(os.name=='nt' and socket.gethostname().upper()=='ZHANGWEI','NATIVE_HOST')
    c.require(sys.version_info[:3]==(3,12,10) and os.path.normcase(sys.executable)==os.path.normcase(EXE),'INTERPRETER')
    c.require((c.pd.__version__,c.pa.__version__,c.np.__version__)==('3.0.3','24.0.0','2.5.4'),'RUNTIME_PIN')
    safe(ROOT);package=ROOT/'package';safe(package)
    c.require(not any((ROOT/n).exists() for n in ['RUN_ONCE.json','OUTER_RUN_ONCE.json','result_001','ACK.json']),'PRIOR_RUN_OR_ACK')
    b=(package/'PACKAGE.json').read_bytes();pkg=json.loads(b)
    c.require({p.name for p in package.iterdir()}=={'PACKAGE.json'}|{r['path'] for r in pkg['files']},'PACKAGE_FILE_SET')
    for r in pkg['files']:c.verify_identity(safe(package/c.relative(r['path'])),r)
    c.write_new(ROOT/'PACKAGE_VERIFY.json',c.packed({'package_sha256':c.sha(b),'verified_payloads':pkg['files']}))
    c.write_new(ROOT/'ACK.json',c.packed({'task_id':pkg['task_id'],'execution_host':socket.gethostname(),'utc':datetime.now(timezone.utc).isoformat(),
     'package_sha256':c.sha(b),'python':sys.version,'executable':sys.executable,'pandas':c.pd.__version__,'pyarrow':c.pa.__version__,'numpy':c.np.__version__,
     'status':'PREPARED_NOT_EXECUTED','ack_upload_readback_required_before_launch':True,'replay_allowed':False,'orders_allowed':False}))
    return 0
if __name__=='__main__':sys.exit(main())
