"""Fixed C: fixture-only P1 conformance task. No native price input or cleaning."""
import json,os,socket,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import p1_layer as layer

ROOT=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_P1_NATIVE_TEST_20261101')
PACKAGE=ROOT/'package'
EXE=r'E:\BLACKBOX\.venv\Scripts\python.exe'
CAL=Path(r'E:\BLACKBOX\STAGING\BLACKBOX_RAW_NONE_INCREMENT_20261027_R1\CALENDAR.json')
PREFLIGHT=Path(r'E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py')
BASE=Path(r'E:\BLACKBOX\脚本\_base.py')

def safe(path):
    for p in [path,*path.parents]:
        if p.exists() or p.is_symlink():
            s=p.lstat()
            if p.is_symlink() or getattr(s,'st_file_attributes',0)&0x400 or (hasattr(p,'is_junction') and p.is_junction()):
                raise RuntimeError('REPARSE:'+str(p))

def write(path,data):
    with path.open('xb') as f:f.write(data)
    if path.read_bytes()!=data:raise RuntimeError('READBACK')

def jwrite(path,obj):write(path,json.dumps(obj,ensure_ascii=False,indent=2).encode())

def run(argv,prefix,out):
    start=datetime.now(timezone.utc).isoformat()
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    with (out/(prefix+'.stdout.txt')).open('xb') as stdout,(out/(prefix+'.stderr.txt')).open('xb') as stderr:
        p=subprocess.run(argv,cwd=PACKAGE,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,timeout=60,env=env,check=False)
    r={'argv':argv,'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat(),'actual_exit':p.returncode}
    jwrite(out/(prefix+'.json'),r)
    if p.returncode:raise RuntimeError(prefix+'_EXIT_'+str(p.returncode))

def main():
    if os.name!='nt' or socket.gethostname().upper()!='ZHANGWEI' or os.path.normcase(sys.executable)!=os.path.normcase(EXE):
        raise RuntimeError('HOST_OR_INTERPRETER')
    for p in [ROOT,PACKAGE,CAL,PREFLIGHT,BASE]:safe(p)
    if (ROOT/'result_001').exists():raise RuntimeError('OUTPUT_EXISTS')
    write(ROOT/'RUN_ONCE.json',b'{"task":"BLACKBOX_P1_NATIVE_TEST_20261101"}')
    out=ROOT/'result_001';out.mkdir(exist_ok=False)
    try:
        package=json.loads((PACKAGE/'PACKAGE.json').read_bytes())
        for row in package['files']:
            p=PACKAGE/row['path'];safe(p);b=p.read_bytes()
            if len(b)!=row['bytes'] or layer.sha(b)!=row['sha256']:raise RuntimeError('PACKAGE_PIN')
        originals={p:p.read_bytes() for p in [CAL,PREFLIGHT,BASE]}
        for p,expected in [(CAL,layer.CAL_SHA),(PREFLIGHT,'3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217'),(BASE,'b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258')]:
            if layer.sha(originals[p])!=expected:raise RuntimeError('SOURCE_PIN:'+str(p))
        contract=layer.load_contract(PACKAGE)
        run([EXE,'-B','-X','utf8',str(PREFLIGHT),'--task-class','DATA'],'preflight',out)
        gate=(out/'preflight.stdout.txt').read_text(encoding='utf-8')
        if 'MUST_READ_PRECHECK = PASS' not in gate:raise RuntimeError('PREFLIGHT_LITERAL_PASS_MISSING')
        run([EXE,'-B','-X','utf8','-m','unittest','-v','test_p1'],'tests',out)
        log=(out/'tests.stderr.txt').read_text(encoding='utf-8')
        if 'Ran 20 tests' not in log or not log.rstrip().endswith('OK'):raise RuntimeError('TEST_COUNT_OR_SKIPS')
        plan=[{'data_date':d,'presumed_available_at':layer.available_at(d,contract),
               'status':'PRESUMED' if layer.available_at(d,contract) else 'UNRESOLVED'} for d in contract['days'][1:]]
        if any(p.read_bytes()!=b for p,b in originals.items()):raise RuntimeError('SOURCE_CHANGED')
        jwrite(out/'DATE_PLAN.json',{'policy_body_sha256':layer.POLICY_SHA,'calendar_sha256':layer.CAL_SHA,'dates':plan})
        jwrite(out/'RESULT.json',{'status':'NATIVE_FIXTURE_CONFORMANCE_ONLY','host':socket.gethostname(),'python':sys.version,
           'policy_approved':True,'tests':20,'native_price_rows_read':0,'cleaning_run':False,
           'backtest_admission':False,'orders_allowed':False,'source_recheck':'EXACT'})
        entries=[]
        for p in sorted(out.iterdir()):
            b=p.read_bytes();entries.append({'path':p.name,'bytes':len(b),'sha256':layer.sha(b)})
        jwrite(out/'LOCAL_READBACK.json',{'files':entries,'scope':'earlier result files only'})
        return 0
    except Exception as e:
        jwrite(out/'FAILED.json',{'error':str(e),'status':'FAILED_RETAINED_NO_RETRY'});return 2

if __name__=='__main__':sys.exit(main())
