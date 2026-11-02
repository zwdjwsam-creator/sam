"""GPT-only execution of pinned CPython's Windows method with a fake OS boundary.

This is not native Windows process execution. It tests the actual upstream
argument lowering and emitted audit event against old/new guard policies.
"""
from pathlib import Path
import ast,hashlib,json,os,sys,subprocess,types,warnings,importlib.util,textwrap
import guard as g
import observe as o

ROOT=Path(__file__).parent
evidence=json.loads(Path('cpython_r3_evidence.json').read_bytes())
source=evidence['sources'][0]['content'];tree=ast.parse(source)
functions=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_execute_child' and 'MS Windows' in (ast.get_docstring(n) or '')]
assert len(functions)==1
body=textwrap.dedent(ast.get_source_segment(source,functions[0]))
spec=importlib.util.spec_from_file_location('old_guard',Path('l1234_r2_original/guard.py'));old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
holder={};traces=[]
def hook(event,args):
    if event in ('subprocess.Popen','_winapi.CreateProcess'):
        traces.append(dict(event=event,argument_count=len(args),argv_type=type(args[1]).__name__))
        holder['check'](event,args)
sys.addaudithook(hook)
argv=[r'E:\BLACKBOX\.venv\Scripts\python.exe','-B','-X','utf8',r'C:\LAN_SHARE_REPORT\package\run_capture.py']
class Startup:
    def __init__(self):self.dwFlags=0;self.lpAttributeList=None
class Self:
    _child_created=False
    def _close_pipe_fds(self,*args):pass
results=[]
for mode in ('old','string_only','vector_then_string','extra_argument','wrong_executable','wrong_cwd','wrong_env','wrong_low_level'):
    traces=[];created=[]
    holder['check']=(old if mode=='old' else g).audit_checker([ROOT],processes=(tuple(argv),))
    def create(exe,cmd,*args):
        cwd=args[5]
        sys.audit('_winapi.CreateProcess',exe,cmd+' extra' if mode=='wrong_low_level' else cmd,cwd)
        created.append(True);return 1,2,3,4
    fake=types.SimpleNamespace(CreateProcess=create,CloseHandle=lambda h:None)
    env=dict(os=os,sys=sys,list2cmdline=subprocess.list2cmdline,STARTUPINFO=Startup,
             Handle=lambda h:h,_winapi=fake,warnings=warnings)
    exec(compile(body,'CPYTHON_3_12_10_WINDOWS_EXECUTE_CHILD','exec'),env)
    call=dict(self=Self(),args=argv+(['extra'] if mode=='extra_argument' else []),executable=argv[0]+'.other' if mode=='wrong_executable' else None,
      preexec_fn=None,close_fds=True,pass_fds=(),cwd=str(Path.cwd().parent) if mode=='wrong_cwd' else None,
      env={'FIXTURE':'value'} if mode=='wrong_env' else None,startupinfo=None,creationflags=0,shell=False,
      p2cread=-1,p2cwrite=-1,c2pread=-1,c2pwrite=-1,errread=-1,errwrite=-1,
      unused_restore_signals=True,unused_gid=None,unused_gids=None,unused_uid=None,
      unused_umask=-1,unused_start_new_session=False,unused_process_group=-1)
    error=None
    try:
        if mode=='vector_then_string':sys.audit('subprocess.Popen',argv[0],argv,None,None)
        env['_execute_child'](**call)
    except o.Safety as e:error=str(e)
    success=mode in ('string_only','vector_then_string')
    assert bool(created)==success,(mode,error,traces)
    assert (error is None)==success,(mode,error)
    results.append(dict(mode=mode,model_OS_boundary_reached=bool(created),error=error,event_shapes=traces))
result=dict(scope='Pinned upstream Windows-method execution with fake CreateProcess; not native execution',
            cpython_tag='v3.12.10',source_sha256=hashlib.sha256(source.encode()).hexdigest(),
            extracted_method_sha256=hashlib.sha256(body.encode()).hexdigest(),results=results,actual_native_execution=False)
(ROOT/'WINDOWS_BRANCH_CHECK.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
