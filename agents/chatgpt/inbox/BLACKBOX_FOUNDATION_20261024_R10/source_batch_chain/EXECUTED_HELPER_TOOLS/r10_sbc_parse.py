import json
from pathlib import Path

DL = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\r10_source_batch_chain_delivery')
raw = (DL / 'captures/DESKTOP_SOURCE_BATCHES.stdout.bin').read_bytes()
j = json.loads(raw.decode('utf-8-sig'))
print('status', j['status'])
for k, v in j.items():
    if isinstance(v, list):
        print(f'  list {k} len={len(v)}', (list(v[0].keys())[:14] if v and isinstance(v[0], dict) else ''))
    elif isinstance(v, dict):
        print(f'  dict {k} len={len(v)}', list(v)[:14])
    else:
        print(f'  scalar {k} = {str(v)[:170]}')
