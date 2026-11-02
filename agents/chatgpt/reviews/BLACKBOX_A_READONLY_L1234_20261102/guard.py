"""Pinned native boundary. No discovery, SDK, credentials or data-plane writes."""
from pathlib import Path
import json, os, socket, sys
import observe as o

PACKAGE=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_A_READONLY_L1234_20261102_PACKAGE\package')
ACK_ROOT=PACKAGE.parent
CONTROL=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_A_READONLY_L1234_20261102_CAPTURE')
OUTER=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_A_READONLY_L1234_20261102_OUTER')
EXE=r'E:\BLACKBOX\.venv\Scripts\python.exe'
ROOT=Path(r'E:\BLACKBOX')

def load(name):return json.loads(o.safe(PACKAGE/name).read_bytes())
def package_sha(root):
    raw=o.safe(root/'PACKAGE.json').read_bytes();m=json.loads(raw)
    o.need(m['task_id']==o.TASK,'PACKAGE_TASK')
    names=[r['path'] for r in m['files']]
    o.need(len(names)==len(set(names)) and all(Path(n).name==n and '\\' not in n and n!='PACKAGE.json' for n in names),'PACKAGE_MEMBER_NAMES')
    for r in m['files']:
        b=o.safe(root/r['path']).read_bytes()
        o.need(len(b)==r['bytes'] and o.sha(b)==r['sha256'],'PACKAGE_PIN:'+r['path'])
    return o.sha(raw)

def rules():
    result=[]
    for r in load('RULE_PINS.json')['files']:
        b=o.safe(Path(r['path'])).read_bytes()
        o.need(len(b)==r['bytes'] and o.sha(b)==r['sha256'],'RULE_RAW_PIN:'+r['path'])
        result.append(dict(path=r['path'],bytes=len(b),sha256=o.sha(b),pin_kind='RAW_BYTES'))
    for r in load('PREFLIGHT_AUX_RULES.json')['files']:
        b=o.safe(Path(r['path'])).read_bytes()
        text=b.decode('utf-8').replace('\r\n','\n').replace('\r','\n')
        o.need(o.sha(text.encode())==r['text_sha256'],'AUX_TEXT_PIN:'+r['path'])
        result.append(dict(path=r['path'],bytes=len(b),sha256=o.sha(b),text_sha256=r['text_sha256'],pin_kind='MANIFEST_TEXT_PLUS_MEASURED_RAW'))
    return result

def check_ack_upload(raw,receipt):
    import hashlib,re
    o.need(receipt['ack_sha256']==o.sha(raw) and receipt['ack_bytes']==len(raw) and
           receipt['ack_blob_sha']==hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() and
           re.fullmatch('[0-9a-f]{40}',receipt['git_commit']) is not None,'ACK_UPLOAD_BINDING')

def validate(ack):
    o.need(os.name=='nt' and socket.gethostname().upper()=='ZHANGWEI','HOST_ZHANGWEI_REQUIRED')
    o.need(sys.version_info[:3]==(3,12,10) and os.path.normcase(sys.executable)==os.path.normcase(EXE),'INTERPRETER_PIN')
    o.need(o.pa.__version__=='24.0.0','ARROW_VERSION_PIN')
    o.need(Path(__file__).parent==PACKAGE,'PACKAGE_FIXED_PATH')
    o.safe(PACKAGE);o.safe(CONTROL);o.safe(OUTER);o.safe(ACK_ROOT)
    s=load('CONTRACT.json')
    o.need(s['task_id']==o.TASK and s['status']=='APPROVED_READ_ONLY_DISPATCH' and s['ORDER_ALLOWED'] is False,'CONTRACT')
    digest=package_sha(PACKAGE)
    if ack:
        raw=o.safe(ACK_ROOT/'ACK.json').read_bytes();a=json.loads(raw)
        o.need(a['task_id']==o.TASK and a['execution_host']=='ZHANGWEI' and a['package_sha256']==digest,'ACK_BINDING')
        o.need(a['rules']==rules(),'ACK_RULE_DRIFT')
        receipt=json.loads(o.safe(ACK_ROOT/'ACK_UPLOAD.json').read_bytes())
        check_ack_upload(raw,receipt)
    return s,digest

def inside(path,root):
    try:Path(path).absolute().relative_to(Path(root).absolute());return True
    except ValueError:return False

def audit_checker(write_roots,processes=()):
    """Python audit guard; fixed native code and read-only handle remain primary.

    Installed interpreter/Arrow DLL reads are trusted runtime dependencies, not
    a claim to sandbox arbitrary native extension code or audit the whole OS.
    """
    def check(event,args):
        if event.startswith('socket.') or event in ('os.system','os.exec','os.posix_spawn'):
            raise o.Safety('NETWORK_OR_SHELL_FORBIDDEN')
        if event=='subprocess.Popen':
            argv=args[1]
            if not isinstance(argv,(list,tuple)) or tuple(argv) not in processes:
                raise o.Safety('UNREVIEWED_SUBPROCESS')
        paths=[]
        if event=='open' and not isinstance(args[0],int):
            mode=args[1] or '';flags=args[2] or 0
            if any(x in mode for x in 'wax+') or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):paths=[args[0]]
        elif event in ('os.mkdir','os.remove','os.rmdir','os.chmod','os.utime','os.truncate'):
            paths=[args[0]]
        elif event in ('os.rename','os.link','os.symlink'):
            raise o.Safety('RENAME_LINK_OR_SYMLINK_FORBIDDEN')
        for p in paths:
            if not any(inside(p,r) for r in write_roots):raise o.Safety('WRITE_OUTSIDE_CAPTURE:'+str(p))
        if event in ('os.listdir','os.scandir') and not isinstance(args[0],int):
            p=str(args[0])
            if p.upper().startswith('E:') and not inside(p,ROOT/'.venv'):
                raise o.Safety('SOURCE_DIRECTORY_ENUMERATION_FORBIDDEN')
    return check

def audit(write_roots,processes=()):
    sys.addaudithook(audit_checker(write_roots,processes))

def write(path,obj):
    p=o.safe(path);b=o.packed(obj)+b'\n'
    with p.open('xb') as f:f.write(b)
    o.need(p.read_bytes()==b,'CONTROL_READBACK')
