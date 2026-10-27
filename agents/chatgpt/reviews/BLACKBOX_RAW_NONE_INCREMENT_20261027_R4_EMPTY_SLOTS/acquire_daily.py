"""One-shot ZHANGWEI RAW_NONE acquisition. No production publication or local fill."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import inspect
import io
import json
import os
import platform
import re
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
TASK = 'BLACKBOX_RAW_NONE_INCREMENT_20261027_R4_EMPTY_SLOTS'
OUTPUT_NAME = 'BLACKBOX_RAW_NONE_INCREMENT_20261027_R4'
INHERITED_SPEND = 5320
LOWER = date(2026, 9, 24)  # observed coverage boundary, not a universal historical start
UPPER = date(2026, 10, 27)
FIELDS = ['open','high','low','close','volume','money','paused','high_limit','low_limit','avg','pre_close','factor']
INDEX = ['000001.XSHG','399001.XSHE','399006.XSHE','000300.XSHG','000905.XSHG','000852.XSHG','000016.XSHG']
PINNED = {
 '数据/清洗成品/CURRENT_CLEANING_RELEASE.json': '9abad90cd952a1d623d124b794cbb0c025161cb9b80053c09980f25c0d481128',
 '数据/回测缓存/CURRENT_CACHE_RELEASE.json': 'b2ce53f05e50e0d38c9f4232f6b5e94040d6a081066d24759e52dd60eb622564',
 '研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json': '574842e7802be26d648d5aa2f6d91a9b4c208744e3ecf9f146e02ece41387d89',
 '研究系统/数据平面/CURRENT/DAILY_DATA_PLANE_CURRENT.json': '8a492440257170577a5c96f66bfd81e3b93fc6dc58e547cc3acd4c7baaf3fe9b',
}
RAW_RELS = {'stock':['P2_stock_daily'], 'etf':['P4_fund_etf_raw_none/fund_etf_price_daily','P8_etf_fund'], 'index':['P3_index']}
CLEAN_RELS = {'stock':['price/stock_ohlcv_daily'], 'etf':['price/ETF_daily'], 'index':['reference/index_daily']}
CACHE_RELS = {'stock':['STOCK_DAILY_RAW_PIT_R1','STOCK_DAILY_PIT_R1'], 'etf':['ETF_DAILY_PIT_R1'], 'index':['INDEX_DAILY_R1']}

class Blocked(Exception):
    pass

def require(ok, code):
    if not ok:
        raise Blocked(code)

def digest(b):
    return hashlib.sha256(b).hexdigest()

def validate_code_column(s, requested, domain):
    import pandas as pd
    require(not s.isna().any(),'CODE_NULL')
    values=s.tolist()
    require(all(type(v) is str for v in values),'CODE_NON_STR_ELEMENT')
    require(s.dtype==object or isinstance(s.dtype,pd.StringDtype),'CODE_UNSUPPORTED_DTYPE')
    if domain=='index':
        require(set(values)<=set(INDEX),'CODE_NAMESPACE')
    else:
        require(all(re.fullmatch(r'\d{6}\.(XSHG|XSHE)',v) for v in values),'CODE_NAMESPACE')
    require(set(values)<=set(requested),'CODE_NOT_REQUESTED')
    return {'supplier_code_dtype':str(s.dtype),'n_codes':len(set(values))}

def compare_code_roundtrip(before, after):
    import pandas as pd
    require(not before.isna().any() and not after.isna().any(),'CODE_NULL')
    require(all(type(v) is str for v in before.tolist()+after.tolist()),'CODE_NON_STR_ELEMENT')
    pd.testing.assert_index_equal(before.index,after.index,exact=True)
    require(before.tolist()==after.tolist(),'CODE_VALUE_OR_ORDER_CHANGED')
    if before.dtype==after.dtype:
        pd.testing.assert_series_equal(before,after,check_dtype=True,check_exact=True)
        return after,None
    require(before.dtype==object and isinstance(after.dtype,pd.StringDtype),'CODE_DTYPE_CHANGE')
    return after.astype(object),{'column':'code','supplier_dtype':str(before.dtype),'stored_dtype':str(after.dtype),
       'rule':'OBJECT_TO_PANDAS_STRING_EXACT_BUILTIN_STR_VALUES_ONLY','values_exact':True,
       'nulls_allowed':False,'supplier_dtype_reconstructible':True,'coerce_to_str':False}

def verify_parquet_roundtrip(source, stored):
    """Allow only exact-value s->ms timestamp representation; every other dtype stays strict."""
    import pandas as pd
    audit={'original_dtypes':{str(c):str(t) for c,t in source.dtypes.items()},
           'stored_dtypes':{str(c):str(t) for c,t in stored.dtypes.items()},
           'original_index_dtype':str(source.index.dtype),'stored_index_dtype':str(stored.index.dtype),
           'timestamp_representation_changes':[],'code_representation_changes':[],'values_exact':False}
    require(source.columns.equals(stored.columns),'ROUNDTRIP_COLUMNS_CHANGED')
    require(source.shape==stored.shape,'ROUNDTRIP_SHAPE_CHANGED')
    require(not source.columns.duplicated().any(),'ROUNDTRIP_DUPLICATE_COLUMNS')
    def restore(left,right,label):
        if left.dtype==right.dtype:return right
        require(pd.api.types.is_datetime64_any_dtype(left.dtype) and pd.api.types.is_datetime64_any_dtype(right.dtype),
                'ROUNDTRIP_NON_TIMESTAMP_DTYPE_CHANGE')
        def unit(dtype):
            return getattr(dtype,'unit',None) or __import__('numpy').datetime_data(dtype)[0]
        require((unit(left.dtype),unit(right.dtype))==('s','ms'),'ROUNDTRIP_UNREVIEWED_UNIT_CHANGE')
        require(getattr(left.dtype,'tz',None)==getattr(right.dtype,'tz',None),'ROUNDTRIP_TIMEZONE_CHANGED')
        lm=pd.isna(left);rm=pd.isna(right)
        require((__import__('numpy').asarray(lm)==__import__('numpy').asarray(rm)).all(),'ROUNDTRIP_TIMESTAMP_NULL_CHANGED')
        # Compare values BEFORE any cast-back, so a subsecond corruption cannot be hidden by truncation.
        lv=left[~lm];rv=right[~rm]
        if isinstance(lv,pd.Series):
            require((lv.reset_index(drop=True)==rv.reset_index(drop=True)).all(),'ROUNDTRIP_TIMESTAMP_VALUE_CHANGED')
        else:
            require((lv==rv).all(),'ROUNDTRIP_TIMESTAMP_VALUE_CHANGED')
        result=right.astype(left.dtype)
        audit['timestamp_representation_changes'].append({'axis':label,'supplier_dtype':str(left.dtype),
          'stored_dtype':str(right.dtype),'rule':'EXACT_VALUE_SECONDS_TO_MILLISECONDS_ONLY',
          'supplier_dtype_reconstructible':True,'local_price_or_date_value_change':False})
        return result
    aligned=stored.copy(deep=True)
    aligned.index=restore(source.index,stored.index,'index')
    pd.testing.assert_index_equal(source.index,aligned.index,exact=True)
    for c in source.columns:
        if c=='code':
            aligned[c],change=compare_code_roundtrip(source[c],aligned[c])
            if change:audit['code_representation_changes'].append(change)
        else:
            aligned[c]=restore(source[c],aligned[c],str(c))
    pd.testing.assert_frame_equal(source,aligned,check_dtype=True,check_exact=True)
    audit['values_exact']=True
    return audit

def now():
    return datetime.now(CN)

def put(path, obj):
    path = Path(path)
    if not path.stem.endswith('_R4'):path=path.with_name(path.stem+'_R4'+path.suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    b = (json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False, default=str)+'\n').encode('utf-8')
    with path.open('xb') as f:
        f.write(b)
        f.flush()
        os.fsync(f.fileno())
    require(path.read_bytes() == b, 'LOCAL_READBACK_MISMATCH')
    return {'path':str(path),'bytes':len(b),'sha256':digest(b)}

def checked_day(value):
    # Never interpret ordinal integers as an epoch or an arbitrary date offset.
    import pandas as pd
    import numpy as np
    require(not isinstance(value,(int,float,np.integer,np.floating,bool)), 'NUMERIC_DATE_AXIS')
    try:
        v = pd.Timestamp(value)
        require(not pd.isna(v), 'NULL_DATE_AXIS')
        return v.date()
    except Blocked:
        raise
    except Exception:
        raise Blocked('UNPARSEABLE_DATE_AXIS') from None

def normalize(frame, codes, day):
    import pandas as pd
    require(isinstance(frame,pd.DataFrame), 'NON_DATAFRAME_RESPONSE')
    raw = frame.copy(deep=True)
    require({'time','code',*FIELDS}.issubset(raw.columns), 'SCHEMA_MISSING_REQUIRED_FIELD')
    require(not raw.columns.duplicated().any(), 'DUPLICATE_COLUMNS')
    require(not raw['time'].isna().any() and not raw['code'].isna().any(), 'NULL_STABLE_KEY')
    days = raw['time'].map(checked_day)
    require(set(days) <= {day}, 'OUT_OF_RANGE_DATE')
    require(all(isinstance(x,str) for x in raw['code']), 'NON_STRING_SECURITY_KEY')
    require(not raw[['time','code']].duplicated().any(), 'DUPLICATE_RESPONSE_KEY')
    actual = set(zip(days, raw['code']))
    require(len(actual)==len(raw),'DUPLICATE_NORMALIZED_DATE_KEY')
    expected = {(day,c) for c in codes}
    key_receipt = {'expected':[[str(day),c] for c in codes],
                   'returned':[[str(d),c] for d,c in sorted(actual)],
                   'missing':[[str(d),c] for d,c in sorted(expected-actual)],
                   'extra':[[str(d),c] for d,c in sorted(actual-expected)]}
    require(not key_receipt['extra'], 'OUT_OF_UNIVERSE_KEY')
    require(not key_receipt['missing'], 'UNEXPLAINED_MISSING_KEY')
    for col in FIELDS:
        require(pd.api.types.is_numeric_dtype(raw[col]), 'NON_NUMERIC_FIELD_'+col)
        require(__import__('numpy').isfinite(raw[col].dropna()).all(), 'NONFINITE_FIELD_'+col)
    # Preserve supplier fill and nulls. Missing price for an explicitly paused row is not locally filled.
    live = raw['paused'].eq(0)
    require(raw['paused'].notna().all() and raw['paused'].isin([0,1]).all(), 'UNKNOWN_PAUSED_STATE')
    require(raw.loc[live,['open','high','low','close','volume','money']].notna().all().all(), 'LIVE_BAR_NULL')
    receipt = {'rows':len(raw), 'keys':key_receipt,
      'nulls':{c:int(raw[c].isna().sum()) for c in FIELDS},
      'observations':{'supplier_paused':int(raw['paused'].eq(1).sum()),'supplier_live':int(live.sum())},
      'local_price_fill':False,'local_duplicate_suppression':False,'factor_used_for_adjustment':False}
    return raw,receipt

def universe(frame, day, ceiling):
    import pandas as pd
    require(isinstance(frame,pd.DataFrame) and len(frame)>0 and len(frame)<=ceiling, 'UNIVERSE_EMPTY_OR_CAP')
    require(not frame.index.duplicated().any(), 'DUPLICATE_UNIVERSE_KEY')
    require({'start_date','end_date'}.issubset(frame.columns), 'UNIVERSE_LIFECYCLE_MISSING')
    codes=list(frame.index)
    require(all(isinstance(c,str) and re.fullmatch(r'\d{6}\.(XSHG|XSHE)',c) for c in codes),'UNSUPPORTED_SECURITY_NAMESPACE')
    for _,r in frame.iterrows():
        require(checked_day(r['start_date'])<=day<=checked_day(r['end_date']), 'UNIVERSE_LIFECYCLE_MISMATCH')
    return sorted(codes)

def sessions(values, clock):
    ds=[checked_day(x) for x in values]
    require(ds==sorted(set(ds)) and all(LOWER<=x<=UPPER for x in ds),'INVALID_CALENDAR_RESPONSE')
    # Reviewed CN cash-market session boundary, not a supplier publication lag.
    return [d for d in ds if d>LOWER and (d<clock.date() or d==clock.date() and clock.timetz().replace(tzinfo=None)>=time(15,30))]

def pinned(root):
    result={}
    for rel,expected in PINNED.items():
        p=root/rel
        b=p.read_bytes()
        require(digest(b)==expected,'BASELINE_DRIFT_'+rel)
        result[rel]=json.loads(b)
    return result

def allowed_windows_path(text):
    value=text.removeprefix('\\\\?\\').casefold()
    return value.startswith(('e:\\blackbox\\','e:\\blackbox_engines\\'))

def require_allowed_read(physical):
    require(os.name!='nt' or allowed_windows_path(str(physical)), 'EXTERNAL_LINK_TARGET')

def coverage(paths, out, max_files=50000, max_depth=8):
    """Current registered product roots only; inspect true time axes, never infer dates from names."""
    import pandas as pd
    import pyarrow.parquet as pq
    seen_dirs=set();seen_files=set();records=[];maximum=LOWER
    def walk(p,depth):
        nonlocal maximum
        require(depth<=max_depth,'REGISTERED_ROOT_DEPTH_CAP')
        require(p.exists(),'REGISTERED_ROOT_MISSING')
        physical=p.resolve(strict=True)
        require_allowed_read(physical)
        ident=str(physical).casefold()
        require(ident not in seen_dirs,'REGISTERED_ROOT_CYCLE_OR_ALIAS')
        seen_dirs.add(ident)
        for child in sorted(p.iterdir(),key=lambda p:p.name):
            if child.is_dir():
                walk(child,depth+1)
                continue
            ext=child.suffix.lower()
            require(ext not in {'.csv','.feather','.h5','.hdf5','.pkl','.arrow'},'UNHANDLED_REGISTERED_DATA_FORMAT')
            if ext!='.parquet':continue
            cp=child.resolve(strict=True);key=str(cp).casefold()
            require_allowed_read(cp)
            if key in seen_files:continue
            seen_files.add(key)
            require(len(seen_files)<=max_files,'REGISTERED_FILE_CAP')
            before=child.stat()
            pf=pq.ParquetFile(child);names=pf.schema_arrow.names
            # This task concerns OHLCV only. Known non-price reference/NAV shapes are not price coverage.
            if not {'open','close'}.issubset(names):
                records.append({'path':str(child),'status':'NON_PRICE_SCHEMA','columns':names})
                continue
            axis=next((x for x in ['time','date','trade_date'] if x in names),None)
            require(axis is not None,'PRICE_DATE_AXIS_MISSING')
            require(not __import__('pyarrow').types.is_integer(pf.schema_arrow.field(axis).type),'NUMERIC_REGISTERED_DATE_AXIS')
            bounds=[];fallback=False
            for i in range(pf.metadata.num_row_groups):
                rg=pf.metadata.row_group(i)
                col=next((rg.column(j) for j in range(rg.num_columns) if rg.column(j).path_in_schema==axis),None)
                if not col or not col.statistics or not col.statistics.has_min_max:
                    fallback=True;break
                bounds.extend([checked_day(col.statistics.min),checked_day(col.statistics.max)])
            if fallback:
                require(before.st_size<=256*1024*1024,'DATE_COLUMN_FALLBACK_BYTE_CAP')
                vals=pf.read(columns=[axis]).column(0).to_pandas()
                require(len(vals)<=2000000,'DATE_COLUMN_ROW_CAP')
                bounds=[checked_day(x) for x in vals.dropna().unique()]
                require(len(vals)==vals.notna().sum(),'NULL_REGISTERED_DATE_AXIS')
            after=child.stat()
            require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'REGISTERED_FILE_DRIFT')
            if bounds:maximum=max(maximum,max(bounds))
            records.append({'path':str(child),'status':'PRICE_TIME_AXIS_READ','bytes':before.st_size,
               'mtime_ns':before.st_mtime_ns,'rows':pf.metadata.num_rows,'axis':axis,
               'min':str(min(bounds)) if bounds else None,'max':str(max(bounds)) if bounds else None,
               'date_column_fallback':fallback})
    # Duplicate registered logical paths can share real roots; collapse only that exact path identity.
    for p in paths:
        if str(p.resolve(strict=True)).casefold() not in seen_dirs:walk(p,0)
    put(out,{'records':records,'maximum_observed_date':str(maximum),'source_absence_claim':False,
             'policy':'Only sessions strictly later than every observed registered price axis; no historical hole backfill'})
    return maximum

def roots_for(root, baseline):
    raw=root/'数据/原始只读/JQData_9999_official_raw'
    clean=root/'数据/清洗成品/releases'
    cache=root/'数据/回测缓存/releases'
    cp=baseline['数据/清洗成品/CURRENT_CLEANING_RELEASE.json']
    kp=baseline['数据/回测缓存/CURRENT_CACHE_RELEASE.json']
    current_clean=clean/cp['release_id'];current_cache=cache/kp['cache_release_id']
    roots={p:[raw/s for s in RAW_RELS[p]] for p in RAW_RELS}
    # Bind the current sealed roots plus newer dated releases only; retained historical search is in EVIDENCE.json.
    for parent,current,rels,standard in [(clean,current_clean,CLEAN_RELS,True),(cache,current_cache,CACHE_RELS,False)]:
        releases=[current]
        for r in parent.iterdir():
            if not r.is_dir() or r==current:continue
            m=re.search(r'ASOF_(\d{8})',r.name)
            if m and m.group(1)>LOWER.strftime('%Y%m%d'):releases.append(r)
        require(len(releases)<=250,'NEWER_RELEASE_CAP')
        for product,names in rels.items():
            require(any((current/('standard' if standard else '')/n).exists() for n in names),'CURRENT_PRODUCT_ROOT_MISSING_'+product)
            for release in releases:
                for n in names:
                    p=release/('standard' if standard else '')/n
                    if p.exists():roots[product].append(p)
    side=root/'数据/原始只读/strategy_data_plane_additions'
    require(side.exists(),'REGISTERED_SIDE_PLANE_MISSING')
    # Price-shaped files anywhere in this already registered side-plane conservatively advance every cursor.
    for p in roots:roots[p].append(side)
    return roots

class Supplier:
    def __init__(self,jq,out,inherited=0):
        self.jq=jq;self.out=out;self.calls=0;self.start=None;self.last=None;self.inherited=inherited
    def quota(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            q=self.jq.get_query_count()
        require(isinstance(q,dict) and type(q.get('spare')) is int,'QUOTA_UNMEASURED')
        v=q['spare']
        if self.start is None:self.start=v
        if self.last is not None:require(v<=self.last,'QUOTA_RESET_OR_CONCURRENT_INCREASE')
        self.last=v
        require(self.inherited+self.start-v<=700000,'MEASURED_QUOTA_CEILING')
        return v
    def call(self,name,args):
        require(name in {'get_all_securities','get_price'},'ENDPOINT_NOT_ALLOWED')
        before=self.quota();used=self.inherited+self.start-before
        require(used+50000<=700000 and before>=50000,'QUOTA_RESERVE_STOP')
        self.calls+=1;require(self.calls<=2500,'CALL_CAP')
        request={'number':self.calls,'endpoint':name,'arguments':args,'started_at':now().isoformat(),
                 'quota_before':before,'namespace':'JQ_OFFICIAL_RAW','pagination':'nonpaged single-day finite code list; exact key reconciliation required'}
        put(self.out/f'request_{self.calls:04d}.json',request)
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                answer=getattr(self.jq,name)(**args)
            after=self.quota()
            put(self.out/f'response_{self.calls:04d}.json',{'finished_at':now().isoformat(),'quota_after':after,
                'quota_delta':before-after,'status':'RESPONSE_RECEIVED_NOT_YET_ACCEPTED'})
            return answer,self.calls
        except Exception as e:
            put(self.out/f'failure_{self.calls:04d}.json',{'type':type(e).__name__,'detail_redacted':True,'retry':False})
            raise

def login(jq,cred):
    # Existing locator and formats only. No credential/hash ever enters a receipt or exception.
    u=p=None;plain=[]
    for line in cred.read_text(encoding='utf-8-sig').strip().splitlines():
        if not line.strip():continue
        pair=re.split('[:：]',line,maxsplit=1)
        if len(pair)==1:plain.append(line.strip());continue
        k,v=pair[0].strip().lower(),pair[1].strip()
        if '账号' in k or 'user' in k:u=v
        if '密码' in k or 'pass' in k:p=v
    if not u and not p and len(plain)==2:u,p=plain
    require(bool(u and p),'CREDENTIAL_LOCATOR_UNUSABLE')
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        jq.auth(u,p)
    u=p=None;plain.clear()
    require(jq.is_auth(),'AUTH_NOT_ESTABLISHED')

def reuse_inputs(root):
    """Hash-bound read-only references. Never copy the retained source into R3."""
    import pandas as pd
    import pyarrow.parquet as pq
    source=root/'STAGING/BLACKBOX_RAW_NONE_INCREMENT_20261027_R1'
    pins=json.loads(Path(__file__).with_name('REUSE_PINS.json').read_text())['files']
    docs={};refs=[]
    for rel,expected in pins.items():
        path=source/rel
        require(not path.is_symlink(),'REUSED_SOURCE_LINK_DRIFT')
        b=path.read_bytes()
        require(digest(b)==expected,'REUSED_SOURCE_IDENTITY_DRIFT_'+rel)
        refs.append({'path':str(path),'bytes':len(b),'sha256':expected,'action':'READ_ONLY_REFERENCE_NOT_COPIED'})
        if path.suffix=='.json':docs[rel]=json.loads(b)
    prior=docs['RESULT.json']
    require(prior['supplier_calls']==3 and prior['quota_start']-prior['quota_last_measured']==INHERITED_SPEND,'INHERITED_QUOTA_MISMATCH')
    day=date(2026,9,28);u=docs['universes/stock_2026-09-28.json'];codes=u['codes']
    require(len(codes)==5222 and codes==sorted(set(codes)),'REUSED_UNIVERSE_INVALID')
    frame=pd.DataFrame({'start_date':[u['lifecycle'][c]['start_date'] for c in codes],
                        'end_date':[u['lifecycle'][c]['end_date'] for c in codes]},index=codes)
    require(universe(frame,day,8000)==codes,'REUSED_LIFECYCLE_INVALID')
    requested=docs['receipts/request_0003.json']['arguments']
    require(requested=={'security':codes[:80],'start_date':str(day),'end_date':str(day),'frequency':'daily',
            'fields':FIELDS,'skip_paused':False,'fill_paused':True,'fq':None,'panel':False},'REUSED_REQUEST_CONTRACT_DRIFT')
    raw=source/'raw/stock/2026-09-28_00000.parquet'
    require(raw.stat().st_size==15544,'REUSED_BATCH_LENGTH')
    stored=pd.read_parquet(raw)
    require(stored.shape==(80,14),'REUSED_BATCH_SHAPE')
    metadata=json.loads(pq.read_schema(raw).metadata[b'pandas'])
    code_meta=next(x for x in metadata['columns'] if x['name']=='code')
    require(code_meta['numpy_type']=='object','REUSED_CODE_SOURCE_METADATA')
    original=stored.copy(deep=True);original['code']=original['code'].astype(object)
    validate_code_column(original['code'],set(codes[:80]),'stock')
    serialization=verify_parquet_roundtrip(original,stored)
    _,quality=normalize(stored,codes[:80],day)
    calendar=docs['CALENDAR.json'];days=sessions(calendar['returned'],now())
    require(len(days)==17 and days[0]==day,'REUSED_CALENDAR_OR_COMPLETION_DRIFT')
    plan=docs['PLAN.json']
    for product in ['stock','etf','index']:
        require(plan['increment_days'][product]==list(map(str,days)),'REUSED_PLAN_DRIFT')
        require(docs[f'COVERAGE_{product}.json']['maximum_observed_date']=='2026-09-24','REUSED_COVERAGE_DRIFT')
    # Metadata freshness only for already registered paths: no repeat Parquet inventory.
    # A new data file/directory or changed existing price file is a blocker, never absence evidence.
    coverage_docs=[docs[f'COVERAGE_{k}.json'] for k in ['stock','etf','index']]
    freshness=check_registered_freshness(coverage_docs,root)
    return {'source_root':str(source),'references':refs,'calendar':calendar,'plan':plan,'stock_codes':codes,
       'retained_batch':{'path':str(raw),'bytes':15544,'sha256':pins['raw/stock/2026-09-28_00000.parquet'],
           'product':'stock','date':str(day),'codes':codes[:80],'quality':quality,'serialization':serialization,
           'original_dtype_evidence':'code reconstructed from retained pandas metadata, not a second supplier response'},
       'coverage_reused':True,'registered_freshness':freshness}

def load_slot_policy(root):
    """Package-pinned reviewer classifications, not discovery or supplier-absence policy."""
    policy=json.loads(Path(__file__).with_name('EMPTY_SLOT_POLICY.json').read_text())
    require(policy['schema']=='BLACKBOX_REVIEWED_EMPTY_SLOTS_R1','SLOT_POLICY_SCHEMA')
    require(policy['unknown_directory_action']=='BLOCK','SLOT_POLICY_UNKNOWN_ACTION')
    result={}
    for row in policy['slots']:
        rel=Path(row['relative_path'])
        require(not rel.is_absolute() and '..' not in rel.parts,'SLOT_POLICY_PATH')
        require(str(rel).replace('\\','/').startswith('数据/原始只读/JQData_9999_official_raw/'),'SLOT_POLICY_ROOT')
        path=root/rel
        require(path not in result,'SLOT_POLICY_DUPLICATE')
        require(row['classification'] in {'DECLARED_EMPTY_SLOT','REVIEWED_EMPTY_LAYOUT_SLOT'},'SLOT_POLICY_CLASS')
        result[path]=row
    require(len(result)==5,'SLOT_POLICY_COUNT')
    return result

def check_reviewed_empty_slot(path, policy):
    """Accept only an exact reviewed ordinary directory, still zero-entry including hidden."""
    require(path in policy,'REGISTERED_DIRECTORY_SET_UNPROVEN')
    row=policy[path]
    before=path.lstat()
    require(not path.is_symlink() and not getattr(path,'is_junction',lambda:False)()
            and not (getattr(before,'st_file_attributes',0)&0x400),'REVIEWED_SLOT_REPARSE_UNPROVEN')
    require(path.is_dir(),'REVIEWED_SLOT_NOT_DIRECTORY')
    require_allowed_read(path.resolve(strict=True))
    require(path.resolve(strict=True)==path.absolute(),'REVIEWED_SLOT_TARGET_DRIFT')
    with os.scandir(path) as scan:
        first=next(scan,None)
    require(first is None,'REVIEWED_SLOT_BECAME_NONEMPTY')
    after=path.lstat()
    ident=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,getattr(s,'st_file_attributes',0))
    require(ident(before)==ident(after),'REVIEWED_SLOT_CHANGED_DURING_CHECK')
    return {'path':str(path),'classification':row['classification'],'entries_including_hidden':0,
            'declaration_evidence':row['declaration_evidence'],'current_empty_evidence':row['current_empty_evidence'],
            'mtime_ns':after.st_mtime_ns,'ctime_ns':after.st_ctime_ns,
            'historical_creator_proven':False,'source_absence_claim':False}

def check_registered_freshness(documents, root=None):
    root=Path(r'E:\BLACKBOX') if root is None else root
    slot_policy=load_slot_policy(root)
    slot_receipts=[]
    records={}
    for doc in documents:
        for row in doc['records']:records.setdefault(row['path'],row)
    parents={};ancestors=set()
    for name in records:
        path=Path(name);parents.setdefault(path.parent,set()).add(path.name)
        ancestors.update(path.parents)
    for parent,expected in parents.items():
        require_allowed_read(parent.resolve(strict=True))
        children=list(parent.iterdir())
        require({c.name for c in children if c.suffix.lower()=='.parquet' and c.is_file()}==expected,
                'REGISTERED_FILE_SET_DRIFT')
        for child in children:
            if child.is_dir() and child not in ancestors:
                slot_receipts.append(check_reviewed_empty_slot(child,slot_policy))
        require(not any(c.suffix.lower() in {'.csv','.h5','.hdf5','.pkl','.arrow','.feather'} for c in children if c.is_file()),
                'REGISTERED_NEW_FORMAT_UNPROVEN')
    import pyarrow.parquet as pq
    for name,row in records.items():
        path=Path(name);require_allowed_read(path.resolve(strict=True))
        if row['status']=='PRICE_TIME_AXIS_READ':
            st=path.stat();require(st.st_size==row['bytes'] and st.st_mtime_ns==row['mtime_ns'],'REGISTERED_PRICE_FILE_DRIFT')
        else:
            require(pq.read_schema(path).names==row['columns'],'REGISTERED_NONPRICE_SCHEMA_DRIFT')
    return {'policy':'EXACT_REVIEWED_EMPTY_SLOTS_ONLY','slots':slot_receipts,
            'registered_files':len(records),'source_absence_claim':False}

def check_execution_location(root,out):
    require(platform.system()=='Windows' and platform.node().upper()=='ZHANGWEI','WRONG_HOST')
    require(root==Path(r'E:\BLACKBOX') and out==root/'STAGING'/OUTPUT_NAME,'WRONG_FIXED_PATH')

def run(root,out):
    check_execution_location(root,out)
    require(not out.exists(),'EXISTING_OUTPUT_NO_REPLAY')
    require(now()<=datetime(2026,10,28,23,59,tzinfo=CN),'CONTRACT_EXPIRED')
    out.mkdir(parents=True,exist_ok=False)
    supplier=None;baseline=None;result={'task_id':TASK,'host':'ZHANGWEI','order_allowed':False,
       'current_switch_allowed':False,'cleaning_allowed':False,'products':{},'status':'IN_PROGRESS'}
    try:
        import pandas as pd
        import pyarrow.parquet as pq
        baseline=pinned(root)
        put(out/'BASELINE.json',{'sha256':PINNED,'at':now().isoformat(),'values':baseline})
        reuse=reuse_inputs(root)
        put(out/'REUSE_MANIFEST.json',reuse)
        put(out/'PLAN.json',{'plan':reuse['plan'],'reuse_first_stock_batch':True,'inherited_quota_spent':INHERITED_SPEND,
             'cumulative_ceiling':700000,'r3_remaining_ceiling':700000-INHERITED_SPEND,
             'no_calendar_or_first_stock_universe_refetch':True})
        # Preserve actual local SDK source identity and signature before authentication.
        import jqdatasdk as jq
        sig=inspect.signature(jq.get_price)
        require(all(x in sig.parameters for x in ['skip_paused','fill_paused','fq','panel']),'SDK_SIGNATURE_UNSUPPORTED')
        require(sig.parameters['skip_paused'].default is False and sig.parameters['fill_paused'].default is True,'SDK_DEFAULT_DRIFT')
        src=Path(inspect.getsourcefile(inspect.unwrap(jq.get_price)))
        put(out/'SDK.json',{'version':getattr(jq,'__version__',None),'signature':str(sig),'source_sha256':digest(src.read_bytes()),
            'explicit_price_parameters':{'skip_paused':False,'fill_paused':True,'fq':None,'panel':False},
            'local_fill':False,'sdk_attempts':1,'timeout_seconds':45})
        jq.set_params(request_timeout=45,request_attempt_count=1,enable_auth_prompt=False)
        login(jq,root/'配置/secrets/已验证/聚宽账号.txt')
        supplier=Supplier(jq,out/'receipts',inherited=INHERITED_SPEND)
        supplier.quota()
        plan={k:[date.fromisoformat(d) for d in v] for k,v in reuse['plan']['increment_days'].items()}
        require(sum(len(v) for v in plan.values())<=75,'PRODUCT_DAY_CAP')
        for product in ['stock','etf','index']:
            accepted=[]
            if product=='stock':accepted.append({'date':'2026-09-28','batch':0,'raw':reuse['retained_batch'],
                'rows':80,'reused':True,'new_supplier_call':False})
            for day in plan[product]:
                pinned(root)
                if product=='index':codes=INDEX
                elif product=='stock' and day==date(2026,9,28):codes=reuse['stock_codes']
                else:
                    master,master_no=supplier.call('get_all_securities',{'types':[product],'date':str(day)})
                    codes=universe(master,day,8000 if product=='stock' else 4000)
                    put(out/'universes'/f'{product}_{day}.json',{'request':master_no,'date':str(day),'codes':codes,
                        'lifecycle':{str(c):{'start_date':str(master.loc[c,'start_date']),'end_date':str(master.loc[c,'end_date'])} for c in codes}})
                for start in range(0,len(codes),80):
                    if product=='stock' and day==date(2026,9,28) and start==0:continue
                    pinned(root)
                    chunk=codes[start:start+80]
                    args={'security':chunk,'start_date':str(day),'end_date':str(day),'frequency':'daily','fields':FIELDS,
                          'skip_paused':False,'fill_paused':True,'fq':None,'panel':False}
                    response,num=supplier.call('get_price',args)
                    batch=out/'raw'/product/f'{day}_{start:05d}_R4.parquet'
                    batch.parent.mkdir(parents=True,exist_ok=True)
                    require(not batch.exists(),'RAW_REPLAY_COLLISION')
                    # Preserve failed responses too: no normalization, no dedup, no fill before byte storage.
                    require(isinstance(response,pd.DataFrame),'NON_DATAFRAME_RESPONSE')
                    # Reject ambiguous identifiers before storing an accepted batch. Keep failure evidence separately.
                    try:
                        code_info=validate_code_column(response['code'],set(chunk),product)
                    except Exception as error:
                        failed=out/'rejected'/product/f'{day}_{start:05d}_R4.parquet'
                        failed.parent.mkdir(parents=True,exist_ok=True);response.to_parquet(failed,index=None)
                        put(out/'quality'/f'{product}_{day}_{start:05d}_FAILED.json',
                            {'request':num,'rejected_raw':str(failed),'error_type':type(error).__name__,
                             'reason':str(error) if isinstance(error,Blocked) else 'CODE_COLUMN_VALIDATION_FAILED'})
                        raise
                    response.to_parquet(batch,index=None)
                    rawbytes=batch.read_bytes()
                    reread=pd.read_parquet(batch)
                    serialization=verify_parquet_roundtrip(response,reread)
                    raw_identity={'path':str(batch),'bytes':len(rawbytes),'sha256':digest(rawbytes)}
                    try:
                        frame,quality=normalize(reread,chunk,day)
                    except Exception as error:
                        put(out/'quality'/f'{product}_{day}_{start:05d}_FAILED.json',{
                          'request':num,'raw':raw_identity,'status':'BLOCKED_PRESERVED','error_type':type(error).__name__,
                          'reason':str(error) if isinstance(error,Blocked) else 'VALUE_VALIDATION_FAILED',
                          'columns':list(map(str,reread.columns)),'rows':len(reread),
                          'returned_keys':reread[[c for c in ['time','code'] if c in reread]].astype(str).values.tolist()})
                        raise
                    receipt={'task_id':TASK,'product':product,'date':str(day),'request':num,'raw':raw_identity,
                      'supplier_response_available':True,'receipt_at':now().isoformat(),'quality':quality,
                      'fields_dictionary':'RAW_NONE_DAILY_12_R1','fq':None,'price_basis':'RAW_NONE',
                      'supplier_fill_paused':True,'local_fill':False,'serialization':serialization,'code_validation':code_info,
                      'cleaning':'NOT_RUN_PENDING_GPT_REVIEW',
                      'pit':'receipt_at is acquisition time only, not historical publication/PIT time',
                      'exhaustion':'all requested single-day keys returned exactly once; no invented page token'}
                    put(out/'quality'/f'{product}_{day}_{start:05d}.json',receipt)
                    accepted.append({'date':str(day),'batch':start,'request':num,'raw':raw_identity,'rows':len(frame)})
                daily=[b for b in accepted if b['date']==str(day)]
                put(out/'coverage'/f'{product}_{day}.json',{'product':product,'date':str(day),
                    'expected_codes':codes,'accepted_rows':sum(b['rows'] for b in daily),
                    'batches':daily,'status':'DAY_STAGED_UNREVIEWED','no_local_fill':True})
            result['products'][product]={'status':'STAGED_UNREVIEWED' if accepted else 'NO_FORWARD_INCREMENT_SELECTED','batches':accepted,
                'daily_coverage':[{ 'date':str(day),'rows':sum(b['rows'] for b in accepted if b['date']==str(day)),
                                  'batches':sum(1 for b in accepted if b['date']==str(day))} for day in plan[product]]}
        pinned(root)
        result['status']='STAGED_UNREVIEWED'
        result['supplier_calls']=supplier.calls
        result['quota_start']=supplier.start;result['quota_end']=supplier.quota()
        result['inherited_quota_spent']=INHERITED_SPEND
        result['cumulative_quota_spent']=INHERITED_SPEND+supplier.start-supplier.last
        put(out/'RESULT.json',result)
        return 0
    except Exception as e:
        result['status']='BLOCKED_PRESERVE_PARTIAL'
        result['error_type']=type(e).__name__
        result['reason']=str(e) if isinstance(e,Blocked) else 'REDACTED_EXCEPTION_NO_RETRY'
        result['supplier_calls']=supplier.calls if supplier else 0
        result['quota_start']=supplier.start if supplier else None
        result['quota_last_measured']=supplier.last if supplier else None
        result['inherited_quota_spent']=INHERITED_SPEND
        result['cumulative_quota_spent']=INHERITED_SPEND+supplier.start-supplier.last if supplier and supplier.start is not None else INHERITED_SPEND
        put(out/'RESULT.json',result)
        return 2

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true',required=True)
    args=parser.parse_args()
    return run(Path(r'E:\BLACKBOX'),Path(r'E:\BLACKBOX')/'STAGING'/OUTPUT_NAME)

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Blocked as e:
        print(json.dumps({'status':'PREFLIGHT_BLOCKED','reason':str(e),'order_allowed':False}))
        raise SystemExit(2)
