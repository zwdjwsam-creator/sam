"""Review-only fixed-path calendar capture. No discovery, RAW copy or policy activation."""
from pathlib import Path
from datetime import date,datetime,timezone,timedelta
import hashlib,io,json,os,socket,sys,subprocess
import pyarrow as pa
import pyarrow.parquet as pq
SOURCE=Path(r'E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P0_meta\calendar_cn_exchange\calendar_cn_exchange_v2_asof_20260924\CALENDAR_TRADE_DAYS.parquet')
CONTROL=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_HISTORICAL_CALENDAR_FREEZE_REVIEW_20261101')
EXE=r'E:\BLACKBOX\.venv\Scripts\python.exe'
ROOT=Path(r'E:\BLACKBOX')
PREFIX='d044d628279d48c1'
class Stop(ValueError):pass
def need(v,s):
 if not v:raise Stop(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def packed(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def safe(p):
 p=Path(p)
 for a in [p,*p.parents]:
  if a.exists() or a.is_symlink():
   st=a.lstat();need(not a.is_symlink() and not getattr(st,'st_file_attributes',0)&0x400 and not (hasattr(a,'is_junction') and a.is_junction()),'REPARSE_PATH')
 return p
def write_new(p,b):
 with p.open('xb') as f:f.write(b)
 need(p.read_bytes()==b,'OUTPUT_READBACK')
def decode(b):
 pf=pq.ParquetFile(io.BytesIO(b));t=pf.read()
 need(t.num_rows>0 and 'trade_date' in t.column_names,'EXACT_TRADE_DATE_COLUMN_REQUIRED')
 column=t['trade_date'];kind=column.type
 need(pa.types.is_date(kind) or pa.types.is_timestamp(kind) or pa.types.is_string(kind),'DATE_TYPE_NOT_ORDINAL')
 days=[]
 for v in column.to_pylist():
  need(v is not None,'NULL_CALENDAR_DAY')
  if isinstance(v,datetime):
   need(v.hour==v.minute==v.second==v.microsecond==0 and getattr(v,'nanosecond',0)==0,'NON_MIDNIGHT_CALENDAR')
   need(v.tzinfo is None or v.utcoffset()==timedelta(hours=8),'UNBOUND_CALENDAR_TIMEZONE')
   day=v.date().isoformat()
  elif isinstance(v,date):day=v.isoformat()
  elif isinstance(v,str):
   need(len(v)==10 and date.fromisoformat(v).isoformat()==v,'NON_ISO_DAY');day=v
  else:raise Stop('DATE_TYPE_NOT_ORDINAL')
  days.append(day)
 need(len(set(days))==len(days),'DUPLICATE_DAY_NO_DEDUP')
 need(days==sorted(days),'UNORDERED_NO_SORT_REPAIR')
 return {'format':'EXPLICIT_RETAINED_TRADE_DATE_COLUMN','trade_days':days,'rows':len(days),'first':days[0],'last':days[-1],
  'physical_row_positions':list(range(len(days))),'arrow_schema':str(t.schema.remove_metadata()),'parquet_footer_schema':str(pf.schema),
  'schema_metadata_sha256':sha(packed({k.decode():v.decode() for k,v in (t.schema.metadata or {}).items()})),
  'calendar_complete':False,'historical_availability_established':False,'policy_calendar_replaced':False}
def collect(source,out,expected_prefix):
 # Production caller supplies only SOURCE. Unit fixtures call this with their owned paths.
 safe(source);need(source.is_file(),'EXACT_SOURCE_NOT_REGULAR_FILE')
 before_stat=source.stat();need(before_stat.st_size<=67108864,'SOURCE_RESOURCE_CAP_64_MIB')
 before=source.read_bytes();identity={'path':str(source),'bytes':len(before),'sha256':sha(before)}
 write_new(out/'SOURCE_IDENTITY.json',packed(identity))
 need(identity['sha256'].startswith(expected_prefix),'REGISTERED_HASH_PREFIX_CHANGED')
 result=decode(before)
 after=safe(source).read_bytes();after_stat=source.stat();need(after==before and (after_stat.st_size,after_stat.st_dev,after_stat.st_ino,after_stat.st_mtime_ns)==(before_stat.st_size,before_stat.st_dev,before_stat.st_ino,before_stat.st_mtime_ns),'SOURCE_CHANGED_DURING_CAPTURE')
 write_new(out/'TRADE_DAY_SEQUENCE.json',packed({'source':identity,**result}))
 write_new(out/'CAPTURE_RESULT.json',packed({'status':'FROZEN_OBSERVATION_AWAITING_GPT','source':identity,'source_before_after_byte_equal':True,'rows':result['rows'],'first':result['first'],'last':result['last'],'no_original_body_copy':True,'calendar_admission':False,'orders_allowed':False}))
 return result

def main():
 contract=json.loads((Path(__file__).parent/'CALENDAR_FREEZE_CONTRACT.json').read_bytes())
 # This published review package cannot run natively. Only a later GPT-reviewed dispatch may replace it.
 need(contract['status']=='APPROVED_NATIVE_DISPATCH','REVIEW_ONLY_NOT_DISPATCHED')
 need(os.name=='nt' and socket.gethostname().upper()=='ZHANGWEI','HOST')
 need(sys.version_info[:3]==(3,12,10) and os.path.normcase(sys.executable)==os.path.normcase(EXE),'INTERPRETER')
 need(pa.__version__=='24.0.0','ARROW_RUNTIME')
 need(contract['source_path']==str(SOURCE) and contract['known_sha256_prefix']==PREFIX,'CONTRACT_SOURCE_CHANGED')
 safe(CONTROL);safe(SOURCE)
 need(not CONTROL.exists(),'CONTROL_EXISTS_NO_RETRY')
 CONTROL.mkdir(exist_ok=False)
 write_new(CONTROL/'RUN_ONCE.json',packed({'task':contract['task_id'],'replay_allowed':False}))
 out=CONTROL/'result_001';out.mkdir(exist_ok=False)
 try:
  pre=safe(ROOT/'脚本/blackbox_must_read_preflight_r1.py');base=safe(ROOT/'脚本/_base.py')
  need(sha(pre.read_bytes())=='3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217' and sha(base.read_bytes())=='b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258','ORIGINAL_PREFLIGHT_PIN')
  start=datetime.now(timezone.utc).isoformat();argv=[EXE,'-B','-X','utf8',str(pre),'--task-class','DATA']
  with (out/'preflight.stdout.txt').open('xb') as a,(out/'preflight.stderr.txt').open('xb') as b:
   p=subprocess.run(argv,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=a,stderr=b,timeout=60,check=False)
  write_new(out/'PREFLIGHT_RUN.json',packed({'argv':argv,'actual_exit':p.returncode,'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat()}))
  need(p.returncode==0 and 'MUST_READ_PRECHECK = PASS' in (out/'preflight.stdout.txt').read_text(encoding='utf-8'),'PREFLIGHT_FAILED')
  collect(SOURCE,out,PREFIX)
  rows=[]
  for p in sorted(out.iterdir()):
   b=p.read_bytes();rows.append({'path':p.name,'bytes':len(b),'sha256':sha(b)})
  write_new(out/'LOCAL_READBACK.json',packed({'files':rows,'scope':'prior files only, no self-hash'}));return 0
 except Exception as e:
  write_new(out/'FAILED.json',packed({'status':'FAILED_RETAINED_NO_RETRY','error_type':type(e).__name__,'error':str(e)}));return 2
if __name__=='__main__':
 try:sys.exit(main())
 except Stop as e:print(str(e),file=sys.stderr);sys.exit(4)
