"""One-shot original preflight, pinned fixtures, then exact allowlist observations."""
from datetime import datetime, timezone
import json,os,subprocess,sys
import guard as g
import observe as o

def child(out,name,argv,timeout):
    start=datetime.now(timezone.utc).isoformat();actual=None;error=None
    try:
        with (out/(name+'.stdout.txt')).open('xb') as a,(out/(name+'.stderr.txt')).open('xb') as b:
            p=subprocess.run(argv,cwd=g.PACKAGE,stdin=subprocess.DEVNULL,stdout=a,stderr=b,timeout=timeout,check=False)
            actual=p.returncode
    except Exception as e:error=dict(error_type=type(e).__name__,error=str(e))
    g.write(out/(name+'_PROCESS.json'),dict(argv=argv,actual_exit=actual,start_utc=start,
                 end_utc=datetime.now(timezone.utc).isoformat(),error=error))
    return actual

def main():
    spec,digest=g.validate(True)
    marker=json.loads(o.safe(g.OUTER/'RUN_ONCE.json').read_bytes())
    o.need(marker['task_id']==o.TASK and marker['package_sha256']==digest,'OUTER_MARKER')
    o.need(not g.CONTROL.exists(),'CAPTURE_EXISTS_NO_RETRY')
    pre=[g.EXE,'-B','-X','utf8',str(g.PACKAGE/'preflight_worker.py')]
    test=[g.EXE,'-B','-X','utf8',str(g.PACKAGE/'test_observe.py')]
    g.audit([g.CONTROL],processes=(tuple(pre),tuple(test)))
    g.CONTROL.mkdir(exist_ok=False);g.write(g.CONTROL/'RUN_ONCE.json',dict(task_id=o.TASK,replay_allowed=False))
    out=g.CONTROL/'result_001';out.mkdir(exist_ok=False)
    for env in ('TMP','TEMP','TMPDIR'):os.environ[env]=str(out/'fixture_tmp')
    (out/'fixture_tmp').mkdir(exist_ok=False)
    rc=2;pins=None
    try:
        pins=g.rules();g.write(out/'RULES_BEFORE.json',pins)
        o.need(child(out,'PREFLIGHT',pre,60)==0,'PREFLIGHT_EXIT')
        o.need('MUST_READ_PRECHECK = PASS' in (out/'PREFLIGHT.stdout.txt').read_text(encoding='utf-8'),'PREFLIGHT_NOT_PASS')
        o.need(child(out,'TESTS',test,120)==0,'NATIVE_FIXTURES_EXIT')
        text=(out/'TESTS.stderr.txt').read_text(encoding='utf-8')
        o.need(('Ran '+str(spec['native_fixture_tests'])+' tests') in text and text.rstrip().endswith('OK'),'NATIVE_TEST_COUNT_OR_FAILURE')
        cat=g.load('INPUTS.json');rc=o.collect(cat,out)
    except Exception as e:
        rc=3 if isinstance(e,o.Safety) else 2
        g.write(out/'FAILED.json',dict(status='FAILED_RETAINED_NO_RETRY',error_type=type(e).__name__,error=str(e)))
    finally:
        try:
            after=g.rules();g.write(out/'RULES_AFTER.json',after)
            if pins is not None and after!=pins:rc=3
        except Exception as e:
            rc=3;g.write(out/'RULE_FAILURE.json',dict(error_type=type(e).__name__,error=str(e)))
    g.write(out/'CAPTURE_EXIT.json',dict(actual_return=rc,task_id=o.TASK,ORDER_ALLOWED=False))
    return rc
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print(type(e).__name__+':'+str(e),file=sys.stderr);sys.exit(4)
