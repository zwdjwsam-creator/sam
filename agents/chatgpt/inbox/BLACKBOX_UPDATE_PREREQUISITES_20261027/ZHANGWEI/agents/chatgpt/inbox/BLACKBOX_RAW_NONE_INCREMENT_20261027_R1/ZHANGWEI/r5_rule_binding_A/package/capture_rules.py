"""Bounded exact rule-body capture only. No original rule/preflight/business execution."""
import hashlib,json,base64,platform
from pathlib import Path
ROOT=Path(r'E:\BLACKBOX')
OUT=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_R5_RULE_BINDING_20261028\capture_001')
PATHS=[
'契约/必读/BLACKBOX_ACQUISITION_MUST_READ.md',
'.cursor/rules/blackbox_jq_incremental_download_hand_rule.mdc',
'运行/BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json',
'脚本/blackbox_must_read_preflight_r1.py','脚本/_base.py',
'契约/必读/MUST_READ_MANIFEST_CURRENT.json']
CAP=2*1024*1024

def capture(root,out):
    if out.exists():raise RuntimeError('EXISTING_OUTPUT_NO_REPLAY')
    out.mkdir(parents=True,exist_ok=False);rows=[]
    for rel in PATHS:
        p=root/rel;row={'path':str(p),'relative_path':rel,'supplier_calls':0}
        try:
            s=p.stat()
            if p.is_symlink() or getattr(p,'is_junction',lambda:False)() or getattr(p.lstat(),'st_file_attributes',0)&0x400:raise RuntimeError('SOURCE_LINK_UNPROVEN')
            if s.st_size>CAP:raise RuntimeError('SOURCE_BYTE_CAP')
            with p.open('rb') as f:b=f.read(CAP+1)
            t=p.stat()
            if len(b)>CAP or (s.st_size,s.st_mtime_ns,s.st_ino)!=(t.st_size,t.st_mtime_ns,t.st_ino):raise RuntimeError('SOURCE_DRIFT_OR_CAP')
            # Complete originals, including original line endings/BOM, kept as base64; no import/evaluation.
            row.update({'status':'CAPTURED','bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'encoding':'base64','content':base64.b64encode(b).decode('ascii')})
            if base64.b64decode(row['content'])!=b:raise RuntimeError('ENCODING_READBACK')
        except Exception as e:row.update({'status':'UNRESOLVED','error_type':type(e).__name__})
        rows.append(row)
    payload={'schema':'BLACKBOX_R5_EXACT_RULE_CAPTURE_R1','host':'ZHANGWEI','supplier_calls':0,'source_written':False,'order_allowed':False,'records':rows}
    b=(json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode()
    with (out/'RULE_BODIES.json').open('xb') as f:f.write(b)
    if (out/'RULE_BODIES.json').read_bytes()!=b:raise RuntimeError('LOCAL_READBACK')
    return 0 if all(r['status']=='CAPTURED' for r in rows) else 2

if __name__=='__main__':
    import sys
    if sys.argv[1:]:raise RuntimeError('ARGS_NOT_ALLOWED')
    if platform.system()!='Windows' or platform.node().upper()!='ZHANGWEI':raise RuntimeError('WRONG_HOST')
    raise SystemExit(capture(ROOT,OUT))
