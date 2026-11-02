"""Bounded observation, never a cleaning, admission, research or trading entry."""
from __future__ import annotations
from pathlib import Path
from datetime import date, datetime, timezone
from collections import Counter, defaultdict
from decimal import Decimal, getcontext
import hashlib, io, json, math, os, re, struct, sys
import pyarrow as pa
import pyarrow.parquet as pq
getcontext().prec = 2000  # Exact finite binary64 sums within the fixed row cap.

TASK = 'BLACKBOX_A_READONLY_L1234_20261102'
FIELDS = ['time','code','open','high','low','close','volume','money','paused',
          'high_limit','low_limit','avg','pre_close','factor']
SCHEMA = pa.schema([('time',pa.timestamp('ns')),('code',pa.string())] +
                   [(f,pa.float64()) for f in FIELDS[2:]] + [('__index_level_0__',pa.int64())])
NUM = ['paused','open','high_limit','low_limit','volume','money']
MAX_FILE = 64 * 1024 * 1024
MAX_TOTAL_SOURCE = 512 * 1024 * 1024
MAX_OUTPUT = 256 * 1024 * 1024
MAX_MEMBER = 8 * 1024 * 1024
MAX_ROWS = 150000

class Blocked(ValueError): pass
class Safety(Blocked): pass
def need(v, reason):
    if not v: raise Blocked(reason)
def sha(b): return hashlib.sha256(b).hexdigest()
def packed(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def safe(path):
    p=Path(path)
    for a in reversed([p,*p.parents]):
        try: st=a.lstat()
        except FileNotFoundError: continue
        if a.is_symlink() or getattr(st,'st_file_attributes',0)&0x400:
            raise Safety('REPARSE_OR_SYMLINK:'+str(a))
    return p

def meta(st):
    return dict(size=st.st_size,dev=st.st_dev,ino=st.st_ino,mtime_ns=st.st_mtime_ns,
                file_attributes=getattr(st,'st_file_attributes',None))

def read_source(path):
    """Open exact source read-only; Windows denies writers/deletion during read."""
    import stat
    p=safe(path); before=p.stat()
    need(stat.S_ISREG(before.st_mode),'NOT_REGULAR')
    need(before.st_size<=MAX_FILE,'SOURCE_SIZE_CAP')
    if os.name=='nt':
        import ctypes, msvcrt
        from ctypes import wintypes
        k=ctypes.WinDLL('kernel32',use_last_error=True)
        k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,
                               wintypes.LPVOID,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
        k.CreateFileW.restype=wintypes.HANDLE
        k.CloseHandle.argtypes=[wintypes.HANDLE]
        h=k.CreateFileW(str(p),0x80000000,1,None,3,0x00200000,None)
        if h==ctypes.c_void_p(-1).value: raise OSError(ctypes.get_last_error(),'READ_ONLY_OPEN_FAILED')
        try: fd=msvcrt.open_osfhandle(h,os.O_RDONLY|os.O_BINARY)
        except BaseException: k.CloseHandle(h); raise
    else: fd=os.open(p,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
    with os.fdopen(fd,'rb') as f:
        fbefore=os.fstat(f.fileno()); data=f.read(MAX_FILE+1); fafter=os.fstat(f.fileno())
    after=safe(p).stat()
    if not (meta(before)==meta(fbefore)==meta(fafter)==meta(after)):
        raise Safety('SOURCE_METADATA_CHANGED_DURING_READ')
    need(len(data)==before.st_size and len(data)<=MAX_FILE,'SOURCE_LENGTH_CHANGED')
    return data,dict(bytes=len(data),sha256=sha(data),metadata=meta(after),utc=datetime.now(timezone.utc).isoformat())

class Output:
    def __init__(self,root): self.root=Path(root); self.total=0; self.handles={}; self.sizes=Counter()
    def append(self,name,obj):
        need(Path(name).name==name,'OUTPUT_NAME')
        b=packed(obj)+b'\n'
        need(self.total+len(b)<=MAX_OUTPUT and self.sizes[name]+len(b)<=MAX_MEMBER,'OUTPUT_RESOURCE_CAP_NO_TRUNCATION')
        if name not in self.handles: self.handles[name]=(safe(self.root/name)).open('xb')
        self.handles[name].write(b);self.total+=len(b);self.sizes[name]+=len(b)
    def close(self):
        for f in self.handles.values(): f.close()
        self.handles={}
    def json(self,name,obj):
        need(name not in self.handles,'OPEN_OUTPUT_MEMBER')
        b=packed(obj)+b'\n'
        need(len(b)<=MAX_MEMBER and self.total+len(b)<=MAX_OUTPUT,'OUTPUT_RESOURCE_CAP_NO_TRUNCATION')
        p=safe(self.root/name)
        with p.open('xb') as f:f.write(b)
        need(p.read_bytes()==b,'OUTPUT_READBACK')
        self.total+=len(b);self.sizes[name]=len(b)

def float_value(v):
    if v is None:return {'state':'NULL'}
    bits=struct.pack('>d',float(v)).hex()
    if math.isnan(v):return {'state':'NAN','ieee754':bits}
    if math.isinf(v):return {'state':'POS_INF' if v>0 else 'NEG_INF','ieee754':bits}
    return {'state':'FINITE','value':v,'ieee754':bits}

def flags(row):
    out=[]
    good=lambda *fs:all(row.get(f) is not None and math.isfinite(row[f]) for f in fs)
    for f in NUM:
        v=row.get(f)
        if v is None:out.append(f+':NULL')
        elif not math.isfinite(v):out.append(f+':NON_FINITE')
        elif f!='paused' and v<=0:out.append(f+(':ZERO' if v==0 else ':NEGATIVE'))
    if good('paused') and row['paused'] not in (0,1):out.append('STATUS_OUTSIDE_0_1')
    if good('high_limit','low_limit') and row['high_limit']<=row['low_limit']:out.append('UPPER_NOT_ABOVE_LOWER')
    if good('paused','open','high_limit','low_limit') and row['paused']==0 and not row['low_limit']<=row['open']<=row['high_limit']:
        out.append('UNPAUSED_OPEN_OUTSIDE_OBSERVED_BOUNDS')
    return out

def board(code):
    if not isinstance(code,str):return None,None
    if code=='689009.XSHG':return 'CDR_HOLD',None
    if code=='302132.XSHE':return 'CHINEXT_SINGLE_EXCEPTION','0.20'
    if re.fullmatch(r'(600|601|603|605)\d{3}\.XSHG',code):return 'SH_MAIN','0.10'
    if re.fullmatch(r'(000|001|002|003)\d{3}\.XSHE',code):return 'SZ_MAIN','0.10'
    if re.fullmatch(r'(300|301)\d{3}\.XSHE',code):return 'CHINEXT','0.20'
    if re.fullmatch(r'688\d{3}\.XSHG',code):return 'STAR','0.20'
    return 'UNSUPPORTED',None

def lifecycle_day(value):
    need(isinstance(value,str) and len(value)==19 and value[10:]==' 00:00:00','UNBOUND_LIFECYCLE_FORMAT')
    return date.fromisoformat(value[:10]).isoformat()

def universe(data,day):
    def unique(pairs):
        d={}
        for k,v in pairs:
            need(k not in d,'DUPLICATE_JSON_KEY');d[k]=v
        return d
    u=json.loads(data,object_pairs_hook=unique)
    need(set(u)=={'request','date','codes','lifecycle'} and u['date']==day,'UNIVERSE_SCHEMA_DAY')
    need(type(u['request']) is int and u['request']>0,'UNIVERSE_REQUEST')
    need(isinstance(u['codes'],list) and all(isinstance(c,str) for c in u['codes']),'UNIVERSE_CODES')
    need(len(set(u['codes']))==len(u['codes']) and set(u['codes'])==set(u['lifecycle']),'UNIVERSE_DUPLICATES_OR_LIFECYCLE_KEYS')
    for code in u['codes']:
        r=u['lifecycle'][code];need(set(r)=={'start_date','end_date'},'LIFECYCLE_COLUMNS')
        start,end=lifecycle_day(r['start_date']),lifecycle_day(r['end_date'])
        need(start<=day<=end,'LIFECYCLE_VALIDITY')
    return u

def classify(code,day,u,sessions,exceptions,session_index=None):
    b,width=board(code)
    result=dict(label='UNKNOWN',board=b,candidate_limit_width=width,st_status='UNKNOWN_NOT_CAPTURED',
                instrument_type='SUPPLIER_STOCK_QUERY_SCOPE_ONLY',regime_admitted=False,
                calendar_basis='REVIEW_ONLY_RETAINED_SEQUENCES_NOT_POLICY_EXTENSION')
    if b in ('CDR_HOLD','UNSUPPORTED'):
        result.update(label='EXCLUDED_UNSUPPORTED_OR_CDR',reason=b);return result
    if u is None or u.get('date')!=day or code not in u['lifecycle']:
        result['reason']='UNKNOWN_MASTER';return result
    try:start=lifecycle_day(u['lifecycle'][code]['start_date'])
    except (Blocked,TypeError,ValueError):result['reason']='UNKNOWN_LISTING_DATE';return result
    result['listing_date']=start
    if (code,day) in exceptions:
        result.update(label='NO_LIMIT_CANDIDATE',reason='DATED_EXCEPTION_DESK_EVIDENCE_NOT_PIT_CERTIFICATE');return result
    if session_index is None:
        if sessions!=sorted(set(sessions)):
            result['reason']='UNKNOWN_CALENDAR';return result
        session_index={d:i for i,d in enumerate(sessions)}
    if day not in session_index or start>day:
        result['reason']='UNKNOWN_CALENDAR';return result
    if start in session_index: ordinal=session_index[day]-session_index[start]+1
    elif start<sessions[0] and session_index[day]>=5: ordinal=None
    else:result['reason']='UNKNOWN_LISTING_SESSION_COVERAGE';return result
    result['listing_session_ordinal']=ordinal
    if ordinal is not None and 1<=ordinal<=5:
        result.update(label='NO_LIMIT_CANDIDATE',reason='IPO_SESSIONS_1_THROUGH_5_INCLUSIVE')
    else:result.update(label='LIMITED_CANDIDATE_PENDING_EXCEPTIONS',reason='EXCEPTION_CENSUS_INCOMPLETE_NOT_ADMITTED')
    return result

def compare_scales(local,official,prereg):
    if not official.get('scope_compatible_and_complete',False):return {'status':'UNRESOLVED','reason':'OFFICIAL_SCOPE_OR_COVERAGE_NOT_BOUND'}
    results={}
    for field in prereg['fields']:
        ratios={s:[] for s in prereg['candidate_multipliers_applied_to_raw_sum_after_explicit_official_unit_normalization']}
        for day in prereg['dates']:
            for ex in prereg['exchanges']:
                key=day+'|'+ex
                a=local.get(key);b=official.get('cells',{}).get(key)
                if not a or not b or a.get('comparison_blockers') or not b.get('scope_bound'):
                    return {'status':'UNRESOLVED','reason':'INCOMPLETE_REQUIRED_CELL'}
                try:raw=Decimal(a[field]);ref=Decimal(b[field])
                except Exception:return {'status':'UNRESOLVED','reason':'NON_DECIMAL_REFERENCE'}
                if not raw.is_finite() or not ref.is_finite() or raw<=0 or ref<=0:
                    return {'status':'UNRESOLVED','reason':'NONPOSITIVE_REFERENCE_OR_RAW'}
                for s in ratios:ratios[s].append(raw*Decimal(s)/ref)
        matching=[s for s,rs in ratios.items() if all(Decimal('.95')<=r<=Decimal('1.05') for r in rs)]
        if len(matching)!=1:return {'status':'UNRESOLVED','reason':'NO_UNIQUE_MULTIPLIER'}
        chosen=matching[0]
        if not all(all(r<=Decimal('.1') or r>=Decimal('10') for r in rs) for s,rs in ratios.items() if s!=chosen):
            return {'status':'UNRESOLVED','reason':'OTHER_MULTIPLIER_NOT_10X_SEPARATED'}
        results[field]=chosen
    return {'status':'ORDER_OF_MAGNITUDE_ONLY','multipliers':results,'unit_admitted':False}

class Profile:
    def __init__(self,out,sessions,exceptions,prereg,universes):
        self.out=out;self.sessions=sessions;self.exceptions=exceptions;self.prereg=prereg;self.universes=universes
        need(sessions==sorted(set(sessions)) and bool(sessions),'REVIEW_CALENDAR_ORDER')
        self.session_index={d:i for i,d in enumerate(sessions)}
        self.counts=Counter();self.date_counts=Counter();self.anomalies=Counter();self.keys=defaultdict(list)
        self.daykeys=defaultdict(list);self.limits=defaultdict(lambda:dict(count=0,examples=[]))
        self.cells={};self.sample=None;self.errors=[];self.seen_codes=defaultdict(set)
        self.rows=0;self.quarantine=0
        self.out.json('ROWS_SCHEMA.json',dict(schema='BLACKBOX_DIAGNOSTIC_ROW_VECTOR_R1',
             columns=['source_id','zero_based_physical_row','code','time_ns','numeric_ieee754','flags','quarantined','candidate'],
             numeric_field_order=NUM,numeric_encoding='Arrow NULL is JSON null; otherwise exact big-endian binary64 hex, including signed zero, NaN and infinities',
             candidate_columns=['label','board','candidate_limit_width','reason','listing_date','listing_session_ordinal'],
             source_binding='source_id joins the full pinned INPUTS.json source path/fullSHA and SOURCE_BEFORE/SOURCE_AFTER observations',
             st_status='UNKNOWN_NOT_CAPTURED',instrument_type='SUPPLIER_STOCK_QUERY_SCOPE_ONLY',
             calendar_basis='REVIEW_ONLY_RETAINED_SEQUENCES_NOT_POLICY_EXTENSION',regime_admitted=False,unit_admitted=False))
        for d in prereg['dates']:
            for ex in prereg['exchanges']:
                self.cells[d+'|'+ex]=dict(money=Decimal(0),volume=Decimal(0),included_rows=0,
                                        excluded_rows=0,excluded_money=Decimal(0),excluded_volume=Decimal(0),
                                        comparison_blockers=['OFFICIAL_REFERENCE_NOT_BOUND','SESSION_SCOPE_NOT_CERTIFIED'],
                                        quantity_scope='PREDECLARED_CODE_PROFILE_A_SHARES_EXCLUDES_CDR')
    def add(self,ref,data):
        need(len(data)==ref['expected_bytes'] and sha(data)==ref['expected_sha256'],'SOURCE_IDENTITY')
        t=pq.ParquetFile(io.BytesIO(data)).read()
        need(t.schema.remove_metadata()==SCHEMA,'RAW_ARROW_SCHEMA_NO_ALIAS_OR_COERCION')
        need(t.num_rows==ref['expected_physical_rows'],'PHYSICAL_ROW_COUNT')
        need(t.num_rows<=10000,'BATCH_ROW_CAP')
        ns=t['time'].cast(pa.int64()).to_pylist();cols={f:t[f].to_pylist() for f in FIELDS[1:]}
        indices=t['__index_level_0__'].to_pylist()
        need(indices==list(range(t.num_rows)),'INDEX_NOT_EXPECTED_PHYSICAL_SEQUENCE')
        day=ref['indexed_session'];u=self.universes.get(day)
        for pos,tm in enumerate(ns):
            self.rows+=1;need(self.rows<=MAX_ROWS,'TOTAL_ROW_CAP')
            r={f:cols[f][pos] for f in NUM};code=cols['code'][pos]
            dt=None if tm is None else t['time'][pos].as_py().isoformat()
            valid_day=dt is not None and dt[:10]==day and tm%86400000000000==0
            tag=flags(r)
            if not valid_day:tag.append('NULL_NONMIDNIGHT_OR_CELL_TIME_MISMATCH')
            if not isinstance(code,str) or not re.fullmatch(r'\d{6}\.(XSHG|XSHE)',code):tag.append('INVALID_CODE')
            q=pos in ref['quarantined_positions'];self.quarantine+=int(q)
            if q:tag.append('EXISTING_QUARANTINE_NOT_ADMITTED')
            loc=dict(source_id=ref['source_id'],physical_row=pos,indexed_session=day)
            if code is not None and tm is not None:
                self.keys[(code,tm)].append(loc);self.daykeys[(code,dt[:10])].append(dict(**loc,time_ns=tm))
            self.counts['physical']+=1;self.date_counts[day]+=1
            for f in tag:self.anomalies[f]+=1
            if isinstance(code,str):self.seen_codes[day].add(code)
            classed=classify(code,day,u,self.sessions,self.exceptions,self.session_index) if valid_day else dict(label='UNKNOWN',reason='INVALID_TIME',regime_admitted=False)
            row=dict(**loc,source_sha256=ref['expected_sha256'],code=code,time_ns=tm,time_iso=dt,
                     values={f:float_value(r[f]) for f in NUM},flags=tag,quarantined=q,classification=classed)
            candidate_vector=[classed.get(f) for f in ['label','board','candidate_limit_width','reason','listing_date','listing_session_ordinal']]
            self.out.append('ROWS_'+day+'.jsonl',[ref['source_id'],pos,code,tm,
                  [None if r[f] is None else struct.pack('>d',r[f]).hex() for f in NUM],tag,q,candidate_vector])
            if ref.get('sample') and pos==68:
                self.sample=row
                need(code=='002270.XSHE' and valid_day and
                     r==dict(paused=0.,open=17.87,high_limit=19.82,low_limit=16.22,volume=14076869.,money=254286654.36),'SAMPLE_002270_VALUES')
            pair=packed([float_value(r['high_limit']),float_value(r['low_limit'])]).decode()
            z=self.limits[(day,pair)];z['count']+=1
            if len(z['examples'])<3:z['examples'].append(loc)
            ex=code[-4:] if isinstance(code,str) else None;key=day+'|'+str(ex)
            if key in self.cells:
                cell=self.cells[key];b,width=board(code)
                if b in ('UNSUPPORTED','CDR_HOLD'):
                    cell['excluded_rows']+=1
                    for f in ('money','volume'):
                        if r[f] is not None and math.isfinite(r[f]):cell['excluded_'+f]+=Decimal.from_float(r[f])
                    continue
                cell['included_rows']+=1
                if q or not valid_day or code not in (u or {}).get('lifecycle',{}):cell['comparison_blockers'].append('QUARANTINE_TIME_OR_UNIVERSE')
                for f in ('money','volume'):
                    if r[f] is None or not math.isfinite(r[f]) or r[f]<0:cell['comparison_blockers'].append('INVALID_'+f)
                    else:cell[f]+=Decimal.from_float(r[f])
    def finish(self,expected_days,official):
        duplicate_groups=[dict(code=k[0],time_ns=k[1],rows=v) for k,v in self.keys.items() if len(v)>1]
        for d in self.prereg['dates']:
            u=self.universes.get(d)
            for ex in self.prereg['exchanges']:
                cell=self.cells[d+'|'+ex]
                expected={c for c in (u or {}).get('codes',[]) if c.endswith('.'+ex) and board(c)[0] not in ('UNSUPPORTED','CDR_HOLD')}
                actual={c for c in self.seen_codes[d] if c.endswith('.'+ex) and board(c)[0] not in ('UNSUPPORTED','CDR_HOLD')}
                cell['expected_vendor_scope_codes']=len(expected);cell['observed_codes']=len(actual)
                cell['universe_key_equal']=expected==actual and u is not None
                if not cell['universe_key_equal']:cell['comparison_blockers'].append('VENDOR_UNIVERSE_COVERAGE')
                if any(g['code'].endswith('.'+ex) and any(r['indexed_session']==d for r in g['rows']) for g in duplicate_groups):
                    cell['comparison_blockers'].append('DUPLICATE_KEYS_PRESENT_NO_DEDUP')
                cell['comparison_blockers']=sorted(set(cell['comparison_blockers']))
                for f in ('money','volume','excluded_money','excluded_volume'):cell[f]=str(cell[f])
        self.out.close()
        self.out.json('DUPLICATES.json',dict(exact_key_groups=duplicate_groups,
                  code_date_groups=[dict(code=k[0],day=k[1],rows=v) for k,v in self.daykeys.items() if len({r['time_ns'] for r in v})>1],
                  suppression_applied=False))
        for (day,pair),z in sorted(self.limits.items()):self.out.append('LIMITS_'+day+'.jsonl',dict(pair=json.loads(pair),**z))
        self.out.close()
        self.out.json('SAMPLE_002270.json',dict(observation=self.sample,found=self.sample is not None))
        self.out.json('L4_TOTALS.json',dict(cells=self.cells,preregistration=self.prereg,scale_result=compare_scales(self.cells,official,self.prereg),unit_admitted=False))
        self.out.json('L2_L3_COUNTS.json',dict(physical_rows=self.rows,quarantined=self.quarantine,
                       nonquarantined=self.rows-self.quarantine,rows_per_indexed_day=dict(self.date_counts),
                       anomaly_flags=dict(self.anomalies),decode_errors=self.errors,
                       expected_days=expected_days,regime_admitted=False,st_status='UNKNOWN_NOT_CAPTURED'))
        return dict(rows=self.rows,quarantined=self.quarantine,decode_errors=len(self.errors))

def collect(catalogue,out,reader=read_source):
    output=Output(out);before=[];after=[];dispositions=[];cache={};total=0;safety=False;blocked=False
    refs=catalogue['historical']+catalogue['universes']+catalogue['stock']
    profile=None
    try:
        for ref in refs:
            path=ref['path'];rec=dict(source_id=ref['source_id'],path=path)
            try:
                data,obs=reader(path);total+=len(data);need(total<=MAX_TOTAL_SOURCE,'TOTAL_SOURCE_CAP')
                rec.update(obs);before.append(rec)
                need(sha(data)==ref['expected_sha256'] and (ref['expected_bytes'] is None or len(data)==ref['expected_bytes']),'PIN_MISMATCH')
                if ref['kind']=='UNIVERSE':cache[ref['indexed_session']]=universe(data,ref['indexed_session'])
                if ref['kind']=='STOCK':
                    if profile is None:profile=Profile(output,catalogue['review_sessions'],{tuple(x) for x in catalogue['no_limit_exceptions']},catalogue['preregistration'],cache)
                    try:profile.add(ref,data)
                    except Exception as e:
                        profile.errors.append(dict(source_id=ref['source_id'],error_type=type(e).__name__,error=str(e)));blocked=True
                dispositions.append(dict(source_id=ref['source_id'],status='MATCHED',bytes=len(data),sha256=sha(data)))
            except Safety as e:
                safety=True;dispositions.append(dict(source_id=ref['source_id'],status='SAFETY_BLOCKED',error=str(e)))
                break
            except (OSError,Blocked,ValueError,json.JSONDecodeError) as e:
                blocked=True
                if not any(x['source_id']==ref['source_id'] for x in before):before.append(dict(**rec,status='READ_FAILED',error_type=type(e).__name__,error=str(e)))
                dispositions.append(dict(source_id=ref['source_id'],status='BOUNDED_READ_OR_IDENTITY_FAILURE_NOT_SOURCE_ABSENCE',error_type=type(e).__name__,error=str(e)))
        output.json('SOURCE_BEFORE.json',dict(files=before))
        output.json('IDENTITY_DISPOSITIONS.json',dict(files=dispositions,unprocessed=[r['source_id'] for r in refs[len(dispositions):]],source_absence_claims=0))
        for rec in before:
            ref=next(r for r in refs if r['source_id']==rec['source_id'])
            try:
                data,obs=reader(ref['path']);post=dict(source_id=rec['source_id'],path=ref['path'],**obs)
                post['equal_before']=all(rec.get(k)==post.get(k) for k in ('bytes','sha256','metadata'))
                if not post['equal_before']:safety=True
            except Exception as e:
                post=dict(source_id=rec['source_id'],path=ref['path'],equal_before=False,error_type=type(e).__name__,error=str(e))
                if rec.get('status')!='READ_FAILED':safety=True
            after.append(post)
        output.json('SOURCE_AFTER.json',dict(files=after))
        result=profile.finish(catalogue['data_sessions'],catalogue['official_reference']) if profile else None
        if result is None or result['rows']!=88812 or result['quarantined']!=1 or len(profile.date_counts)!=17 or profile.sample is None:blocked=True
        exit_code=3 if safety else 2 if blocked else 0
        output.json('OBSERVATION_RESULT.json',dict(task_id=TASK,status='OBSERVATION_AWAITING_GPT' if exit_code==0 else 'BLOCKED_OBSERVATION_RETAINED',
                      intended_exit=exit_code,profile=result,expected_sources=len(refs),processed_sources=len(dispositions),
                      supplier_calls=0,source_absence_claims=0,regime_admitted=False,unit_admitted=False,ORDER_ALLOWED=False))
        return exit_code
    finally:output.close()
