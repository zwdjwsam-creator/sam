import base64
import hashlib
import json
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

W = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
DL = W / 'r10_source_batch_chain_delivery'
REPO = 'zwdjwsam-creator/sam'
DEST = 'agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/source_batch_chain'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime())


tok = [l.strip() for l in open(r'C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT',
                               encoding='utf-8', errors='ignore')
       if l.strip().startswith(('gho_', 'ghp_', 'github_pat_', 'ghu_'))][0]
H = {'Authorization': 'Bearer ' + tok, 'Accept': 'application/vnd.github+json', 'User-Agent': 'BB'}
API = 'https://api.github.com/repos/' + REPO


def req(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    for i in range(6):
        try:
            r = urllib.request.Request(url, data=data, headers=H, method=method)
            return json.loads(urllib.request.urlopen(r, timeout=240).read() or b'{}')
        except urllib.error.HTTPError as e:
            if e.code in (409, 422) and i < 3:
                time.sleep(3)
                continue
            raise
        except Exception:
            if i == 5:
                raise
            time.sleep(3 + 3 * i)


# rename prior index snapshot
old = DL / 'INBOX_EXISTING.md'
new = DL / 'INBOX_FOR_CHATGPT_PRIOR_BYTES.md'
if old.exists():
    old.replace(new)

# helper tools used this round
TOOLS = DL / 'EXECUTED_HELPER_TOOLS'
TOOLS.mkdir(exist_ok=True)
for n in ('r10_sbc_stage.py', 'r10_sbc_parse.py', 'r10_sbc_summary.py', 'r10_sbc_detail.py',
          'r10_sbc_build.py', 'r10_sbc_manifest_upload.py'):
    p = W / 'tools' / n
    if p.exists():
        shutil.copyfile(p, TOOLS / n)

members = sorted([p for p in DL.rglob('*')
                  if p.is_file() and p.name not in ('DELIVERY_MANIFEST.json',
                                                    'FINAL_BYTE_READBACK.json')])
man = {'schema': 'R10_SOURCE_BATCH_CHAIN_DELIVERY_MANIFEST_1',
       'round': 'R10_SOURCE_BATCH_CHAIN_20261025',
       'built_cn': now(),
       'excludes': ['DELIVERY_MANIFEST.json (this file)', 'FINAL_BYTE_READBACK.json (written after upload)'],
       'parquet_uploaded': False,
       'members': [{'path': str(p.relative_to(DL)), 'bytes': p.stat().st_size,
                    'sha256': sha(p.read_bytes())} for p in members],
       'FOUNDATION_ACCEPTANCE': False, 'FORMAL_ENGINE_ADMISSION': False,
       'NEW_DATA_ACQUISITION_AUTHORIZED': False, 'CURRENT_SWITCH_ALLOWED': False,
       'ORDER_ALLOWED': False}
(DL / 'DELIVERY_MANIFEST.json').write_bytes((json.dumps(man, indent=1, ensure_ascii=False) + '\n').encode())
print('manifest members', len(man['members']))

# single upload cycle
upload_win = [now()]
files = sorted([p for p in DL.rglob('*') if p.is_file()])
log = []
for p in files:
    rel = str(p.relative_to(DL)).replace('\\', '/')
    url = API + '/contents/' + DEST + '/' + rel
    body = {'message': 'R10: deliver declared source-batch chain evidence (' + rel + ')',
            'content': base64.b64encode(p.read_bytes()).decode(), 'branch': 'main'}
    try:
        ex = req('GET', url + '?ref=main')
        body['sha'] = ex['sha']
        act = 'UPDATE'
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        act = 'CREATE'
    r = req('PUT', url, body)
    log.append({'path': rel, 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes()),
                'action': act, 'commit': r['commit']['sha']})
    print(act, rel, p.stat().st_size)
upload_win.append(now())

# separate final byte readback
rb = []
for p in files:
    rel = str(p.relative_to(DL)).replace('\\', '/')
    local = p.read_bytes()
    c = req('GET', API + '/contents/' + DEST + '/' + rel + '?ref=main')
    if c.get('content'):
        remote = base64.b64decode(c['content'])
        via = 'contents_api_inline'
    else:
        b = req('GET', API + '/git/blobs/' + c['sha'])
        remote = base64.b64decode(b['content'])
        via = 'git_blobs_api'
    rb.append({'path': rel, 'local_bytes': len(local), 'remote_bytes': c['size'],
               'local_sha256': sha(local), 'remote_sha256': sha(remote),
               'git_blob_sha': c['sha'], 'payload_via': via,
               'bytes_match': len(local) == c['size'], 'sha256_match': sha(local) == sha(remote)})

out = {'schema': 'R10_SOURCE_BATCH_CHAIN_FINAL_BYTE_READBACK_1',
       'repo': REPO, 'dest': DEST, 'dir_url': 'https://github.com/' + REPO + '/tree/main/' + DEST,
       'readback_cn': now(), 'single_upload_cycle': {'started_cn': upload_win[0], 'finished_cn': upload_win[1]},
       'files_uploaded': len(log), 'commit_log': log,
       'members_verified': len(rb), 'all_bytes_match': all(x['bytes_match'] for x in rb),
       'all_sha256_match': all(x['sha256_match'] for x in rb),
       'manifest_sha256': sha((DL / 'DELIVERY_MANIFEST.json').read_bytes()),
       'parquet_uploaded': False, 'second_upload_cycle': False,
       'readback': rb,
       'FOUNDATION_ACCEPTANCE': False, 'FORMAL_ENGINE_ADMISSION': False,
       'NEW_DATA_ACQUISITION_AUTHORIZED': False, 'CURRENT_SWITCH_ALLOWED': False,
       'ORDER_ALLOWED': False}
(DL / 'FINAL_BYTE_READBACK.json').write_bytes((json.dumps(out, indent=1, ensure_ascii=False) + '\n').encode())
print('READBACK', out['members_verified'], 'all_sha_match', out['all_sha256_match'],
      'all_bytes', out['all_bytes_match'])
