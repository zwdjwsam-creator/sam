"""Owner-scoped R5 append-only continuation; imports the unchanged reviewed R4 helpers.

This entry never calls acquire_daily.run/main. R4 storage, dtype and key guards
remain available unchanged; only the explicitly isolated stock observation can
be excluded from admission. Quarantine is evidence, never a repaired price.
"""
from __future__ import annotations
import argparse
import contextlib
import io
import inspect
import json
import os
import platform
from collections import Counter
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import acquire_daily as a

TASK='BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_ISOLATE_RESUME'
OUTPUT_NAME='BLACKBOX_RAW_NONE_INCREMENT_20261027_R5'
CONTROL=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_R5_ISOLATE_RESUME_20261028')
INHERITED=175858
NEW_CAP=150000
FAILED_REL='raw/stock/2026-10-27_03360_R4.parquet'
FAILED_SHA='fb1a0ccb4918e6035d7e6a3695d6fbac6cbf9818c3ea2ca01bcf7928b2e8b2c7'
LABEL='SUPPLIER_ZERO_TRADE_PRICE_INCOMPLETE_CANDIDATE'

def put(path,obj):
    path=Path(path)
    if not path.stem.endswith('_R5'):path=path.with_name(path.stem+'_R5'+path.suffix)
    path.parent.mkdir(parents=True,exist_ok=True)
    data=(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n').encode()
    with path.open('xb') as f:
        f.write(data);f.flush();os.fsync(f.fileno())
    a.require(path.read_bytes()==data,'LOCAL_READBACK_MISMATCH')
    return {'path':str(path),'bytes':len(data),'sha256':a.digest(data)}

def read_exact(path,pin):
    path=Path(path);before=path.stat();ls=path.lstat()
    a.require(not path.is_symlink() and not (getattr(ls,'st_file_attributes',0)&0x400),'REUSE_REPARSE_DRIFT')
    a.require_allowed_read(path.resolve(strict=True))
    b=path.read_bytes();after=path.stat()
    a.require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'REUSE_READ_DRIFT')
    a.require(len(b)==pin['bytes'] and a.digest(b)==pin['sha256'],'REUSE_IDENTITY_DRIFT')
    return b

def is_quarantine_candidate(row):
    import pandas as pd
    if not all(pd.notna(row[k]) for k in ['paused','volume','money']):return False
    if not (row['paused']==0 and row['volume']==0 and row['money']==0):return False
    if not all(pd.isna(row[k]) for k in ['open','high','low']):return False
    if not all(pd.notna(row[k]) for k in ['close','pre_close','avg','high_limit','low_limit','factor']):return False
    if not (row['close']==row['pre_close']==row['avg']):return False
    pc=Decimal(str(row['pre_close']))
    def limit(ratio,sign):
        return (pc*(Decimal(1)+sign*Decimal(ratio))).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
    return any(Decimal(str(row['high_limit']))==limit(r,+1) and
               Decimal(str(row['low_limit']))==limit(r,-1) for r in ['0.05','0.10','0.20','0.30'])

def classify(frame,codes,day,product):
    """Validate all schema/keys/numeric guards before considering row isolation."""
    import pandas as pd
    a.validate_code_column(frame['code'],set(codes),product)
    try:
        _,quality=a.normalize(frame,codes,day)
        return {'admitted_positions':list(range(len(frame))),'quarantined_positions':[],'quality':quality}
    except a.Blocked as e:
        if str(e)!='LIVE_BAR_NULL' or product!='stock':raise
    # No mutation: a.normalize on the whole batch already passed every earlier guard.
    candidates=[i for i,(_,r) in enumerate(frame.iterrows()) if is_quarantine_candidate(r)]
    a.require(bool(candidates),'LIVE_BAR_NULL')
    admitted=[i for i in range(len(frame)) if i not in set(candidates)]
    good=frame.iloc[admitted]
    good_codes=[c for c in codes if c not in set(frame.iloc[candidates]['code'])]
    _,quality=a.normalize(good,good_codes,day)
    return {'admitted_positions':admitted,'quarantined_positions':candidates,'quality':quality}

class Quarantine:
    def __init__(self):self.rows=[];self.per_day=Counter()
    def add(self,frame,positions,source,day):
        import pandas as pd
        a.require(self.per_day[str(day)]+len(positions)<=3 and len(self.rows)+len(positions)<=10,'QUARANTINE_CAP')
        for position in positions:
            row=frame.iloc[position]
            def value(v):
                if pd.isna(v):return None
                if hasattr(v,'item') and not isinstance(v,(str,datetime)):return v.item()
                if isinstance(v,(date,datetime)):return v.isoformat()
                return v
            self.rows.append({'source':source,'row_position_zero_based':position,
                'source_index':str(frame.index[position]),'date':str(day),'code':str(row['code']),
                'source_values':{str(k):value(v) for k,v in row.items()},'label':LABEL,
                'legal_suspension_status':'NOT_INFERRED','source_values_changed':False,
                'observed_at':a.now().isoformat(),'historical_pit_timestamp':'NOT_ASSIGNED'})
        self.per_day[str(day)]+=len(positions)

def reconcile(expected,admitted,quarantined):
    a.require(len(expected)==len(set(expected)),'EXPECTED_DUPLICATE')
    a.require(len(admitted)==len(set(admitted)) and len(quarantined)==len(set(quarantined)),'DUPLICATE_BOUNDARY')
    a.require(not set(admitted)&set(quarantined),'ADMISSION_QUARANTINE_OVERLAP')
    a.require(set(admitted)|set(quarantined)<=set(expected),'OUT_OF_UNIVERSE_KEY')
    missing=sorted(set(expected)-set(admitted)-set(quarantined))
    return {'expected':len(expected),'admitted':len(admitted),'quarantined':len(quarantined),
      'unacquired_codes':missing,'PAGINATION_COMPLETE':'YES' if not missing else 'NO',
      'ORDER_DETERMINISTIC':'YES','PAGE_BOUNDARY_STABLE':'YES','DUPLICATE_LOSS':0,
      'SILENT_TRUNCATION':0,'source_absence_claim':False}

def validate_remaining(universe_codes,fetched):
    a.require(universe_codes==sorted(set(universe_codes)) and len(universe_codes)==5224,'R4_LAST_UNIVERSE')
    a.require(len(fetched)==3440 and len(set(fetched))==3440,'R4_FETCHED_KEY_SET')
    a.require(set(fetched)<=set(universe_codes),'R4_FETCHED_FOREIGN_KEY')
    remaining=sorted(set(universe_codes)-set(fetched))
    a.require(len(remaining)==1784,'R4_REMAINING_NOT_1784')
    return remaining

def readmit_failed(frame,codes):
    a.require(frame.shape==(80,14),'FAILED_CONTRACT')
    decision=classify(frame,codes,a.UPPER,'stock')
    a.require(len(decision['admitted_positions'])==79 and len(decision['quarantined_positions'])==1,'FAILED_79_1')
    pos=decision['quarantined_positions'][0]
    a.require(frame.iloc[pos]['code']=='600621.XSHG' and a.checked_day(frame.iloc[pos]['time'])==a.UPPER,'FAILED_WRONG_ISOLATE')
    return decision

def reuse_r4(root,reuse,q):
    """Exact identified files only; revalidate retained RAW without another supplier call."""
    import pandas as pd
    src=root/'STAGING/BLACKBOX_RAW_NONE_INCREMENT_20261027_R4'
    pins=json.loads(Path(__file__).with_name('R4_BINDINGS.json').read_bytes())
    docs={};raw_bodies={};refs=[]
    for group in ['metadata','raw']:
        for rel,pin in pins[group].items():
            b=read_exact(src/rel,pin)
            refs.append({'path':str(src/rel),**pin,'reuse':True,'new_supplier_call':False})
            if group=='metadata':docs[rel]=json.loads(b)
            else:raw_bodies[rel]=b
    prior=docs['RESULT_R4.json']
    a.require(prior['reason']=='LIVE_BAR_NULL' and prior['supplier_calls']==1114 and
       prior['cumulative_quota_spent']==INHERITED and
       prior['quota_start']-prior['quota_last_measured']==170538,'R4_RESULT_BINDING')
    days=[date.fromisoformat(d) for d in reuse['plan']['increment_days']['stock']]
    admitted={str(d):[] for d in days};isolated={str(d):[] for d in days};entries=[];fetched=[]
    # The R1 first80 were already independently revalidated by reuse_inputs.
    first=reuse['retained_batch'];admitted[first['date']].extend(first['codes'])
    entries.append({'product':'stock','date':first['date'],'source':{k:first[k] for k in ['path','bytes','sha256']},
      'admitted_positions':list(range(80)),'quarantined_positions':[],'reused':True})
    accepted=0
    for rel,receipt in docs.items():
        if not rel.startswith('quality/') or '_FAILED_' in rel:continue
        a.require(receipt['product']=='stock','R4_UNEXPECTED_PRODUCT')
        day=date.fromisoformat(receipt['date']);req=receipt['request']
        args=docs[f'receipts/request_{req:04d}_R4.json']['arguments'];codes=args['security']
        a.require(args==price_args(codes,day),'R4_PRICE_ARGUMENT_DRIFT')
        raw=receipt['raw'];relraw=Path(raw['path'].replace('\\','/')).as_posix().split('/BLACKBOX_RAW_NONE_INCREMENT_20261027_R4/')[-1]
        a.require(relraw in pins['raw'] and raw['sha256']==pins['raw'][relraw]['sha256'],'R4_RAW_RECEIPT_PIN')
        frame=pd.read_parquet(io.BytesIO(raw_bodies[relraw]));a.validate_code_column(frame['code'],set(codes),'stock')
        _,quality=a.normalize(frame,codes,day)  # Existing accepted batches keep the original hard stop.
        a.require(quality['keys']==receipt['quality']['keys'] and len(frame)==receipt['quality']['rows'],'R4_QUALITY_DRIFT')
        admitted[str(day)].extend(frame['code'].tolist());accepted+=1
        entries.append({'product':'stock','date':str(day),'source':raw,'admitted_positions':list(range(len(frame))),
                        'quarantined_positions':[],'reused':True})
        if day==a.UPPER:fetched.extend(frame['code'].tolist())
    a.require(accepted==1097,'R4_ACCEPTED_BATCH_COUNT')
    pin=pins['raw'][FAILED_REL];a.require(pin=={'bytes':15489,'sha256':FAILED_SHA},'FAILED_PIN')
    failed=pd.read_parquet(io.BytesIO(raw_bodies[FAILED_REL]))
    faildoc=docs['quality/stock_2026-10-27_03360_FAILED_R4.json']
    args=docs['receipts/request_1114_R4.json']['arguments'];codes=args['security']
    a.require(args==price_args(codes,a.UPPER) and failed.shape==(80,14),'FAILED_CONTRACT')
    decision=readmit_failed(failed,codes)
    pos=decision['quarantined_positions'][0]
    source={'path':str(src/FAILED_REL),**pin};q.add(failed,[pos],source,a.UPPER)
    admitted[str(a.UPPER)].extend(failed.iloc[decision['admitted_positions']]['code'].tolist())
    isolated[str(a.UPPER)].append('600621.XSHG');fetched.extend(failed['code'].tolist())
    entries.append({'product':'stock','date':str(a.UPPER),'source':source,**decision,'reused':True})
    universe_codes=docs['universes/stock_2026-10-27_R4.json']['codes']
    remaining=validate_remaining(universe_codes,fetched)
    for day in days[:-1]:
        cov=docs[f'coverage/stock_{day}_R4.json'];r=reconcile(cov['expected_codes'],admitted[str(day)],[])
        a.require(r['PAGINATION_COMPLETE']=='YES','R4_COMPLETED_DAY_KEY_GAP')
    a.require(sum(map(len,admitted.values()))==87027,'R4_ADMITTED_TOTAL')
    a.require(len(admitted[str(a.UPPER)])==3439,'R4_LAST_ADMITTED_COUNT')
    return {'source_root':str(src),'references':refs,'admission':entries,'days':list(map(str,days)),
       'admitted':admitted,'isolated':isolated,'last_universe':universe_codes,'remaining':remaining,
       'expected_by_day':{str(d):(universe_codes if d==a.UPPER else docs[f'coverage/stock_{d}_R4.json']['expected_codes']) for d in days}}

def price_args(codes,day):
    return {'security':codes,'start_date':str(day),'end_date':str(day),'frequency':'daily','fields':a.FIELDS,
            'skip_paused':False,'fill_paused':True,'fq':None,'panel':False}

class Supplier(a.Supplier):
    def __init__(self,jq,out):super().__init__(jq,out,inherited=INHERITED);self.deltas=[]
    def quota(self):
        v=super().quota()
        a.require(self.start-v<=NEW_CAP,'R5_NEW_QUOTA_CEILING')
        return v
    def call(self,name,args):
        a.require(name in {'get_all_securities','get_price'},'ENDPOINT_NOT_ALLOWED')
        if name=='get_price':
            codes=args['security'];a.require(1<=len(codes)<=80,'BATCH_CAP');reserve=len(codes)
        else:
            a.require(args['types']==['etf'],'UNIVERSE_ENDPOINT_SCOPE');reserve=4000
        before=self.quota();used=self.start-before
        a.require(used+reserve<=NEW_CAP and INHERITED+used+reserve<=700000 and before>=reserve,'QUOTA_RESERVE_STOP')
        self.calls+=1;a.require(self.calls<=1000,'CALL_CAP')
        put(self.out/f'request_{self.calls:04d}.json',{'number':self.calls,'endpoint':name,'arguments':args,
            'quota_before':before,'projected_max_units':reserve,'started_at':a.now().isoformat(),'retry':False})
        try:
            with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
                answer=getattr(self.jq,name)(**args)
            after=self.quota();delta=before-after;self.deltas.append(delta)
            put(self.out/f'response_{self.calls:04d}.json',{'number':self.calls,'quota_after':after,
                'quota_delta':delta,'response_received_at':a.now().isoformat(),'acceptance':'PENDING'})
            a.require(delta<=reserve,'SUPPLIER_COST_EXCEEDS_BOUND')
            return answer,self.calls
        except Exception as e:
            put(self.out/f'failure_{self.calls:04d}.json',{'error_type':type(e).__name__,
              'reason':str(e) if isinstance(e,a.Blocked) else 'REDACTED','retry':False})
            raise

def ensure_gate():
    # Identity/raw-result verification, not trust in a caller-provided boolean.
    from precheck_r5 import validate_gate
    return validate_gate(CONTROL)

def save_batch(response,codes,day,product,start,out,request,q):
    import pandas as pd
    a.require(isinstance(response,pd.DataFrame),'NON_DATAFRAME_RESPONSE')
    path=out/'raw'/product/f'{day}_{start:05d}_R5.parquet'
    path.parent.mkdir(parents=True,exist_ok=True);a.require(not path.exists(),'RAW_REPLAY_COLLISION')
    # Store the exact response before any quality transform; failed artifacts survive.
    response.to_parquet(path,index=None);stored=pd.read_parquet(path)
    identity={'path':str(path),'bytes':path.stat().st_size,'sha256':a.digest(path.read_bytes())}
    try:
        code_info=a.validate_code_column(response['code'],set(codes),product)
        serialization=a.verify_parquet_roundtrip(response,stored)
        decision=classify(stored,codes,day,product)
        q.add(stored,decision['quarantined_positions'],identity,day)
    except Exception as e:
        put(out/'quality'/f'{product}_{day}_{start:05d}_FAILED.json',{'request':request,'raw':identity,
            'status':'PARTIAL_BLOCKED','reason':str(e) if isinstance(e,a.Blocked) else 'REDACTED',
            'error_type':type(e).__name__,'raw_preserved':True})
        raise
    entry={'product':product,'date':str(day),'request':request,'source':identity,**decision,'reused':False,
       'code_validation':code_info,'serialization':serialization,'source_rows':len(stored),
       'acquired_at':a.now().isoformat(),'cleaning':'NOT_RUN','pit':'NOT_ASSIGNED',
       'fields_dictionary':'RAW_NONE_DAILY_12_R1','price_basis':'RAW_NONE','local_fill':False}
    put(out/'quality'/f'{product}_{day}_{start:05d}.json',entry)
    return entry,stored.iloc[decision['admitted_positions']]['code'].tolist(),stored.iloc[decision['quarantined_positions']]['code'].tolist()

def check_location(root,out):
    a.require(platform.system()=='Windows' and platform.node().upper()=='ZHANGWEI','WRONG_HOST')
    a.require(root==Path(r'E:\BLACKBOX') and out==root/'STAGING'/OUTPUT_NAME,'WRONG_FIXED_PATH')

def run(root,out):
    check_location(root,out)
    a.require(not out.exists(),'EXISTING_OUTPUT_NO_REPLAY')
    a.require(a.now()<=datetime(2026,10,29,23,59,tzinfo=a.CN),'CONTRACT_EXPIRED')
    gate=ensure_gate()  # No auth, SDK import or E-output before the two independent gates.
    out.mkdir(parents=True,exist_ok=False)
    q=Quarantine();admission=[];coverage={};supplier=None;result={'task_id':TASK,'host':'ZHANGWEI',
       'order_allowed':False,'current_switch_allowed':False,'cleaning_allowed':False,'products':{}}
    try:
        import pandas as pd
        baseline=a.pinned(root);put(out/'BASELINE.json',{'sha256':a.PINNED,'values':baseline,'gate':gate})
        reuse=a.reuse_inputs(root);old=reuse_r4(root,reuse,q)
        admission.extend(old['admission'])
        put(out/'REUSE_MANIFEST.json',{'r1':reuse,'r4':{k:v for k,v in old.items() if k not in ['admission','admitted','isolated']}})
        put(out/'PLAN.json',{'dates':old['days'],'stock_remaining':old['remaining'],'stock_batches':23,
           'inherited_quota':INHERITED,'new_quota_cap':NEW_CAP,'cumulative_cap':700000,
           'no_calendar_or_stock_universe_or_retained_price_refetch':True,'etf_quarantine':False,
           'stock_candidate_label':LABEL,'only_new_increments':True})
        for day in old['days']:
            coverage[('stock',day)]={'expected_codes':old['expected_by_day'][day],
                'admitted':old['admitted'][day],'quarantined':old['isolated'][day]}
        # Plan all unstarted products explicitly before the first supplier call.
        for product in ['etf','index']:
            for day in old['days']:coverage[(product,day)]={'expected_codes':None,'admitted':[],'quarantined':[]}
        import jqdatasdk as jq
        sig=inspect.signature(jq.get_price)
        a.require(getattr(jq,'__version__',None)=='1.9.8','SDK_VERSION_DRIFT')
        a.require(sig.parameters['skip_paused'].default is False and sig.parameters['fill_paused'].default is True,'SDK_DEFAULT_DRIFT')
        put(out/'SDK.json',{'version':jq.__version__,'signature':str(sig),
            'source_sha256':a.digest(Path(inspect.getsourcefile(inspect.unwrap(jq.get_price))).read_bytes()),
            'request_attempt_count':1,'request_timeout':45,'fields':a.FIELDS,'explicit_price_parameters':price_args([],a.UPPER)})
        jq.set_params(request_timeout=45,request_attempt_count=1,enable_auth_prompt=False)
        a.login(jq,root/'配置/secrets/已验证/聚宽账号.txt')
        supplier=Supplier(jq,out/'receipts');supplier.quota()
        for product in ['stock','etf','index']:
            days=[str(a.UPPER)] if product=='stock' else old['days']
            for ds in days:
                day=date.fromisoformat(ds);a.pinned(root)
                if product=='stock':codes=old['remaining'];offset=3440
                elif product=='index':codes=list(a.INDEX);offset=0
                else:
                    master,num=supplier.call('get_all_securities',{'types':['etf'],'date':ds})
                    codes=a.universe(master,day,4000);offset=0
                    put(out/'universes'/f'etf_{ds}.json',{'request':num,'date':ds,'codes':codes,
                       'lifecycle':{c:{'start_date':str(master.loc[c,'start_date']),'end_date':str(master.loc[c,'end_date'])} for c in codes}})
                cov=coverage[(product,ds)]
                if product!='stock':cov['expected_codes']=codes
                for begin in range(0,len(codes),80):
                    a.pinned(root);chunk=codes[begin:begin+80]
                    response,num=supplier.call('get_price',price_args(chunk,day))
                    entry,good,bad=save_batch(response,chunk,day,product,offset+begin,out,num,q)
                    admission.append(entry);cov['admitted'].extend(good);cov['quarantined'].extend(bad)
                    reconcile(cov['expected_codes'],cov['admitted'],cov['quarantined'])
                final=reconcile(cov['expected_codes'],cov['admitted'],cov['quarantined'])
                a.require(final['PAGINATION_COMPLETE']=='YES','PRODUCT_DAY_NOT_EXHAUSTED')
                put(out/'coverage'/f'{product}_{ds}.json',{'product':product,'date':ds,**final,
                    'admitted_codes':sorted(cov['admitted']),'quarantined_codes':sorted(cov['quarantined']),
                    'status':'ACQUIRED','staging_only':True})
        a.pinned(root);supplier.quota()
        a.require(supplier.start-supplier.last==sum(supplier.deltas),'QUOTA_RECEIPT_RECONCILIATION')
        # Registered source freshness is checked again without refetching or a global inventory.
        a.reuse_inputs(root)
        for ref in old['references']:read_exact(Path(ref['path']),ref)
        result['status']='RAW_STAGED_UNREVIEWED'
        code=0
    except Exception as e:
        result.update(status='PARTIAL_BLOCKED',reason=str(e) if isinstance(e,a.Blocked) else 'REDACTED_EXCEPTION_NO_RETRY',error_type=type(e).__name__)
        if supplier and supplier.start is not None:
            try:
                supplier.quota()  # End accounting only; never retry the failed data request.
                result['failure_final_quota_measurement']='MEASURED'
            except Exception:
                result['failure_final_quota_measurement']='FAILED_LAST_MEASUREMENT_ONLY'
        code=2
    # These final receipts are append-only even when a new batch fails.
    put(out/'ADMISSION.json',{'entries':admission,'row_position_base':0,'source_values_changed':False})
    put(out/'QUARANTINE.json',{'rows':q.rows,'per_day_cap':3,'total_cap':10,'label':LABEL,'source_flag_changed':False})
    summary=[]
    for (product,ds),cov in coverage.items():
        expected=cov['expected_codes']
        try:
            counts=reconcile(expected,cov['admitted'],cov['quarantined']) if expected is not None else None
        except a.Blocked as error:
            counts={'integrity_error':str(error),'unacquired_codes':None,'admitted':len(cov['admitted']),
                    'quarantined':len(cov['quarantined']),'PAGINATION_COMPLETE':'NO'}
            result['status']='PARTIAL_BLOCKED';code=2
        summary.append({'product':product,'date':ds,'status':('ACQUIRED' if counts and counts['PAGINATION_COMPLETE']=='YES' else
           'PARTIAL_BLOCKED' if expected is not None else 'NOT_ATTEMPTED'), 'coverage':counts})
    put(out/'COVERAGE.json',{'cells':summary,'source_absence_claim':False,'staging_only':True})
    try:
        a.pinned(root)
        result['baseline_after']='UNCHANGED'
    except Exception:
        result['baseline_after']='DRIFT_OR_UNVERIFIED';result['status']='PARTIAL_BLOCKED';code=2
    result.update(supplier_calls=supplier.calls if supplier else 0,inherited_quota_spent=INHERITED,
       quota_start=supplier.start if supplier else None,quota_last_measured=supplier.last if supplier else None,
       quota_spent=(supplier.start-supplier.last if supplier and supplier.start is not None else 0),
       receipt_quota_sum=sum(supplier.deltas) if supplier else 0,quarantined_rows=len(q.rows),
       admitted_manifest_entries=len(admission),retry=False)
    result['cumulative_quota_spent']=INHERITED+result['quota_spent']
    put(out/'RESULT.json',result)
    return code

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true',required=True);parser.parse_args()
    root=Path(r'E:\BLACKBOX');return run(root,root/'STAGING'/OUTPUT_NAME)

if __name__=='__main__':
    try:raise SystemExit(main())
    except a.Blocked as e:
        print(json.dumps({'status':'PREFLIGHT_BLOCKED','reason':str(e),'order_allowed':False}));raise SystemExit(2)
