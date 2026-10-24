"""Negative controls against exact R08 originals and their R09 successors.

Only stdlib and reviewed leaf definitions are executed. No production imports.
"""
import argparse
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch
from contextlib import ExitStack

from build_r09_control_successor import build,PINS,TARGETS,read_packet
from r09_control_runtime import leaf,shadow_gate,fixture_payload,successor_text,ordered_run


def reject(fn,reason):
    try:
        fn()
    except (ValueError,RuntimeError) as exc:
        assert reason in str(exc),str(exc)
    else:
        raise AssertionError('UNEXPECTED_PASS:'+reason)


def capability(text):
    contracts={'products':{'P':{'aliases':[]}}}
    vocab={'REQUEST_READINESS':['AVAILABLE_FORMAL','AVAILABLE_FORMAL_WITH_DECLARED_GAP','NO_CACHE_REQUIRED_FORMAL_ROUTE','UNRESOLVED'],
           'SOURCE_STATE':['WINDOW_PRESENT'],'PROCESSING_STATE':['PROCESSED'],'AUTHORITY_STATE':['WINDOW_MOUNTED'],
           'GAP_CLASSIFICATION':['NONE','AUTHORITY_DECLARED_GAP']}
    ns=leaf(text,{'canonicalize_request','request_fingerprint','_window_covered','_parse_iso','evaluate_causal','derive_request_readiness','compute_capability'},
            {'_load_json':lambda p:contracts if p=='contracts' else vocab,'CONTRACTS_PATH':'contracts','VOCAB_PATH':'vocab'},('REQUEST_KEYS',))
    return ns


def preflight(text,root,manifest,argv=()):
    pack=root/'pack';pack.mkdir(exist_ok=True)
    # Fixture files only. No real BLACKBOX Manifest or BOOTSTRAP is ever edited.
    names={'BOOTSTRAP':'BLACKBOX_BOOTSTRAP_MUST_READ.md','DATA_ACCESS':'BLACKBOX_DATA_ACCESS_MUST_READ.md'}
    for name in names.values():
        (pack/name).write_text('rule\n',encoding='utf-8')
    kernel=root/'kernel';kernel.write_text('kernel\n',encoding='utf-8')
    mp=root/'manifest.json';mp.write_text(json.dumps(manifest),encoding='utf-8')
    def forbid(*a,**kw):
        raise AssertionError('PREFLIGHT_UNEXPECTED_WRITE')
    ns=leaf(text,{'_parse_classes','_required_keys','_meta','main'},
            {'ROOT':root,'PACK_DIR':pack,'MANIFEST_PATH':mp,'KERNEL_PATH':kernel,
             'set_runtime_context':lambda **kw:None,'OK':0,'FAIL':3,'argparse':argparse,
             'read_text':lambda p:Path(p).read_text(encoding='utf-8'),
             'sha256_text':lambda x:hashlib.sha256(x.encode('utf-8')).hexdigest(),'write_text':forbid},
            ('DEFAULT_BUDGETS','CLASS_ALIASES','FILE_KEYS'))
    with patch.object(sys,'argv',['preflight','--task-class','CACHE','--json',*argv]),contextlib.redirect_stdout(io.StringIO()) as out:
        code=ns['main']()
    return code,out.getvalue()


def main(packet):
    controls=[]
    def passed(name):controls.append(name)
    req=dict(PRODUCT_ID='P',REQUEST_START_DATE='2026-09-01',REQUEST_END_DATE='2026-09-01',FREQUENCY='1d',
             UNIVERSE='A_SHARE',REQUIRED_FIELDS=['close'],USAGE_MODE='BACKTEST_SIGNAL_AND_FILL',
             CAUSAL_MODE='PREVIOUS_DAY_CAUSAL',SIGNAL_TIME='2026-09-02T09:00:00+08:00')
    facts=dict(SYSTEM_GENERATION_ID='G',AUTHORITY_STATE='WINDOW_MOUNTED',SOURCE_STATE='WINDOW_PRESENT',
               PROCESSING_STATE='PROCESSED',FORMAL_COVERAGE_MIN='2026-09-01',FORMAL_COVERAGE_MAX='2026-09-01',
               REQUIRED_FIELDS_OK=True,KNOWN_AT='2026-09-01T15:00:00+08:00')
    with tempfile.TemporaryDirectory(prefix='r09_controls_') as td:
        root=Path(td);dest=root/'successor'
        assert build(packet,dest)['status']=='CONTROL_SUCCESSOR_BUILT';passed('source-pinned four-module build')
        assert build(packet,dest)['status']=='ALREADY_BUILT_VERIFIED';passed('unchanged replay')
        partial=root/'partial';partial.mkdir()
        reject(lambda:build(packet,partial),'PARTIAL_SUCCESSOR');passed('partial successor preserved')
        target=dest/TARGETS['REQ_CAPABILITY'];saved=target.read_bytes();target.write_bytes(saved+b'\n')
        reject(lambda:build(packet,dest),'REPLAY_PATCH_CHANGED');target.write_bytes(saved);passed('tampered successor rejected')
        original=capability(read_packet(packet,'REQ_CAPABILITY').decode('utf-8-sig'))
        fixed=capability(successor_text(dest,'REQ_CAPABILITY'))
        assert original['compute_capability'](req,{k:v for k,v in facts.items() if k!='REQUIRED_FIELDS_OK'})['TASK_DATA_GATE']=='PASS'
        passed('original missing-field permissiveness reproduced')
        assert fixed['compute_capability'](req,facts)['TASK_DATA_GATE']=='PASS';passed('evidenced positive request retained')
        for variant in ('plain','declared_gap','alternate'):
            f=copy.deepcopy(facts)
            if variant=='declared_gap':f.update(DECLARED_GAPS=['2026-09-01'],GAP_CLASSIFICATION='AUTHORITY_DECLARED_GAP')
            if variant=='alternate':f.update(NO_CACHE_REQUIRED=True,FORMAL_ALTERNATE_ROUTE=True)
            for value in (None,False,'false'):
                f['REQUIRED_FIELDS_OK']=value
                assert fixed['compute_capability'](req,f)['TASK_DATA_GATE']=='FAIL_CLOSED'
            passed('strict required-field evidence blocks '+variant)
        for r,f,reason in [({**req,'SIGNAL_TIME':None},facts,'SIGNAL_TIME_REQUIRED'),
                            (req,{k:v for k,v in facts.items() if k!='KNOWN_AT'},'KNOWN_AT_EVIDENCE_REQUIRED'),
                            ({**req,'SIGNAL_TIME':'2026-09-02T09:00:00'},facts,'EXPLICIT_TIMEZONE_REQUIRED'),
                            (req,{**facts,'KNOWN_AT':'2026-09-01T15:00:00'},'EXPLICIT_TIMEZONE_REQUIRED'),
                            (req,{**facts,'KNOWN_AT':'bad'},'INVALID_CAUSAL_TIMESTAMP'),
                            ({**req,'SIGNAL_TIME':'2026-09-01T10:00:00+08:00'},facts,'SIGNAL_BEFORE_KNOWN_AT')]:
            v=fixed['compute_capability'](r,f);assert v['TASK_DATA_GATE']=='FAIL_CLOSED' and reason in v['CAUSAL_DETAIL']['reason'];passed(reason)
        assert fixed['compute_capability']({**req,'SYSTEM_GENERATION_ID':'OTHER'},facts)['TASK_DATA_GATE']=='FAIL_CLOSED';passed('generation mismatch retained')
        pref=successor_text(dest,'PREFLIGHT')
        sha=lambda x:hashlib.sha256(x.encode('utf-8')).hexdigest()
        man={'files':{k:{'sha256':sha('rule\n')} for k in ('BOOTSTRAP','DATA_ACCESS')},'kernel':{'sha256':sha('kernel\n')}}
        assert preflight(pref,root,man)[0]==0;passed('valid preflight retained')
        for label in ('BOOTSTRAP','DATA_ACCESS','KERNEL'):
            m=copy.deepcopy(man)
            (m['kernel'] if label=='KERNEL' else m['files'][label]).pop('sha256')
            rc,out=preflight(pref,root,m);assert rc==3 and 'SHA_AUTHORITY_MISSING' in out;passed('missing SHA blocks '+label)
        for bad in (None,'x'*64,'0'*63):
            m=copy.deepcopy(man);m['kernel']['sha256']=bad
            assert preflight(pref,root,m)[0]==3
        passed('malformed hash authority rejected')
        for arg in ('--acceptance','--write-manifest'):
            rc,out=preflight(pref,root,man,[arg]);assert rc==3 and 'READONLY_PREFLIGHT_ONLY' in out;passed('mutating option denied '+arg)
        ns=shadow_gate(dest,packet)
        def gate():return ns['PreIngestionGate']({'close'},{'1d'},{'stock'},{'fixture_v1'})
        p=fixture_payload();g=gate();a=g.validate(p);assert a.allowed
        assert g.parse_after_gate(a,p)['value']==1.;passed('bound synthetic fixture parses once')
        reject(lambda:g.parse_after_gate(a,p),'CURRENT_ADMISSION');passed('ticket replay rejected')
        g=gate();a=g.validate(p)
        reject(lambda:g.parse_after_gate(a,{**p,'synthetic_value':2.}),'PAYLOAD_CHANGED');assert g._parse_calls==0;passed('post-admission payload replacement rejected')
        g=gate();a=g.validate(p);denied=g.validate({})
        assert not denied.allowed
        reject(lambda:g.parse_after_gate(a,p),'CURRENT_ADMISSION');passed('failed validation invalidates previous ticket')
        g=gate();forged=ns['AdmissionResult'](True,None)
        reject(lambda:g.parse_after_gate(forged,p),'CURRENT_ADMISSION');passed('forged allowed result rejected')
        for role in sorted(ns['FORBIDDEN_ROLES']):
            g=gate();g.real_data_authorized=True;a=g.validate({**p,'requested_engine_role':role})
            assert not a.allowed and g._parse_calls==g._write_calls==0
        passed('all seven real roles remain forbidden even with real-data flag')
        calls=[]
        pub=leaf(successor_text(dest,'PUBLISH_GATE'),{'publish_atomic'},
                 {'run_production_matrix':lambda *a:calls.append('matrix') or {'CURRENT_PUBLISH':'ALLOWED','OPERATIONAL_READINESS':'PASS'},
                  'wjson':lambda *a:calls.append('WRITE'), 'refresh_scope_from_live':lambda:calls.append('REFRESH')})
        base=dict(cache_pointer={'release_root':str(root/'cache'),'cache_release_id':'G','source_cleaning_release':'C'},
                  cache_root=root/'cache',facts={'SYSTEM_GENERATION_ID':'G'},target='2026-09-01',cleaning_pointer={'release_id':'C'},dry_run=True)
        dry=pub['publish_atomic'](**base)
        assert dry['published'] is False and dry['CURRENT_PUBLISH']=='FORBIDDEN' and dry['CANDIDATE_MATRIX_RESULT']=='ALLOWED' and calls==['matrix'];passed('matching pair dry-run only')
        for delta,reason in [({'dry_run':False},'R09_SUCCESSOR_DRY_RUN_ONLY'),
                             ({'cache_root':root/'other'},'CACHE_ROOT_IDENTITY_MISMATCH'),
                             ({'cleaning_pointer':{'release_id':'OTHER'}},'CLEANING_CACHE_PAIR_MISMATCH'),
                             ({'facts':{'SYSTEM_GENERATION_ID':'OTHER'}},'CAPABILITY_FACTS_GENERATION_STALE')]:
            calls.clear();out=pub['publish_atomic'](**{**base,**delta})
            assert reason==out['reason'] and out['CURRENT_PUBLISH']=='FORBIDDEN' and not calls;passed(reason)
        calls.clear()
        trace=[]
        fail=lambda:(_ for _ in ()).throw(ValueError('STOP'))
        reject(lambda:ordered_run(fail,lambda:trace.append('bind'),lambda b:trace.append('read'),lambda:trace.append('controls')),'STOP')
        assert not trace;passed('failed preflight prevents bind, parse and publisher')
        result=ordered_run(lambda:{'ok':True},lambda:trace.append('bind') or {},lambda b:trace.append('read') or {},lambda:trace.append('controls') or {})
        assert trace==['bind','read','controls'] and not result['FOUNDATION_ACCEPTANCE'];passed('ordered four-stage entry with limited acceptance')
        # Real Parquet paths through the desktop entry; all sources are synthetic.
        import pandas as pd
        import r09_control_runtime as runtime
        stock=pd.DataFrame({'date':pd.to_datetime(['2026-08-31','2026-09-01']),
                            'code':['000001.XSHE']*2,'close':[10.,11.]})
        price=root/'price.parquet';factor=root/'factor.parquet'
        stock.to_parquet(price,index=False);stock.to_parquet(factor,index=False)
        ix=pd.DataFrame({'trade_date':pd.date_range('2010-01-01',periods=5242),'canonical_code':['399303.XSHE']*5242,
                         'price_variant':['PRICE_INDEX']*5242,'return_variant':['PRICE']*5242,'source_fq':['NOT_APPLICABLE']*5242})
        for col in ('open','high','low','close','pre_close','volume','amount'):
            ix[col]=[1.]*3004+[float('nan')]*(5242-3004)
        index=root/'index.parquet';ix.to_parquet(index,index=False)
        pair=[root/'CURRENT_CACHE_RELEASE.json',root/'CURRENT_CLEANING_RELEASE.json']
        for p in pair:p.write_text('{}',encoding='utf-8')
        manifest=root/'candidate.json'
        manifest.write_text(json.dumps({'source_pins':{str(p):runtime.file_sha(p) for p in pair},
                  'cache_overrides':{'STOCK_DAILY_RAW_PIT_R1':{'year=2026/part_2026.parquet':str(price)}},
                  'r08_artifacts':[{'product':'STOCK_FACTOR_DAILY_R1','path':str(factor)}],
                  'artifacts':[{'path':str(p),'sha256':runtime.file_sha(p)} for p in (price,factor)]}),encoding='utf-8')
        with ExitStack() as stack:
            for name,value in {'DEFAULT_MANIFEST':manifest,'MANIFEST_SHA':runtime.file_sha(manifest),
                               'INDEX_PATH':index,'INDEX_SHA':runtime.file_sha(index),'RULE_PINS':{},
                               'run_preflight':lambda p:{'ok':True}}.items():
                stack.enter_context(patch.object(runtime,name,value))
            result=runtime.desktop_run(packet,dest)
            assert result['bounded_read']['stock_request_rows']==2 and len(result['steps'])==4
            assert result['controls']['synthetic_parse_calls']==1 and not result['FOUNDATION_ACCEPTANCE']
            passed('actual Arrow ordered-entry positive read with scoped claims')
            price.write_bytes(price.read_bytes()+b'x')
            reject(lambda:runtime.desktop_run(packet,dest),'SELECTED_ARTIFACT_CHANGED')
            passed('ordered entry rejects changed Parquet before parsing')
    print(json.dumps({'status':'PASS','controls_passed':len(controls),'controls':controls,'scope':'OFFLINE_CONTROLS_ONLY',
                      'supplier_calls':0,'production_writes':0,'FOUNDATION_ACCEPTANCE':False},ensure_ascii=True))


if __name__=='__main__':
    main(Path(sys.argv[1]))
