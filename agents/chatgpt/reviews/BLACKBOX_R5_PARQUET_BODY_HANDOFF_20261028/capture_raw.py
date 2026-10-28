"""Hash-bound raw-byte handoff only. No Parquet decode, SDK or business imports."""
import hashlib,json,os,platform,stat,zipfile
from pathlib import Path
TASK='BLACKBOX_R5_PARQUET_BODY_HANDOFF_20261028'
OUT=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_R5_PARQUET_BODY_HANDOFF_20261028\capture_001')
ROOTS={k:Path(r'E:\BLACKBOX\STAGING')/('BLACKBOX_RAW_NONE_INCREMENT_20261027_'+k) for k in ['R1','R4','R5']}
MAX_SOURCE_PART=7*1024*1024
MAX_ZIP=8*1024*1024
class Blocked(Exception):pass
def need(ok,reason):
 if not ok:raise Blocked(reason)
def sha(b):return hashlib.sha256(b).hexdigest()
def put(path,obj):
 b=(json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode()
 with path.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 need(path.read_bytes()==b,'OUTPUT_READBACK')
def verify_package(folder):
 p=json.loads((folder/'PACKAGE.json').read_bytes())
 for n,pin in p['files'].items():
  need(Path(n).name==n,'PACKAGE_PATH');b=(folder/n).read_bytes()
  need(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'PACKAGE_DRIFT')
 return sha((folder/'PACKAGE.json').read_bytes())
def read_source(root,row):
 rel=Path(row['relative_path']);need(not rel.is_absolute() and '..' not in rel.parts,'SOURCE_PATH')
 need(rel.suffix=='.parquet' and rel.parts[0]=='raw','SOURCE_FORMAT')
 p=root/rel;before=p.stat();ls=p.lstat()
 need(stat.S_ISREG(ls.st_mode) and not (getattr(ls,'st_file_attributes',0)&0x400),'SOURCE_REPARSE_OR_TYPE')
 physical=p.resolve(strict=True);need(physical.is_relative_to(root.resolve(strict=True)),'SOURCE_EXTERNAL_LINK')
 need(before.st_size==row['bytes'] and before.st_size<=2*1024*1024,'SOURCE_LENGTH')
 b=p.read_bytes();after=p.stat()
 need((before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino),'SOURCE_DRIFT')
 need(len(b)==row['bytes'] and sha(b)==row['sha256'],'SOURCE_HASH')
 return b
def capture(rows,roots,out):
 need(not out.exists(),'EXISTING_OUTPUT_NO_REPLAY');out.mkdir(parents=True,exist_ok=False)
 sources=[];archives=[];writer=None;part_bytes=0;seen=set()
 def close():
  nonlocal writer
  if writer:
   writer.close();writer=None
   p=out/f'raw_part_{len(archives):03d}.zip'
   need(p.stat().st_size<=MAX_ZIP,'ARCHIVE_CAP')
   with zipfile.ZipFile(p) as z:
    need(z.testzip() is None,'ARCHIVE_CRC')
    for item in [s for s in sources if s.get('archive')==p.name]:
     b=z.read(item['member']);need(len(b)==item['bytes'] and sha(b)==item['sha256'],'ARCHIVE_BODY_READBACK')
   archives[-1].update(bytes=p.stat().st_size,sha256=sha(p.read_bytes()))
 try:
  for row in rows:
   key=(row['root'],row['relative_path']);need(key not in seen,'DUPLICATE_PLAN');seen.add(key)
   need(row['root'] in roots and row['action'] in ['CAPTURE','REUSE_HUB_BODY'],'PLAN_SCOPE')
   b=read_source(roots[row['root']],row)
   item=dict(row)
   if row['action']=='CAPTURE':
    if writer is None or part_bytes+len(b)>MAX_SOURCE_PART:
     close();archives.append({'name':f'raw_part_{len(archives)+1:03d}.zip'});part_bytes=0
     writer=zipfile.ZipFile(out/archives[-1]['name'],'x',compression=zipfile.ZIP_STORED)
    member=row['root']+'/'+row['relative_path'];writer.writestr(member,b);part_bytes+=len(b)
    item.update(archive=archives[-1]['name'],member=member)
   sources.append(item)
  close();result={'task_id':TASK,'status':'EXACT_RAW_BODY_HANDOFF_ONLY','supplier_calls':0,'source_written':False,
    'cleaning_run':False,'order_allowed':False,'sources':sources,'archives':archives,
    'new_body_count':sum(x['action']=='CAPTURE' for x in sources),'reused_body_count':sum(x['action']=='REUSE_HUB_BODY' for x in sources)}
  put(out/'RAW_BODY_MANIFEST.json',result);return 0
 except Exception as e:
  if writer:writer.close()
  put(out/'FAILURE_PRESERVED.json',{'task_id':TASK,'reason':str(e) if isinstance(e,Blocked) else type(e).__name__,
      'completed_source_records':sources,'supplier_calls':0,'source_written':False,'retry':False})
  return 2
def main():
 need(platform.system()=='Windows' and platform.node().upper()=='ZHANGWEI','WRONG_HOST')
 folder=Path(__file__).parent;verify_package(folder)
 rows=json.loads((folder/'RAW_TRANSFER_PLAN.json').read_bytes())['rows']
 need(len(rows)==1504 and sum(r['action']=='CAPTURE' for r in rows)==1502,'PLAN_COUNT')
 return capture(rows,ROOTS,OUT)
if __name__=='__main__':
 try:raise SystemExit(main())
 except Blocked as e:print(json.dumps({'task_id':TASK,'status':'NOT_RUN','reason':str(e)}));raise SystemExit(2)
