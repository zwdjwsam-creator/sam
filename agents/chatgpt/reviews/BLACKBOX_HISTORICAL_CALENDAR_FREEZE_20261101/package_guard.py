"""Fixed package and ACK checks; no discovery of source paths."""
from pathlib import Path
import json,os,socket,sys
import freeze_calendar as c
PACKAGE=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_HISTORICAL_CALENDAR_FREEZE_20261101_PACKAGE\package')
ACK_ROOT=PACKAGE.parent
OUTER=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_HISTORICAL_CALENDAR_FREEZE_REVIEW_20261101_OUTER')
def manifest_at(root):
 raw=c.safe(root/'PACKAGE.json').read_bytes();m=json.loads(raw)
 c.need(m['task_id']=='BLACKBOX_HISTORICAL_CALENDAR_FREEZE_20261101','PACKAGE_TASK')
 names=[r['path'] for r in m['files']]
 c.need(len(names)==len(set(names)) and all(Path(n).name==n and n not in ('PACKAGE.json','ACK.json') for n in names),'PACKAGE_MEMBERS')
 c.need({x.name for x in root.iterdir()}==set(names)|{'PACKAGE.json'},'PACKAGE_EXACT_SET')
 for r in m['files']:
  b=c.safe(root/r['path']).read_bytes();c.need(len(b)==r['bytes'] and c.sha(b)==r['sha256'],'PACKAGE_MEMBER_CHANGED:'+r['path'])
 return c.sha(raw)
def rules():
 pins=json.loads((PACKAGE/'RULE_PINS.json').read_bytes())['files'];observed=[]
 for r in pins:
  b=c.safe(Path(r['path'])).read_bytes();c.need(len(b)==r['bytes'] and c.sha(b)==r['sha256'],'OPERATIONAL_PIN_CHANGED:'+r['path'])
  observed.append({'path':r['path'],'bytes':len(b),'sha256':c.sha(b)})
 return observed
def validate(require_ack):
 spec=json.loads((Path(__file__).parent/'CALENDAR_FREEZE_CONTRACT.json').read_bytes())
 c.need(spec['status']=='APPROVED_NATIVE_DISPATCH','REVIEW_ONLY_NOT_DISPATCHED')
 c.need(os.name=='nt' and socket.gethostname().upper()=='ZHANGWEI','HOST')
 c.need(sys.version_info[:3]==(3,12,10) and os.path.normcase(sys.executable)==os.path.normcase(c.EXE),'INTERPRETER')
 c.need(c.pa.__version__=='24.0.0','ARROW_RUNTIME')
 c.need(Path(__file__).parent==PACKAGE,'FIXED_PACKAGE_ROOT')
 c.need(spec['source_path']==str(c.SOURCE) and spec['known_sha256_prefix']==c.PREFIX,'CONTRACT_SOURCE_CHANGED')
 c.safe(PACKAGE);c.safe(ACK_ROOT);digest=manifest_at(PACKAGE)
 if require_ack:
  ack=json.loads(c.safe(ACK_ROOT/'ACK.json').read_bytes())
  c.need(ack['task_id']==spec['task_id'] and ack['package_sha256']==digest and ack['execution_host']=='ZHANGWEI','ACK_PACKAGE_BINDING')
 return spec
