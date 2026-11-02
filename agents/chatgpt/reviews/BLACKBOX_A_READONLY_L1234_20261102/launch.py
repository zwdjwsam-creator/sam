"""Exclusive run root and real OS child exit; no retry or production mutations."""
from datetime import datetime,timezone
import subprocess,sys
import guard as g
import observe as o

def main():
    spec,digest=g.validate(True)
    o.need(not g.OUTER.exists() and not g.CONTROL.exists(),'PRIOR_RUN_NO_RETRY')
    argv=[g.EXE,'-B','-X','utf8',str(g.PACKAGE/'run_capture.py')]
    g.audit([g.OUTER],processes=(tuple(argv),))
    g.OUTER.mkdir(exist_ok=False);g.write(g.OUTER/'RUN_ONCE.json',dict(task_id=o.TASK,package_sha256=digest,replay_allowed=False))
    start=datetime.now(timezone.utc).isoformat();actual=None;error=None
    try:
        with (g.OUTER/'OUTER.stdout.txt').open('xb') as a,(g.OUTER/'OUTER.stderr.txt').open('xb') as b:
            p=subprocess.run(argv,cwd=g.PACKAGE,stdin=subprocess.DEVNULL,stdout=a,stderr=b,timeout=900,check=False);actual=p.returncode
    except Exception as e:error=dict(error_type=type(e).__name__,error=str(e))
    g.write(g.OUTER/'OUTER_PROCESS.json',dict(argv=argv,actual_child_exit=actual,error=error,
               start_utc=start,end_utc=datetime.now(timezone.utc).isoformat()))
    return 2 if actual is None else actual
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print(type(e).__name__+':'+str(e),file=sys.stderr);sys.exit(4)
