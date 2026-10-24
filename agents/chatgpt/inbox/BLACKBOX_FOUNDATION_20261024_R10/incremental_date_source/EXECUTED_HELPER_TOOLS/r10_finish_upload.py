import base64
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

DL = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_source_batch_chain_delivery')
REPO = 'zwdjwsam-creator/sam'
API = 'https://api.github.com/repos/' + REPO
DEST = 'agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/source_batch_chain'
NAME = 'FINAL_BYTE_READBACK.json'
tok = [l.strip() for l in open(r'C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT',
                               encoding='utf-8', errors='ignore')
       if l.strip().startswith(('gho_', 'ghp_', 'github_pat_', 'ghu_'))][0]
H = {'Authorization': 'Bearer ' + tok, 'Accept': 'application/vnd.github+json', 'User-Agent': 'BB'}


def req(method, url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    for i in range(6):
        try:
            r = urllib.request.Request(url, data=data, headers=H, method=method)
            return json.loads(urllib.request.urlopen(r, timeout=240).read() or b'{}')
        except urllib.error.HTTPError as e:
            if e.code in (404,):
                raise
            if i == 5:
                raise
            time.sleep(4)
        except Exception:
            if i == 5:
                raise
            time.sleep(4 + 3 * i)


def sha(b):
    return hashlib.sha256(b).hexdigest()


p = DL / NAME
local = p.read_bytes()
local_sha = sha(local)
url = API + '/contents/' + DEST + '/' + NAME

before = None
try:
    ex = req('GET', url + '?ref=main')
    before = {'found': True, 'sha': ex['sha'], 'size': ex['size']}
except urllib.error.HTTPError as e:
    before = {'found': False, 'http': e.code}

payload = {'message': 'R10: upload existing final byte readback receipt for source-batch chain',
           'content': base64.b64encode(local).decode(), 'branch': 'main'}
if before['found']:
    payload['sha'] = before['sha']
t_up = time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime())
r = req('PUT', url, payload)
t_up2 = time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime())

c = req('GET', url + '?ref=main')
if c.get('content'):
    remote = base64.b64decode(c['content'])
    via = 'contents_api_inline'
else:
    remote = base64.b64decode(req('GET', API + '/git/blobs/' + c['sha'])['content'])
    via = 'git_blobs_api'

out = {
    'schema': 'R10_SOURCE_BATCH_CHAIN_FINAL_RECEIPT_UPLOAD_READBACK_1',
    'note': 'uploads the ALREADY EXISTING local r10_source_batch_chain_delivery/FINAL_BYTE_READBACK.json; '
            'no time regenerated, no prior capture overwritten, no measurement or member upload repeated',
    'local_path': str(p), 'local_bytes': len(local), 'local_sha256': local_sha,
    'remote_path': DEST + '/' + NAME,
    'preexisting_remote': before,
    'upload_started_cn': t_up, 'upload_finished_cn': t_up2,
    'put_commit': r['commit']['sha'],
    'readback_cn': time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime()),
    'remote_size': c['size'], 'remote_sha256': sha(remote), 'git_blob_sha': c['sha'],
    'payload_via': via,
    'bytes_match': len(local) == c['size'], 'sha256_match': local_sha == sha(remote),
    'final_receipt_remotely_readable': True,
    'readback_payload_unchanged': json.loads(remote.decode('utf-8')).get('readback_cn'),
    'FOUNDATION_ACCEPTANCE': False, 'FORMAL_ENGINE_ADMISSION': False,
    'NEW_DATA_ACQUISITION_AUTHORIZED': False, 'CURRENT_SWITCH_ALLOWED': False, 'ORDER_ALLOWED': False}
o = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_incremental_date_source_delivery')
o.mkdir(parents=True, exist_ok=True)
(o / 'SOURCE_BATCH_CHAIN_FINAL_RECEIPT_UPLOAD.json').write_bytes(
    (json.dumps(out, indent=1, ensure_ascii=False) + '\n').encode('utf-8'))
print(json.dumps(out, indent=1, ensure_ascii=False))
