import json
from pathlib import Path

DL = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_source_batch_chain_delivery')
j = json.loads((DL / 'captures/DESKTOP_SOURCE_BATCHES.stdout.bin').read_bytes().decode('utf-8-sig'))
b0 = j['batch_observations'][0]
print('batch keys:', list(b0))
print(json.dumps(b0, ensure_ascii=False, indent=1)[:1800])
print()
empties = [(Path(b['path']).parent.name, Path(b['path']).name, b['rows'], b['bytes']) for b in j['batch_observations'] if b['empty']]
print('empty batches', len(empties))
for e in empties:
    print('  ', e)
print()
side = {}
for b in j['batch_observations']:
    if 'sidecar_agreement' in b:
        side[str(b['sidecar_agreement'])] = side.get(str(b['sidecar_agreement']), 0) + 1
print('sidecar_agreement tally', side)
print('real_preflight:', json.dumps({k: v for k, v in j['real_preflight'].items() if k != 'preflight_block'}, ensure_ascii=False)[:800])
print('preflight argv/exit:', j['preflight']['argv'], j['preflight']['exit_code'])
print('year_result keys:', list(j['year_results'][0]))
