"""One fixed print-only spawn; literal audit telemetry, no policy/data admission."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,sys,subprocess,_thread
import guard as g
import observe as o
from subprocess_io import run_readonly_stdin

OUT=g.ACK_ROOT/'diagnostic_001'
TOKEN=b'READ_ONLY_STARTUP_PROBE_OK'

def callable_identity(f):
    code=getattr(f,'__code__',None)
    return dict(type=type(f).__name__,module=getattr(f,'__module__',None),
                qualname=getattr(f,'__qualname__',None),
                code_filename=getattr(code,'co_filename',None),first_line=getattr(code,'co_firstlineno',None))

def runtime_identity():
    w=getattr(subprocess,'_winapi',None)
    return dict(os_name=os.name,executable=sys.executable,base_executable=getattr(sys,'_base_executable',None),
                prefix=sys.prefix,base_prefix=sys.base_prefix,version=sys.version,
                subprocess_file=subprocess.__file__,Popen_execute_child=callable_identity(subprocess.Popen._execute_child),
                winapi_file=getattr(w,'__file__',None),CreateProcess=callable_identity(getattr(w,'CreateProcess',None)),
                current_directory=os.getcwd(),environment_values_collected=False,
                runtime_source_bodies_read=False,runtime_binaries_read=False)

def text_or_none(x):
    if x is None or isinstance(x,str):return x
    return dict(unexpected_type=type(x).__name__)

def differences(actual,expected):
    if not isinstance(actual,str):return []
    rows=[]
    for want in expected:
        i=next((i for i,(a,b) in enumerate(zip(actual,want)) if a!=b),min(len(actual),len(want)))
        equal=actual==want
        rows.append(dict(expected=want,equal=equal,actual_length=len(actual),expected_length=len(want),
            first_different_index=None if equal else i,
            actual_segment=actual[max(0,i-16):i+64],expected_segment=want[max(0,i-16):i+64],
            actual_codepoints=[ord(c) for c in actual[max(0,i-2):i+8]],
            expected_codepoints=[ord(c) for c in want[max(0,i-2):i+8]]))
    return rows

def recorder(trace):
    def record(event,args,policy,before,decision,error):
        # Only fixed worker spawn events; never record env contents or other audit events.
        cmd=args[1] if len(args)>1 else None
        if isinstance(cmd,(list,tuple)):literal=list(cmd)
        else:literal=text_or_none(cmd)
        expected=list(policy.commands)
        trace.append(dict(event=event,argument_count=len(args),argv_type=type(cmd).__name__,
            executable=text_or_none(args[0]) if args else None,command_literal=literal,
            command_repr=repr(cmd) if isinstance(cmd,(str,list,tuple)) else None,
            cwd=text_or_none(args[2]) if len(args)>2 else None,
            explicit_environment=(args[3] is not None) if event=='subprocess.Popen' and len(args)==4 else None,
            thread_id=_thread.get_ident(),pending_before=before,pending_after=getattr(policy.local,'pending',None),
            reviewed_command_keys=expected,reviewed_vectors=[list(a) for a in sorted(policy.vectors)],
            reviewed_effective_cwd=policy.cwd,decision=decision,rejection_reason=error,
            exact_differences=differences(cmd,expected)))
    return record

def capture(out,exe,cwd,install_audit=True):
    argv=[exe,'-B','-X','utf8','-c',"print('READ_ONLY_STARTUP_PROBE_OK')"]
    trace=[];runtime=runtime_identity();start=datetime.now(timezone.utc).isoformat();actual=None;error=None
    if install_audit:g.audit([out],processes=(tuple(argv),),spawn_observer=recorder(trace))
    try:
        with (out/'PROBE.stdout.txt').open('xb') as a,(out/'PROBE.stderr.txt').open('xb') as b:
            actual=run_readonly_stdin(argv,cwd=cwd,stdout=a,stderr=b,timeout=30,check=False).returncode
    except Exception as e:error=dict(error_type=type(e).__name__,error=str(e))
    result=dict(task_id=o.TASK,scope='ONE_FIXED_PRINT_ONLY_SPAWN_DIAGNOSTIC_NOT_DATA_ACCEPTANCE',
        argv=argv,expected_command_line=subprocess.list2cmdline(argv),runtime_identity=runtime,
        actual_child_exit=actual,error=error,start_utc=start,end_utc=datetime.now(timezone.utc).isoformat(),
        audit_events=trace,source_data_reads=False,source_writes=False,ACK_written=False,
        further_launch_authorized=False,ORDER_ALLOWED=False)
    result['exact_success_token']=actual==0 and (out/'PROBE.stdout.txt').read_bytes().strip()==TOKEN
    result['status']='DIAGNOSTIC_COMPLETE_CHILD_EXIT_ZERO_NOT_ACCEPTANCE' if result['exact_success_token'] else 'DIAGNOSTIC_COMPLETE_SPAWN_FAILED_RETAINED_NOT_ACCEPTANCE'
    g.write(out/'DIAGNOSTIC.json',result)
    return result

def main():
    spec,digest=g.validate(False)
    o.need(not OUT.exists() and not (g.ACK_ROOT/'ACK.json').exists() and not g.CONTROL.exists() and not g.OUTER.exists(),'PRIOR_ROOT_OR_ACK_NO_RETRY')
    pins=g.rules();OUT.mkdir(exist_ok=False)
    # capture installs the only diagnostic audit hook; all writes are confined to OUT.
    result=capture(OUT,g.EXE,g.PACKAGE)
    after=g.rules()
    g.write(OUT/'RULE_IDENTITIES.json',dict(before=pins,after=after,equal=pins==after,package_sha256=digest))
    o.need(pins==after,'RULE_DRIFT')
    return 0  # Diagnostic collection completed; nullable/failed child is explicitly retained above.

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print(type(e).__name__+':'+str(e),file=sys.stderr);sys.exit(4)
