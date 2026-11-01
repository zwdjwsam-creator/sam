import ast,collections,datetime,hashlib,io,json,re,zipfile
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import candidate_adapter as c
R=Path(__file__).parent;ret=R/'return';out=ret/'result_001';pkg=Path('p3_dispatch');spec=json.loads((R/'SOURCE_FILES.json').read_bytes());checks=[]
def ok(v,name):
 if not v:raise AssertionError(name)
 checks.append(name)
def sha(b):return hashlib.sha256(b).hexdigest()
def j(p):return json.loads(p.read_bytes())
for r in spec['files']:
 p=ret/r['path'].split('/p3_native_candidate_20261101/')[1];b=p.read_bytes();ok(len(b)==r['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['sha'],'git_body:'+p.relative_to(ret).as_posix())
package=j(pkg/'PACKAGE.json');pb=(pkg/'PACKAGE.json').read_bytes();pv=j(ret/'PACKAGE_VERIFY.json');ack=j(ret/'ACK.json');res=j(out/'P3_RESULT.json')
ok(pv['verified_payloads']==package['files'],'package_exact_payloads')
ok(pv['package_sha256']==ack['package_sha256']==res['package_sha256']==sha(pb),'package_binding')
for r in package['files']:
 b=(pkg/r['path']).read_bytes();ok(len(b)==r['bytes'] and sha(b)==r['sha256'],'issued_code:'+r['path'])
outer=j(ret/'OUTER_RUN.json');pre=j(out/'preflight.json');tests=j(out/'tests.json')
ok([outer['actual_exit'],pre['actual_exit'],tests['actual_exit']]==[0,0,0],'three_actual_exits')
dt=datetime.datetime.fromisoformat
ok(dt(ack['utc'])<dt(outer['start_utc'])<=dt(pre['start_utc'])<dt(pre['end_utc'])<=dt(tests['start_utc'])<dt(tests['end_utc'])<=dt(outer['end_utc']),'actual_time_order')
ok('MUST_READ_PRECHECK = PASS' in (out/'preflight.stdout.txt').read_text(),'preflight_literal')
log=(out/'tests.stderr.txt').read_text();names=re.findall(r'^(test_\w+) \(test_p3.P3Fixtures\.\w+\) \.\.\. ok$',log,re.M)
expected=[n.name for n in ast.walk(ast.parse((pkg/'test_p3.py').read_text())) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
ok(len(names)==35 and set(names)==set(expected) and log.rstrip().endswith('OK') and 'skipped' not in log,'35_exact_native_tests_no_skip')
for p in [ret/'OUTER.stderr.txt',ret/'OUTER.stdout.txt',out/'preflight.stderr.txt',out/'tests.stdout.txt']:ok(p.read_bytes()==b'','empty_stream:'+p.name)
delivery=j(out/'CANDIDATE_BODY_DELIVERY.json');members={};arcbytes=0
for a in delivery['files']:
 b=(out/a['path']).read_bytes();arcbytes+=len(b);ok(len(b)==a['bytes'] and sha(b)==a['sha256'] and len(b)<=7500000,'archive_identity:'+a['path'])
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  ok(z.namelist()==a['members'] and z.testzip() is None,'archive_members_crc:'+a['path'])
  for info in z.infolist():
   ok(info.compress_type==zipfile.ZIP_STORED and info.filename not in members,'zip_stored_unique:'+info.filename);members[info.filename]=z.read(info.filename)
ok(len(members)==125,'125_candidate_members')
man=json.loads(members['MANIFEST.json']);built=json.loads(members['BUILD_COMPLETE.json']);report=json.loads(members['RESULT.json']);gen=res['generation']
B=j(pkg/'bindings.json');identity={'output_root':r'E:\BLACKBOX\STAGING\BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101','bindings_sha256':sha(c.packed(B)),'implementation_sha256':sha((pkg/'candidate_adapter.py').read_bytes()),'package_sha256':sha(pb)}
ok(gen=='P3_R5_'+sha(c.packed(identity)).upper(),'independent_native_generation_recomputation')
ok(man['generation']==built['generation']==report['generation']==delivery['generation']==gen,'coherent_generation')
ok(built['manifest_sha256']==res['candidate_manifest_sha256']==sha(members['MANIFEST.json']),'manifest_receipt_binding')
ok(set(members)=={r['path'] for r in man['files']}|{'MANIFEST.json','BUILD_COMPLETE.json'} and len(man['files'])==123,'manifest_exact_set')
for r in man['files']:ok(len(members[r['path']])==r['bytes'] and sha(members[r['path']])==r['sha256'],'candidate_hash:'+r['path'])
for name,b in members.items():
 if name.endswith('.parquet'):
  md=pq.ParquetFile(io.BytesIO(b)).schema_arrow.metadata
  ok(md[b'candidate_generation'].decode()==gen and md[b'historical_pit']==b'NOT_ESTABLISHED' and md[b'price_basis']==b'RAW_NONE' and md[b'supplier_namespace']==b'JQ' and json.loads(md[b'permitted_uses'])==['OFFLINE_VALUE_AUDIT','SCHEMA_INSPECTION'],'parquet_binding:'+name)
def table(name):return pq.ParquetFile(io.BytesIO(members[name])).read().replace_schema_metadata(None)
reader=c.BodyReader('evidence',B);sources=json.loads(members['SOURCES.json']);qrecords=json.loads(members['EXCLUSIONS.json']);wanted=collections.defaultdict(list);lines=collections.defaultdict(list);rawcells=collections.defaultdict(list);qcells=collections.defaultdict(list);qtable=[]
ok(len(sources)==1504,'1504_source_records')
for i,(e,key) in enumerate(zip(reader.admission['entries'],reader.entry_keys)):
 b=reader.read(e,key);raw=pq.ParquetFile(io.BytesIO(b)).read().select(c.FIELDS).replace_schema_metadata(None);s=sources[i];cell=e['product'],e['date']
 ok(s['source_id']==i and s['sha256']==sha(b)==e['source']['sha256'] and s['bytes']==len(b) and s['path']==e['source']['path'] and s['original_path']==e['source']['path'] and s['relative_path']==key[1] and s['root']==key[0],'source_provenance:'+str(i))
 aa=e['admitted_positions'];qq=e['quarantined_positions'];ok(len(set(aa))==len(aa) and len(set(qq))==len(qq) and not set(aa)&set(qq) and set(aa)|set(qq)==set(range(len(raw))),'physical_partition:'+str(i))
 wanted[cell].append(raw.take(pa.array(aa,pa.int64())));rawcells[cell].append(raw)
 for pos in aa:lines[cell].append({'source_id':i,'source_sha256':sha(b),'physical_row_position':pos,'output_row_position':len(lines[cell])})
 if qq:qtable.append(raw.take(pa.array(qq,pa.int64())));qcells[cell].append(qtable[-1])
compared=0
for row in report['outputs']:
 cell=row['product'],row['date'];got=table(row['path']);expected=pa.concat_tables(wanted[cell]);ok(got.equals(expected),'independent_all14_values:'+str(cell));ok(json.loads(members['lineage/'+cell[0]+'/'+cell[1]+'.json'])==lines[cell],'all_row_provenance:'+str(cell));compared+=len(got)
 f=got.to_pandas();ok(not f.duplicated(['time','code']).any() and not f[c.FIELDS].isna().any().any(),'unique_nonnull:'+str(cell));ok(set(str(x.date()) for x in f.time)=={cell[1]},'exact_date:'+str(cell))
 if cell[0]=='stock':ok(table('dictionary/stock_daily/'+cell[1]+'.parquet').rename_columns(c.FIELDS).equals(got),'reversible_dictionary:'+cell[1])
ok(compared==117460 and len(wanted)==51,'independent_total_and_51_cells')
ok(len(qtable)==len(qrecords)==1 and table('quarantine/original_row.parquet').equals(qtable[0]),'exact_quarantine_values')
ok(qrecords[0]['physical_row_position']==7 and qrecords[0]['code']=='600621.XSHG' and qrecords[0]['source_sha256']=='fb1a0ccb4918e6035d7e6a3695d6fbac6cbf9818c3ea2ca01bcf7928b2e8b2c7','quarantine_identity')
# Recompute observation statistics without using builder observations().
def facts(t):
 f=t.to_pandas();paused=f.paused.eq(1);zero=f.volume.eq(0)&f.money.eq(0);equal=f[['open','high','low','close']].eq(f.pre_close,axis=0).all(axis=1);factor=f.factor
 return {'rows':len(f),'paused_1':int(paused.sum()),'paused_0':int(f.paused.eq(0).sum()),'paused_1_ohlc_eq_pre_close_volume_money_zero':int((paused&zero&equal).sum()),'volume_money_zero':int(zero.sum()),'paused_0_zero_trade_price_incomplete':int((~paused&zero&f[['open','high','low','close']].isna().any(axis=1)).sum()),'nulls':f[c.FIELDS].isna().sum().astype(int).to_dict(),'factor':{'null':int(factor.isna().sum()),'inf':int(factor.isin([float('inf'),float('-inf')]).sum()),'zero':int(factor.eq(0).sum()),'negative':int(factor.lt(0).sum()),'one':int(factor.eq(1).sum()),'not_one_nonnull':int((factor.notna()&factor.ne(1)).sum()),'minimum':None if not len(f) else float(factor.min()),'maximum':None if not len(f) else float(factor.max())}}
for row in report['cells']:
 cell=row['product'],row['date'];raw=pa.concat_tables(rawcells[cell]);admitted=pa.concat_tables(wanted[cell]);q=pa.concat_tables(qcells[cell]) if qcells[cell] else raw.slice(0,0)
 ok(row['input']==len(raw) and row['output']==len(admitted) and row['excluded']==len(q) and len(raw)==len(admitted)+len(q),'per_cell_conservation:'+str(cell))
 ok(row['facts']=={'raw':facts(raw),'admitted':facts(admitted),'quarantined':facts(q)},'independent_observation_states:'+str(cell))
raw=pa.concat_tables([x for v in rawcells.values() for x in v]);ok(facts(raw)==report['facts']['raw'],'all_raw_observations')
ok(report['conservation']=={'input':117461,'output':117460,'excluded':1} and report['product_output_rows']=={'stock':88811,'etf':28530,'index':119},'product_and_total_conservation')
ok(report['backtest_admission'] is False and report['release_admission'] is False and report['historical_pit']=='NOT_ESTABLISHED' and res['p1_sidecar_built'] is False and res['dictionary_formal_admission'] is False,'no_PIT_P1_dictionary_release_admission')
for r in j(out/'LOCAL_READBACK.json')['files']:
 b=(out/r['path']).read_bytes();ok(len(b)==r['bytes'] and sha(b)==r['sha256'],'local_readback:'+r['path'])
result={'source_snapshot':spec['snapshot'],'status':'CANDIDATE_CONTENT_RECONCILED_DELIVERY_CLOSURE_PENDING','assertions':len(checks),'checks':checks,'returned_git_files':len(spec['files']),'archive_bytes':arcbytes,'candidate_files':125,'source_files':1504,'input_rows':117461,'all14_admitted_rows_compared':compared,'all_admitted_lineages_compared':compared,'quarantine_rows':1,'cells':51,'actual_exits':[0,0,0],'native_tests':35,'generation':gen,'pending':['REPORT.md','DELIVERY_MANIFEST.json','UPLOAD_READBACK.json','Preparation actual exit/streams and ACK upload/readback sequence evidence'],'task_closed':False,'current_switch_allowed':False,'backtest_admission':False,'orders_allowed':False}
(R/'AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
