"""Bounded, read-only source search. Never imports or executes producer code."""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

sys.dont_write_bytecode = True
WORK = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
ROOTS = [Path(r'E:\BLACKBOX\脚本'), Path(r'E:\BLACKBOX\任务')]
SKIP = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', 'staging', 'data',
        '数据', 'releases', 'runtime', 'captures', 'secrets', '配置', '_ops',
        'source_batches', 'backup', 'backups', 'archive', 'archives'}
LIMITS = {'directories': 3000, 'files': 20000, 'bytes': 100 * 1024 * 1024,
          'file_bytes': 2 * 1024 * 1024, 'depth': 6, 'candidates': 40}
ENTRY_SHA = '1b04bb3a373e2a4276563c62c2514905dde49910f69e519e8b3626090ef18ec9'
FALSE = {k: False for k in ('FOUNDATION_ACCEPTANCE', 'FORMAL_ENGINE_ADMISSION',
        'NEW_DATA_ACQUISITION_AUTHORIZED', 'CURRENT_SWITCH_ALLOWED', 'ORDER_ALLOWED',
        'SOURCE_ABSENCE_CLAIM_ALLOWED')}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def guard(event, args):
    if event in ('socket.connect', 'socket.connect_ex', 'socket.getaddrinfo',
                 'subprocess.Popen', 'os.system', 'os.mkdir', 'os.remove',
                 'os.rename', 'os.rmdir', 'os.link', 'os.symlink', 'os.truncate'):
        raise PermissionError('SOURCE_SEARCH_SIDE_EFFECT_FORBIDDEN')
    if event == 'open':
        path, mode, flags = args
        if (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (flags or 0) & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise PermissionError('SOURCE_SEARCH_WRITE_FORBIDDEN')

def scan():
    result = {'roots': list(map(str, ROOTS)), 'limits': LIMITS,
              'directories': 0, 'files': 0, 'bytes': 0, 'candidates': [],
              'skipped': [], 'errors': [], 'source_absence_claim': False}
    stack = [(r, 0) for r in reversed(ROOTS)]
    while stack:
        directory, depth = stack.pop()
        result['directories'] += 1
        if result['directories'] > LIMITS['directories']:
            raise ValueError('DIRECTORY_SEARCH_CAP')
        try:
            with os.scandir(directory) as items:
                for item in items:
                    st = item.stat(follow_symlinks=False)
                    if getattr(st, 'st_file_attributes', 0) & 0x400 or item.is_symlink():
                        result['skipped'].append({'path': item.path, 'reason': 'REPARSE_OR_SYMLINK'})
                        continue
                    if item.is_dir(follow_symlinks=False):
                        if item.name.lower() in SKIP or depth >= LIMITS['depth']:
                            result['skipped'].append({'path': item.path, 'reason': 'EXCLUDED_OR_DEPTH_BOUND'})
                        else:
                            stack.append((Path(item.path), depth + 1))
                        continue
                    if not item.is_file(follow_symlinks=False) or Path(item.name).suffix.lower() not in ('.py', '.ps1'):
                        continue
                    result['files'] += 1
                    if result['files'] > LIMITS['files']:
                        raise ValueError('FILE_SEARCH_CAP')
                    if st.st_size > LIMITS['file_bytes']:
                        result['skipped'].append({'path': item.path, 'reason': 'FILE_SIZE_BOUND'})
                        continue
                    data = Path(item.path).read_bytes()
                    result['bytes'] += len(data)
                    if result['bytes'] > LIMITS['bytes']:
                        raise ValueError('TOTAL_SOURCE_BYTES_CAP')
                    # No code text or credential values are emitted. Original encoding is retained.
                    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
                        text = data.decode('utf-16')
                    else:
                        text = data.decode('utf-8-sig', errors='replace')
                    lowered = text.lower()
                    factor = 'adjust_factor' in lowered or ('factor' in lowered and 'get_price' in lowered)
                    incremental = 'incremental' in lowered or '增量' in text
                    writer = any(x in lowered for x in ('to_parquet', 'save_parquet', 'write_parquet'))
                    if factor and incremental and writer:
                        if len(result['candidates']) >= LIMITS['candidates']:
                            raise ValueError('CANDIDATE_SEARCH_CAP')
                        if Path(item.path).read_bytes() != data:
                            raise ValueError('SOURCE_CHANGED_DURING_READ')
                        result['candidates'].append({'path': item.path, 'bytes': len(data),
                            'sha256': digest(data), 'identity': 'NEW_MEASURED_SOURCE_CANDIDATE',
                            'matched': ['factor', 'incremental', 'parquet_writer']})
        except OSError as exc:
            result['errors'].append({'path': str(directory), 'error_type': type(exc).__name__})
    result['status'] = 'BOUNDED_SOURCE_CANDIDATES_MEASURED'
    result['interpretation'] = 'Text candidates only; no producer identity, execution, coverage or source-absence conclusion.'
    return result

def desktop():
    if os.name != 'nt' or socket.gethostname().upper() != 'ZHANGWEI':
        raise ValueError('WRONG_EXECUTION_HOST')
    if Path(sys.executable).resolve() != (WORK / 'runtime/.venv/Scripts/python.exe').resolve():
        raise ValueError('WRONG_RUNTIME')
    entry = WORK / 'reviews/R10/operating_entry/blackbox_operate_r10.py'
    if digest(entry.read_bytes()) != ENTRY_SHA:
        raise ValueError('OPERATING_ENTRY_PIN_CHANGED')
    argv = [sys.executable, '-X', 'utf8', str(entry), 'describe', '--product', 'ADJUST_FACTOR_PIT_R1']
    env = os.environ.copy(); env.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    p = subprocess.run(argv, cwd=WORK, env=env, capture_output=True, timeout=60)
    capture = {'argv': argv, 'exit_code': p.returncode,
               'stdout_base64': base64.b64encode(p.stdout).decode(),
               'stderr_base64': base64.b64encode(p.stderr).decode()}
    if p.returncode:
        return {'status': 'STOP_PREFLIGHT', 'preflight': capture, **FALSE}
    pf = json.loads(p.stdout.decode('utf-8-sig')).get('real_preflight', {})
    if pf.get('ok') is not True or pf.get('MUST_READ_PRECHECK') != 'PASS':
        return {'status': 'STOP_PREFLIGHT', 'preflight': capture, **FALSE}
    sys.addaudithook(guard)
    return {**scan(), 'preflight': capture, 'supplier_calls': 0, **FALSE}

if __name__ == '__main__':
    if sys.argv[1:] != ['--desktop-check']:
        raise SystemExit('ONLY --desktop-check IS SUPPORTED')
    try:
        out = desktop()
        print(json.dumps(out, ensure_ascii=True))
        raise SystemExit(0 if out['status'] == 'BOUNDED_SOURCE_CANDIDATES_MEASURED' else 3)
    except Exception as exc:
        print(json.dumps({'status': 'STOP', 'reason': str(exc) if isinstance(exc, ValueError)
                          else type(exc).__name__, **FALSE}))
        raise SystemExit(3)
