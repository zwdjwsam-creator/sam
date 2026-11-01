import io,json,hashlib
from pathlib import Path
from datetime import datetime,date,time,timedelta,timezone
import pyarrow.parquet as pq
import candidate_adapter as old
import p4_consumer as p
ROOT=Path(__file__).resolve().parent.parent
consumer=p.Consumer(ROOT/'p3_native_review/return/result_001',ROOT/'p1_dispatch',ROOT/'p4_offline/INPUT_PINS.json')
answer=consumer.select('2026-10-27T09:00:00+08:00',p.PUBLIC)
bindings=json.loads((ROOT/'p3_dispatch/bindings.json').read_bytes());reader=old.BodyReader(ROOT/'evidence',bindings)
days=json.loads((ROOT/'p1_dispatch/CALENDAR.json').read_bytes())['returned'];cn=timezone(timedelta(hours=8));decision=datetime(2026,10,27,9,tzinfo=cn);expected={};stock_paused=0
for e,key in zip(reader.admission['entries'],reader.entry_keys):
 if e['product']!='stock':continue
 raw=pq.ParquetFile(io.BytesIO(reader.read(e,key))).read().select(old.FIELDS)
 for pos in e['admitted_positions']:
  row=raw.slice(pos,1).to_pylist()[0];day=row['time'].date().isoformat();stock_paused+=int(row['paused']==1)
  i=days.index(day) if day in days else None
  if i is None or i+1==len(days):continue
  at=datetime.combine(date.fromisoformat(days[i+1]),time(9),cn)
  if at>decision:continue
  row['time']=day;expected[(day,row['code'])]=(row,e['source']['path'],e['source']['sha256'],pos,at.isoformat())
seen=set()
for r in answer:
 v=r['values'];key=v['time'],v['code'];assert key not in seen;seen.add(key);raw,path,sha,pos,at=expected[key]
 assert v=={k:raw[k] for k in p.PUBLIC}
 assert r['states']=={'paused':raw['paused'],'volume':raw['volume'],'money':raw['money'],'high_limit':raw['high_limit'],'low_limit':raw['low_limit'],'missing_price':False,'execution_allowed':False}
 assert r['provenance']['source_file']==path and r['provenance']['source_sha256']==sha and r['provenance']['physical_row_position']==pos
 assert r['availability']['presumed_available_at']==at
assert seen==set(expected);assert stock_paused==consumer.summary['paused_by_product']['stock']
out={'audit':'INDEPENDENT_RAW_TO_P4_VALUE_STATE_PROVENANCE_AND_DATETIME','rows_compared':len(answer),'all_public_fields_exact':True,'all_mandatory_states_exact':True,'all_raw_source_positions_exact':True,'all_presumed_times_independently_recomputed':True,'exact_keys_equal':True,'stock_paused_measured':stock_paused,'stock_rows_total':88811,'stock_dates_returned':len({x[0] for x in seen}),'unresolved_stock_rows':consumer.summary['UNRESOLVED_rows'],'backtest_run':False,'native_execution':False,'orders_allowed':False}
(ROOT/'p4_offline/INDEPENDENT_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
