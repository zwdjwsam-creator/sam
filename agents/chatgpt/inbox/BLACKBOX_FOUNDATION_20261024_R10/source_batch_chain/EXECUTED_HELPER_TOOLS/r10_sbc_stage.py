import hashlib
import json
import shutil
import time
from pathlib import Path

W = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
SRC = W / 'reviews/R10/source_batch_chain_20261025'
STG = W / 'reviews/R10/source_batch_chain'
DL = W / 'r10_source_batch_chain_delivery'
STG.mkdir(parents=True, exist_ok=True)
(DL / 'captures').mkdir(parents=True, exist_ok=True)


def sha(b):
    return hashlib.sha256(b).hexdigest()


t0 = time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime())
pkg = json.loads((SRC / 'PACKAGE.json').read_text(encoding='utf-8'))
# copy manifest FIRST so it is present before execution
shutil.copyfile(SRC / 'PACKAGE.json', STG / 'PACKAGE.json')
for e in pkg['files']:
    shutil.copyfile(SRC / e['path'], STG / e['path'])

checks, allok = [], True
for e in pkg['files']:
    b = (STG / e['path']).read_bytes()
    ok = len(b) == e['bytes'] and sha(b) == e['sha256']
    allok &= ok
    checks.append({'path': e['path'], 'declared_bytes': e['bytes'], 'actual_bytes': len(b),
                   'declared_sha256': e['sha256'], 'actual_sha256': sha(b),
                   'bytes_match': len(b) == e['bytes'], 'sha256_match': sha(b) == e['sha256'], 'ok': ok})
mp = STG / 'PACKAGE.json'
mb = mp.read_bytes()
man_ok = mb == (SRC / 'PACKAGE.json').read_bytes()
allok &= man_ok

out = {'schema': 'R10_SOURCE_BATCH_CHAIN_PRE_EXECUTION_PIN_CHECK_1',
       'checked_at_cn_start': t0,
       'checked_at_cn_end': time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime()),
       'stage_dir': str(STG),
       'manifest_present_before_execution': mp.exists(),
       'manifest_bytes': len(mb), 'manifest_sha256': sha(mb),
       'manifest_byte_identical_to_supplied': man_ok,
       'rule': 'exact byte count AND exact SHA256 for every PACKAGE member, and PACKAGE.json itself present and '
               'byte-identical to the supplied copy BEFORE any control runs',
       'all_pins_match': allok, 'stop_triggered': not allok, 'files': checks,
       'no_substitute_harness': True, 'no_repinning': True,
       'line_endings_preserved': {c['path']: (STG / c['path']).read_bytes().count(b'\r\n') for c in checks},
       'staged_ctimes_utc': {p.name: time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(p.stat().st_ctime))
                             for p in sorted(STG.iterdir()) if p.is_file()}}
(DL / 'PRE_EXECUTION_PIN_CHECK.json').write_bytes(
    (json.dumps(out, indent=1, ensure_ascii=False) + '\n').encode('utf-8'))
print('all_pins_match', allok, 'manifest_present', mp.exists(), len(mb), sha(mb)[:16])
for c in checks:
    print(('OK  ' if c['ok'] else 'BAD '), c['path'], c['actual_bytes'], c['actual_sha256'][:16])
