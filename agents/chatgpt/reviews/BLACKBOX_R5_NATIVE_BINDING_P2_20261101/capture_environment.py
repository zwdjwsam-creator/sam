"""One bounded ZHANGWEI read-only binding handoff. No data processing or supplier imports."""
import base64
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import socket
import stat
import subprocess
import sys
from datetime import datetime, timezone

TASK = 'BLACKBOX_R5_NATIVE_BINDING_P2_20261101'
CONTROL = Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_R5_NATIVE_BINDING_P2_20261101')
ROOT = Path(r'E:\BLACKBOX')
EXE = r'E:\BLACKBOX\.venv\Scripts\python.exe'
PREFLIGHT = '脚本/blackbox_must_read_preflight_r1.py'
PINS = {PREFLIGHT:'3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217',
        '脚本/_base.py':'b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258'}
POINTERS = ['数据/清洗成品/CURRENT_CLEANING_RELEASE.json',
 '数据/回测缓存/CURRENT_CACHE_RELEASE.json',
 '研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json',
 '研究系统/数据平面/CURRENT/DAILY_DATA_PLANE_CURRENT.json']
INPUTS = POINTERS + [PREFLIGHT,'脚本/_base.py',
 '.cursor/rules/BLACKBOX_KERNEL_ALWAYS_APPLY.mdc',
 '契约/必读/MUST_READ_MANIFEST_CURRENT.json'] + [
 '契约/必读/BLACKBOX_'+n+'_MUST_READ.md' for n in
 ['BOOTSTRAP','DATA_ACCESS','ACQUISITION','FACTOR_RESEARCH','BACKTEST','QMT']] + [
 'STAGING/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1/CALENDAR.json',
 '数据/原始只读/JQData_reference_dictionary/20_unified_data_schema_contract_freeze_full_R1/02_domain_schema/domain_schema_contract.csv',
 '数据/原始只读/JQData_reference_dictionary/20_unified_data_schema_contract_freeze_full_R1/04_pit_schema/pit_schema_contract.csv']

def digest(b):
    return hashlib.sha256(b).hexdigest()

def blocked_reparse(s):
    return bool(getattr(s,'st_file_attributes',0) & 0x400) or stat.S_ISLNK(s.st_mode)

def check_path(p):
    p = Path(p)
    for part in [*reversed(p.parents),p]:
        if part.exists() or part.is_symlink():
            s = part.lstat()
            if blocked_reparse(s) or (hasattr(part,'is_junction') and part.is_junction()):
                raise RuntimeError('REPARSE_PATH:'+str(part))

def read_one(p):
    p=Path(p);check_path(p)
    a=p.stat()
    if not stat.S_ISREG(a.st_mode) or a.st_size>2*1024*1024:
        raise RuntimeError('NOT_BOUNDED_REGULAR_FILE')
    b=p.read_bytes();z=p.stat()
    if (a.st_size,a.st_mtime_ns,a.st_ino)!=(z.st_size,z.st_mtime_ns,z.st_ino) or len(b)!=a.st_size:
        raise RuntimeError('SOURCE_DRIFT')
    return b

def write_exact(p,b):
    p=Path(p);check_path(p.parent)
    with p.open('xb') as f:f.write(b)
    if p.read_bytes()!=b:raise RuntimeError('OUTPUT_READBACK')

def dump(p,obj):
    write_exact(p,json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False).encode('utf-8'))

def reserve(control):
    control=Path(control);check_path(control)
    if (control/'capture_001').exists():raise RuntimeError('CAPTURE_EXISTS')
    # Marker survives removal of the candidate/capture subdirectory.
    write_exact(control/'RUN_ONCE.json',json.dumps({'task_id':TASK,'at':datetime.now(timezone.utc).isoformat()}).encode())
    (control/'capture_001').mkdir(exist_ok=False)
    return control/'capture_001'

def package_versions():
    out={}
    for name in ['pandas','pyarrow','numpy']:
        try:
            d=importlib.metadata.distribution(name)
            out[name]={'version':d.version,'location':str(d.locate_file(''))}
        except importlib.metadata.PackageNotFoundError:out[name]={'status':'MISSING'}
    return out

def main():
    if os.name!='nt' or socket.gethostname().upper()!='ZHANGWEI':
        raise RuntimeError('WRONG_HOST_OR_OS')
    if os.path.normcase(os.path.abspath(sys.executable))!=os.path.normcase(EXE):
        raise RuntimeError('UNAPPROVED_INTERPRETER')
    out=reserve(CONTROL)
    report={'task_id':TASK,'host':socket.gethostname(),'execution_host':'ZHANGWEI',
      'python':sys.version,'executable':sys.executable,'platform':platform.platform(),
      'packages':package_versions(),'supplier_calls':0,'order_allowed':False,
      'cleaning_run':False,'current_switched':False,'files':[],'problems':[]}
    originals={}
    for rel in INPUTS:
        try:
            b=read_one(ROOT/rel);originals[rel]=b
            report['files'].append({'path':str(ROOT/rel),'bytes':len(b),'sha256':digest(b),
                'body_base64':base64.b64encode(b).decode('ascii')})
        except Exception as e:report['problems'].append({'path':rel,'error':str(e)})
    gate={'status':'NOT_RUN','reason':'SOURCE_PIN_MISMATCH_OR_MISSING'}
    if all(rel in originals and digest(originals[rel])==pin for rel,pin in PINS.items()):
        argv=[EXE,'-X','utf8',str(ROOT/PREFLIGHT),'--task-class','DATA']
        start=datetime.now(timezone.utc).isoformat()
        try:
            result=subprocess.run(argv,stdin=subprocess.DEVNULL,capture_output=True,timeout=60,check=False)
            write_exact(out/'preflight.stdout.txt',result.stdout)
            write_exact(out/'preflight.stderr.txt',result.stderr)
            gate={'argv':argv,'started_utc':start,'ended_utc':datetime.now(timezone.utc).isoformat(),
                  'actual_exit_code':result.returncode,'status':'RETURNED_FOR_GPT_REVIEW'}
            if result.returncode!=0:report['problems'].append({'preflight_exit':result.returncode})
        except subprocess.TimeoutExpired as e:
            write_exact(out/'preflight.stdout.txt',e.stdout or b'')
            write_exact(out/'preflight.stderr.txt',e.stderr or b'')
            gate={'argv':argv,'started_utc':start,'status':'TIMEOUT_NO_SUCCESS_EXIT_CLAIM'}
            report['problems'].append({'preflight':'TIMEOUT'})
    else:report['problems'].append({'preflight':'PIN_MISMATCH_OR_MISSING'})
    for rel,before in originals.items():
        try:
            if read_one(ROOT/rel)!=before:report['problems'].append({'changed_source':rel})
        except Exception as e:report['problems'].append({'recheck':rel,'error':str(e)})
    report['status']='COMPLETE_HANDOFF_ONLY' if not report['problems'] else 'PARTIAL_OR_BLOCKED_RETAINED'
    dump(out/'ENVIRONMENT_AND_BODIES.json',report);dump(out/'PREFLIGHT_RUN.json',gate)
    files=[]
    for p in sorted(out.iterdir()):
        b=p.read_bytes();files.append({'path':p.name,'bytes':len(b),'sha256':digest(b)})
    dump(out/'LOCAL_READBACK.json',{'task_id':TASK,'files':files,'readback':'EXACT'})
    return 0 if not report['problems'] else 2

if __name__=='__main__':
    sys.exit(main())
