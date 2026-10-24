"""Import the original engine package in a guarded child, without constructing it.

No source patch, provider registration, auth, download, strategy run or order.
Successful import is reported as import readiness only, never engine admission.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(r'E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine')
PINS={'bullet_trade/core/engine.py':'7e31f9ee391f3bc6b913fbc8bb308eab92b3e492cdf635e19b5ac5174eb258e2',
      'bullet_trade/data/api.py':'49c49697504202fb24a73241d14f0025729a08d03ff12a67a7f694e325383dee',
      'bullet_trade/data/providers/base.py':'be053cf0693aa1adcd54b077c3fa3748f0db42922aff369f1fca07049185002e'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def launch(root,pins):
    root=Path(root).resolve()
    for name,wanted in pins.items():
        if sha(root/name)!=wanted:raise ValueError('ENGINE_SOURCE_PIN_CHANGED:'+name)
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','TEMP','TMP','LANG','LC_ALL'}}
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONNOUSERSITE='1')
    try:
        p=subprocess.run([sys.executable,'-X','utf8',str(Path(__file__).resolve()),'--child',str(root),json.dumps(pins)],
                         capture_output=True,text=True,encoding='utf-8',env=env,cwd=Path(__file__).resolve().parent,timeout=60)
    except subprocess.TimeoutExpired:
        return {'status':'IMPORT_TIMEOUT_NO_RETRY','formal_backtest_active':False,'ORDER_ALLOWED':False}
    if p.returncode!=0:return {'status':'CHILD_EXIT_WITHOUT_RECEIPT','exit_code':p.returncode,'formal_backtest_active':False,'ORDER_ALLOWED':False}
    return json.loads(p.stdout)


def child(root,pins):
    import contextlib
    import tempfile
    import traceback
    root=Path(root).resolve();tempfile.tempdir=str(root)
    blocked=[]
    def profile(frame,event,arg):
        if event!='call':return
        mod=frame.f_globals.get('__name__','')
        name=frame.f_code.co_name
        forbidden={'auth','_ensure_auth','_ensure_auth_for','get_data_provider','set_data_provider','get_price',
                   'create_backtest','run_backtest','order','order_value','order_target','order_target_value'}
        if mod.startswith('bullet_trade') and (name in forbidden or (mod=='bullet_trade.core.engine' and name=='__init__')):
            blocked.append('business_call:'+mod+':'+name)
            raise PermissionError('ENGINE_IMPORT_BUSINESS_CALL_BLOCKED')
    def guard(event,args):
        if event in ('socket.connect','socket.connect_ex','socket.getaddrinfo','subprocess.Popen','os.system','os.remove','os.rename','os.mkdir','os.rmdir','os.truncate','os.link','os.symlink'):
            blocked.append(event);raise PermissionError('ENGINE_IMPORT_SIDE_EFFECT_BLOCKED')
        if event=='open':
            path,mode,flags=args;flags=flags or 0
            if isinstance(path,(str,bytes)):
                text=os.fsdecode(path).replace('\\','/').lower()
                if '/secrets/' in text or text.endswith('/.env'):
                    blocked.append('credential_file_read');raise PermissionError('CREDENTIAL_READ_BLOCKED')
            if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
                blocked.append('file_write');raise PermissionError('ENGINE_IMPORT_WRITE_BLOCKED')
    # Open the null sink before the no-write guard. No file is created.
    with open(os.devnull,'w') as sink,contextlib.redirect_stdout(sink),contextlib.redirect_stderr(sink):
        sys.dont_write_bytecode=True;sys.path.insert(0,str(root));sys.addaudithook(guard);sys.setprofile(profile)
        try:
            import importlib
            engine=importlib.import_module('bullet_trade.core.engine')
            api=importlib.import_module('bullet_trade.data.api')
            base=importlib.import_module('bullet_trade.data.providers.base')
            modules={'bullet_trade/core/engine.py':engine,'bullet_trade/data/api.py':api,'bullet_trade/data/providers/base.py':base}
            for name,mod in modules.items():
                if Path(mod.__file__).resolve()!=root/name or sha(root/name)!=pins[name]:
                    raise ValueError('IMPORTED_MODULE_IDENTITY_MISMATCH')
            # Even a caught side effect invalidates a clean import result.
            result={'status':'MODULES_IMPORTED_NO_ENGINE_CONSTRUCTED' if not blocked else 'IMPORT_ATTEMPTED_FORBIDDEN_SIDE_EFFECT',
                    'BacktestEngine_class_present':isinstance(getattr(engine,'BacktestEngine',None),type),
                    'DataProvider_class_present':isinstance(getattr(base,'DataProvider',None),type),
                    'data_api_callable_present':callable(getattr(api,'get_price',None))}
        except BaseException as exc:
            result={'status':'IMPORT_NOT_READY','error_type':type(exc).__name__,
                    'missing_module':getattr(exc,'name',None) if isinstance(exc,ModuleNotFoundError) else None,
                    'trace_locations':[{'file':f.filename,'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__)[-5:]]}
    return {**result,'blocked_events':blocked,'engine_root':str(root),'source_pins':pins,
            'engine_constructed':False,'explicit_provider_registration_calls':0,'explicit_auth_calls_by_probe':0,
            'formal_backtest_active':False,'FOUNDATION_ACCEPTANCE':False,'ORDER_ALLOWED':False}


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--child':
        print(json.dumps(child(sys.argv[2],json.loads(sys.argv[3])),ensure_ascii=True))
    elif sys.argv[1:]==['--desktop-import']:
        print(json.dumps(launch(ROOT,PINS),ensure_ascii=True))
    else:raise SystemExit('ONLY_THE_R10_DESKTOP_IMPORT_COMMAND_IS_SUPPORTED')
