import json,hashlib,zipfile,io,subprocess,re,math
from pathlib import Path
from collections import Counter,defaultdict
import pandas as pd
import pyarrow.parquet as pq
R=Path(__file__).parent
J=lambda p:json.loads(p.read_bytes())
S=lambda b:hashlib.sha256(b).hexdigest()
manifest=J(R/'capture_001/RAW_BODY_MANIFEST.json');plan=J(R.parent/'r5_raw_handoff_20261028/RAW_TRANSFER_PLAN.json')['rows']
admission=J(R.parent/'r5_work/full_return/staging_output/ADMISSION_R5.json')
assert admission['row_position_base']==0 and admission['source_values_changed'] is False
def ident(p):
 m=re.fullmatch(r'E:\\BLACKBOX\\STAGING\\BLACKBOX_RAW_NONE_INCREMENT_20261027_(R[145])\\(.*)',p)
 assert m,p
 return m[1],m[2].replace('\\','/')
entries={ident(x['source']['path']):x for x in admission['entries']}
assert len(entries)==len(plan)==1504
zips={}
for a in manifest['archives']:
 b=(R/'capture_001'/a['name']).read_bytes();assert len(b)==a['bytes'] and S(b)==a['sha256']
 z=zipfile.ZipFile(io.BytesIO(b));assert z.testzip() is None;assert len(set(z.namelist()))==len(z.namelist())
 expected={x['member'] for x in manifest['sources'] if x.get('archive')==a['name']}
 assert set(z.namelist())==expected
 assert all(x.compress_type==zipfile.ZIP_STORED for x in z.infolist());zips[a['name']]=z
refs={('R1','raw/stock/2026-09-28_00000.parquet'):'65f0ea0d68ad1d9961f3bd723a4d29838e7a38e1',('R4','raw/stock/2026-10-27_03360_R4.parquet'):'6902414166f01ea3eeaaa172f960c63b64797741'}
refbytes={k:subprocess.check_output(['git','-C','allhub_work/repo','cat-file','blob',v]) for k,v in refs.items()}
quality={ident(j['source']['path']):j for f in (R.parent/'r5_work/full_return/staging_output/quality').glob('*.json') for j in [J(f)]}
r4quality={ident(j['raw']['path']):j for f in (R.parent/'r4_result_review_20261027/bodies/r4_staging_output/quality').glob('*.json') for j in [J(f)]}
r4matches=0
fields=['open','high','low','close','volume','money','paused','high_limit','low_limit','avg','pre_close','factor']
totals=Counter();cells=defaultdict(lambda:Counter());schemas=Counter();dtypes=Counter();nulls=Counter();observations=Counter();keys=set();perfile=[];quarantine=[];quality_matches=0;anomalies=[]
for expected,src in zip(plan,manifest['sources']):
 assert all(src[k]==v for k,v in expected.items())
 key=src['root'],src['relative_path'];entry=entries[key]
 assert entry['source']['sha256']==src['sha256'] and entry['source']['bytes']==src['bytes']
 b=zips[src['archive']].read(src['member']) if src['action']=='CAPTURE' else refbytes[key]
 assert len(b)==src['bytes'] and S(b)==src['sha256']
 table=pq.read_table(io.BytesIO(b));df=table.to_pandas();footer=pq.ParquetFile(io.BytesIO(b)).metadata
 assert list(df.columns)==['time','code']+fields,(key,list(df.columns))
 assert footer.num_rows==len(df) and len(df)>0
 assert pd.api.types.is_datetime64_any_dtype(df['time']) and df.time.notna().all() and df.code.notna().all()
 assert all(type(c) is str and re.fullmatch(r'\d{6}\.(XSHG|XSHE)',c) for c in df.code.tolist())
 assert df.time.dt.normalize().equals(df.time)
 assert set(df.time.dt.strftime('%Y-%m-%d'))=={entry['date']}
 assert entry['product']==src['relative_path'].split('/')[1]
 pairs=list(zip(df.time.dt.strftime('%Y-%m-%d'),df.code));assert len(set(pairs))==len(df)
 globalkeys={(entry['product'],d,c) for d,c in pairs};assert not globalkeys&keys;keys.update(globalkeys)
 aps=entry['admitted_positions'];qps=entry['quarantined_positions'];assert len(set(aps+qps))==len(df) and sorted(aps+qps)==list(range(len(df)))
 assert all(pd.api.types.is_numeric_dtype(df[f]) for f in fields)
 numeric=df[fields];bad_inf={f:int(numeric[f].map(lambda v:math.isinf(v)).sum()) for f in fields};assert not any(bad_inf.values())
 rownulls={f:int(df[f].isna().sum()) for f in fields};nulls.update(rownulls)
 assert df.paused.isin([0,1]).all();assert (df.volume>=0).all() and (df.money>=0).all()
 obs={'supplier_paused':int((df.paused==1).sum()),'supplier_live':int((df.paused==0).sum())};observations.update(obs)
 for pos in qps:
  row=df.iloc[pos];assert row.code=='600621.XSHG' and entry['date']=='2026-10-27'
  assert row.paused==0 and row.volume==row.money==0 and row.close==row.pre_close==row.avg==14.9 and pd.isna(row[['open','high','low']]).all()
  quarantine.append({'source':key,'row_position':pos,'code':row.code,'date':entry['date']})
 admitted=df.iloc[aps];live=admitted[admitted.paused==0]
 if live[['open','high','low','close']].isna().any().any():anomalies.append({'source':key,'reason':'ADMITTED_LIVE_OHLC_NULL'})
 if key in quality:
  q=quality[key]['quality'];assert q['rows']==len(df) and q['nulls']==rownulls and q['observations']==obs
  assert set(map(tuple,q['keys']['returned']))==set(pairs)
  assert quality[key]['admitted_positions']==aps and quality[key]['quarantined_positions']==qps
  quality_matches+=1
 if key in r4quality and 'quality' in r4quality[key]:
  q=r4quality[key]['quality'];assert q['rows']==len(df) and q['nulls']==rownulls and q['observations']==obs
  assert set(map(tuple,q['keys']['returned']))==set(pairs)
  r4matches+=1
 elif key in r4quality:
  assert key==('R4','raw/stock/2026-10-27_03360_R4.parquet') and len(qps)==1
 cell=entry['product']+'/'+entry['date'];cells[cell].update(input=len(df),admitted=len(aps),quarantined=len(qps),files=1)
 totals.update(input=len(df),admitted=len(aps),quarantined=len(qps),files=1)
 schemas[str(table.schema.remove_metadata())]+=1;dtypes[str(dict(df.dtypes.astype(str)))]+=1
 perfile.append({'root':src['root'],'relative_path':src['relative_path'],'sha256':src['sha256'],'bytes':len(b),'rows':len(df),'admitted':len(aps),'quarantined':len(qps),'row_groups':footer.num_row_groups,'nulls':rownulls})
assert quality_matches==405 and r4matches==1097 and totals['input']==117461 and totals['admitted']==117460 and totals['quarantined']==1 and len(keys)==117461 and not anomalies
delivery=J(R/'DELIVERY_MANIFEST.json')
for p in delivery['files']:
 b=(R/p['path']).read_bytes();assert len(b)==p['bytes'] and S(b)==p['sha256']
audit={'schema':'BLACKBOX_INDEPENDENT_RAW_DECODE_R1','snapshot':J(R/'new_tree_index.json')['head'],'status':'EXACT_BODY_AND_RAW_KEY_POSITION_CONSERVATION_VERIFIED_NOT_CLEANING','totals':dict(totals),'new_quality_receipts_matched':quality_matches,'r4_quality_receipts_matched':r4matches,'unique_product_date_code_keys':len(keys),'cells':{k:dict(v) for k,v in sorted(cells.items())},'schemas':dict(schemas),'pandas_dtypes':dict(dtypes),'nulls':dict(nulls),'source_observations':dict(observations),'quarantine':quarantine,'anomalies':anomalies,'source_files':perfile,'source_blob_index':J(R/'new_tree_index.json')['files'],'limits':['Original source cells decoded, including1excluded supplier-inconsistent row; no external quote truth or legal suspension conclusion established.','No historical PIT availability timestamp inferred from capture time.','Native final UPLOAD_READBACK receipt was absent at the pinned snapshot; do not certify full native handoff completion until received.','No Cleaning, release, CURRENT switch or formal-engine acceptance.']}
(R/'INDEPENDENT_RAW_DECODE_AUDIT.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:v for k,v in audit.items() if k not in ['source_files','source_blob_index','cells','schemas']},ensure_ascii=False))
