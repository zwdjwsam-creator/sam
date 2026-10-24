"""Exercise the actual child guard before and after the GPT tempdir fix.

Uses a minimal _base fixture carrying the observed tempfile.gettempdir() call.
It is not a substitute for the real desktop preflight or the ordered entry.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import r09_control_runtime as original
from build_r09_control_successor import build
from fix_r09_preflight_tempdir import repair,build as fix,SOURCE_SHA


def main(source,packet):
    controls=[]
    def ok(name):controls.append(name)
    source=Path(source)
    raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    changed=repair(source);compile(changed,'<fixed>','exec')
    assert original.run_preflight.__globals__['__name__']=='r09_control_runtime'
    assert b"tempfile.tempdir=temp_root" in changed
    # The denial predicate itself must remain byte-for-byte identical.
    def guard_part(s):return s.split('def guard(event,args):',1)[1].split('sys.addaudithook(guard)',1)[0]
    assert guard_part(raw.decode())==guard_part(changed.decode())
    ok('original source pin and exact guard byte preservation')
    with tempfile.TemporaryDirectory(prefix='r09_tempdir_fix_') as td:
        root=Path(td);copied=root/'r09_control_runtime.py';copied.write_bytes(raw)
        result=fix(copied);assert result['status']=='FIXED_ENTRY_CREATED'
        assert fix(copied)['status']=='ALREADY_FIXED_VERIFIED';ok('new sibling only and unchanged replay')
        fixed_path=Path(result['path'])
        fixed_path.write_bytes(changed+b'\n')
        try:fix(copied)
        except ValueError as e:assert 'DIFFERENT_BYTES' in str(e)
        else:raise AssertionError('tampered fixed entry accepted')
        fixed_path.write_bytes(changed);ok('tampered destination preserved and rejected')
        assert copied.read_bytes()==raw;ok('original runtime unchanged')
        spec=importlib.util.spec_from_file_location('r09_preflight_fixed_test',fixed_path)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        successor=root/'successor';build(packet,successor)
        def command(mod):
            with patch.object(mod.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='{"ok":true,"required":["BOOTSTRAP","DATA_ACCESS"]}',stderr='')) as run:
                mod.run_preflight(successor)
                return list(run.call_args.args[0])
        oldcmd=command(original);newcmd=command(module)
        bb=root/'BLACKBOX';scripts=bb/'scripts';scripts.mkdir(parents=True)
        pack=bb/'契约'/'必读';pack.mkdir(parents=True)
        kernel=bb/'.cursor'/'rules'/'BLACKBOX_KERNEL_ALWAYS_APPLY.mdc';kernel.parent.mkdir(parents=True);kernel.write_text('kernel\n',encoding='utf-8')
        files={}
        for key,name in [('BOOTSTRAP','BLACKBOX_BOOTSTRAP_MUST_READ.md'),('DATA_ACCESS','BLACKBOX_DATA_ACCESS_MUST_READ.md')]:
            p=pack/name;p.write_text('fixture\n',encoding='utf-8');files[key]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        manifest={'files':files,'kernel':{'sha256':hashlib.sha256(kernel.read_bytes()).hexdigest()}}
        mp=pack/'MUST_READ_MANIFEST_CURRENT.json';mp.write_text(json.dumps(manifest),encoding='utf-8')
        stub='''import tempfile,hashlib
from pathlib import Path
PROBE_LOCATION=tempfile.gettempdir()
ROOT=Path(__file__).parent.parent
OK=0
FAIL=3
def read_text(path):return Path(path).read_text(encoding='utf-8')
def sha256_text(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def set_runtime_context(**kwargs):pass
'''
        base=scripts/'_base.py';base.write_text(stub,encoding='utf-8')
        def run(cmd):
            cmd=list(cmd);cmd[-1]=str(scripts)
            return subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),timeout=30)
        before=run(oldcmd)
        assert before.returncode and 'No usable temporary directory' in before.stderr;ok('original child reproduces real import-probe failure')
        after=run(newcmd)
        assert after.returncode==0,after.stderr
        report=json.loads(after.stdout)
        assert report['ok'] and report['required']==['BOOTSTRAP','DATA_ACCESS'];ok('fixed child runs actual successor preflight without bypass')
        mp.write_text(json.dumps({**manifest,'kernel':{'sha256':None}}),encoding='utf-8')
        bad=run(newcmd);assert bad.returncode and 'SHA_AUTHORITY_MISSING_KERNEL' in bad.stdout;ok('real preflight hash rejection retained')
        mp.write_text(json.dumps(manifest),encoding='utf-8')
        output=root/'forbidden'
        base.write_text(stub+f"\nopen({str(output)!r},'w').write('bad')\n",encoding='utf-8')
        deny=run(newcmd);assert deny.returncode and 'WRITE_BLOCKED' in deny.stderr and not output.exists();ok('import-time write still denied')
        base.write_text(stub+"\nimport socket\nsocket.getaddrinfo('example.test',443)\n",encoding='utf-8')
        deny=run(newcmd);assert deny.returncode and 'SIDE_EFFECT_BLOCKED:socket.getaddrinfo' in deny.stderr;ok('import-time network still denied before connection')
        base.write_text(stub+f"\nimport os\nos.mkdir({str(output)!r})\n",encoding='utf-8')
        deny=run(newcmd);assert deny.returncode and 'SIDE_EFFECT_BLOCKED:os.mkdir' in deny.stderr and not output.exists();ok('directory creation still denied')
    print(json.dumps({'status':'PASS','controls_passed':len(controls),'controls':controls,
                      'scope':'OFFLINE_REAL_CHILD_AND_PREFLIGHT_WITH_BASE_FIXTURE; NOT_DESKTOP_ACCEPTANCE',
                      'guard_write_exceptions':0,'supplier_calls':0,'FOUNDATION_ACCEPTANCE':False},ensure_ascii=True))


if __name__=='__main__':
    main(Path(sys.argv[1]),Path(sys.argv[2]))
