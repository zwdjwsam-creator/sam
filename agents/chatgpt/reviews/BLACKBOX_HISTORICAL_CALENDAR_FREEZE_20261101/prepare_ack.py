"""Prepare once, then upload/read back ACK before launch; no data-source read."""
import sys
from datetime import datetime,timezone
import freeze_calendar as c
import package_guard as g

def main():
 spec=g.validate(require_ack=False)
 for root in (c.CONTROL,g.OUTER):
  c.safe(root);c.need(not root.exists(),'PRIOR_RUN_NO_RETRY')
 c.need(not (g.ACK_ROOT/'ACK.json').exists(),'ACK_EXISTS_NO_REPREPARE')
 pins=g.rules()
 ack={'task_id':spec['task_id'],'execution_host':'ZHANGWEI','package_sha256':g.manifest_at(g.PACKAGE),'status':'ACK_READY_NOT_EXECUTED','utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'executable':sys.executable,'pyarrow':c.pa.__version__,'operational_files':pins,'source_read':False,'orders_allowed':False}
 c.write_new(g.ACK_ROOT/'ACK.json',c.packed(ack));return 0
if __name__=='__main__':
 try:sys.exit(main())
 except c.Stop as e:print(str(e),file=sys.stderr);sys.exit(4)
