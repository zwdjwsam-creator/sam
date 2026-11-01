"""Fixed native P3 candidate. No supplier, releases, CURRENT switch or strategy entry."""
import json,os,socket,subprocess,sys,zipfile,re
from datetime import datetime,timezone
from pathlib import Path
import candidate_adapter as c
from native_reader import NativeBodyReader,safe,ROOT
from p3_common import verify_values,expected_files

TASK='BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101'
CONTROL=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101')
PACKAGE=CONTROL/'package'
OUTPUT=ROOT/'STAGING/BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101'
EXE=r'E:\BLACKBOX\.venv\Scripts\python.exe'
POINTERS={
 '数据/清洗成品/CURRENT_CLEANING_RELEASE.json':'9abad90cd952a1d623d124b794cbb0c025161cb9b80053c09980f25c0d481128',
 '数据/回测缓存/CURRENT_CACHE_RELEASE.json':'b2ce53f05e50e0d38c9f4232f6b5e94040d6a081066d24759e52dd60eb622564',
 '研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json':'574842e7802be26d648d5aa2f6d91a9b4c208744e3ecf9f146e02ece41387d89',
 '研究系统/数据平面/CURRENT/DAILY_DATA_PLANE_CURRENT.json':'8a492440257170577a5c96f66bfd81e3b93fc6dc58e547cc3acd4c7baaf3fe9b'}

def reserve():
    safe(CONTROL);safe(OUTPUT)
    c.require(not OUTPUT.exists() and not (CONTROL/'result_001').exists(),'P3_OUTPUT_EXISTS')
    c.write_new(CONTROL/'RUN_ONCE.json',c.packed({'task_id':TASK,'output':str(OUTPUT)}))
    out=CONTROL/'result_001';out.mkdir(exist_ok=False);return out

def command(argv,name,out,timeout):
    start=datetime.now(timezone.utc).isoformat()
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    with (out/(name+'.stdout.txt')).open('xb') as stdout,(out/(name+'.stderr.txt')).open('xb') as stderr:
        p=subprocess.run(argv,cwd=PACKAGE,stdin=subprocess.DEVNULL,stdout=stdout,stderr=stderr,env=env,timeout=timeout,check=False)
    c.write_new(out/(name+'.json'),c.packed({'argv':argv,'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat(),'actual_exit':p.returncode}))
    c.require(p.returncode==0,name+'_NONZERO')

def pack(candidate,out):
    manifest=json.loads((candidate/'MANIFEST.json').read_bytes())
    names=sorted([x['path'] for x in manifest['files']]+['MANIFEST.json','BUILD_COMPLETE.json'])
    pieces=[];group=[];size=22
    for name in names:
        b=(candidate/name).read_bytes();cost=len(b)+2*len(name.encode())+98
        c.require(cost+22<=7500000,'ZIP_SINGLE_MEMBER_CAP')
        if group and size+cost>7500000:pieces.append(group);group=[];size=22
        group.append(name);size+=cost
    if group:pieces.append(group)
    result=[]
    for i,members in enumerate(pieces,1):
        path=out/('candidate_part_%03d.zip'%i)
        with zipfile.ZipFile(path,'x',compression=zipfile.ZIP_STORED,allowZip64=False) as z:
            for name in members:z.write(candidate/name,name)
        b=path.read_bytes();c.require(len(b)<=7500000,'ZIP_CAP')
        with zipfile.ZipFile(path) as z:
            c.require(z.namelist()==members and z.testzip() is None,'ZIP_READBACK')
            for name in members:c.require(z.read(name)==(candidate/name).read_bytes(),'ZIP_MEMBER_READBACK')
        result.append({'path':path.name,'bytes':len(b),'sha256':c.sha(b),'members':members})
    return result

def main():
    c.require(os.name=='nt' and socket.gethostname().upper()=='ZHANGWEI','NATIVE_HOST')
    c.require(sys.version_info[:3]==(3,12,10) and os.path.normcase(sys.executable)==os.path.normcase(EXE),'INTERPRETER')
    safe(PACKAGE);out=reserve()
    try:
        pkg=json.loads((PACKAGE/'PACKAGE.json').read_bytes())
        c.require({p.name for p in PACKAGE.iterdir()}=={'PACKAGE.json'}|{r['path'] for r in pkg['files']},'PACKAGE_FILE_SET')
        for row in pkg['files']:c.verify_identity(safe(PACKAGE/c.relative(row['path'])),row)
        pre=ROOT/'脚本/blackbox_must_read_preflight_r1.py';base=ROOT/'脚本/_base.py'
        c.require(c.sha(safe(pre).read_bytes())=='3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217','PREFLIGHT_PIN')
        c.require(c.sha(safe(base).read_bytes())=='b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258','BASE_PIN')
        originals={rel:safe(ROOT/rel).read_bytes() for rel in POINTERS}
        c.require(all(c.sha(originals[rel])==pin for rel,pin in POINTERS.items()),'CURRENT_IDENTITY_CHANGED')
        command([EXE,'-B','-X','utf8',str(pre),'--task-class','DATA'],'preflight',out,60)
        c.require('MUST_READ_PRECHECK = PASS' in (out/'preflight.stdout.txt').read_text(encoding='utf-8'),'LITERAL_PREFLIGHT')
        command([EXE,'-B','-X','utf8','-m','unittest','-v','test_p3'],'tests',out,120)
        log=(out/'tests.stderr.txt').read_text(encoding='utf-8')
        c.require('Ran 35 tests' in log and log.rstrip().endswith('OK') and 'skipped=' not in log,'TEST_COUNT_LOG_OR_SKIPS')
        reader=NativeBodyReader(PACKAGE,gate_verified=True)
        c.write_new(out/'SEMANTIC_BINDINGS.json',c.packed(reader.semantic))
        generation=c.generation_for(OUTPUT,reader.bindings)
        result=c.build(reader,OUTPUT,generation)
        c.require({p.relative_to(OUTPUT).as_posix() for p in OUTPUT.rglob('*') if p.is_file()}==expected_files(reader.bindings['expected_cells']),'P3_EXPECTED_FILES')
        hashes=verify_values(OUTPUT,json.loads((PACKAGE/'PORTABLE_EXPECTED.json').read_bytes()))
        reader.verify_storage_again()
        c.require(all(safe(ROOT/rel).read_bytes()==b for rel,b in originals.items()),'CURRENT_CHANGED')
        c.require(c.sha(pre.read_bytes())=='3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217'
                  and c.sha(base.read_bytes())=='b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258','RULE_EXECUTION_SOURCE_CHANGED')
        c.write_new(out/'PORTABLE_OBSERVED.json',c.packed(hashes))
        archives=pack(OUTPUT,out)
        c.write_new(out/'CANDIDATE_BODY_DELIVERY.json',c.packed({'generation':generation,'files':archives}))
        c.write_new(out/'P3_RESULT.json',c.packed({'task_id':TASK,'status':'BUILT_VALUE_PRESERVING_CANDIDATE_AWAITING_GPT',
          'generation':generation,'candidate_manifest_sha256':c.sha((OUTPUT/'MANIFEST.json').read_bytes()),
          'package_sha256':c.sha((PACKAGE/'PACKAGE.json').read_bytes()),'expected_candidate_files':125,
          'conservation':result['conservation'],'portable_cells_equal':51,'original_prices_rechecked':1504,
          'current_unchanged':True,'dictionary_formal_admission':False,'backtest_admission':False,
          'p1_sidecar_built':False,'supplier_calls':0,'orders_allowed':False}))
        rows=[]
        for p in sorted(out.iterdir()):
            b=p.read_bytes();rows.append({'path':p.name,'bytes':len(b),'sha256':c.sha(b)})
        c.write_new(out/'LOCAL_READBACK.json',c.packed({'files':rows,'scope':'prior result files'}))
        return 0
    except Exception as e:
        c.write_new(out/'FAILED.json',c.packed({'task_id':TASK,'error_type':type(e).__name__,'error':str(e),'status':'FAILED_RETAINED_NO_RETRY'}));return 2

if __name__=='__main__':sys.exit(main())
