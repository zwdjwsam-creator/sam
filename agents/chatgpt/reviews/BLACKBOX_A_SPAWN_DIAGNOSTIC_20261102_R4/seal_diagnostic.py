"""Finite C: receipt seal; never reopen a data source or repair a failure."""
from pathlib import Path
import sys
import guard as g
import observe as o
from diagnostic_probe import OUT
DELIVERY=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_A_SPAWN_DIAGNOSTIC_20261102_R4_DELIVERY')

def main():
    spec,digest=g.validate(False);o.safe(DELIVERY);o.need(not DELIVERY.exists(),'DELIVERY_EXISTS_NO_REPLAY')
    g.audit([DELIVERY]);DELIVERY.mkdir(exist_ok=False)
    refs=[(OUT/n,'diagnostic/'+n) for n in ['PROBE.stdout.txt','PROBE.stderr.txt','DIAGNOSTIC.json','RULE_IDENTITIES.json']]
    refs += [(g.ACK_ROOT/'control_logs'/('probe'+suffix),'control_logs/probe'+suffix) for suffix in ['.started.json','.stdout.txt','.stderr.txt','.process.json']]
    rows=[];absent=[];total=0
    for src,relative in refs:
        o.safe(src)
        if not src.exists():absent.append(relative);continue
        b=src.read_bytes();o.need(len(b)<=o.MAX_MEMBER,'RECEIPT_FILE_CAP');total+=len(b);o.need(total<=o.MAX_OUTPUT,'DELIVERY_CAP')
        dst=DELIVERY/relative;dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open('xb') as f:f.write(b)
        o.need(dst.read_bytes()==b,'BYTE_READBACK');rows.append(dict(path=relative,bytes=len(b),sha256=o.sha(b)))
    g.write(DELIVERY/'DELIVERY_MANIFEST.json',dict(task_id=o.TASK,package_sha256=digest,files=rows,bytes=total,
        absent_conditional_members=absent,scope='STARTUP_DIAGNOSTIC_ONLY_NOT_L1_L2_L3_L4',ACK_REQUESTED=False,ORDER_ALLOWED=False))
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print(type(e).__name__+':'+str(e),file=sys.stderr);sys.exit(4)
