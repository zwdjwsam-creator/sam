"""ADDITIVE Windows completion of the supplied R09 tempdir-fix controls.

The supplied test_r09_preflight_tempdir.py (pin 875283920c..., 5918 B) is NOT modified
and remains the authoritative control list. On Windows its fixture builds the expected
SHA256 from `p.read_bytes()` after `write_text('fixture\\n')` — text mode stores CRLF —
while the child's `read_text()` translates CRLF back to LF, so the two hashes can never
match on this platform:

    expected = sha256(b'fixture\\r\\n') = 5bd17a4a66c4126008a147278511f1fb55774b443fa32bf571a0ffd5a8efc073
    actual   = sha256(b'fixture\\n')    = e80b71cd14d3cbd65f4173abcbfcf01a545dbca32a72d575108b553a648cc96f

That is a fixture portability defect, not a repair defect and not evidence about market
data. This harness reproduces the SAME ten invariants with byte-exact fixture writes so
the remaining controls can actually run on this host. It asserts nothing less than the
supplied test: identical guard predicate bytes, identical rejection strings.
"""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'reviews/R09/control_2100'))
sys.path.insert(0, str(HERE.parent / 'reviews/R09/preflight_fix_2140'))

import r09_control_runtime as original  # noqa: E402
from build_r09_control_successor import build  # noqa: E402
from fix_r09_preflight_tempdir import SOURCE_SHA, build as fix, repair  # noqa: E402


def main(source, packet):
    controls = []

    def ok(name):
        controls.append(name)

    source = Path(source)
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    changed = repair(source)
    compile(changed, '<fixed>', 'exec')
    assert original.run_preflight.__globals__['__name__'] == 'r09_control_runtime'
    assert b'tempfile.tempdir=temp_root' in changed

    def guard_part(s):
        return s.split('def guard(event,args):', 1)[1].split('sys.addaudithook(guard)', 1)[0]

    assert guard_part(raw.decode()) == guard_part(changed.decode())
    ok('original source pin and exact guard byte preservation')

    with tempfile.TemporaryDirectory(prefix='r09_tempdir_win_') as td:
        root = Path(td)
        copied = root / 'r09_control_runtime.py'
        copied.write_bytes(raw)
        result = fix(copied)
        assert result['status'] == 'FIXED_ENTRY_CREATED'
        assert fix(copied)['status'] == 'ALREADY_FIXED_VERIFIED'
        ok('new sibling only and unchanged replay')

        fixed_path = Path(result['path'])
        fixed_path.write_bytes(changed + b'\n')
        try:
            fix(copied)
        except ValueError as exc:
            assert 'DIFFERENT_BYTES' in str(exc)
        else:
            raise AssertionError('tampered fixed entry accepted')
        fixed_path.write_bytes(changed)
        ok('tampered destination preserved and rejected')

        assert copied.read_bytes() == raw
        ok('original runtime unchanged')

        spec = importlib.util.spec_from_file_location('r09_preflight_fixed_win', fixed_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        successor = root / 'successor'
        build(packet, successor)

        def command(mod):
            with patch.object(mod.subprocess, 'run',
                              return_value=type('R', (), {'returncode': 0,
                                                          'stdout': '{"ok":true,"required":["BOOTSTRAP","DATA_ACCESS"]}',
                                                          'stderr': ''})()) as run:
                mod.run_preflight(successor)
                return list(run.call_args.args[0])

        oldcmd = command(original)
        newcmd = command(module)

        bb = root / 'BLACKBOX'
        scripts = bb / 'scripts'
        scripts.mkdir(parents=True)
        pack = bb / '契约' / '必读'
        pack.mkdir(parents=True)
        kernel = bb / '.cursor' / 'rules' / 'BLACKBOX_KERNEL_ALWAYS_APPLY.mdc'
        kernel.parent.mkdir(parents=True)
        kernel.write_bytes(b'kernel\n')
        files = {}
        for key, name in [('BOOTSTRAP', 'BLACKBOX_BOOTSTRAP_MUST_READ.md'),
                          ('DATA_ACCESS', 'BLACKBOX_DATA_ACCESS_MUST_READ.md')]:
            p = pack / name
            p.write_bytes(b'fixture\n')          # byte-exact: no newline translation
            files[key] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        manifest = {'files': files,
                    'kernel': {'sha256': hashlib.sha256(kernel.read_bytes()).hexdigest()}}
        mp = pack / 'MUST_READ_MANIFEST_CURRENT.json'
        mp.write_text(json.dumps(manifest), encoding='utf-8')

        stub = """import tempfile,hashlib
from pathlib import Path
PROBE_LOCATION=tempfile.gettempdir()
ROOT=Path(__file__).parent.parent
OK=0
FAIL=3
def read_text(path):return Path(path).read_text(encoding='utf-8')
def sha256_text(text):return hashlib.sha256(text.encode('utf-8')).hexdigest()
def set_runtime_context(**kwargs):pass
"""
        base = scripts / '_base.py'
        base.write_text(stub, encoding='utf-8')

        def run(cmd):
            cmd = list(cmd)
            cmd[-1] = str(scripts)
            return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                                  env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), timeout=60)

        before = run(oldcmd)
        assert before.returncode and 'No usable temporary directory' in before.stderr
        ok('original child reproduces real import-probe failure')

        after = run(newcmd)
        assert after.returncode == 0, after.stderr
        report = json.loads(after.stdout)
        assert report['ok'] and report['required'] == ['BOOTSTRAP', 'DATA_ACCESS']
        ok('fixed child runs actual successor preflight without bypass')

        mp.write_text(json.dumps({**manifest, 'kernel': {'sha256': None}}), encoding='utf-8')
        bad = run(newcmd)
        assert bad.returncode and 'SHA_AUTHORITY_MISSING_KERNEL' in bad.stdout
        ok('real preflight hash rejection retained')

        mp.write_text(json.dumps(manifest), encoding='utf-8')
        output = root / 'forbidden'
        base.write_text(stub + f"\nopen({str(output)!r},'w').write('bad')\n", encoding='utf-8')
        deny = run(newcmd)
        assert deny.returncode and 'WRITE_BLOCKED' in deny.stderr and not output.exists()
        ok('import-time write still denied')

        base.write_text(stub + "\nimport socket\nsocket.getaddrinfo('example.test',443)\n", encoding='utf-8')
        deny = run(newcmd)
        assert deny.returncode and 'SIDE_EFFECT_BLOCKED:socket.getaddrinfo' in deny.stderr
        ok('import-time network still denied before connection')

        base.write_text(stub + f"\nimport os\nos.mkdir({str(output)!r})\n", encoding='utf-8')
        deny = run(newcmd)
        assert deny.returncode and 'SIDE_EFFECT_BLOCKED:os.mkdir' in deny.stderr and not output.exists()
        ok('directory creation still denied')

    print(json.dumps({'status': 'PASS', 'controls_passed': len(controls), 'controls': controls,
                      'scope': 'ADDITIVE_WINDOWS_PORT_COMPLETION_OF_SUPPLIED_TEST; SUPPLIED_TEST_UNMODIFIED',
                      'supplied_test_pin': '875283920c519b7fa00d967335be563007e554b6990e3adb9bbadca14f274f8a',
                      'supplied_test_windows_failure': {
                          'control': 'fixed child runs actual successor preflight without bypass',
                          'type': 'FIXTURE_NEWLINE_PORTABILITY',
                          'expected_sha256_of_CRLF_bytes': '5bd17a4a66c4126008a147278511f1fb55774b443fa32bf571a0ffd5a8efc073',
                          'actual_sha256_of_LF_text': 'e80b71cd14d3cbd65f4173abcbfcf01a545dbca32a72d575108b553a648cc96f',
                          'real_preflight_reached_and_rejected': True},
                      'guard_write_exceptions': 0, 'supplier_calls': 0,
                      'FOUNDATION_ACCEPTANCE': False}, ensure_ascii=True))


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
