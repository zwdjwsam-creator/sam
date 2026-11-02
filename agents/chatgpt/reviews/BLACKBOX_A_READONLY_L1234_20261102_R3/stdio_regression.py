"""Isolated C:-fixture subprocess tests; never opens a BLACKBOX data original."""
from pathlib import Path
import json,os,subprocess,sys,tempfile
import guard as g
import observe as o
from subprocess_io import run_readonly_stdin


def scenario(mode,root):
    root=Path(root)
    o.need(root==Path(os.environ['BLACKBOX_STDIO_FIXTURE_ROOT'])/mode,'FIXED_OWNED_FIXTURE_ROOT')
    o.need(g.inside(root,tempfile.gettempdir()),'TEMP_FIXTURE_BOUNDARY')
    if os.name=='nt':o.need(g.inside(root,g.CONTROL/'result_001/fixture_tmp'),'NATIVE_C_FIXTURE_ONLY')
    o.safe(root);allowed=root/'allowed';allowed.mkdir(exist_ok=False)
    device=root/'outside_capture_null_fixture';device.write_bytes(b'')
    before=device.stat();real_null=os.devnull
    if mode in ('old','fixed'):os.devnull=str(device)
    argv=[sys.executable,'-B','-c',"print('CHILD_STARTED')"]
    trace=[]
    def audit(event,args):
        if event=='open' and str(args[0])==os.devnull:
            trace.append(dict(event='null_open',mode=args[1],flags=args[2]))
        if event=='subprocess.Popen':trace.append(dict(event='Popen'))
    sys.addaudithook(audit)
    g.audit([allowed],processes=(tuple(argv),))
    result=dict(mode=mode,actual_child_exit=None,child_output=None,guard_error=None)
    try:
        if mode=='old':p=subprocess.run(argv,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        else:p=run_readonly_stdin(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
        result.update(actual_child_exit=p.returncode,child_output=p.stdout.decode().strip())
    except o.Safety as e:result['guard_error']=str(e)
    result['trace']=trace
    result['fixture_unchanged']=device.stat().st_size==before.st_size and device.stat().st_mtime_ns==before.st_mtime_ns
    os.devnull=real_null
    if mode=='old':
        assert result['actual_child_exit'] is None and result['guard_error'].startswith('WRITE_OUTSIDE_CAPTURE:')
        assert not any(r['event']=='Popen' for r in trace)
        assert any(r['event']=='null_open' and r['flags']&os.O_RDWR for r in trace)
    else:
        assert result['actual_child_exit']==0 and result['child_output']=='CHILD_STARTED' and result['guard_error'] is None
        assert any(r['event']=='Popen' for r in trace)
        assert all(not(r['flags']&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)) for r in trace if r['event']=='null_open')
    assert result['fixture_unchanged']
    print(json.dumps(result));return 0


if __name__=='__main__':
    o.need(len(sys.argv)==3 and sys.argv[1] in ('old','fixed','real'),'FIXED_STDIO_REGRESSION_ARGUMENTS')
    sys.exit(scenario(sys.argv[1],sys.argv[2]))
