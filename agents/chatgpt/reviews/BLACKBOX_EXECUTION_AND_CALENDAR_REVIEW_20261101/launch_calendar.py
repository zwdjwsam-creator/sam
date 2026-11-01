"""Review-only programmatic outer exit capture. No native permission in draft contract."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,socket,subprocess,sys
import freeze_calendar as c
OUTER=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_HISTORICAL_CALENDAR_FREEZE_REVIEW_20261101_OUTER')
def main():
 spec=json.loads((Path(__file__).parent/'CALENDAR_FREEZE_CONTRACT.json').read_bytes())
 c.need(spec['status']=='APPROVED_NATIVE_DISPATCH','REVIEW_ONLY_NOT_DISPATCHED')
 c.need(os.name=='nt' and socket.gethostname().upper()=='ZHANGWEI','HOST')
 c.need(os.path.normcase(sys.executable)==os.path.normcase(c.EXE),'INTERPRETER')
 c.safe(OUTER);c.safe(c.CONTROL);c.need(not OUTER.exists() and not c.CONTROL.exists(),'PRIOR_RUN_NO_RETRY')
 OUTER.mkdir(exist_ok=False);c.write_new(OUTER/'RUN_ONCE.json',c.packed({'task_id':spec['task_id']}))
 argv=[c.EXE,'-B','-X','utf8',str(Path(__file__).parent/'freeze_calendar.py')];start=datetime.now(timezone.utc).isoformat()
 with (OUTER/'OUTER.stdout.txt').open('xb') as a,(OUTER/'OUTER.stderr.txt').open('xb') as b:
  p=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=a,stderr=b,check=False)
 c.write_new(OUTER/'OUTER_RUN.json',c.packed({'argv':argv,'actual_exit':p.returncode,'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat()}));return p.returncode
if __name__=='__main__':
 try:sys.exit(main())
 except c.Stop as e:print(str(e),file=sys.stderr);sys.exit(4)
