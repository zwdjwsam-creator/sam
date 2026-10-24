"""Reviewed leaf-function loader and ordered candidate read entry.

No production import at module load; no SDK, credential reads, or publisher writes.
This is a diagnostic candidate, never a full MASTER/engine admission certificate.
"""
import argparse
import ast
import base64
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import types
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from build_r09_control_successor import PINS, TARGETS, WORK, require

MANIFEST_SHA='89d2a903fe01701c43c6cf8a90906c096aede74db082012fb6bc31d31735787f'
INDEX_SHA='1c5b5d2b3d89c9001e23f5c221f27e2d27104fd27b77d78187abc5e85352f200'
BLOCK_SHA='1dd483be9df1fffddfe846c44cfec2a71f543ee2821aa087d73038534e0bfab3'
RULE_PINS={'VERTICAL_RULE':'2bc031a1abac3d62002d41d13e83e5adec4de910e1aca65068d1c133f6fefd78',
           'GOV_RULE':'a1dcbb86c5d0cabe69aaedcd379b1042a9a1681794efb93fb621d52bbbd078ac',
           'UNIFIED_ACQ_RULE':'adf4b9e19bad1992be420cc0fc7bd15e59c53b84fbfe4f20600b48497c0bb52b',
           'ERROR_LESSONS':'c85cd258383f56b3164ae7f935542fd0ee76acbb6630a7d687fe5b715a82fa01'}
HELPERS={'canonical_index_schema_r1.py':'38c0290e3c50313879924d0fd41866e62badeaa2066421647f3a9e305f6957cc',
         'r08_coverage_gate.py':'9d90046c252b7f4c08786906cd3a95d28a5b3099493e4cb1f0ca8931fae982af'}
DEFAULT_MANIFEST=WORK/'candidate_releases'/'R08'/'R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024'/'CANDIDATE_MANIFEST.json'
INDEX_PATH=Path(r'E:\BLACKBOX\数据\原始只读\strategy_data_plane_additions\INDEX_DAILY_RAW_FULL_HISTORY_R1\REL_INDEX_DAILY_FULL_HISTORY_R1_20260805_073123\RAW_FILES\index_daily__399303_XSHE__to_20260804.parquet')


def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def carrier(packet,key,sha):
    item=load_json(Path(packet)/(key+'.body.json'))
    data=base64.b64decode(item['payload_base64'],validate=True)
    require(hashlib.sha256(data).hexdigest()==sha==item['original_sha256'],'BODY_PIN_CHANGED:'+key)
    return data


def leaf(text,names,namespace=None,assignments=()):
    """Execute only the named, reviewed definitions and literal assignments.

    Top-level imports, calls, file writes, CLI and other definitions are excluded.
    Source hashes must have been checked by the caller. This is not a sandbox.
    """
    tree=ast.parse(text)
    nodes=[]
    found=set()
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names:
            nodes.append(node);found.add(node.name)
        elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in assignments:
            ast.literal_eval(node.value)
            nodes.append(node);found.add(node.targets[0].id)
    require(found==set(names)|set(assignments),'REVIEWED_DEFINITION_SET_CHANGED')
    module_name='_r09_reviewed_leaf_'+str(len(sys.modules))
    module=types.ModuleType(module_name)
    module.__dict__.update(globals());module.__dict__.update(namespace or {})
    module.__dict__['__name__']=module_name
    sys.modules[module_name]=module
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<reviewed-r09-leaves>','exec'),module.__dict__)
    return module.__dict__


def successor_text(root,key):
    manifest=load_json(Path(root)/'SUCCESSOR_BUILD_MANIFEST.json')
    require(manifest['source_pins']==PINS,'SUCCESSOR_SOURCE_SET_CHANGED')
    path=Path(root)/TARGETS[key]
    require(file_sha(path)==manifest['outputs'][path.name],'SUCCESSOR_OUTPUT_CHANGED:'+key)
    return path.read_text(encoding='utf-8')


def shadow_gate(root,packet):
    text=carrier(packet,'BLOCK_CODES',BLOCK_SHA).decode('utf-8-sig')
    codes=leaf(text,{'normalize_block_reason'},{},('BLOCK_REASON_CODES',))
    codes['CODE_SET']=set(codes['BLOCK_REASON_CODES'])
    return leaf(successor_text(root,'PRE_INGESTION_GATE'),{'AdmissionResult','PreIngestionGate'},
                {'normalize_block_reason':codes['normalize_block_reason']},
                ('ALLOWED_ROLES','FORBIDDEN_ROLES','REQUIRED_FIELDS'))


def fixture_payload():
    return dict(source_type='SYNTHETIC_TEST',release_id='R09_SYNTHETIC',manifest='fixture',fingerprint='fixture',
                dictionary_version='fixture_v1',asset_id='SYNTHETIC_A',domain='price',field='close',frequency='1d',
                timezone='Asia/Shanghai',price_basis='RAW_NONE',PIT_status='SYNTHETIC_NO_PIT_CLAIM',
                historical_backtest_eligible=False,factor_export_allowed=False,fixture_only=True,
                requested_engine_role='SYNTHETIC_FIXTURE',synthetic_data=True,PIT_claim_allowed=False,
                performance_claim_allowed=False,formal_result_allowed=False,live_usage_allowed=False,synthetic_value=1.)


def run_preflight(root):
    """Execute the patched known preflight, denying network and all file writes.

    Existing _base is resolved from the established script directory. Its import
    may fail under the guard; that is a STOP, never a reason to remove the guard.
    """
    path=Path(root)/TARGETS['PREFLIGHT']
    successor_text(root,'PREFLIGHT')
    child='''import sys,os,runpy
sys.dont_write_bytecode=True
def guard(event,args):
 if event in ('socket.connect','socket.connect_ex','socket.getaddrinfo','subprocess.Popen','os.system','os.remove','os.rename','os.mkdir','os.rmdir','os.truncate','os.link','os.symlink'):
  raise PermissionError('R09_PREFLIGHT_SIDE_EFFECT_BLOCKED:'+event)
 if event=='open':
  mode=args[1];flags=args[2] or 0
  if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
   raise PermissionError('R09_PREFLIGHT_WRITE_BLOCKED')
sys.addaudithook(guard)
sys.path.insert(0,sys.argv[2])
script=sys.argv[1];sys.argv=[script,'--task-class','CACHE','--json']
runpy.run_path(script,run_name='__main__')
'''
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
    result=subprocess.run([sys.executable,'-X','utf8','-c',child,str(path),r'E:\BLACKBOX\脚本'],
                          capture_output=True,text=True,encoding='utf-8',env=env,timeout=120)
    require(result.returncode==0,'MUST_READ_PREFLIGHT_FAILED:'+result.stderr[-500:])
    report=json.loads(result.stdout)
    require(report.get('ok') is True and report.get('required')==['BOOTSTRAP','DATA_ACCESS'],'CACHE_PREFLIGHT_NOT_VERIFIED')
    return report


def ordered_run(preflight,source_bind,read,negative_controls):
    """No downstream callback runs when an earlier stage rejects."""
    trace=[]
    a=preflight();require(a.get('ok') is True,'PREFLIGHT_NOT_PASS');trace.append('1_MUST_READ')
    b=source_bind();trace.append('2_PINNED_SOURCE_AND_RULE_BINDING')
    c=read(b);trace.append('3_BOUNDED_CANDIDATE_READ')
    d=negative_controls();trace.append('4_SHADOW_AND_PUBLISH_BLOCK_CONTROLS')
    return {'steps':trace,'preflight':a,'bounded_read':c,'controls':d,
            'FOUNDATION_ACCEPTANCE':False,'formal_backtest_active':False,
            'CURRENT_SWITCH_ALLOWED':False,'NEW_DATA_ACQUISITION_AUTHORIZED':False,
            'SOURCE_ABSENCE_CLAIMS':0,'ORDER_ALLOWED':False,
            'scope':'R09_ORDERED_DIAGNOSTIC_CANDIDATE; NOT_FULL_ENGINE_OR_LATEST_UPDATE_ACCEPTANCE'}


def desktop_run(packet,successor):
    import pandas as pd
    import pyarrow.parquet as pq
    for name,sha in HELPERS.items():
        require(file_sha(Path(__file__).with_name(name))==sha,'HELPER_PIN_CHANGED:'+name)
    from canonical_index_schema_r1 import normalize_canonical_index
    from r08_coverage_gate import compare
    def bind():
        require(file_sha(DEFAULT_MANIFEST)==MANIFEST_SHA,'R08_MANIFEST_CHANGED')
        body=load_json(DEFAULT_MANIFEST)
        pointers={p:s for p,s in body['source_pins'].items() if Path(p).name in ('CURRENT_CLEANING_RELEASE.json','CURRENT_CACHE_RELEASE.json')}
        require(len(pointers)==2,'CURRENT_PAIR_NOT_BOUND')
        for p,s in pointers.items():
            require(file_sha(p)==s,'CURRENT_CHANGED_BEFORE_READ')
        price=body['cache_overrides']['STOCK_DAILY_RAW_PIT_R1']['year=2026/part_2026.parquet']
        factor=next(x for x in body['r08_artifacts'] if x['product']=='STOCK_FACTOR_DAILY_R1')['path']
        wanted={price,factor}
        records={a['path']:a['sha256'] for a in body['artifacts']}
        require(wanted<=set(records),'UNPINNED_ARTIFACT')
        for p in wanted:
            require(file_sha(p)==records[p],'SELECTED_ARTIFACT_CHANGED')
        require(file_sha(INDEX_PATH)==INDEX_SHA,'INDEX_SOURCE_CHANGED')
        for key,sha in RULE_PINS.items():
            item=load_json(Path(packet)/(key+'.body.json'))
            raw=carrier(packet,key,sha)
            require(Path(item['original_path']).read_bytes()==raw,'APPLICABLE_RULE_CHANGED:'+key)
        return dict(price=price,factor=factor,pointers=pointers,artifacts={p:records[p] for p in wanted})
    def read(binding):
        def physical(path,cols):
            pf=pq.ParquetFile(path);require(pf.metadata.num_rows<=1100000,'BOUNDED_READ_ROW_LIMIT')
            return pf.read(columns=cols).to_pandas()
        a=physical(binding['price'],['date','code','close'])
        b=physical(binding['factor'],['date','code','close'])
        conservation=compare(a,b,('date','code'),('close',))
        require(conservation['coverage_non_regression_pass'],'R08_CANDIDATE_KEY_REGRESSION')
        target=pd.to_datetime(['2026-08-31','2026-09-01'])
        qa=a[(a['code']=='000001.XSHE') & a['date'].isin(target)].sort_values('date')
        qb=b[(b['code']=='000001.XSHE') & b['date'].isin(target)].sort_values('date')
        require(len(qa)==2 and qa['close'].notna().all(),'BOUNDED_REQUEST_NOT_SERVED')
        pd.testing.assert_frame_equal(qa.reset_index(drop=True),qb.reset_index(drop=True),check_dtype=False)
        ix=normalize_canonical_index(pq.ParquetFile(INDEX_PATH).read().to_pandas())
        require(len(ix)==5242 and int(ix['close'].notna().sum())==3004,'INDEX_BINDING_CHANGED')
        require(file_sha(INDEX_PATH)==INDEX_SHA,'INDEX_CHANGED_DURING_READ')
        for p,s in binding['pointers'].items():
            require(file_sha(p)==s,'CURRENT_CHANGED_DURING_READ')
        for p,s in binding['artifacts'].items():
            require(file_sha(p)==s,'ARTIFACT_CHANGED_DURING_READ')
        return dict(stock_request_rows=len(qa),stock_values=qa.to_dict('records'),
                    conservation=conservation,index_adapter_rows=len(ix),
                    index_diagnostic_only=True,index_master_admission=False,
                    calendar_asof='2026-09-24',latest_download_performed=False)
    def negative_controls():
        ns=shadow_gate(successor,packet)
        gate=ns['PreIngestionGate']({'close'},{'1d'},{'stock'},{'fixture_v1'})
        payload=fixture_payload();ticket=gate.validate(payload)
        require(ticket.allowed,'SYNTHETIC_CONTROL_REJECTED')
        gate.parse_after_gate(ticket,payload)
        real=dict(payload,requested_engine_role='REAL_MARKET_DATA')
        denied=gate.validate(real);require(not denied.allowed,'REAL_DATA_ROLE_OPENED')
        pub=leaf(successor_text(successor,'PUBLISH_GATE'),{'publish_atomic'},
                 {'run_production_matrix':lambda *a:(_ for _ in ()).throw(AssertionError('LIVE_MATRIX_CALLED'))})
        blocked=pub['publish_atomic'](cache_pointer={},cache_root=Path('.'),facts={},target='2026-09-24',cleaning_pointer=None,dry_run=False)
        require(blocked.get('published') is False and blocked.get('CURRENT_PUBLISH')=='FORBIDDEN','LIVE_PUBLISH_NOT_BLOCKED')
        return dict(synthetic_parse_calls=gate._parse_calls,real_role_reason=denied.block_reason_code,
                    live_publish_reason=blocked['reason'],supplier_calls=0)
    return ordered_run(lambda:run_preflight(successor),bind,read,negative_controls)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--packet',required=True);ap.add_argument('--successor',required=True)
    args=ap.parse_args();sys.dont_write_bytecode=True
    def no_network(event,args):
        if event in ('socket.connect','socket.connect_ex','socket.getaddrinfo'):
            raise PermissionError('R09_NETWORK_FORBIDDEN')
    sys.addaudithook(no_network)
    try:
        result=desktop_run(args.packet,args.successor)
        print(json.dumps(dict(status='ORDERED_CANDIDATE_CHECK_COMPLETE',**result),default=str,ensure_ascii=True))
    except Exception as exc:
        print(json.dumps(dict(status='STOP',error=type(exc).__name__,reason=str(exc),FOUNDATION_ACCEPTANCE=False,ORDER_ALLOWED=False),ensure_ascii=True))
        raise SystemExit(3)
