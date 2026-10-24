import csv
import hashlib
import json
import shutil
import time
from pathlib import Path

W = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
SRC = W / 'reviews/R10/source_batch_chain_20261025'
STG = W / 'reviews/R10/source_batch_chain'
DL = W / 'r10_source_batch_chain_delivery'
CAP = DL / 'captures'
SUP = DL / 'SUPPLIED_SOURCES'
MET = DL / 'METADATA_ORIGINAL'
for d in (SUP, MET):
    d.mkdir(parents=True, exist_ok=True)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%S+08:00', time.localtime())


j = json.loads((CAP / 'DESKTOP_SOURCE_BATCHES.stdout.bin').read_bytes().decode('utf-8-sig'))
pkg = json.loads((SRC / 'PACKAGE.json').read_text(encoding='utf-8'))

# supplied sources, exact bytes
for e in pkg['files']:
    shutil.copyfile(SRC / e['path'], SUP / e['path'])
shutil.copyfile(SRC / 'PACKAGE.json', SUP / 'PACKAGE.json')
sup_ids = []
for p in sorted(SUP.iterdir()):
    b = p.read_bytes()
    sup_ids.append({'path': 'SUPPLIED_SOURCES/' + p.name, 'bytes': len(b), 'sha256': sha(b)})

# exact driver output (same bytes as the raw capture)
shutil.copyfile(CAP / 'DESKTOP_SOURCE_BATCHES.stdout.bin', DL / 'DRIVER_OUTPUT.json')

# original metadata bytes read by the driver, re-read by exact path only
T = Path(r'E:\BLACKBOX\任务\BLACKBOX_ADJUST_FACTOR_PIT_R1_FULL_REBUILD_AND_BACKWARD_REFRESH_R1\staging')
meta_ids = []
for n in ('UNIVERSE.json', 'DOWNLOAD_STATE.json'):
    b = (T / n).read_bytes()
    (MET / n).write_bytes(b)
    meta_ids.append({'path': 'METADATA_ORIGINAL/' + n, 'bytes': len(b), 'sha256': sha(b),
                     'crlf_count': b.count(b'\r\n'), 'lf_only': b.count(b'\n') - b.count(b'\r\n')})

# CSVs
with (DL / 'BATCH_OBSERVATIONS.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['year_dir', 'batch_file', 'rows', 'empty', 'bytes', 'sha256', 'sidecar_sha256', 'identity'])
    for b in j['batch_observations']:
        pp = Path(b['path'])
        w.writerow([pp.parent.name, pp.name, b['rows'], b['empty'], b['bytes'], b['sha256'],
                    b['sidecar_sha256'], b['identity']])
with (DL / 'YEAR_RESULTS.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['year', 'source_rows', 'clean_rows', 'source_only_keys', 'clean_only_keys',
                'shared_keys', 'unequal_shared_values', 'clean_sha256'])
    for y in j['year_results']:
        w.writerow([y['year'], y['source_rows'], y['clean_rows'], y['source_only_keys'],
                    y['clean_only_keys'], y['shared_keys'], y['unequal_shared_values'],
                    y['clean_sha256']])

empty = [b for b in j['batch_observations'] if b['empty']]
tot = {k: sum(y[k] for y in j['year_results'])
       for k in ('source_rows', 'clean_rows', 'source_only_keys', 'clean_only_keys',
                 'shared_keys', 'unequal_shared_values')}
summary = {
    'status': j['status'],
    'batch_files': len(j['batch_observations']),
    'sidecar_files': sum(1 for b in j['batch_observations'] if b['sidecar_sha256']),
    'batch_count_per_year': j['batch_count_per_year'],
    'years': len(j['year_results']),
    'total_rows': tot['source_rows'],
    'empty_batches': len(empty),
    'empty_batch_files': [Path(b['path']).parent.name + '/' + Path(b['path']).name for b in empty],
    'empty_batch_bytes': sorted({b['bytes'] for b in empty}),
    'distinct_parquet_sha256': len({b['sha256'] for b in j['batch_observations']}),
    'totals': tot,
    'exact_key_and_value_identity_all_years': (
        tot['source_only_keys'] == 0 and tot['clean_only_keys'] == 0
        and tot['unequal_shared_values'] == 0),
    'source_scope_end': j['source_scope_end'],
    'source_files_changed': j['source_files_changed'],
    'supplier_calls': j['supplier_calls'],
    'all_layer_search_performed': j['all_layer_search_performed'],
    'B1_CLOSED': j['B1_CLOSED'],
}
(DL / 'MEASUREMENT_SUMMARY.json').write_bytes(
    (json.dumps(summary, indent=1, ensure_ascii=False) + '\n').encode('utf-8'))

corr = {
    'schema': 'R10_SOURCE_BATCH_CHAIN_CORRECTIONS_APPEND_ONLY_1',
    'rows': [
        {'id': 'C1', 'type': 'SEQUENCING_DISCLOSURE',
         'text': 'Order executed exactly as instructed: pre-execution byte/SHA pin check, then the single 8-control '
                 'run, then one --desktop-check. No member was re-pinned and no second driver run was made. '
                 'PACKAGE.json was placed in the stage directory before any execution, so no staging-incomplete '
                 'stopped attempt occurred in this round (unlike the prior dirty_branch round).'},
        {'id': 'C2', 'type': 'READ_SCOPE_DISCLOSURE',
         'text': 'The fixed driver read UNIVERSE.json and DOWNLOAD_STATE.json and reported only parsed metadata. '
                 'Those two exact paths were then re-read read-only by this executor solely to satisfy the '
                 'instruction to deliver the original metadata bytes. No directory was enumerated for that step, '
                 'no other file was opened, and no value was recomputed or repaired.'},
        {'id': 'C3', 'type': 'PRIOR_DELIVERY_REUSE',
         'text': 'The dirty_branch final upload/readback had already been completed under '
                 'r10_dirty_branch_delivery/FINAL_BYTE_READBACK.json; it was reused and not re-uploaded. '
                 'No dirty_branch measurement, old-writer run, 13-year Cleaning-vs-CACHE comparison, catalog '
                 'inventory or original-source lookup was repeated here.'},
        {'id': 'C4', 'type': 'SIDECAR_AGREEMENT_BASIS',
         'text': 'The driver does not emit a per-batch sidecar agreement flag; validate_batch raises and the run '
                 'would have exited 3 with status STOP on any count/bound/fq/sidecar conflict. A MEASURED result '
                 'therefore means every one of the 182 sidecars agreed within the driver contract. This is a '
                 'control-flow property of the supplied code, not an additional independent assertion.'},
        {'id': 'C5', 'type': 'EMPTY_BATCH_INTERPRETATION',
         'text': '15 of 182 batch parquet files are empty (1,851 B, identical bytes, years 2014-2018, batch indices '
                 '006/012/013). They were measured as empty, not rejected, and Cleaning has no keys in those ranges '
                 '(clean_only_keys=0 everywhere). Empty is measurable-but-not-complete; no cause is asserted here.'},
        {'id': 'C6', 'type': 'SCOPE_BOUNDARY',
         'text': 'Key and value identity holds only inside the declared request window ending 2026-08-14. It does '
                 'not certify post-2026-08-14 records, the 83,503 physical-minus-declared discrepancy, supplier '
                 'execution, expected historical daily universe or PIT authority. B1..B7 remain OPEN.'},
    ],
    'append_only': True,
}
(DL / 'CORRECTIONS_APPEND_ONLY.json').write_bytes(
    (json.dumps(corr, indent=1, ensure_ascii=False) + '\n').encode('utf-8'))

ledger = {
    'schema': 'R10_SOURCE_BATCH_CHAIN_COMMAND_LEDGER_1',
    'cwd': str(W),
    'python': str(W / 'runtime/.venv/Scripts/python.exe'),
    'env': {'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'},
    'commands': [
        {'seq': 1, 'kind': 'stage_and_pin_check', 'script': 'tools/r10_sbc_stage.py', 'exit_code': 0,
         'result': 'all_pins_match=true'},
        {'seq': 2, 'command': r'.\runtime\.venv\Scripts\python.exe -X utf8 '
                              r'reviews\R10\source_batch_chain\test_r10_factor_source_batches.py',
         'exit_code': 0, 'started_cn': '2026-10-25T01:21:12.7502055+08:00',
         'finished_cn': '2026-10-25T01:21:14.7667690+08:00',
         'stdout_bytes': (CAP / 'TEST_8_CONTROLS.stdout.bin').stat().st_size,
         'stderr_bytes': (CAP / 'TEST_8_CONTROLS.stderr.bin').stat().st_size,
         'stdout_sha256': sha((CAP / 'TEST_8_CONTROLS.stdout.bin').read_bytes()),
         'stderr_sha256': sha((CAP / 'TEST_8_CONTROLS.stderr.bin').read_bytes()),
         'stdout_text': (CAP / 'TEST_8_CONTROLS.stdout.bin').read_bytes().decode('utf-8', 'replace'),
         'stderr_text': (CAP / 'TEST_8_CONTROLS.stderr.bin').read_bytes().decode('utf-8', 'replace')},
        {'seq': 3, 'command': r'.\runtime\.venv\Scripts\python.exe -X utf8 '
                              r'reviews\R10\source_batch_chain\r10_factor_source_batches.py --desktop-check',
         'executions': 1, 'exit_code': 0, 'started_cn': '2026-10-25T01:21:22.3567943+08:00',
         'finished_cn': '2026-10-25T01:22:52.0472258+08:00',
         'stdout_bytes': (CAP / 'DESKTOP_SOURCE_BATCHES.stdout.bin').stat().st_size,
         'stderr_bytes': (CAP / 'DESKTOP_SOURCE_BATCHES.stderr.bin').stat().st_size,
         'stdout_sha256': sha((CAP / 'DESKTOP_SOURCE_BATCHES.stdout.bin').read_bytes()),
         'stderr_sha256': sha((CAP / 'DESKTOP_SOURCE_BATCHES.stderr.bin').read_bytes()),
         'status_field': j['status']},
    ],
    'not_executed': ['download_source_fq_pre_r1.py (any mode, import, CLI, help, resume)',
                     'any updater or production writer', 'any supplier/network call',
                     'any drive or all-layer enumeration', 'dirty_branch rerun',
                     '13-year Cleaning-vs-CACHE basis rerun', 'catalog inventory', 'original-source lookup'],
    'supplier_calls': 0,
    'network_calls_by_measured_driver': 0,
    'FOUNDATION_ACCEPTANCE': False, 'FORMAL_ENGINE_ADMISSION': False,
    'NEW_DATA_ACQUISITION_AUTHORIZED': False, 'CURRENT_SWITCH_ALLOWED': False, 'ORDER_ALLOWED': False,
}
(DL / 'COMMAND_LEDGER.json').write_bytes(
    (json.dumps(ledger, indent=1, ensure_ascii=False) + '\n').encode('utf-8'))

pre = json.loads((DL / 'PRE_EXECUTION_PIN_CHECK.json').read_text(encoding='utf-8'))
pre['checked_at_cn_note'] = 'pins checked before command seq 2 and seq 3'
(DL / 'PRE_EXECUTION_PIN_CHECK.json').write_bytes(
    (json.dumps(pre, indent=1, ensure_ascii=False) + '\n').encode('utf-8'))

print('built; summary', json.dumps(summary['totals']), 'empty', summary['empty_batches'],
      'distinct', summary['distinct_parquet_sha256'])
for m in meta_ids:
    print('META', m)
