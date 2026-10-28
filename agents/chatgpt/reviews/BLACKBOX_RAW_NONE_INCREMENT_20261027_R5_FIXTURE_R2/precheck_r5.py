"""Run the exact original host preflight, then the complete package suite.

No SDK import, no auth, no credential read, no E: output, no source rewrite.
"""
from __future__ import annotations
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import acquire_daily as a

TASK='BLACKBOX_RAW_NONE_INCREMENT_20261027_R5_ISOLATE_RESUME'
CONTROL=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_R5_ISOLATE_RESUME_FIXTURE_R2_20261028')

def write_exact(path,data):
    with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    a.require(path.read_bytes()==data,'CONTROL_READBACK')
    return {'path':str(path),'bytes':len(data),'sha256':a.digest(data)}

def rule_binding(root):
    pins=json.loads(Path(__file__).with_name('RULE_PINS.json').read_bytes())['files'];rows=[]
    for rel,pin in pins.items():
        p=root/rel;b=p.read_bytes()
        if pin['hash_mode']=='RAW_BYTES':value=b
        else:value=b.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n').encode()
        a.require(a.digest(value)==pin['sha256'],'RULE_IDENTITY_DRIFT_'+rel)
        if 'bytes' in pin:a.require(len(b)==pin['bytes'],'RULE_BYTE_DRIFT_'+rel)
        rows.append({'relative_path':rel,'raw_bytes':len(b),'raw_sha256':a.digest(b),
                    'binding_sha256':a.digest(value),'hash_mode':pin['hash_mode']})
    return rows

def verify_package():
    root=Path(__file__).parent
    manifest=json.loads((root/'PACKAGE.json').read_bytes())
    for name,pin in manifest['files'].items():
        a.require(Path(name).name==name,'PACKAGE_PATH')
        b=(root/name).read_bytes();a.require(len(b)==pin['bytes'] and a.digest(b)==pin['sha256'],'PACKAGE_IDENTITY_'+name)
    return a.digest((root/'PACKAGE.json').read_bytes())

def verify_preflight_stdout(data):
    text=data.decode('utf-8-sig')
    for token in ['MUST_READ_PRECHECK = PASS','TASK_CLASS = ACQUISITION','KERNEL_STATUS = VERIFIED',
                  'AUTHORITY_READY = YES','TASK_EXECUTION = ALLOWED','TASK_EXECUTION_FORBIDDEN = FALSE']:
        a.require(token in text,'NATIVE_PREFLIGHT_NOT_PASS')
    a.require(text.count('status = VERIFIED')==3,'NATIVE_REQUIRED_RULE_COUNT')
    # Exact Manifest/rule bodies are bound separately; HAND_READ is a fixed informational line.
    return text

def verify_tests(data,expected):
    text=data.decode('utf-8-sig');matches=re.findall(r'^Ran (\d+) tests? in ',text,re.M)
    a.require(matches==[str(expected)],'TEST_COUNT_MISMATCH')
    a.require(re.search(r'^OK\s*$',text,re.M) is not None,'TEST_SUITE_NOT_OK')
    a.require(not re.search(r'^(FAILED|ERROR:|FAIL:)|\bskipped\b',text,re.M|re.I),'TEST_FAILURE_OR_SKIP')

def validate_gate(control):
    root=Path(r'E:\BLACKBOX');package_sha=verify_package();rules=rule_binding(root)
    data=(control/'GATE_R5.json').read_bytes();gate=json.loads(data)
    a.require(gate['task_id']==TASK and gate['package_sha256']==package_sha,'GATE_IDENTITY')
    manifest=json.loads(Path(__file__).with_name('PACKAGE.json').read_bytes())
    a.require(gate['expected_tests']==manifest['expected_tests'],'GATE_TEST_REQUIREMENT_CHANGED')
    at=datetime.fromisoformat(gate['finished_at'])
    a.require(timedelta(0)<=a.now()-at<=timedelta(hours=6),'GATE_STALE')
    a.require(gate['rule_bindings']==rules,'GATE_RULE_DRIFT')
    for phase in ['preflight','tests']:
        run=gate[phase];a.require(run['actual_os_exit']==0,'GATE_EXIT')
        for channel in ['stdout','stderr']:
            row=run[channel]
            a.require(row['name']==f'{phase.upper()}_{channel.upper()}_R5.txt','GATE_STREAM_PATH')
            b=(control/row['name']).read_bytes()
            a.require(len(b)==row['bytes'] and a.digest(b)==row['sha256'],'GATE_RAW_STREAM_DRIFT')
    verify_preflight_stdout((control/gate['preflight']['stdout']['name']).read_bytes())
    verify_tests((control/gate['tests']['stderr']['name']).read_bytes(),gate['expected_tests'])
    a.require(a.digest((control/'ACK_R5.json').read_bytes())==gate['ack_sha256'],'ACK_DRIFT')
    a.require(gate['preflight']['argv']==[str(root/'.venv/Scripts/python.exe'),'-X','utf8',
       str(root/'脚本/blackbox_must_read_preflight_r1.py'),'--task-class','ACQUISITION'],'GATE_PREFLIGHT_COMMAND')
    a.require(gate['tests']['argv']==[str(root/'.venv/Scripts/python.exe'),'-X','utf8','-m','unittest','-v',
       'test_acquire_daily','test_r3_code_and_reuse','test_r4_empty_slots','test_r5_resume'],'GATE_TEST_COMMAND')
    return {'path':str(control/'GATE_R5.json'),'sha256':a.digest(data),'actual_preflight_exit':0,
            'actual_test_exit':0,'tests':gate['expected_tests'],'rule_bindings':rules}

def main():
    a.require(platform.system()=='Windows' and platform.node().upper()=='ZHANGWEI','WRONG_HOST')
    root=Path(r'E:\BLACKBOX');control=CONTROL
    a.require(control.is_dir() and not (control/'GATE_R5.json').exists(),'GATE_ALREADY_EXISTS_NO_RETRY')
    a.require(not (root/'STAGING/BLACKBOX_RAW_NONE_INCREMENT_20261027_R5').exists(),'R5_OUTPUT_ALREADY_EXISTS')
    package_sha=verify_package();rules=rule_binding(root)
    ack_bytes=(control/'ACK_R5.json').read_bytes();ack=json.loads(ack_bytes)
    a.require(ack['task_id']==TASK and ack['execution_host']=='ZHANGWEI','ACK_IDENTITY')
    a.require(ack['rule_bodies_read']==[r['relative_path'] for r in rules],'ACK_RULE_READ_LIST')
    a.require(ack['package_sha256']==package_sha and ack['upload_readback_completed'] is True,'ACK_NOT_BOUND')
    def run_capture(label,argv):
        started=a.now().isoformat()
        timed_out=False
        try:
            result=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,stdin=subprocess.DEVNULL,
                                  cwd=Path(__file__).parent,timeout=1800,check=False)
            stdout,stderr,exit_code=result.stdout,result.stderr,result.returncode
        except subprocess.TimeoutExpired as error:
            stdout,stderr,exit_code=error.stdout or b'',error.stderr or b'',None;timed_out=True
        streams={}
        for name,content in [('stdout',stdout),('stderr',stderr)]:
            path=control/f'{label}_{name.upper()}_R5.txt';pin=write_exact(path,content)
            streams[name]={'name':path.name,'bytes':pin['bytes'],'sha256':pin['sha256']}
        ledger={'argv':argv,'started_at':started,'finished_at':a.now().isoformat(),
                'actual_os_exit':exit_code,'timeout':timed_out,**streams}
        write_exact(control/f'{label}_RUN_R5.json',(json.dumps(ledger,indent=2)+'\n').encode())
        a.require(exit_code==0 and not timed_out,label+'_EXIT_NONZERO_OR_TIMEOUT')
        return ledger
    preflight=run_capture('PREFLIGHT',[str(root/'.venv/Scripts/python.exe'),'-X','utf8',
                                    str(root/'脚本/blackbox_must_read_preflight_r1.py'),'--task-class','ACQUISITION'])
    verify_preflight_stdout((control/preflight['stdout']['name']).read_bytes())
    manifest=json.loads(Path(__file__).with_name('PACKAGE.json').read_bytes())
    tests=run_capture('TESTS',[str(root/'.venv/Scripts/python.exe'),'-X','utf8','-m','unittest','-v',
       'test_acquire_daily','test_r3_code_and_reuse','test_r4_empty_slots','test_r5_resume'])
    verify_tests((control/tests['stderr']['name']).read_bytes(),manifest['expected_tests'])
    a.require(rule_binding(root)==rules,'RULE_DRIFT_DURING_GATES')
    gate={'task_id':TASK,'package_sha256':package_sha,'ack_sha256':a.digest(ack_bytes),'rule_bindings':rules,
          'preflight':preflight,'tests':tests,'expected_tests':manifest['expected_tests'],'finished_at':a.now().isoformat()}
    write_exact(control/'GATE_R5.json',(json.dumps(gate,ensure_ascii=False,indent=2)+'\n').encode())
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except a.Blocked as e:
        print(json.dumps({'status':'BLOCKED_NO_SUPPLIER_CALL','reason':str(e)}));raise SystemExit(2)
