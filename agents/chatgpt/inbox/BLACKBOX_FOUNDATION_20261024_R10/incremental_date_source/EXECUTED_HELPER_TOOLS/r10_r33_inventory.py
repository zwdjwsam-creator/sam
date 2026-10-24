import json
from pathlib import Path

W = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
DL = W / 'r10_incremental_date_source_delivery'
RAW = Path(r'E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P1_adjust_factor')
R33 = Path(r'E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439\standard\reference\adjust_factor')

raws = [
    ('adjust_factor_stock__incremental_20260831__20260831_163108.parquet',
     'e8f16f6dda011907c598ae3a7b91b752d3a16f6135dd1b4f8773894aba142fec'),
    ('adjust_factor_stock__incremental_20260901__20260901_171005.parquet',
     'fb127145b83a2b43fc392b4e9a0ff42ec7236c2a73527de781cc149be8ccc289'),
    ('adjust_factor_stock__incremental_20260924__20260925_030214.parquet',
     '59ca656ea171c198f4dbf238c3d39b69481b02ae563c6a8421934b3fddc7cac6'),
]

import hashlib


def sha(b):
    return hashlib.sha256(b).hexdigest()


# bounded, non-recursive enumeration of the declared R33 product directory only
MAX_ENTRIES, MAX_PARQUET = 256, 64
entries = []
if R33.exists():
    for i, x in enumerate(R33.iterdir()):
        if i >= MAX_ENTRIES:
            break
        entries.append(x)
entries = sorted(entries, key=lambda p: p.name)
parq = [p for p in entries if p.is_file() and p.suffix.lower() == '.parquet'][:MAX_PARQUET]
inv = {'schema': 'R10_R33_ADJUST_FACTOR_BOUNDED_INVENTORY_1',
       'root': str(R33), 'root_exists': R33.exists(),
       'limits': {'max_entries': MAX_ENTRIES, 'max_parquet': MAX_PARQUET},
       'entry_count_observed': len(entries),
       'parquet_count_observed': len(parq),
       'non_parquet_entries': [p.name for p in entries if not (p.is_file() and p.suffix.lower() == '.parquet')],
       'reparse_points': [p.name for p in entries if p.is_symlink()],
       'recursive': False,
       'files': [{'name': p.name, 'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())}
                 for p in parq]}
(DL / 'R33_BOUNDED_INVENTORY.json').write_bytes((json.dumps(inv, indent=1, ensure_ascii=False) + '\n').encode())
print('R33 entries', inv['entry_count_observed'], 'parquet', inv['parquet_count_observed'],
      'nonparquet', inv['non_parquet_entries'])

spec = {'targets': [{'path': str(RAW / n), 'sha256': s} for n, s in raws]
                  + [{'path': f['path'], 'sha256': f['sha256']} for f in inv['files']],
        'out': str(DL / 'SCHEMA_EXAMINATION.json')}
(W / 'tools/schema_spec.json').write_bytes((json.dumps(spec, indent=1, ensure_ascii=False) + '\n').encode())
print('targets', len(spec['targets']))
