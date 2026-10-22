"""One existing-scheduler tick: fetch HUB, persist events, call local UI adapter.

No GUI code is embedded. A trusted sibling adapter must expose handle(event, mode)
and return status DELIVERED, QUEUED, UNCERTAIN or DEFERRED. VERIFY never types.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import subprocess
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

ROOTS = {'agents/chatgpt/outbox/': 'GPT_TO_CURSOR',
         'agents/chatgpt/reviews/': 'GPT_TO_CURSOR',
         'agents/chatgpt/inbox/': 'CURSOR_TO_GPT'}
NOTIFIER = ('LOCAL_AI_AUTODOCK', 'LOCAL_AI_GEMMA_DIRECT_OPERATOR',
            'LOCAL_AI_TWO_WINDOW_HUB_NOTIFIER', 'LOCAL_AI_HUB_TWO_SIGNAL_ONLY')

def stamp():
    return datetime.now(timezone.utc).isoformat()

def save(path, state):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.new')
    with tmp.open('w', encoding='utf-8') as file:
        json.dump(state, file, ensure_ascii=False, indent=2)
        file.flush(); os.fsync(file.fileno())
    os.replace(tmp, path)

@contextmanager
def single_instance(path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as file:
        file.seek(0, 2)
        if file.tell() == 0: file.write(b'0'); file.flush()
        file.seek(0)
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try: yield
        finally:
            file.seek(0)
            if os.name == 'nt': msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            else: fcntl.flock(file, fcntl.LOCK_UN)

def direction(path):
    return next((value for prefix, value in ROOTS.items() if path.startswith(prefix)), None)

def actionable(path):
    upper = path.upper(); basename = path.rsplit('/', 1)[-1].upper()
    if not direction(path) or Path(path).suffix.lower() not in {'.md', '.json'}: return False
    if any('/' + part + '/' in upper for part in ('SOURCE', 'EVIDENCE', 'LOGS', 'STATE')): return False
    if any(part in basename for part in ('PILOT_', 'ACK_', 'HEARTBEAT', 'RECEIPT', 'CURSOR_CLAIMED')): return False
    if basename.startswith('INBOX_FOR_') or basename == 'STATUS_PROGRESS.JSON': return False
    if direction(path) == 'CURSOR_TO_GPT' and any(part in upper for part in NOTIFIER): return False
    return True

def git_snapshot(repo):
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
    def git(*args):
        proc = subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                              env=env, timeout=90)
        # Do not expose remote URLs, credential helpers or stderr in evidence.
        if proc.returncode: raise RuntimeError('GIT_OPERATION_FAILED:' + args[0])
        return proc.stdout
    git('fetch', '--quiet', 'origin', 'main')
    commit = git('rev-parse', 'FETCH_HEAD').decode('ascii').strip()
    raw = git('ls-tree', '-r', '-z', commit, '--', *(x.rstrip('/') for x in ROOTS))
    files = {}
    for record in raw.split(b'\0'):
        if not record: continue
        metadata, path = record.split(b'\t', 1)
        mode, kind, sha = metadata.split(b' ')
        if kind == b'blob': files[path.decode('utf-8')] = sha.decode('ascii')
    return commit, files

def initialize(path, commit, files):
    if Path(path).exists(): raise RuntimeError('STATE_ALREADY_EXISTS_KEEP_HISTORY')
    state = {'schema': 1, 'created_at': stamp(), 'last_remote_commit': commit,
             'seen': files, 'queue': [], 'explicit_tests': [], 'cycles': []}
    save(path, state); return state

def tick(path, snapshot, adapter=None, send=False, test_event=None):
    path = Path(path)
    state = json.loads(path.read_text(encoding='utf-8-sig'))
    if state.get('schema') != 1: raise RuntimeError('STATE_SCHEMA_MISMATCH')
    # A remote failure leaves all event state untouched. Never treat failure as silence.
    commit, files = snapshot()
    if test_event and test_event not in files: raise RuntimeError('TEST_FILE_NOT_ON_REMOTE_MAIN')
    additions = []
    known = {(item['path'], item['blob_sha']) for group in state['queue'] for item in group['items']}
    for remote_path, sha in files.items():
        forced = remote_path == test_event
        event_key = remote_path + '|' + sha
        if forced:
            if event_key in state['explicit_tests']: continue
        elif not actionable(remote_path) or state['seen'].get(remote_path) == sha or (remote_path, sha) in known:
            continue
        event = {'path': remote_path, 'blob_sha': sha}
        additions.append((direction(remote_path), event, forced))
    for side in dict.fromkeys(ROOTS.values()):
        candidates = [(item, test) for value, item, test in additions if value == side]
        if not candidates: continue
        # One HUB for all new files in this direction. Never mutate an in-flight batch.
        group = next((g for g in state['queue'] if g['direction'] == side and g['status'] == 'READY'), None)
        if group is None:
            group = {'id': f"{commit}_{side}_{len(state['queue'])}", 'direction': side,
                     'status': 'READY', 'created_at': stamp(), 'body': 'HUB', 'items': []}
            state['queue'].append(group)
        existing = {(item['path'], item['blob_sha']) for item in group['items']}
        for item, forced in candidates:
            if (item['path'], item['blob_sha']) not in existing:
                group['items'].append(item); existing.add((item['path'], item['blob_sha']))
            if forced: state['explicit_tests'].append(item['path'] + '|' + item['blob_sha'])
    state['seen'] = files; state['last_remote_commit'] = commit
    save(path, state)  # queue and seen are ONE atomic transaction
    attempted = []
    if send:
        if adapter is None: raise RuntimeError('NO_LOCAL_UI_ADAPTER')
        for side in dict.fromkeys(ROOTS.values()):
            group = next((g for g in state['queue'] if g['direction'] == side and g['status'] != 'DELIVERED'), None)
            if group is None: continue
            mode = 'SUBMIT' if group['status'] == 'READY' else 'VERIFY'
            # Crash after this save can only VERIFY, never automatically submit again.
            group['status'] = 'SENDING' if mode == 'SUBMIT' else group['status']
            group['last_mode'] = mode; group['last_attempt_at'] = stamp(); save(path, state)
            try:
                result = adapter.handle(dict(group), mode)
                status = result.get('status', 'UNCERTAIN')
                if status not in {'DELIVERED', 'QUEUED', 'UNCERTAIN', 'DEFERRED'}: status = 'UNCERTAIN'
                # DEFERRED guarantees no input was typed/submitted. Once uncertain,
                # even a later DEFERRED result must NOT permit another SUBMIT.
                group['status'] = 'READY' if status == 'DEFERRED' and mode == 'SUBMIT' else ('UNCERTAIN' if status == 'DEFERRED' else status)
                group['last_result'] = result
            except Exception as error:
                group['status'] = 'UNCERTAIN'; group['last_result'] = {'status': 'UNCERTAIN', 'error_type': type(error).__name__}
            save(path, state); attempted.append({'direction': side, 'mode': mode, 'status': group['status']})
    cycle = {'at': stamp(), 'remote_commit': commit, 'new_objects': len(additions),
             'send_enabled': bool(send), 'attempted': attempted,
             'pending_batches': sum(g['status'] != 'DELIVERED' for g in state['queue'])}
    state['cycles'] = (state['cycles'] + [cycle])[-5000:]; save(path, state)
    return cycle

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True, type=Path)
    ap.add_argument('--state', type=Path, default=Path(__file__).resolve().parent/'state'/'autodock_remote.json')
    ap.add_argument('--init', action='store_true')
    ap.add_argument('--adapter', type=Path)
    ap.add_argument('--send', action='store_true')
    ap.add_argument('--test-event', help='One existing remote file, explicitly allowed once despite pilot/self-report filters')
    args = ap.parse_args()
    with single_instance(args.state.with_suffix('.lock')):
        if args.init:
            commit, files = git_snapshot(args.repo)
            initialize(args.state, commit, files)
            print(json.dumps({'status':'BASELINE_INITIALIZED_NO_GUI_ACTION','remote_commit':commit,'objects':len(files)})); return
        adapter = None
        if args.send:
            if not args.adapter: ap.error('--send requires --adapter')
            spec = importlib.util.spec_from_file_location('trusted_local_ui_adapter', args.adapter)
            adapter = importlib.util.module_from_spec(spec); spec.loader.exec_module(adapter)
        result = tick(args.state, lambda: git_snapshot(args.repo), adapter, args.send, args.test_event)
        print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__': main()
