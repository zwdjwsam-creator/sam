"""Finite phase capture; retain real child stdout/stderr/OS exit, including failures."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,socket,subprocess,sys
PACKAGE=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_A_READONLY_L1234_20261102_PACKAGE\package')
LOG=PACKAGE.parent/'control_logs'
EXE=r'E:\BLACKBOX\.venv\Scripts\python.exe'
TASK='BLACKBOX_A_READONLY_L1234_20261102'

def main():
    if not(os.name=='nt' and socket.gethostname().upper()=='ZHANGWEI' and sys.version_info[:3]==(3,12,10) and
           os.path.normcase(sys.executable)==os.path.normcase(EXE) and Path(__file__).parent==PACKAGE):raise ValueError('HOST_RUNTIME_PACKAGE')
    if len(sys.argv)<2 or sys.argv[1] not in ('prepare','bind','launch','seal'):raise ValueError('FINITE_PHASE_REQUIRED')
    phase=sys.argv[1];extra=sys.argv[2:]
    if (phase=='bind' and (len(extra)!=2 or not all(re.fullmatch('[0-9a-f]{40}',x) for x in extra))) or (phase!='bind' and extra):raise ValueError('PHASE_ARGUMENTS')
    m=json.loads((PACKAGE/'PACKAGE.json').read_bytes())
    if m['task_id']!=TASK:raise ValueError('PACKAGE_TASK')
    for r in m['files']:
        n=r['path']
        if Path(n).name!=n or '\\' in n:raise ValueError('FLAT_PACKAGE_ONLY')
        b=(PACKAGE/n).read_bytes()
        if len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:raise ValueError('PACKAGE_MEMBER_PIN:'+n)
    # These are task-owned C: control files. No data source is opened here.
    for a in reversed([LOG,*LOG.parents]):
        if a.exists() and (a.is_symlink() or getattr(a.lstat(),'st_file_attributes',0)&0x400):raise ValueError('CONTROL_REPARSE')
    LOG.mkdir(exist_ok=True)
    with (LOG/(phase+'.started.json')).open('xb') as f:f.write(json.dumps(dict(task_id=TASK,phase=phase,replay_allowed=False)).encode())
    target={'prepare':'prepare_ack.py','bind':'bind_ack_upload.py','launch':'launch.py','seal':'seal_delivery.py'}[phase]
    argv=[EXE,'-B','-X','utf8',str(PACKAGE/target),*extra]
    start=datetime.now(timezone.utc).isoformat();rc=None;error=None
    try:
        with (LOG/(phase+'.stdout.txt')).open('xb') as a,(LOG/(phase+'.stderr.txt')).open('xb') as b:
            p=subprocess.run(argv,cwd=PACKAGE,stdin=subprocess.DEVNULL,stdout=a,stderr=b,timeout=1000,check=False);rc=p.returncode
    except Exception as e:error=dict(error_type=type(e).__name__,error=str(e))
    result=dict(argv=argv,actual_child_exit=rc,error=error,start_utc=start,end_utc=datetime.now(timezone.utc).isoformat())
    with (LOG/(phase+'.process.json')).open('xb') as f:f.write(json.dumps(result,indent=2).encode())
    if phase=='seal':
        members=[]
        for suffix in ['.started.json','.stdout.txt','.stderr.txt','.process.json']:
            p=LOG/('seal'+suffix);b=p.read_bytes()
            members.append(dict(path='control_logs/'+p.name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
        with (LOG/'SEAL_CONTROL_MANIFEST.json').open('xb') as f:
            f.write(json.dumps(dict(task_id=TASK,files=members,manifest_excludes_itself=True),indent=2).encode())
    print(json.dumps(result));return 2 if rc is None else rc
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print(type(e).__name__+':'+str(e),file=sys.stderr);sys.exit(4)
