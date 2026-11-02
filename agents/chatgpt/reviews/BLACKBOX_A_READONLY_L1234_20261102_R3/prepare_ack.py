"""Prepare once; ACK upload/readback precedes launch. No data-source reads."""
import sys
from datetime import datetime, timezone
import guard as g
import observe as o
import startup_probe

def main():
    spec,digest=g.validate(False)
    o.need(not g.CONTROL.exists() and not g.OUTER.exists(),'PRIOR_RUN_NO_RETRY')
    o.need(not (g.ACK_ROOT/'ACK.json').exists() and not (g.ACK_ROOT/'ACK_UPLOAD.json').exists(),'ACK_EXISTS_NO_REPREPARE')
    pins=g.rules()
    probe=startup_probe.run(g.ACK_ROOT,g.EXE,g.PACKAGE)
    g.audit([g.ACK_ROOT])
    g.write(g.ACK_ROOT/'ACK.json',dict(task_id=o.TASK,execution_host='ZHANGWEI',
            status='ACK_READY_NOT_EXECUTED',package_sha256=digest,rules=pins,
            utc=datetime.now(timezone.utc).isoformat(),executable=sys.executable,
            python=sys.version,pyarrow=o.pa.__version__,startup_probe=probe,data_source_reads=False,ORDER_ALLOWED=False))
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print(type(e).__name__+':'+str(e),file=sys.stderr);sys.exit(4)
