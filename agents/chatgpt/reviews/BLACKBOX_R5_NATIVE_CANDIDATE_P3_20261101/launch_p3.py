"""Programmatic outer exit receipt. Launch exactly once after uploaded ACK."""
import json,os,socket,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101')
EXE=r'E:\BLACKBOX\.venv\Scripts\python.exe'
def write(p,b):
    with p.open('xb') as f:f.write(b)
    if p.read_bytes()!=b:raise RuntimeError('OUTER_READBACK')
def main():
    if os.name!='nt' or socket.gethostname().upper()!='ZHANGWEI' or os.path.normcase(sys.executable)!=os.path.normcase(EXE):raise RuntimeError('HOST_OR_INTERPRETER')
    from native_reader import safe
    safe(ROOT);safe(ROOT/'package')
    import hashlib
    ack=json.loads(safe(ROOT/'ACK.json').read_bytes())
    package_hash=hashlib.sha256((ROOT/'package/PACKAGE.json').read_bytes()).hexdigest()
    if ack['package_sha256']!=package_hash or ack['status']!='PREPARED_NOT_EXECUTED':raise RuntimeError('ACK_PACKAGE')
    if (ROOT/'OUTER_RUN.json').exists():raise RuntimeError('OUTER_EXISTS')
    write(ROOT/'OUTER_RUN_ONCE.json',b'{"task_id":"BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101"}')
    argv=[EXE,'-B','-X','utf8',str(ROOT/'package/run_p3.py')]
    start=datetime.now(timezone.utc).isoformat()
    with (ROOT/'OUTER.stdout.txt').open('xb') as out,(ROOT/'OUTER.stderr.txt').open('xb') as err:
        p=subprocess.run(argv,cwd=ROOT/'package',stdin=subprocess.DEVNULL,stdout=out,stderr=err,check=False,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
    receipt={'argv':argv,'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat(),'actual_exit':p.returncode}
    write(ROOT/'OUTER_RUN.json',json.dumps(receipt,ensure_ascii=False,indent=2).encode())
    return p.returncode
if __name__=='__main__':sys.exit(main())
