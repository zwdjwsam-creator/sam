"""Bounded source-batch versus registered Cleaning comparison, read-only."""
import base64
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
sys.dont_write_bytecode = True
import pandas as pd
import pyarrow.parquet as pq
from r10_factor_input_contract import flatten_factor, require
from r10_factor_desktop_check import WORK, pinned_bytes, no_side_effects, FALSE_FLAGS
from r10_factor_reconcile import read_snapshot, sha, compare_shared
CONTEXT = {}


def validate_batch(frame, meta, year, batch, requested):
    require(meta.get('year') == year and meta.get('batch') == batch and meta.get('fq') == 'pre',
            'SOURCE_SIDECAR_IDENTITY_CONFLICT')
    require(meta.get('n_codes_requested') == requested, 'REQUESTED_BATCH_SIZE_CONFLICT')
    require(set(['date','code','factor']).issubset(frame.columns), 'SOURCE_FIELDS_NOT_BOUND')
    require(meta.get('rows') == len(frame), 'SIDECAR_ROW_COUNT_CONFLICT')
    if frame.empty:
        require(meta.get('n_codes') == 0 and meta.get('date_min') is None and meta.get('date_max') is None,
                'EMPTY_BATCH_SIDECAR_CONFLICT')
        return frame[['date','code','factor']].copy()
    out = flatten_factor(frame)
    require(out.date.dt.year.eq(year).all() and out.date.le('2026-08-14').all(),
            'SOURCE_REQUEST_DATE_RANGE_CONFLICT')
    require(out.code.nunique() <= requested and meta.get('n_codes') == out.code.nunique(),
            'SIDECAR_CODE_COUNT_CONFLICT')
    require(meta.get('date_min') == out.date.min().date().isoformat() and
            meta.get('date_max') == out.date.max().date().isoformat(), 'SIDECAR_DATE_BOUND_CONFLICT')
    return out


def merge_batches(frames):
    nonempty = [x for x in frames if len(x)]
    require(bool(nonempty), 'ALL_YEAR_BATCHES_EMPTY')
    # Never pick the last file when batches overlap, even for identical values.
    return flatten_factor(pd.concat(nonempty, ignore_index=True))


def desktop():
    require(os.name == 'nt' and socket.gethostname().upper() == 'ZHANGWEI', 'WRONG_EXECUTION_HOST')
    require(Path(sys.executable).resolve() == (WORK/'runtime/.venv/Scripts/python.exe').resolve(), 'WRONG_RUNTIME')
    here = Path(__file__).parent
    pkg = json.loads((here/'PACKAGE.json').read_text(encoding='utf-8'))
    for item in pkg['files']:
        require(len(pinned_bytes(here/item['path'], item['sha256'])) == item['bytes'], 'PACKAGE_SIZE_CHANGED')
    spec = json.loads((here/'INPUTS.json').read_text(encoding='utf-8'))
    entry = WORK/'reviews/R10/operating_entry/blackbox_operate_r10.py'
    pinned_bytes(entry,'1b04bb3a373e2a4276563c62c2514905dde49910f69e519e8b3626090ef18ec9')
    argv = [sys.executable,'-X','utf8',str(entry),'describe','--product','ADJUST_FACTOR_PIT_R1']
    env = os.environ.copy(); env.update(PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.run(argv,cwd=WORK,env=env,capture_output=True,timeout=60)
    capture = {'argv':argv,'exit_code':p.returncode,'stdout_base64':base64.b64encode(p.stdout).decode(),
               'stderr_base64':base64.b64encode(p.stderr).decode()}
    require(p.returncode == 0,'REAL_PREFLIGHT_COMMAND_FAILED')
    pf = json.loads(p.stdout.decode('utf-8-sig')).get('real_preflight',{})
    require(pf.get('ok') is True and pf.get('MUST_READ_PRECHECK') == 'PASS','REAL_PREFLIGHT_NOT_PASS')
    sys.addaudithook(no_side_effects)
    pins=[]
    def read(path, expected=None):
        CONTEXT.update(step='READ_DECLARED_FILE', path=str(path))
        b=read_snapshot(path,expected);pins.append((path,sha(b)));return b
    # Source generator identity is already measured and verified in the preceding delivery.
    read(Path(spec['generator']['path']),spec['generator']['sha256'])
    staging=Path(spec['staging']);root=staging/'source_batches'
    ub=read(staging/'UNIVERSE.json');u=json.loads(ub.decode('utf-8-sig'))
    require(u.get('start')=='2014-01-01' and u.get('end')=='2026-08-14' and
            u.get('fq')=='pre' and u.get('batch')==400 and type(u.get('n')) is int and
            4000<=u['n']<=20000,'STAGING_UNIVERSE_SPEC_UNBOUND')
    batches=(u['n']+399)//400
    state_bytes=read(staging/'DOWNLOAD_STATE.json');state=json.loads(state_bytes.decode('utf-8-sig'))
    require(state.get('start')=='2014-01-01' and state.get('end')=='2026-08-14' and
            state.get('fq')=='pre','DOWNLOAD_STATE_SPEC_CONFLICT')
    wanted_years={f'year={y}' for y in range(2014,2027)}
    CONTEXT.update(step='CHECK_SOURCE_YEAR_LAYOUT', path=str(root))
    require(root.is_dir(),'DECLARED_BATCH_DIRECTORY_NOT_PRESENT')
    observed_years={x.name for x in root.iterdir()}
    CONTEXT.update(missing=sorted(wanted_years-observed_years),unexpected=sorted(observed_years-wanted_years)[:100])
    require(observed_years==wanted_years,'SOURCE_YEAR_LAYOUT_UNBOUND')
    observations=[];year_results=[]
    for clean_pin in spec['clean']:
        year=clean_pin['year'];ydir=root/f'year={year}'
        wanted={name for i in range(batches) for name in
                (f'batch_{i:03d}.parquet',f'batch_{i:03d}.sidecar.json')}
        CONTEXT.clear();CONTEXT.update(step='CHECK_YEAR_BATCH_LAYOUT',path=str(ydir))
        observed_names={x.name for x in ydir.iterdir()}
        CONTEXT.update(missing=sorted(wanted-observed_names)[:100],unexpected=sorted(observed_names-wanted)[:100])
        require(observed_names==wanted,'SOURCE_BATCH_LAYOUT_UNBOUND')
        frames=[]
        for batch in range(batches):
            path=ydir/f'batch_{batch:03d}.parquet';meta_path=path.with_suffix('.sidecar.json')
            data=read(path);meta_bytes=read(meta_path);meta=json.loads(meta_bytes.decode('utf-8-sig'))
            parquet=pq.ParquetFile(io.BytesIO(data))
            require(parquet.metadata.num_rows<=2500000,'SOURCE_BATCH_ROW_CAP')
            raw=parquet.read(columns=['date','code','factor']).to_pandas()
            requested=min(400,u['n']-batch*400)
            out=validate_batch(raw,meta,year,batch,requested);frames.append(out)
            observations.append({'path':str(path),'sha256':sha(data),'bytes':len(data),'rows':len(out),
                'empty':out.empty,'sidecar_path':str(meta_path),'sidecar_sha256':sha(meta_bytes),
                'identity':'NEW_MEASURED_NOT_ADMITTED'})
        source=merge_batches(frames)
        clean_bytes=read(Path(clean_pin['path']),clean_pin['sha256'])
        clean=flatten_factor(pq.ParquetFile(io.BytesIO(clean_bytes)).read(columns=['date','code','factor']).to_pandas())
        comparison=compare_shared(source,clean)
        year_results.append({'year':year,'source_rows':len(source),'clean_rows':len(clean),
            'source_only_keys':comparison['clean_only'],'clean_only_keys':comparison['cache_only'],
            'shared_keys':comparison['shared'],'unequal_shared_values':comparison['unequal_values_on_shared_keys'],
            'unequal_sample':comparison['unequal_sample'],'clean_sha256':clean_pin['sha256']})
    for path,pin in pins:read_snapshot(path,pin)
    return {'status':'DECLARED_SOURCE_BATCH_CHAIN_MEASURED','preflight':capture,'real_preflight':pf,
        'source_root':str(root),'source_scope_end':'2026-08-14','batch_count_per_year':batches,
        'universe_metadata':u,'download_state_metadata':state,'batch_observations':observations,
        'year_results':year_results,'source_files_changed':False,'supplier_calls':0,
        'all_layer_search_performed':False,'B1_CLOSED':False,
        'interpretation':'Source/sidecar to Cleaning content comparison only. Aggregate or key equality does not independently prove supplier execution, expected market universe, later-date coverage or PIT authority.',**FALSE_FLAGS}


if __name__=='__main__':
    if sys.argv[1:]!=['--desktop-check']:raise SystemExit('ONLY --desktop-check IS SUPPORTED')
    try:
        print(json.dumps(desktop(),ensure_ascii=True,allow_nan=False))
    except Exception as exc:
        print(json.dumps({'status':'STOP','reason':str(exc) if isinstance(exc,ValueError) else type(exc).__name__,'context':CONTEXT,**FALSE_FLAGS}))
        raise SystemExit(3)
