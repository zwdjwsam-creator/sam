import json
from pathlib import Path

DL = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_source_batch_chain_delivery')
j = json.loads((DL / 'captures/DESKTOP_SOURCE_BATCHES.stdout.bin').read_bytes().decode('utf-8-sig'))

print('real_preflight ok', j['real_preflight']['ok'], j['real_preflight']['MUST_READ_PRECHECK'])
print('universe_metadata', json.dumps(j['universe_metadata'], ensure_ascii=False)[:600])
print('download_state_metadata', json.dumps(j['download_state_metadata'], ensure_ascii=False))
print()
print('=== batches: identity tally ===')
tally = {}
for b in j['batch_observations']:
    tally[b['identity']] = tally.get(b['identity'], 0) + 1
print(tally)
print('total batches', len(j['batch_observations']))
print('empty batches', sum(1 for b in j['batch_observations'] if b['empty']))
print('total rows', sum(b['rows'] for b in j['batch_observations']))
print('distinct shas', len({b['sha256'] for b in j['batch_observations']}))
side = {}
for b in j['batch_observations']:
    side[b['identity']] = side.get(b['identity'], 0) + (1 if b.get('sidecar_sha256') else 0)
print('with sidecar hash by identity', side)
print()
print('=== per-year source vs Cleaning ===')
tot = {}
for y in j['year_results']:
    extra = {k: v for k, v in y.items()
             if k not in ('year', 'source_rows', 'clean_rows', 'source_only_keys', 'clean_only_keys',
                          'shared_keys', 'unequal_shared_values', 'unequal_sample', 'clean_sha256')}
    print(f"{y['year']} src={y['source_rows']:>9} clean={y['clean_rows']:>9} "
          f"src_only={y['source_only_keys']:>7} clean_only={y['clean_only_keys']:>7} "
          f"shared={y['shared_keys']:>9} unequal={y['unequal_shared_values']:>7}"
          + (f" EXTRA={json.dumps(extra, ensure_ascii=False, default=str)[:300]}" if extra else ''))
    for k in ('source_rows', 'clean_rows', 'source_only_keys', 'clean_only_keys', 'shared_keys',
              'unequal_shared_values'):
        tot[k] = tot.get(k, 0) + y[k]
print('TOTAL', tot)
print()
print('=== sample batches (first 6) ===')
for b in j['batch_observations'][:6]:
    print(json.dumps(b, ensure_ascii=False)[:400])
print()
print('=== unequal samples (first 3 years with any) ===')
n = 0
for y in j['year_results']:
    if y['unequal_shared_values'] and n < 3:
        print(y['year'], json.dumps(y['unequal_sample'], ensure_ascii=False)[:500])
        n += 1
