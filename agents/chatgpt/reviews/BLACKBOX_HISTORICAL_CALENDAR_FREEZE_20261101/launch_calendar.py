"""Capture the real child exit once; retain all outcomes, no replay."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,sys
import freeze_calendar as c
import package_guard as g
OUTER=g.OUTER

def main():
 spec=g.validate(require_ack=True)
 c.safe(OUTER);c.safe(c.CONTROL);c.need(not OUTER.exists() and not c.CONTROL.exists(),'PRIOR_RUN_NO_RETRY')
 OUTER.mkdir(exist_ok=False);c.write_new(OUTER/'RUN_ONCE.json',c.packed({'task_id':spec['task_id'],'replay_allowed':False}))
 argv=[c.EXE,'-B','-X','utf8',str(g.PACKAGE/'freeze_calendar.py')];start=datetime.now(timezone.utc).isoformat()
 try:
  with (OUTER/'OUTER.stdout.txt').open('xb') as a,(OUTER/'OUTER.stderr.txt').open('xb') as b:
   p=subprocess.run(argv,cwd=g.PACKAGE,stdin=subprocess.DEVNULL,stdout=a,stderr=b,check=False)
  c.write_new(OUTER/'OUTER_RUN.json',c.packed({'argv':argv,'actual_exit':p.returncode,'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat()}));return p.returncode
 except Exception as e:
  c.write_new(OUTER/'OUTER_RUN.json',c.packed({'argv':argv,'actual_exit':None,'start_utc':start,'end_utc':datetime.now(timezone.utc).isoformat(),'error_type':type(e).__name__,'error':str(e)}));return 2
if __name__=='__main__':
 try:sys.exit(main())
 except c.Stop as e:print(str(e),file=sys.stderr);sys.exit(4)
