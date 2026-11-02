"""GPT scratch assembly/check program, not a Windows or local-data entry point.

Uses only already staged HUB evidence files. Its scratch-relative inputs below
are not instructions to seek files on ZHANGWEI. No source drive/vendor access.
"""
import hashlib
import json
from pathlib import Path, PureWindowsPath
from collections import Counter

ROOT = Path(__file__).resolve().parent


def digest(b):
    return hashlib.sha256(b).hexdigest()


def blob(b):
    return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()


def read(p):
    return json.loads(Path(p).read_bytes())


def write(name, obj):
    (ROOT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


checks = []


def check(condition, name):
    if not condition:
        raise AssertionError(name)
    checks.append(name)


matrix = read('coverage_desk_review/DAILY_EVIDENCE_MATRIX.json')
plan = read('evidence/RAW_TRANSFER_PLAN.json')
bindings = read('p3_dispatch/bindings.json')
identities = read(ROOT / 'REVIEWED_SOURCE_BLOBS.json')
by_path = {x['path']: x['git_blob_sha'] for x in identities['files']}
local_pins = {
    'evidence/RAW_TRANSFER_PLAN.json': 'agents/chatgpt/reviews/BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101/RAW_TRANSFER_PLAN.json',
    'p3_dispatch/bindings.json': 'agents/chatgpt/reviews/BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101/bindings.json',
    'a_inputs_review/DATASET_STATE.json': 'agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10/end_to_end_completion/DATASET_STATE.json',
    'p1_dispatch/CALENDAR.json': 'agents/chatgpt/reviews/BLACKBOX_P1_NATIVE_TEST_20261101/CALENDAR.json',
}
for local, hub in local_pins.items():
    check(blob(Path(local).read_bytes()) == by_path[hub], 'INPUT_BLOB:' + hub)

historical = []
for day in matrix['dates']:
    for src in day['historical_exact_sources']:
        historical.append(dict(source_id='HISTORICAL_%03d' % len(historical),
                               original_path=src['path'],
                               windows_path_candidate=str(PureWindowsPath(src['path'])),
                               expected_sha256=src['sha256'], expected_bytes=None,
                               reported_rows=src['reported_rows'],
                               reported_session=day['trade_date'],
                               evidence_host='SAM_HISTORICAL', target_observation_host='ZHANGWEI',
                               read_scope='L1_IDENTITY_ONLY_NO_ALTERNATE_PATH'))
stock = []
for i, row in enumerate(plan['rows']):
    if not row['relative_path'].startswith('raw/stock/'):
        continue
    path = bindings['source_prefixes'][row['root']] + row['relative_path'].replace('/', '\\')
    stock.append(dict(source_id='P3_STOCK_%04d' % len(stock),
                      transfer_plan_zero_based_row=i, root=row['root'],
                      relative_path=row['relative_path'], original_path=path,
                      windows_path_candidate=str(PureWindowsPath(path)),
                      expected_bytes=row['bytes'], expected_sha256=row['sha256'],
                      indexed_filename_session=row['relative_path'].split('/')[-1][:10],
                      target_observation_host='ZHANGWEI',
                      read_scope='L1_IDENTITY_THEN_L2_PHYSICAL_PROFILE'))

check(len(historical) == 17, 'EXACTLY_17_HISTORICAL_REFS')
check(len(stock) == 1122, 'EXACTLY_1122_STOCK_REFS')
check(len({x['original_path'] for x in historical + stock}) == 1139, '1139_DISTINCT_ORIGINAL_PATHS')
check(len({x['windows_path_candidate'] for x in historical + stock}) == 1139, 'NO_WINDOWS_PATH_COLLISIONS')
check(all(len(x['expected_sha256']) == 64 for x in historical + stock), 'FULL_SHA256_ALL_REFS')
check(len({x['reported_session'] for x in historical}) == 15, '15_HISTORICAL_LISTED_SESSIONS')
check(Counter(x['reported_session'] for x in historical)['2026-09-10'] == 2, 'SEP10_DUPLICATE_REFS_RETAINED')
check(Counter(x['reported_session'] for x in historical)['2026-09-24'] == 2, 'SEP24_DUPLICATE_REFS_RETAINED')
counts = Counter(x['indexed_filename_session'] for x in stock)
check(len(counts) == 17 and set(counts.values()) == {66}, '17_INDEXED_CELLS_66_REFS_EACH_NOT_CONTENT_DATE_CERTIFICATE')
check(all('raw/stock/' in x['relative_path'] for x in stock), 'NO_ETF_INDEX_BODIES')
for ref in stock:
    row = plan['rows'][ref['transfer_plan_zero_based_row']]
    check(ref['expected_bytes'] == row['bytes'] and ref['expected_sha256'] == row['sha256'], 'PLAN_MEMBER_IDENTITY:' + ref['source_id'])

calendar = read('p1_dispatch/CALENDAR.json')
sessions = calendar['returned']
signal = sorted(counts)[:-1]
pairs = [(s, sessions[sessions.index(s) + 1]) for s in signal]
check(len(pairs) == 16, '16_SIGNAL_EXECUTION_PAIRS')
check(pairs[0] == ('2026-09-28', '2026-09-29'), 'FIRST_PAIR')
check(pairs[-1] == ('2026-10-26', '2026-10-27'), 'LAST_PAIR')
check('2026-10-28' not in sessions and '2026-10-28' not in counts, 'OCT28_NOT_AUTHORIZED_OR_INVENTED')
sample = [x for x in stock if x['root'] == 'R4' and x['relative_path'] == 'raw/stock/2026-10-15_00720_R4.parquet']
check(len(sample) == 1 and sample[0]['expected_bytes'] == 15545 and sample[0]['expected_sha256'] == '158937b474c53184087ef5a05968ba36e5b81a4348f49ed66cf5cad77fa6763f', 'EXACT_SAMPLE_MEMBER_PIN')

master = read('a_inputs_review/DATASET_STATE.json')['datasets'][13]
check(master['dataset_id'] == 'SECURITY_MASTER', 'MASTER_METADATA_ROW_IDENTITY')
check(master['layers']['CLEAN']['measurement']['n_files_total'] == 11, 'MASTER_11_MEMBER_METADATA_ONLY')

catalogue = dict(status='DRAFT_NOT_NATIVE_ALLOWLIST',
                reviewed_snapshot=identities['reviewed_snapshot'], execution_host='ZHANGWEI',
                local_command='NONE', ACK_REQUESTED=False, ORDER_ALLOWED=False,
                historical_refs=historical, stock_refs=stock,
                master=dict(status='BLOCKED_EXACT_MASTER_MEMBERS_NOT_BOUND',
                            registered_root=master['layers']['CLEAN']['root'],
                            metadata_member_count=11, exact_members=[],
                            root_scan_allowed=False),
                signal_execution_pairs=[dict(signal_session=s, execution_session=e) for s, e in pairs],
                normalized_path_status='CANDIDATE_SPELLINGS_REQUIRE_FINAL_REVIEW_NOT_ALIAS_DISCOVERY')
write('INPUT_CATALOGUE_DRAFT.json', catalogue)
check(not catalogue['master']['exact_members'] and not catalogue['master']['root_scan_allowed'], 'MISSING_MASTER_NEVER_ROOT_SCAN')
check(catalogue['local_command'] == 'NONE' and not catalogue['ACK_REQUESTED'] and not catalogue['ORDER_ALLOWED'], 'NO_NATIVE_DISPATCH')
public = read(ROOT / 'PUBLIC_EVIDENCE.json')
check(not public['complete_exception_census'] and not public['unit_admitted'], 'G1_G2_OPEN')
check(not public['original_public_pdf_bytes_captured'], 'NO_PDF_HASH_CLAIM')
contract = (ROOT / 'CONTRACT_DRAFT.txt').read_text()
for phrase in ['local_command=NONE', 'ordinals1 THROUGH5', 'UNKNOWN', 'BLOCKED_EXACT_MASTER_MEMBERS_NOT_BOUND', 'No winner or suppression policy', 'No executable command']:
    check(phrase in contract, 'DRAFT_SAFETY_TEXT:' + phrase)
write('DESK_CHECKS.json', dict(status='PASS_DRAFT_INDEX_AND_CONTRACT_CHECKS_ONLY',
                             assertions=len(checks), checks=checks,
                             native_reads=0, supplier_calls=0, master_members_bound=0,
                             source_absence_claims=0, native_dispatch_issued=False))
print(json.dumps(dict(assertions=len(checks), historical_refs=len(historical), stock_refs=len(stock),
                      signal_execution_pairs=len(pairs), native_dispatch_issued=False)))
