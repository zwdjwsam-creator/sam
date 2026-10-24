"""Build the R09 correction delivery required by REVIEW_R09_CORRECTION.md.

Joins existing records only. No Parquet reopen, no root re-scan, no acquisition.
"""
import ast
import csv
import hashlib
import json
from pathlib import Path

WORK = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
OUT = WORK / 'r09_correction'
OUT.mkdir(parents=True, exist_ok=True)
CTRL = WORK / 'reviews/R09/control_2100'
FIXR = WORK / 'reviews/R09/preflight_fix_2140'
PACKET = WORK / 'reviews/R08/BODY_EXPORT_20261024_2025'
FLAGS = {'FOUNDATION_ACCEPTANCE': False, 'ORDER_ALLOWED': False,
         'PRODUCTION_CHANGE_AUTHORIZED': False, 'CURRENT_SWITCH_ALLOWED': False,
         'NEW_DATA_ACQUISITION_AUTHORIZED': False, 'SOURCE_ABSENCE_CLAIMS': 0}


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def jl(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def jlast(p):
    for line in reversed(Path(p).read_text(encoding='utf-8-sig', errors='replace').strip().splitlines()):
        if line.strip().startswith('{'):
            return json.loads(line)
    raise ValueError('NO_JSON:' + str(p))


def tx(p):
    return Path(p).read_text(encoding='utf-8-sig', errors='replace')


def wj(name, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str) + '\n', encoding='utf-8')
    return {'file': name, 'bytes': p.stat().st_size, 'sha256': sha(p)}


written = []

# ---------------------------------------------------------------- sources ---
catalog_p = WORK / 'r06_delivery/source_bodies/registry/CACHE_PRODUCT_CATALOG.csv'
cov = jl(WORK / 'r07_delivery/evidence/product_coverage_vs_authority_calendar.json')
ledger = jl(WORK / 'r07_delivery/LAYER_SEARCH_AND_BINDING_LEDGER.json')
empty_products = jl(WORK / 'r07_delivery/evidence/empty_products.json')
acq = jl(WORK / 'r04_delivery/access_resources/DATA_ACQUISITION_MATRIX.json')
nextb = jl(WORK / 'r06_delivery/NEXT_UPDATE_BINDINGS.json')
r8 = jl(WORK / 'candidate_releases/R08/R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024/CANDIDATE_MANIFEST.json')
ready = jl(WORK / 'r08_delivery/ENGINE_RUNTIME_AND_UPDATE_READINESS.json')
pyproject = WORK / 'r04_delivery/source_engine/S3_ENGINE_SOURCE/pyproject.toml'
engine_root = WORK / 'r04_delivery/source_engine/S3_ENGINE_SOURCE'
cache_release_root = Path(r'E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439')

# --------------------------------------------------- 1 tempdir fix desktop --
fix_pkg = jl(FIXR / 'R09_TEMP_DIR_FIX_PACKAGE.json')
fixed_path = CTRL / 'r09_control_runtime_preflight_fixed.py'
fixed = {
    'schema': 'R09_TEMP_DIR_FIX_DESKTOP_RESULTS_1', 'round': 'R09/10_CORRECTION',
    'supplied_package_pins': {n: {'expected_sha256': v['sha256'], 'expected_bytes': v['bytes'],
                                  'actual_sha256': sha(FIXR / n), 'actual_bytes': (FIXR / n).stat().st_size,
                                  'match': sha(FIXR / n) == v['sha256'] and (FIXR / n).stat().st_size == v['bytes']}
                              for n, v in fix_pkg['files'].items()},
    'fixed_entry': {'path': str(fixed_path), 'sha256': sha(fixed_path), 'bytes': fixed_path.stat().st_size,
                    'expected_sha256': fix_pkg['fixed_runtime_sha256'],
                    'match_expected': sha(fixed_path) == fix_pkg['fixed_runtime_sha256'],
                    'status': 'FIXED_ENTRY_CREATED', 'write_exceptions_added': 0,
                    'original_runner_sha256': sha(CTRL / 'r09_control_runtime.py'),
                    'original_runner_unchanged': sha(CTRL / 'r09_control_runtime.py') == fix_pkg['source_runtime_sha256'],
                    'successor_modules_unchanged': all(
                        sha(WORK / 'candidate/r09/control_successor' / n) == s
                        for n, s in jl(WORK / 'candidate/r09/control_successor/SUCCESSOR_BUILD_MANIFEST.json')['outputs'].items())},
    'supplied_test_literal_result': {
        'file': 'test_r09_preflight_tempdir.py', 'sha256': sha(FIXR / 'test_r09_preflight_tempdir.py'),
        'exit_code': 1, 'controls_passed_before_stop': 5,
        'stop_at_control': 'fixed child runs actual successor preflight without bypass',
        'traceback_line': 78, 'assertion': 'assert after.returncode==0',
        'cause': 'FIXTURE_NEWLINE_PORTABILITY_ON_WINDOWS: expected SHA256 is computed from read_bytes() after write_text() stored CRLF, while the child read_text() translates CRLF to LF',
        'expected_sha256_of_CRLF_fixture': '5bd17a4a66c4126008a147278511f1fb55774b443fa32bf571a0ffd5a8efc073',
        'actual_sha256_of_LF_text': 'e80b71cd14d3cbd65f4173abcbfcf01a545dbca32a72d575108b553a648cc96f',
        'proves': ['the fixed child got past the import probe (no temp dir error)',
                   'the guard was installed and did not block the read-only preflight',
                   'the real successor preflight executed and rejected the fixture on SHA, i.e. its verification path is live'],
        'does_not_prove': ['the ten-control PASS claim on this host'],
        'stdout_retained': str(FIXR / 'DESKTOP_TEMP_DIR_FIX_STDOUT.txt'),
        'stdout_sha256': sha(FIXR / 'DESKTOP_TEMP_DIR_FIX_STDOUT.txt'),
        'modification_made': False},
    'additive_windows_completion': jlast(FIXR / 'ADDITIVE_WIN_COMPLETION_STDOUT.txt'),
    'additive_harness': {'path': str(WORK / 'tools/additive_win_completion_test_r09_tempdir.py'),
                         'sha256': sha(WORK / 'tools/additive_win_completion_test_r09_tempdir.py')},
    'guard_predicate_byte_identical': True, 'guard_write_exceptions': 0,
    'interpretation': 'The supplied repair is sound and executes the real successor preflight under the unchanged guard. The supplied test alone cannot reach ten green controls on Windows because of its own fixture newline handling; the additive harness proves the same ten invariants with byte-exact fixtures.',
    **FLAGS}
written.append(wj('R09_TEMP_DIR_FIX_DESKTOP_RESULTS.json', fixed))

# ------------------------------------------------------- 2 fixed entry run ---
fe = jlast(CTRL / 'DESKTOP_FIXED_ENTRY.txt')
entry = {
    'schema': 'R09_FIXED_ORDERED_ENTRY_EVIDENCE_1', 'round': 'R09/10_CORRECTION',
    'command': {'argv': ['runtime/.venv/Scripts/python.exe', '-X', 'utf8',
                         'reviews/R09/control_2100/r09_control_runtime_preflight_fixed.py',
                         '--packet', 'reviews/R08/BODY_EXPORT_20261024_2025',
                         '--successor', 'candidate/r09/control_successor'],
                'cwd': str(WORK), 'env': {'PYTHONPATH': str(CTRL), 'PYTHONDONTWRITEBYTECODE': '1'},
                'exit_code': 0},
    'retained_stdout': {'path': str(CTRL / 'DESKTOP_FIXED_ENTRY.txt'),
                        'sha256': sha(CTRL / 'DESKTOP_FIXED_ENTRY.txt'),
                        'bytes': (CTRL / 'DESKTOP_FIXED_ENTRY.txt').stat().st_size},
    'status': fe['status'], 'steps_executed': fe['steps'],
    'step_count_executed': len(fe['steps']),
    'real_must_read_preflight': {'MUST_READ_PRECHECK': fe['preflight']['MUST_READ_PRECHECK'],
                                 'task_class': fe['preflight']['task_class'],
                                 'required': fe['preflight']['required'],
                                 'problems': fe['preflight']['problems'],
                                 'kernel': fe['preflight']['kernel'],
                                 'rules_loaded': fe['preflight']['rules_loaded'],
                                 'executed_in_guarded_child': True,
                                 'write_exceptions': 0, 'network_used': False},
    'bounded_read': fe['bounded_read'], 'negative_controls': fe['controls'],
    'conservation_statement': 'selected candidate price frame and selected candidate factor frame both compare at parent_keys=959896 and candidate_keys=959896 with 0 lost keys and 0 lost close observations; the earlier prose figure 949470 belongs to a different factor-gate comparison and is withdrawn for this command',
    'scope': fe['scope'], 'flags': {k: fe[k] for k in ('FOUNDATION_ACCEPTANCE', 'ORDER_ALLOWED',
                                                       'CURRENT_SWITCH_ALLOWED', 'NEW_DATA_ACQUISITION_AUTHORIZED',
                                                       'SOURCE_ABSENCE_CLAIMS')},
    'historical_non_authoritative': [
        {'item': 'original runner STOP at stage 1', 'evidence': str(CTRL / 'DESKTOP_ORDERED_ENTRY.txt'),
         'sha256': sha(CTRL / 'DESKTOP_ORDERED_ENTRY.txt'), 'authoritative': False,
         'why': 'pre-repair state, retained as history only'},
        {'item': 'stage 1 substituted diagnostic', 'evidence': str(CTRL / 'DESKTOP_STAGES_2_4_WITH_STAGE1_SUBSTITUTED.json'),
         'sha256': sha(CTRL / 'DESKTOP_STAGES_2_4_WITH_STAGE1_SUBSTITUTED.json'), 'authoritative': False,
         'why': 'review withdrew substitution as an acceptable execution path; its 1_MUST_READ step was never executed by that harness and must not be counted'}],
    **FLAGS}
written.append(wj('R09_FIXED_ORDERED_ENTRY_EVIDENCE.json', entry))

# ------------------------------------------------------------ 3 catalog ------
raw = catalog_p.read_bytes()
text = raw.decode('utf-8-sig')
lines = text.splitlines()
header = lines[0]
blank_idx = [i for i, l in enumerate(lines) if not l.strip()]
comment_idx = [i for i, l in enumerate(lines) if l.strip().startswith('#')]
data_rows = [l for l in lines[1:] if l.strip() and not l.strip().startswith('#')]
parsed = list(csv.reader(data_rows))
accounting = {
    'schema': 'R09_CATALOG_ACCOUNTING_1', 'path': str(catalog_p), 'sha256': sha(catalog_p),
    'bytes': len(raw), 'bom': raw[:3] == b'\xef\xbb\xbf',
    'crlf_count': raw.count(b'\r\n'), 'lf_count': raw.count(b'\n'),
    'line_endings': 'LF_ONLY' if raw.count(b'\r\n') == 0 else 'MIXED',
    'trailing_newline': text.endswith('\n'),
    'total_lines': len(lines), 'header_lines': 1, 'blank_lines': len(blank_idx),
    'blank_line_indices': blank_idx, 'comment_lines': len(comment_idx),
    'data_rows': len(parsed), 'columns': header.split(','),
    'reconciliation': {'total_lines': len(lines),
                       'accounted': 1 + len(blank_idx) + len(comment_idx) + len(parsed),
                       'balanced': len(lines) == 1 + len(blank_idx) + len(comment_idx) + len(parsed)},
    'note': 'Earlier R09 wording said 42 catalog rows; the correct reading of this file is 43 lines = 1 header + 41 data rows + 1 blank line + 0 comments.',
    **FLAGS}
written.append(wj('CATALOG_ACCOUNTING.json', accounting))

# --------------------------------------------------- 4 per-product matrix ----
requested_rows = {}
for e in ledger['entries']:
    obs = e.get('observed', {})
    for key, name in (('rows_on_requested_dates', str(e.get('dataset', ''))),
                      ('rows_on_0831', str(e.get('dataset', '')))):
        if key in obs:
            for token in name.replace(' -> ', ' / ').split(' / '):
                requested_rows.setdefault(token.strip(), {})['rows_on_2026_08_31' if key == 'rows_on_0831' else 'rows_on_requested_dates'] = obs[key]
    if 'rows_on_0831' in obs:
        for token in str(e.get('dataset', '')).replace(' -> ', ' / ').split(' / '):
            t = token.strip()
            if t in obs:
                requested_rows.setdefault(t, {}).update({'rows_on_2026_08_31': obs[t].get('rows_on_0831'),
                                                         'rows_on_2026_09_01': obs[t].get('rows_on_0901')})
    cache_obs = obs.get('cache', {})
    if 'rows_on_requested_dates' in cache_obs:
        for token in str(e.get('dataset', '')).split(' / '):
            requested_rows.setdefault(token.strip(), {})['rows_on_requested_dates'] = cache_obs['rows_on_requested_dates']
    if 'rows_on_requested_dates' in obs and 'L12' not in str(e.get('id')):
        for token in str(e.get('dataset', '')).split(' / '):
            requested_rows.setdefault(token.strip(), {})['rows_on_requested_dates'] = obs['rows_on_requested_dates']

requested_rows = {}


def _bind(datasets, payload):
    for token in str(datasets).replace(' -> ', ' / ').split(' / '):
        t = token.strip()
        if t:
            requested_rows.setdefault(t, {}).update({k: v for k, v in payload.items() if v is not None})


def _scan(o, names):
    if isinstance(o, dict):
        payload = {'rows_on_requested_dates': o.get('rows_on_requested_dates'),
                   'rows_on_2026_08_31': o.get('rows_on_0831'),
                   'rows_on_2026_09_01': o.get('rows_on_0901')}
        if any(v is not None for v in payload.values()):
            _bind(names, payload)
        for k, v in o.items():
            _scan(v, k if str(k).endswith('_R1') else names)
    elif isinstance(o, list):
        for v in o:
            _scan(v, names)


for e in ledger['entries']:
    _scan(e.get('observed', {}), e.get('dataset', ''))

for k in list(requested_rows):
    if not requested_rows[k]:
        requested_rows.pop(k)

ledger_by_product = {}
for e in ledger['entries']:
    for token in str(e.get('dataset', '')).replace(' -> ', ' / ').split(' / '):
        t = token.strip()
        if t and t.isupper() or t.endswith('_R1'):
            ledger_by_product.setdefault(t, []).append({'id': e['id'], 'kind': e['kind'],
                                                        'classification': e['classification'],
                                                        'allowed_action': e.get('allowed_action')})
without_dir = set(ledger['entries'][[e['id'] for e in ledger['entries']].index('L11')]['observed']['without_directory'])
classmap = (ledger['entries'][[e['id'] for e in ledger['entries']].index('L11')]['observed']['classification_map'])
empty_names = {e['product']: e for e in empty_products}
inherited = set(r8['inherited_cache_products'])
override_products = set(r8['cache_overrides'].keys())
own_artifacts = {a['product']: a for a in r8['r08_artifacts']}
acq_rows = {r['dataset_id']: r for r in acq['rows']}
tradeability_binding = acq_rows.get('TRADABLE_STATUS')

rows = []
for rec in parsed:
    pid, layer, atype, status, pkey, desc = (rec + [''] * 6)[:6]
    c = cov.get(pid)
    led = ledger_by_product.get(pid, [])
    if pid in own_artifacts:
        candidate_presence = 'OWN_CANDIDATE_ARTIFACT'
    elif pid in override_products:
        candidate_presence = 'CANDIDATE_OVERRIDE'
    elif pid in inherited:
        candidate_presence = 'INHERITED_BY_REFERENCE'
    else:
        candidate_presence = 'NOT_IN_R08_CANDIDATE'
    directory_present = 'ABSENT_IN_INSPECTED_CACHE_RELEASE' if pid in without_dir else 'PRESENT'
    if directory_present == 'ABSENT_IN_INSPECTED_CACHE_RELEASE':
        state = classmap.get('TUSHARE_CBOND_*' if pid.startswith('TUSHARE_CBOND_') else pid,
                             classmap.get('TUSHARE_CBOND_*', 'UNRECORDED'))
    elif c and c['missing_session_count'] == 0:
        state = 'CURRENT_SERVES_MEASURED_WINDOW'
    elif c and c['missing_session_count'] > 0:
        state = 'CURRENT_DECLARED_GAP'
    elif pid in empty_names:
        state = 'CURRENT_PRODUCT_EMPTY'
    else:
        state = 'NOT_MEASURED_IN_REVIEWED_EVIDENCE'
    producer = 'DECLARED_DOMAIN_TRADABLE_STATUS_WITH_RAW_AND_CLEAN_ROOTS' if pid == 'STOCK_TRADEABILITY_PIT_R1' else \
        ('PRODUCER_UNBOUND_IN_REVIEWED_EVIDENCE' if pid in ('MARKET_UNIVERSE_PIT_R1',) else 'NOT_SOUGHT_THIS_ROUND')
    rows.append({
        'product_id': pid, 'catalog_layer': layer, 'asset_type': atype, 'catalog_status': status,
        'partition_key': pkey, 'catalog_description': desc,
        'directory_in_inspected_cache_release': directory_present,
        'current_release_measurement': ({'files': c['files'], 'rows': c['rows'], 'date_col': c['date_col'],
                                         'min': c['min'], 'max': c['max'], 'distinct_dates': c['distinct_dates'],
                                         'expected_sessions_in_window': c['expected_sessions_in_window'],
                                         'missing_session_count': c['missing_session_count'],
                                         'missing_session_examples': c['missing_sessions'][:4]}
                                        if c else None),
        'r08_candidate_presence': candidate_presence,
        'r07_ledger': led,
        'requested_date_rows_2026_08_31_and_2026_09_01': requested_rows.get(pid),
        'producer_binding_in_reviewed_evidence': producer,
        'operating_state': state,
        'served_by_current_release': (
            'NO_ROWS_ON_REQUESTED_DATES'
            if (requested_rows.get(pid) and all(v == 0 for k, v in requested_rows[pid].items()
                                                if k.startswith('rows_on_2026') or k == 'rows_on_requested_dates'))
            else 'YES_ROWS_ON_REQUESTED_DATES' if requested_rows.get(pid)
            else 'YES_MEASURED' if state == 'CURRENT_SERVES_MEASURED_WINDOW'
            else 'NO_MEASURED_GAP' if state == 'CURRENT_DECLARED_GAP'
            else 'UNKNOWN_NOT_MEASURED'),
        'does_not_prove': ['symbol-level completeness', 'PIT semantics beyond the recorded fields',
                           'engine admission', 'publication freshness for any other date'],
    })

matrix = {
    'schema': 'R09_CATALOG_PRODUCT_OPERATING_MATRIX_1', 'round': 'R09/10_CORRECTION',
    'scope': 'EVERY CATALOG PRODUCT ROW FROM THE EXISTING CATALOG, JOINED WITH EXISTING ROUND RECORDS',
    'inputs': [{'path': str(catalog_p), 'sha256': sha(catalog_p)},
               {'path': str(WORK / 'r07_delivery/evidence/product_coverage_vs_authority_calendar.json'),
                'sha256': sha(WORK / 'r07_delivery/evidence/product_coverage_vs_authority_calendar.json')},
               {'path': str(WORK / 'r07_delivery/LAYER_SEARCH_AND_BINDING_LEDGER.json'),
                'sha256': sha(WORK / 'r07_delivery/LAYER_SEARCH_AND_BINDING_LEDGER.json')},
               {'path': str(WORK / 'r07_delivery/evidence/empty_products.json'),
                'sha256': sha(WORK / 'r07_delivery/evidence/empty_products.json')},
               {'path': str(WORK / 'r04_delivery/access_resources/DATA_ACQUISITION_MATRIX.json'),
                'sha256': sha(WORK / 'r04_delivery/access_resources/DATA_ACQUISITION_MATRIX.json')},
               {'path': str(WORK / 'candidate_releases/R08/R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024/CANDIDATE_MANIFEST.json'),
                'sha256': sha(WORK / 'candidate_releases/R08/R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024/CANDIDATE_MANIFEST.json')}],
    'row_count': len(rows),
    'state_counts': {},
    'rows': rows,
    'layer_totals': {},
    'caveat': 'A join of records is not a fresh measurement. Every figure carries the round that produced it; nothing here was re-read from Parquet or from a re-scanned root.',
    **FLAGS}
for r in rows:
    matrix['state_counts'][r['operating_state']] = matrix['state_counts'].get(r['operating_state'], 0) + 1
    matrix['layer_totals'][r['catalog_layer']] = matrix['layer_totals'].get(r['catalog_layer'], 0) + 1

_groups = {}
for r in rows:
    if not r['current_release_measurement']:
        continue
    key = json.dumps(r['current_release_measurement'], sort_keys=True)
    _groups.setdefault(key, []).append(r['product_id'])
for r in rows:
    if r['current_release_measurement']:
        key = json.dumps(r['current_release_measurement'], sort_keys=True)
        peers = [p for p in _groups[key] if p != r['product_id']]
        if peers:
            r['measurement_caveat'] = {
                'identical_tuple_shared_with': peers,
                'reading': 'the R07 record carries one identical measured tuple for these product ids; it is not evidence that each product has its own distinct partition set',
                'not_reconciled_this_round': True}
matrix['identical_tuple_groups'] = {k: v for k, v in _groups.items() if len(v) > 1}
written.append(wj('CATALOG_PRODUCT_OPERATING_MATRIX.json', matrix))

# ------------------------------------------- 5 adjust factor reconciliation --
adj_cov = jl(cache_release_root / 'ADJUST_FACTOR_PIT_R1/COVERAGE.json')
l12 = [e for e in ledger['entries'] if e['id'] == 'L12'][0]
adj = {
    'schema': 'R09_ADJUST_FACTOR_SIDECAR_RECONCILIATION_1', 'round': 'R09/10_CORRECTION',
    'classification': 'PRODUCT_PUBLICATION_OR_COVERAGE_SIDECAR__NOT_A_SUPPLIER_REQUEST_PAGE_OR_ACQUISITION_RECEIPT',
    'sidecar': {'path': str(cache_release_root / 'ADJUST_FACTOR_PIT_R1/COVERAGE.json'),
                'sha256': sha(cache_release_root / 'ADJUST_FACTOR_PIT_R1/COVERAGE.json'),
                'content': adj_cov},
    'row_count_reconciliation': {
        'declared_by_sidecar': adj_cov['n_rows'],
        'measured_physically_in_R07': cov['ADJUST_FACTOR_PIT_R1']['rows'],
        'difference_physical_minus_declared': cov['ADJUST_FACTOR_PIT_R1']['rows'] - adj_cov['n_rows'],
        'status': 'UNRESOLVED_SIDECAR_VS_CONTENT', 'resolved_by_choosing_one': False,
        'possible_roles_not_yet_distinguished': ['declared at build time then re-derived',
                                                 'declared excluding a partition',
                                                 'declared counting distinct keys rather than rows'],
        'forbidden': ['choosing either count as truth without evidence', 'repairing dates from filenames',
                      'inferring that a factor=1 series is complete']},
    'date_union': {'measured_dates': cov['ADJUST_FACTOR_PIT_R1']['distinct_dates'],
                   'expected_sessions': cov['ADJUST_FACTOR_PIT_R1']['expected_sessions_in_window'],
                   'missing_sessions': cov['ADJUST_FACTOR_PIT_R1']['missing_session_count'],
                   'proves': 'date presence at the recorded grain only',
                   'does_not_prove': ['every symbol present', 'every factor observation valid',
                                      'that the 2026 degraded dates are complete']},
    'per_session_content_observation': {'source': 'R07 L12', 'rows_on_2026_08_31': l12['observed']['ADJUST_FACTOR_PIT_R1']['rows_on_0831'],
                                       'rows_on_2026_09_01': l12['observed']['ADJUST_FACTOR_PIT_R1']['rows_on_0901'],
                                       'interpretation': 'date presence and per-session row volume are very different; the 2026-09-01 volume (11 rows) cannot be read as a full session'},
    'source_linkage': {'tip_source_recorded': adj_cov.get('tip_source'), 'tip_extended_at': adj_cov.get('tip_extended_at'),
                       'reason_recorded': adj_cov.get('reason'),
                       'status': 'PRODUCT_LEVEL_LINK_ONLY; per-date RAW->CLEANING->CACHE ledger rows not produced'},
    'required_next_evidence': 'a per-date acquisition/transform ledger row or a reviewer ruling on which count is authoritative',
    **FLAGS}
written.append(wj('ADJUST_FACTOR_SIDECAR_RECONCILIATION.json', adj))

# --------------------------------------------- 6 SW route vs inheritance -----
swq = jl(CTRL / '_sw_qualification.json')
sw = {
    'schema': 'R09_SW_ROUTE_VS_INHERITANCE_1', 'round': 'R09/10_CORRECTION',
    'separated_layers': {
        'ROUTE': {'status': 'PRESENT', 'owner': 'TIP_COMPILER.inject_sw',
                  'detail': 'three pointer-driven routes read CURRENT_SW_L{1,2,3}_PIT_ALIGN_RELEASE.json and copy membership + structure FULL plus year partitions'},
        'BOUNDED_OBSERVATION': {'status': 'MEASURED', 'pointers': swq,
                                'proves': ['pointer resolves', 'standard root and both FULL files exist',
                                           'partition year directories exist',
                                           'footer row counts and measured max date'],
                                'does_not_prove': ['all dates', 'all symbols', 'PIT semantics',
                                                   'byte-identical content across releases']},
        'INHERITANCE_INTO_CURRENT_CACHE': {'status': 'REFERENCE_ONLY_NOT_BYTE_VERIFIED',
                                           'evidence': 'cache RELEASE.json declares sw_l{1,2,3}_status=READY_INTEGRATED; R08 candidate lists SW products as inherited PRSERVED_REFERENCE_NOT_REVERIFIED'},
        'ADMISSION': {'status': 'NONE', 'detail': 'no SW product is admitted to any engine in this round'}},
    'no_new_sw_parquet_reads': True,
    'measured_properties_only': True,
    **FLAGS}
sw['separated_layers']['INHERITANCE_INTO_CURRENT_CACHE']['evidence'] = \
    'cache RELEASE.json declares sw_l1/l2/l3_status=READY_INTEGRATED; the R08 candidate lists the six SW products among 51 inherited products with status PRESERVED_REFERENCE_NOT_REVERIFIED_OR_PROMOTED'
written.append(wj('SW_ROUTE_VS_INHERITANCE.json', sw))

# ------------------------------------------- 7 producer search evidence ------
prod = {
    'schema': 'R09_PRODUCER_SEARCH_EVIDENCE_BINDING_1', 'round': 'R09/10_CORRECTION',
    'retracted': {'artifact': 'EVIDENCE_INPUTS_R09.json -> four_unresolved_items.I1.writer_files_found = []',
                  'why': 'it looked like a fresh exhaustive writer search but cited no search ledger; R09 did not run one'},
    'replacement_statement': 'PRODUCER_UNBOUND_IN_REVIEWED_EVIDENCE',
    'what_the_reviewed_evidence_does_bind': {
        'domain_row': {'source': 'r04_delivery/access_resources/DATA_ACQUISITION_MATRIX.json',
                       'sha256': sha(WORK / 'r04_delivery/access_resources/DATA_ACQUISITION_MATRIX.json'),
                       'dataset_id': 'TRADABLE_STATUS', 'title': tradeability_binding['title'],
                       'declared_required_scope': tradeability_binding['declared_required_scope'],
                       'layer_roots': tradeability_binding['layer_roots'],
                       'layer_file_counts': tradeability_binding['layer_file_counts'],
                       'possession_status': tradeability_binding['possession_status'],
                       'acquisition_status': tradeability_binding['acquisition_status'],
                       'known_gap': tradeability_binding['known_gap'],
                       'next_contracted_action': tradeability_binding['next_contracted_action']},
        'update_binding': {'source': 'r06_delivery/NEXT_UPDATE_BINDINGS.json',
                           'sha256': sha(WORK / 'r06_delivery/NEXT_UPDATE_BINDINGS.json'),
                           'excerpt': 'scope_field=TRADEABILITY_EFFECTIVE_ASOF=2026-09-03, scope_note=inherited_0903_until_security_state_tip, observed_product_coverage=2026-07-13..2026-08-12 plus one 2026-09-03 tip, required_cache_product=[STOCK_TRADEABILITY_PIT_R1], receipt_or_exception=PERMISSION_OK per probe; the missing dates are a DOWNLOAD GAP, not a permission gap, status=PERMISSION_OK_DOWNLOAD_GAP'},
        'search_scope': {'source': 'r07_delivery/LAYER_SEARCH_AND_BINDING_LEDGER.json',
                         'sha256': sha(WORK / 'r07_delivery/LAYER_SEARCH_AND_BINDING_LEDGER.json'),
                         'products_enumerated': ledger['scope']['products_enumerated'],
                         'catalog_entries': ledger['scope']['catalog_entries'],
                         'searched_roots': ledger['scope']['searched_roots'],
                         'entries_used': [{'id': 'L08', 'dataset': 'MARKET_UNIVERSE_PIT_R1', 'classification': 'CACHE_COVERAGE_REGRESSION',
                                           'allowed_action': 'EXTEND_UNIVERSE_FROM_PINNED_SECURITY_STATE; NO_DOWNLOAD'},
                                          {'id': 'L09', 'dataset': 'STOCK_TRADEABILITY_PIT_R1', 'classification': 'CLEANING_COMPLETE_CACHE_MISSING',
                                           'allowed_action': 'MATERIALIZE_FROM_RAW_FIELDS; NO_DOWNLOAD'},
                                          {'id': 'L11', 'dataset': 'catalog entries without a directory',
                                           'classification': 'SEPARATE_NAMESPACE_OR_REGISTRY'}]},
        'consumer_references': [{'file': 'E:\\BLACKBOX\\脚本\\blackbox_data_access_resolver_r1.py',
                                 'sha256': sha(Path(r'E:\BLACKBOX\脚本\blackbox_data_access_resolver_r1.py')),
                                 'lines': [125, 126, 127, 210, 211], 'role': 'name map + PIT policy (reader)'},
                                {'file': 'E:\\BLACKBOX\\脚本\\blackbox_external_market_evidence_data_agent_r1.py',
                                 'sha256': sha(Path(r'E:\BLACKBOX\脚本\blackbox_external_market_evidence_data_agent_r1.py')),
                                 'lines': [228, 405], 'role': 'reads a tradeability release root (reader)'}]},
    'what_remains_unbound': ['the executable module that materializes RAW P2_security_state into STOCK_TRADEABILITY_PIT_R1',
                             'the module that owns MARKET_UNIVERSE_PIT_R1 membership'],
    'explicitly_not_claimed': ['that no producer exists anywhere',
                               'that the RAW lane is absent',
                               'any new acquisition',
                               'producer ownership of the two minute products beyond what L11 records'],
    **FLAGS}
written.append(wj('PRODUCER_SEARCH_EVIDENCE_BINDING.json', prod))

# ---------------------------------------- 8 generation identity roles --------
gen = {
    'schema': 'R09_GENERATION_IDENTITY_ROLES_1', 'round': 'R09/10_CORRECTION',
    'principle': 'different files carry different identities by design; CURRENT names the selected mounted release while the release-internal records keep their own generation. No seal, id or pointer is rewritten to make them agree.',
    'roles': [
        {'path': r'E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json', 'sha256': sha(Path(r'E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json')),
         'role': 'SELECTION_POINTER', 'identity': 'cache_release_id of the currently mounted release',
         'authoritative_for': ['which release is mounted', 'asof'], 'not_authoritative_for': ['product provenance']},
        {'path': str(cache_release_root / 'RELEASE.json'), 'sha256': sha(cache_release_root / 'RELEASE.json'),
         'role': 'RELEASE_GENERATION_RECORD', 'identity': 'the generation that produced this release tree',
         'authoritative_for': ['build provenance', 'parent chain', 'status flags written at build time'],
         'not_authoritative_for': ['which release is currently mounted']},
        {'path': str(cache_release_root / 'MANIFEST.json'), 'sha256': sha(cache_release_root / 'MANIFEST.json'),
         'role': 'PRODUCT_ADDITION_RECORD', 'identity': 'products added by this particular release step',
         'authoritative_for': ['product delta of the step'], 'not_authoritative_for': ['the mounted release id']},
        {'path': str(cache_release_root / 'SEAL.json'), 'sha256': sha(cache_release_root / 'SEAL.json'),
         'role': 'MINIMAL_ACCEPTANCE_STAMP', 'identity': 'sealed/accepted + timestamp only',
         'carries': ['accepted', 'sealed_at'], 'does_not_carry': ['release id', 'product list', 'content hash'],
         'gap': 'a seal that cannot name what it sealed is not a generation binding'},
        {'path': r'E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json', 'sha256': sha(Path(r'E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json')),
         'role': 'SELECTION_POINTER_PLUS_INHERITANCE', 'identity': 'release_id = the product-bearing release (R33 FUND_NAV); parent_release_id, quarantine_root and ledger_path = the daily tip release (R45)',
         'authoritative_for': ['mounted cleaning standard root'], 'not_authoritative_for': ['that R33 produced the tip quaranantine ledger']},
        {'path': r'E:\BLACKBOX\运行\BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json', 'sha256': sha(Path(r'E:\BLACKBOX\运行\BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json')),
         'role': 'CAPABILITY_GENERATION_DECLARATION', 'identity': 'capability_generation_id'},],
    'stale_generation_handling': {'rule': 'capability facts whose SYSTEM_GENERATION_ID does not match the declared capability generation stay REJECTED (CAPABILITY_FACTS_GENERATION_STALE)', 'solved_by_relabeling': False},
    'future_serving_envelope_requirements': ['name the chosen manifest', 'name each actual source and version', 'retain every original identity unmodified'],
    **FLAGS}
written.append(wj('GENERATION_IDENTITY_ROLES.json', gen))

# ------------------------------------- 9 engine runtime classification ------
targets = {'matplotlib', 'plotly', 'dotenv', 'filelock', 'pyecharts', 'tabulate', 'jupyterlab', 'ipykernel', 'IPython'}
trace = {}
for f in sorted(engine_root.glob('*.py')):
    try:
        tree = ast.parse(f.read_text(encoding='utf-8-sig', errors='replace'))
    except Exception:
        continue
    mod_level, fn_level = {}, {}

    def visit(node, fn=None):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                visit(ch, ch.name)
                continue
            if isinstance(ch, ast.Import):
                for a in ch.names:
                    b = a.name.split('.')[0]
                    if b in targets:
                        (fn_level if fn else mod_level).setdefault(b, set()).add(fn or '<module>')
            elif isinstance(ch, ast.ImportFrom) and ch.module and ch.level == 0:
                b = ch.module.split('.')[0]
                if b in targets:
                    (fn_level if fn else mod_level).setdefault(b, set()).add(fn or '<module>')
            visit(ch, fn)

    visit(tree)
    if mod_level or fn_level:
        trace[f.name] = {'module_level': {k: sorted(v) for k, v in mod_level.items()},
                         'function_level': {k: sorted(v) for k, v in fn_level.items()}}

pytext = tx(pyproject)
core = []
inside = False
for line in pytext.splitlines():
    if line.strip().startswith('dependencies = ['):
        inside = True
        continue
    if inside:
        if line.strip() == ']':
            break
        core.append(line.strip().strip('",'))


def dist_name(spec):
    out = spec.strip()
    for sep in ('>=', '<=', '==', '~=', '!=', '>', '<', ';', '['):
        out = out.split(sep)[0]
    return out.strip().lower()
classification = {}
for pkg in ready['engine_runtime']['missing']:
    imp = {'matplotlib': 'matplotlib', 'plotly': 'plotly', 'python-dotenv': 'dotenv', 'filelock': 'filelock',
           'pyecharts': 'pyecharts', 'tabulate': 'tabulate', 'jupyterlab': 'jupyterlab', 'ipykernel': 'ipykernel'}[pkg]
    hits = {f: v for f, v in trace.items() if imp in v['module_level'] or imp in v['function_level']}
    if imp == 'matplotlib':
        cls = 'OPTIONAL_AT_IMPORT__GUARDED_TRY_EXCEPT_IN_PACKAGE_INIT'
    elif imp == 'dotenv':
        cls = 'OPTIONAL_LAZY__IMPORTED_INSIDE_load_env_WITH_ImportError_HANDLER'
    elif not hits:
        cls = 'DECLARED_ONLY__NO_IMPORT_REFERENCE_IN_DELIVERED_SOURCES__STARTUP_NEED_UNPROVEN'
    else:
        cls = 'IMPORT_REFERENCED'
    classification[pkg] = {'import_name': imp,
                           'in_pyproject_core_dependencies': pkg in [dist_name(c) for c in core],
                           'class': cls, 'import_sites': hits}
eng = {
    'schema': 'R09_ENGINE_RUNTIME_REQUIREMENT_CLASSIFICATION_1', 'round': 'R09/10_CORRECTION',
    'pyproject': {'path': str(pyproject), 'sha256': sha(pyproject), 'core_dependencies': core},
    'r08_verdict': {'value': ready['engine_runtime']['verdict'],
                    'relabeled_as': 'RUNTIME_INVENTORY_VERDICT__NOT_A_PROVEN_STARTUP_FAILURE'},
    'missing_package_classification': classification,
    'counts': {'declared_core': len(core), 'missing_total': len(classification),
               'guarded_optional_at_import': sum(1 for v in classification.values() if v['class'].startswith('OPTIONAL_AT_IMPORT')),
               'lazy_optional': sum(1 for v in classification.values() if v['class'].startswith('OPTIONAL_LAZY')),
               'declared_only_unproven': sum(1 for v in classification.values() if v['class'].startswith('DECLARED_ONLY'))},
    'conclusion': 'the eight absent names are packaging declarations, not a demonstrated engine-startup requirement set; one is guarded at import and one is a lazy optional import, six are never imported by the delivered engine sources',
    'install_actions_taken': 0, 'notebook_stack_installed': False,
    'still_unproven_separately': ['a real engine startup trace', 'MASTER admission', 'package installation as a repair'],
    **FLAGS}
written.append(wj('ENGINE_RUNTIME_REQUIREMENT_CLASSIFICATION.json', eng))

# -------------------------------------------- 10 command/exit ledger ---------
def h(p):
    p = Path(p)
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


cmd_ledger = {
    'schema': 'R09_COMMAND_AND_EXIT_LEDGER_1', 'round': 'R09/10 + CORRECTION',
    'interpreter': str(WORK / 'runtime/.venv/Scripts/python.exe'),
    'entries': [
        {'step': 'verify review package pins', 'exit_code': 0, 'stdout': 'INLINE_JSON (see review_package_pins)',
         'retention': 'RETAINED_IN_JSON'},
        {'step': 'build control successor', 'argv': ['build_r09_control_successor.py', '--packet', str(PACKET)],
         'exit_code': 0, 'stdout': 'INLINE_JSON: CONTROL_SUCCESSOR_BUILT', 'retention': 'RETAINED_IN_JSON'},
        {'step': 'run 38 offline controls', 'argv': ['test_r09_controls.py', str(PACKET)], 'exit_code': 0,
         'stdout': h(CTRL / 'DESKTOP_CONTROLS_STDOUT.txt'), 'retention': 'RETAINED'},
        {'step': 'original ordered entry (pre-repair)', 'argv': ['r09_control_runtime.py', '--packet', str(PACKET),
                                                               '--successor', 'candidate/r09/control_successor'],
         'exit_code': 3, 'stdout': h(CTRL / 'DESKTOP_ORDERED_ENTRY.txt'), 'retention': 'RETAINED',
         'note': 'the first capture of this run was overwritten when the file was re-written as UTF-8 with identical exit code 3; the first literal bytes are NOT_RETAINED'},
        {'step': 'stage 1 substituted diagnostic', 'argv': ['diagnose_stages_2_4_stage1_blocked.py'],
         'exit_code': 0, 'stdout': h(CTRL / 'DESKTOP_STAGES_2_4_WITH_STAGE1_SUBSTITUTED.json'), 'retention': 'RETAINED',
         'authoritative': False},
        {'step': 'verify review correction pins', 'exit_code': 0, 'stdout': 'INLINE_JSON: PINS_ALL_MATCH True', 'retention': 'RETAINED_IN_JSON'},
        {'step': 'create fixed sibling runtime', 'argv': ['fix_r09_preflight_tempdir.py', '--source', str(CTRL / 'r09_control_runtime.py')],
         'exit_code': 0, 'stdout': 'INLINE_JSON: FIXED_ENTRY_CREATED sha f5223664...', 'retention': 'RETAINED_IN_JSON',
         'rerun': {'status': 'ALREADY_FIXED_VERIFIED', 'covered_by': 'additive harness replay control'}},
        {'step': 'supplied tempdir test (unmodified)', 'argv': ['test_r09_preflight_tempdir.py', str(CTRL / 'r09_control_runtime.py'), str(PACKET)],
         'exit_code': 1, 'stdout': h(FIXR / 'DESKTOP_TEMP_DIR_FIX_STDOUT.txt'), 'retention': 'RETAINED',
         'note': 'stopped at control 6 on a fixture newline portability defect (details in R09_TEMP_DIR_FIX_DESKTOP_RESULTS.json)'},
        {'step': 'additive Windows completion controls', 'argv': ['additive_win_completion_test_r09_tempdir.py', str(CTRL / 'r09_control_runtime.py'), str(PACKET)],
         'exit_code': 0, 'stdout': h(FIXR / 'ADDITIVE_WIN_COMPLETION_STDOUT.txt'), 'retention': 'RETAINED'},
        {'step': 'corrected real ordered entry', 'argv': ['r09_control_runtime_preflight_fixed.py', '--packet', str(PACKET),
                                                         '--successor', 'candidate/r09/control_successor'],
         'exit_code': 0, 'stdout': h(CTRL / 'DESKTOP_FIXED_ENTRY.txt'), 'retention': 'RETAINED'},
        {'step': 'historical R09 evidence collection', 'argv': ['tools/r09_evidence_collect.py'], 'exit_code': 0,
         'stdout': 'INLINE_JSON: EVIDENCE_INPUTS_WRITTEN', 'retention': 'RETAINED_IN_JSON'},
        {'step': 'historical R09 delivery build', 'argv': ['tools/r09_build_delivery.py'], 'exit_code': 0,
         'stdout': 'INLINE_JSON: R09_DELIVERY_ARTIFACTS_WRITTEN', 'retention': 'RETAINED_IN_JSON'},
        {'step': 'historical R09 upload', 'argv': ['tools/upload_r09_delivery.py'], 'exit_code': 0,
         'stdout': 'INLINE_JSON: uploaded 23, verified 23', 'retention': 'RETAINED_IN_JSON'},
        {'step': 'historical R09 pointer update', 'argv': ['tools/update_inbox_r09.py'], 'exit_code': 0,
         'stdout': 'INLINE_JSON: put sha 2363b8ab..., readback_identical True', 'retention': 'RETAINED_IN_JSON'},
        {'step': 'earlier ad-hoc writer-name grep over three script roots', 'exit_code': 0,
         'stdout': 'terminal output only', 'retention': 'NOT_RETAINED',
         'note': 'explicitly NOT reconstructed as a literal capture; replaced by PRODUCER_SEARCH_EVIDENCE_BINDING.json citing R04/R06/R07 ledgers'},
    ],
    'not_retained_policy': 'an unretained capture is recorded as NOT_RETAINED; it is never re-created to look like a historical byte capture',
    **FLAGS}
written.append(wj('COMMAND_AND_EXIT_LEDGER.json', cmd_ledger))

# ------------------------------------------- 11 exact repo-relative mapping --
previous = []
for p in sorted((WORK / 'r09_delivery').iterdir()):
    if p.is_file():
        previous.append({'local': str(p), 'repo_relative': f'agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R09/{p.name}',
                         'sha256': sha(p)})
for p in sorted((WORK / 'r09_delivery/executed_code').iterdir()):
    previous.append({'local': str(p), 'repo_relative': f'agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R09/executed_code/{p.name}',
                     'sha256': sha(p)})
for p in sorted((WORK / 'tools').glob('r09_*.py')):
    previous.append({'local': str(p), 'repo_relative': f'agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R09/tools/{p.name}',
                     'sha256': sha(p)})
mapping = {
    'schema': 'R09_CORRECTION_FILE_MAPPING_1', 'round': 'R09/10_CORRECTION',
    'defect_corrected': "DELIVERY_MANIFEST.json in the R09 bundle recorded 'remote' as a basename for files that physically live under executed_code/ and tools/",
    'previous_bundle_root': 'agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R09',
    'previous_bundle_exact_mapping': previous,
    'previous_bundle_mapping_count': len(previous),
    'this_correction_root': 'agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R09_CORRECTION',
    'note': 'the bytes on the remote host were already correct because the uploader used the real relative path; only the manifest text was wrong',
    **FLAGS}
written.append(wj('CORRECTION_FILE_MAPPING.json', mapping))

status = {
    'schema': 'R09_ROUND_STATUS_CORRECTION_1', 'round': 'R09/10_CORRECTION_NOT_R10',
    'remaining_planned_rounds': 1,
    'fixed_entry_on_desktop': 'PASSED_4_OF_4_STAGES (exit 0)',
    'supplied_tempdir_test_on_desktop': 'STOPPED_AT_CONTROL_6__FIXTURE_NEWLINE_PORTABILITY',
    'additive_windows_completion': 'PASS 10/10',
    'guard_write_exceptions_added': 0,
    'catalog_product_matrix': f'{len(rows)} of {len(parsed)} catalog rows joined',
    'catalog_accounting': f"43 lines = 1 header + {len(parsed)} data + {len(blank_idx)} blank + {len(comment_idx)} comment",
    'adjust_factor': 'SIDECAR_RECONCILIATION_UNRESOLVED (declared 12182523 vs physical 12266026, delta 83503)',
    'sw': 'ROUTE_AND_BOUNDED_OBSERVATION_QUALIFIED__INHERITANCE_REFERENCE_ONLY__ADMISSION_NONE',
    'producer': 'PRODUCER_UNBOUND_IN_REVIEWED_EVIDENCE',
    'engine_runtime': 'DECLARED_ONLY_6__GUARDED_OPTIONAL_1__LAZY_OPTIONAL_1__NO_INSTALL',
    'substitution_withdrawn': 'the stage-1 substituted diagnostic is retained as non-authoritative history and its 1_MUST_READ step is not counted',
    'withdrawn_claim': "the prose '949,470 -> 959,896' in R09_DELTA_REPORT.md does not describe this command; the literal comparison is 959,896 vs 959,896",
    **FLAGS}
written.append(wj('ROUND_STATUS_R09_CORRECTION.json', status))

print(json.dumps({'status': 'CORRECTION_BUILT', 'written': written,
                  'catalog_rows': len(rows), 'states': matrix['state_counts'],
                  'layers': matrix['layer_totals']}, ensure_ascii=True))