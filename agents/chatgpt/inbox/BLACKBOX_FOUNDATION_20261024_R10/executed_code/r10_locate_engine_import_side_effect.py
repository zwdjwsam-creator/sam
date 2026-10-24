"""ADDITIVE R10 diagnostic: locate the source frame of the blocked import side effect.

The supplied engine_import_probe_r10.py reports only the audit event name (`os.mkdir`).
This harness re-runs the same guarded import in a child and records WHERE the attempt
came from. It does not relax, reorder or bypass any denial: the guard still raises
PermissionError for the same events, still blocks writes/network/credentials, still
forbids business calls and engine construction, and no package is installed.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

PROBE_DIR = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\reviews\R10\operating_entry')
ROOT = Path(r'E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine')


def child(root):
    import contextlib
    import tempfile
    import traceback

    root = Path(root).resolve()
    tempfile.tempdir = str(root)
    blocked = []
    locations = []

    def guard(event, args):
        if event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo', 'subprocess.Popen',
                     'os.system', 'os.remove', 'os.rename', 'os.mkdir', 'os.rmdir', 'os.truncate',
                     'os.link', 'os.symlink'):
            blocked.append({'event': event, 'arg0': os.fsdecode(args[0]) if args and isinstance(args[0], (str, bytes)) else None})
            stack = traceback.extract_stack()
            inside = [f for f in stack if 'bullet_trade' in f.filename.replace('\\', '/') or 'jqdata' in Path(f.filename).name]
            if inside:
                locations.append({'event': event, 'frames': [
                    {'file': f.filename, 'line': f.lineno, 'function': f.name, 'source': (f.line or '').strip()}
                    for f in inside[-4:]]})
            raise PermissionError('ENGINE_IMPORT_SIDE_EFFECT_BLOCKED')

    def guard_open(event, args):
        path, mode, flags = args
        flags = flags or 0
        if isinstance(path, (str, bytes)):
            text = os.fsdecode(path).replace('\\', '/').lower()
            if '/secrets/' in text or text.endswith('/.env'):
                blocked.append({'event': 'credential_file_read', 'arg0': text})
                raise PermissionError('CREDENTIAL_READ_BLOCKED')
        if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or flags & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            blocked.append({'event': 'file_write', 'arg0': os.fsdecode(path) if isinstance(path, (str, bytes)) else None})
            raise PermissionError('ENGINE_IMPORT_WRITE_BLOCKED')

    def audit(event, args):
        guard(event, args)
        if event == 'open':
            guard_open(event, args)

    with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(root))
        sys.addaudithook(audit)
        try:
            import importlib
            for name in ('bullet_trade', 'bullet_trade.core.engine', 'bullet_trade.data.api',
                         'bullet_trade.data.providers.base'):
                importlib.import_module(name)
            outcome = 'IMPORT_COMPLETED'
        except BaseException as exc:
            outcome = 'IMPORT_STOPPED:' + type(exc).__name__
            locations.append({'event': 'import_stop', 'frames': [
                {'file': f.filename, 'line': f.lineno, 'function': f.name, 'source': (f.line or '').strip()}
                for f in traceback.extract_tb(exc.__traceback__)[-4:]]})
    return {'outcome': outcome, 'blocked_events': blocked, 'locations': locations}


def main():
    env = {k: v for k, v in os.environ.items()
           if k.upper() in {'SYSTEMROOT', 'WINDIR', 'PATH', 'PATHEXT', 'TEMP', 'TMP', 'LANG', 'LC_ALL'}}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONNOUSERSITE='1')
    p = subprocess.run([sys.executable, '-X', 'utf8', str(Path(__file__).resolve()), '--child', str(ROOT)],
                       capture_output=True, text=True, encoding='utf-8', env=env,
                       cwd=str(PROBE_DIR), timeout=90)
    if p.returncode != 0:
        print(json.dumps({'status': 'CHILD_EXIT_WITHOUT_RECEIPT', 'exit_code': p.returncode,
                          'stderr_tail': p.stderr[-1500:]}, ensure_ascii=True))
        return
    inner = json.loads(p.stdout)
    print(json.dumps({'status': 'ENGINE_IMPORT_SIDE_EFFECT_LOCATED', **inner,
                      'guard_relaxed': False, 'packages_installed': 0, 'engine_constructed': False,
                      'network_used': False, 'FOUNDATION_ACCEPTANCE': False, 'ORDER_ALLOWED': False},
                     ensure_ascii=True))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--child':
        print(json.dumps(child(sys.argv[2]), ensure_ascii=True))
    else:
        main()
