"""P4 offline audit consumer only. No execution, backtest admission or native entry."""
from pathlib import Path,PurePosixPath
from datetime import datetime,date,time,timedelta,timezone
from collections import Counter
import hashlib,io,json,zipfile
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import numpy as np

SHA='31dee3a67f7674db25b0ba4d56c169c941e28f857b8656454b6006401938f884'
APPROVAL_SHA='d31a903da4f189702fbaec15e41db3b4fe9dee3d613fc42b1d67a725e3152dbb'
CAL='ab00fa8c597c9b01977cc060a202371d2de73a6a32b8a4fe6cc533a705d056d9'
GEN='P3_R5_C0C7EB71218FB8EE679D8D9727D99A45E829FC1E765359B2ED7BAD3CA146DF9B'
MAN='6984f606af60230b7bfc444dbd926e141a7dbe54a1bf63d3ccc1eeb3d4a7be41'
SOURCE_FIELDS=['time','code','open','high','low','close','volume','money','paused','high_limit','low_limit','avg','pre_close','factor']
PUBLIC=[x for x in SOURCE_FIELDS if x not in {'factor','avg','pre_close'}]
STATUS=['paused','volume','money','high_limit','low_limit','missing_price','execution_allowed']
CN=timezone(timedelta(hours=8));PURPOSE='OFFLINE_P1_CONSUMER_AUDIT'
class Rejected(ValueError):pass
def need(v,n):
 if not v:raise Rejected(n)
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
def available(day,days):
 if day not in days or days.index(day)+1==len(days):return None
 return datetime.combine(date.fromisoformat(days[days.index(day)+1]),time(9),CN).isoformat()
def validate_status(r):
 need(set(SOURCE_FIELDS)<=set(r),'MISSING_STATE_OR_FIELD')
 need(r['paused'] in (0.,1.),'INVALID_PAUSED')
 need(all(r[k] is not None and np.isfinite(r[k]) for k in SOURCE_FIELDS[2:]),'NULL_OR_NONFINITE_STATE_OR_PRICE')
 need(r['volume']>=0 and r['money']>=0,'NEGATIVE_VOLUME_OR_MONEY')

def _decision_rows(records,days,decision_time,fields,product='stock',purpose=PURPOSE):
 need(product=='stock','PRODUCT_DENIED');need(purpose==PURPOSE,'NO_BACKTEST_OR_EXECUTION_ADMISSION')
 need(fields and set(fields)<=set(PUBLIC) and len(fields)==len(set(fields)),'FIELD_DENIED')
 d=datetime.fromisoformat(decision_time);need(d.tzinfo is not None and d.utcoffset()==timedelta(hours=8),'DECISION_MUST_HAVE_UTC_PLUS_08')
 output=[];seen=set()
 for r in records:
  validate_status(r);key=(r['time'],r['code']);need(key not in seen,'DUPLICATE_KEY');seen.add(key)
  need(key!=('2026-10-27','600621.XSHG'),'QUARANTINE_KEY')
  at=available(r['time'],days)
  if at is None or datetime.fromisoformat(at)>d:continue
  states={k:r[k] for k in STATUS if k in r};need(set(states)==set(STATUS),'MANDATORY_STATES_MISSING')
  need(r['missing_price'] is False and r['execution_allowed'] is False,'STATE_TAMPER')
  output.append({'values':{k:r[k] for k in fields},'states':states,'availability':{'status':'PRESUMED','presumed_available_at':at,'availability_basis':'PRESUMED_T1_PREOPEN','revision_assumption':'PRESUMED_UNCHANGED','historical_pit':'NOT_ESTABLISHED','policy_body_sha256':SHA,'calendar_sha256':CAL},'provenance':dict(r['provenance'])})
 return output

class Consumer:
 def __init__(self,archive_root,policy_root,pins_file):
  need((pd.__version__,pa.__version__,np.__version__)==('3.0.3','24.0.0','2.5.4'),'RUNTIME_PIN')
  self.archive_root=Path(archive_root);self.policy_root=Path(policy_root);self.pins_file=Path(pins_file)
  self._pins_bytes=self.pins_file.read_bytes();self.pins=json.loads(self._pins_bytes)
  need(self.pins['source_generation']==GEN and self.pins['manifest_sha256']==MAN and self.pins['policy_sha256']==SHA and self.pins['calendar_sha256']==CAL,'PIN_CONTRACT')
  self._load()
 def _load(self):
  need(self.pins_file.read_bytes()==self._pins_bytes,'PIN_FILE_CHANGED')
  pb=(self.policy_root/'POLICY_BODY.txt').read_bytes();cb=(self.policy_root/'CALENDAR.json').read_bytes();ab=(self.policy_root/'APPROVAL.json').read_bytes();need(sha(ab)==APPROVAL_SHA,'APPROVAL_IDENTITY');ap=json.loads(ab)
  need(sha(pb)==SHA and sha(cb)==CAL and ap['policy_body_sha256']==SHA and ap['calendar_sha256']==CAL and ap['status']=='OWNER_APPROVED_POLICY_ONLY','POLICY_OR_CALENDAR_IDENTITY')
  days=json.loads(cb)['returned'];need(days==sorted(set(days)),'CALENDAR_ORDER')
  for day in days:need(date.fromisoformat(day).isoformat()==day,'CALENDAR_DATE')
  self.days=days;members={}
  for pin in self.pins['archives']:
   b=(self.archive_root/pin['path']).read_bytes();need(len(b)==pin['bytes'] and sha(b)==pin['sha256'],'ARCHIVE_IDENTITY')
   with zipfile.ZipFile(io.BytesIO(b)) as z:
    need(z.testzip() is None,'ARCHIVE_CRC')
    for x in z.infolist():
     p=PurePosixPath(x.filename);need(not p.is_absolute() and '..' not in p.parts and str(p)==x.filename and '\\' not in x.filename and x.filename not in members,'MEMBER_PATH_OR_DUPLICATE')
     need(x.compress_type==zipfile.ZIP_STORED,'ARCHIVE_ENCODING');members[x.filename]=z.read(x.filename)
  need(len(members)==125 and sha(members['MANIFEST.json'])==MAN,'CANDIDATE_SET_OR_MANIFEST')
  m=json.loads(members['MANIFEST.json']);r=json.loads(members['RESULT.json']);end=json.loads(members['BUILD_COMPLETE.json'])
  need(m['generation']==r['generation']==end['generation']==GEN and end['manifest_sha256']==MAN,'GENERATION')
  need({x['path'] for x in m['files']}|{'MANIFEST.json','BUILD_COMPLETE.json'}==set(members) and len(m['files'])==123,'MANIFEST_SET')
  for x in m['files']:need(len(members[x['path']])==x['bytes'] and sha(members[x['path']])==x['sha256'],'PAYLOAD_IDENTITY')
  need(r['historical_pit']=='NOT_ESTABLISHED' and r['backtest_admission'] is False and r['product_output_rows']=={'stock':88811,'etf':28530,'index':119},'CANDIDATE_SCOPE')
  src=json.loads(members['SOURCES.json']);need(len(src)==1504,'SOURCE_COUNT')
  need(sha(members['SOURCES.json'])==self.pins['sources_sha256'] and sha(members['EXCLUSIONS.json'])==self.pins['exclusions_sha256'],'PROVENANCE_BINDING')
  records=[];split=Counter();date_counts={};products=Counter();stock_dates=[]
  for cell in r['outputs']:
   product=cell['product'];day=cell['date'];pf=pq.ParquetFile(io.BytesIO(members[cell['path']]));md=pf.schema_arrow.metadata
   need(md[b'candidate_generation'].decode()==GEN and md[b'historical_pit']==b'NOT_ESTABLISHED' and md[b'price_basis']==b'RAW_NONE' and md[b'supplier_namespace']==b'JQ','TABLE_METADATA')
   t=pf.read().replace_schema_metadata(None);need(t.column_names==SOURCE_FIELDS,'FIELD_SET')
   f=t.to_pandas();need(not f.duplicated(['time','code']).any() and len(f)==cell['rows'],'TABLE_KEYS')
   need(all(x==pd.Timestamp(day) for x in f.time),'TABLE_DAY');split[product]+=int(f.paused.eq(1).sum());products[product]+=len(t)
   if product!='stock':continue
   stock_dates.append(day);date_counts[day]=len(t);line=json.loads(members['lineage/stock/'+day+'.json']);need(len(line)==len(t),'LINEAGE_COUNT')
   for i,row in enumerate(t.to_pylist()):
    row['time']=day;validate_status(row);v=line[i];s=src[v['source_id']]
    need(v['output_row_position']==i and s['source_id']==v['source_id'] and v['source_sha256']==s['sha256'] and type(v['physical_row_position']) is int and 0<=v['physical_row_position']<s['rows'],'ROW_PROVENANCE')
    need(row['code'].endswith(('.XSHG','.XSHE')) and len(row['code'])==11 and row['code'][:6].isdigit(),'JQ_NAMESPACE')
    row.update(missing_price=False,execution_allowed=False,provenance={'source_generation':GEN,'source_manifest_sha256':MAN,'source_file':s['path'],'source_sha256':s['sha256'],'physical_row_position':v['physical_row_position'],'output_row_position':i,'data_date':day,'product':'stock'})
    records.append(row)
  need(dict(products)=={'etf':28530,'index':119,'stock':88811} and len(stock_dates)==17 and len(set(stock_dates))==17,'PRODUCT_DATE_COVERAGE')
  need(len(records)==88811 and not any(r['time']=='2026-10-27' and r['code']=='600621.XSHG' for r in records),'STOCK_ADMISSION')
  self._records=records;self.summary={'stock_rows':len(records),'stock_date_counts':date_counts,'paused_by_product':dict(split),'PRESUMED_rows':sum(available(r['time'],days) is not None for r in records),'UNRESOLVED_rows':sum(available(r['time'],days) is None for r in records),'resolved_dates':[d for d in stock_dates if available(d,days)],'unresolved_dates':[d for d in stock_dates if available(d,days) is None],'backtest_admission':False,'execution_allowed':False}
 def select(self,decision_time,fields,product='stock',purpose=PURPOSE):
  # Revalidate immutable inputs each call; no cached result survives a changed source.
  self._load()
  return _decision_rows(self._records,self.days,decision_time,fields,product,purpose)
 def availability(self,day):
  self._load();at=available(day,self.days)
  return {'data_date':day,'status':'PRESUMED' if at else 'UNRESOLVED','presumed_available_at':at,'reason':None if at else 'DATA_DAY_OR_SUCCESSOR_NOT_IN_FROZEN_CALENDAR'}
