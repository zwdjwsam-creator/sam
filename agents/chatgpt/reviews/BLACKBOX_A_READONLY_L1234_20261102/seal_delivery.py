"""Copy fixed C: receipts only into a fresh C: delivery, then byte-read them back."""
from pathlib import Path
import json,sys
import guard as g
import observe as o

DELIVERY=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_A_READONLY_L1234_20261102_DELIVERY')
BASE=['RULES_BEFORE.json','RULES_AFTER.json','RULE_FAILURE.json','PREFLIGHT.stdout.txt','PREFLIGHT.stderr.txt','PREFLIGHT_PROCESS.json',
      'TESTS.stdout.txt','TESTS.stderr.txt','TESTS_PROCESS.json','FAILED.json','CAPTURE_EXIT.json',
      'SOURCE_BEFORE.json','SOURCE_AFTER.json','IDENTITY_DISPOSITIONS.json','DUPLICATES.json','SAMPLE_002270.json',
      'L4_TOTALS.json','L2_L3_COUNTS.json','OBSERVATION_RESULT.json','ROWS_SCHEMA.json']

def main():
    # Failure receipts must remain deliverable if ACK/rules blocked execution.
    spec,digest=g.validate(False);o.safe(DELIVERY);o.need(not DELIVERY.exists(),'DELIVERY_EXISTS_NO_REPLAY')
    g.audit([DELIVERY]);DELIVERY.mkdir(exist_ok=False)
    refs=[(g.ACK_ROOT/'ACK.json','ACK.json'),(g.ACK_ROOT/'ACK_UPLOAD.json','ACK_UPLOAD.json')]
    refs += [(g.ACK_ROOT/'control_logs'/(phase+suffix),'control_logs/'+phase+suffix)
             for phase in ['prepare','bind','launch'] for suffix in ['.started.json','.stdout.txt','.stderr.txt','.process.json']]
    refs += [(g.OUTER/n,'outer/'+n) for n in ['RUN_ONCE.json','OUTER.stdout.txt','OUTER.stderr.txt','OUTER_PROCESS.json']]
    refs += [(g.CONTROL/'RUN_ONCE.json','capture/RUN_ONCE.json')]
    names=BASE+[prefix+d+'.jsonl' for d in g.load('INPUTS.json')['data_sessions'] for prefix in ['ROWS_','LIMITS_']]
    refs += [(g.CONTROL/'result_001'/n,'capture/result_001/'+n) for n in names]
    rows=[];absent=[];total=0
    for src,relative in refs:
        o.safe(src)
        if not src.exists():absent.append(relative);continue
        raw=src.read_bytes();o.need(len(raw)<=o.MAX_MEMBER,'RECEIPT_FILE_CAP')
        total+=len(raw);o.need(total<=o.MAX_OUTPUT,'DELIVERY_CAP')
        dest=DELIVERY/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as f:f.write(raw)
        o.need(dest.read_bytes()==raw,'DELIVERY_BYTE_READBACK')
        rows.append(dict(path=relative,bytes=len(raw),sha256=o.sha(raw)))
    fixture=o.safe(g.CONTROL/'result_001/fixture_tmp')
    fixture_status=dict(path=str(fixture),exists=fixture.exists(),empty=None,
                        scope='Task-owned C: fixture directory only; no original enumeration/deletion')
    if fixture.is_dir():fixture_status['empty']=not any(fixture.iterdir())
    g.write(DELIVERY/'FIXTURE_STATUS.json',fixture_status)
    fb=(DELIVERY/'FIXTURE_STATUS.json').read_bytes()
    rows.append(dict(path='FIXTURE_STATUS.json',bytes=len(fb),sha256=o.sha(fb)));total+=len(fb)
    observation=g.CONTROL/'result_001/OBSERVATION_RESULT.json'
    observed=json.loads(observation.read_bytes()) if observation.is_file() else {'status':'NO_OBSERVATION_RESULT'}
    text=('BLACKBOX READ-ONLY OBSERVATION RETURN\n'
          'Execution host: ZHANGWEI\nTask: '+o.TASK+'\n'
          'Observed result: '+observed['status']+'\n'
          'This delivery is not GPT acceptance, source absence, supplier-unit or regime certification.\n'
          'No supplier, research, backtest, CURRENT, release, calendar or order action was authorized.\n'
          'Source and schema failures are retained; do not retry or edit code/pins.\n'
          'Rows use ROWS_SCHEMA.json; all IEEE encodings and physical positions are preserved.\n'
          'ORDER_ALLOWED=false\n').encode('utf-8')
    with (DELIVERY/'REPORT.txt').open('xb') as f:f.write(text)
    o.need((DELIVERY/'REPORT.txt').read_bytes()==text,'REPORT_READBACK')
    rows.append(dict(path='REPORT.txt',bytes=len(text),sha256=o.sha(text)));total+=len(text)
    report=dict(task_id=o.TASK,status='CAPTURE_RECEIPTS_AWAITING_GPT_NOT_ACCEPTANCE',package_sha256=digest,
                files=rows,absent_conditional_members=absent,source_data_copied=False,
                bytes=total,ORDER_ALLOWED=False)
    g.write(DELIVERY/'DELIVERY_MANIFEST.json',report)
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print(type(e).__name__+':'+str(e),file=sys.stderr);sys.exit(4)
