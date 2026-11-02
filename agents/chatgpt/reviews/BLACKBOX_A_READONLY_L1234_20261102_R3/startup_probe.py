"""Native prepare-time spawn proof before ACK/data reads; same exact audit policy."""
from pathlib import Path
from datetime import datetime,timezone
import sys
import guard as g
import observe as o
from subprocess_io import run_readonly_stdin


def run(out,exe,cwd):
    out=Path(out);argv=[exe,'-B','-X','utf8','-c',"print('READ_ONLY_STARTUP_PROBE_OK')"]
    trace=[]
    def record(event,args):
        if event in ('subprocess.Popen','_winapi.CreateProcess'):
            trace.append(dict(event=event,argument_count=len(args),
                executable_is_none=args[0] is None if args else None,
                argv_type=type(args[1]).__name__ if len(args)>1 else None))
    sys.addaudithook(record)
    g.audit([out],processes=(tuple(argv),))
    actual=None;error=None;start=datetime.now(timezone.utc).isoformat()
    try:
        with (out/'STARTUP.stdout.txt').open('xb') as a,(out/'STARTUP.stderr.txt').open('xb') as b:
            p=run_readonly_stdin(argv,cwd=cwd,stdout=a,stderr=b,timeout=30,check=False);actual=p.returncode
    except Exception as e:error=dict(error_type=type(e).__name__,error=str(e))
    result=dict(argv=argv,actual_child_exit=actual,error=error,start_utc=start,
                end_utc=datetime.now(timezone.utc).isoformat(),audit_event_shapes=trace,
                data_source_reads=False,source_writes=False,ORDER_ALLOWED=False)
    g.write(out/'STARTUP_PROCESS.json',result)
    o.need(actual==0 and error is None and (out/'STARTUP.stdout.txt').read_bytes().strip()==b'READ_ONLY_STARTUP_PROBE_OK','NATIVE_STARTUP_PROBE_FAILED')
    return result
