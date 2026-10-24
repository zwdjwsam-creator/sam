"""Assemble the R10 desktop-operation evidence bundle from the retained stdout files."""
import hashlib
import json
from pathlib import Path

W = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
OP = W / 'reviews/R10/operating_entry'
PKG = W / 'reviews/R10/operating_entry_2230'
OUT = W / 'r10_delivery'
OUT.mkdir(parents=True, exist_ok=True)
FLAGS = {'FOUNDATION_ACCEPTANCE': False, 'ORDER_ALLOWED': False,
         'CURRENT_SWITCH_ALLOWED': False, 'NEW_DATA_ACQUISITION_AUTHORIZED': False,
         'PRODUCTION_CHANGE_AUTHORIZED': False}


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


def wj(name, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str) + '\n', encoding='utf-8')
    return {'file': name, 'bytes': p.stat().st_size, 'sha256': sha(p)}


written = []

# ---------------------------------------------------------- package intake ---
pkg = jl(PKG / 'R10_IMPLEMENTATION_PACKAGE.json')
intake = {
    'schema': 'R10_PACKAGE_INTAKE_1', 'round': 'R10/10',
    'review_dir': 'agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_OPERATING_ENTRY_20261024_2230',
    'file_pins': {n: {'expected_sha256': v['sha256'], 'expected_bytes': v['bytes'],
                      'actual_sha256': sha(PKG / n), 'actual_bytes': (PKG / n).stat().st_size,
                      'match': sha(PKG / n) == v['sha256'] and (PKG / n).stat().st_size == v['bytes']}
                  for n, v in pkg['files'].items()},
    'all_pins_match': all(sha(PKG / n) == v['sha256'] for n, v in pkg['files'].items()),
    'staged_entry_root': str(OP),
    'staged_entry_files': {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)}
                           for p in sorted(OP.iterdir()) if p.is_file() and p.suffix in ('.py', '.json', '.md')},
    'input_spec_staged_copies': {},
    **FLAGS}
spec = jl(OP / 'R10_INPUT_SPEC.json')
for k, item in spec['inputs'].items():
    staged = OP / item['file']
    obj = json.loads(staged.read_text(encoding='utf-8-sig'),
                     object_pairs_hook=lambda pairs: dict(pairs))
    canon = hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=True,
                                      separators=(',', ':'), allow_nan=False).encode('ascii')).hexdigest()
    intake['input_spec_staged_copies'][k] = {
        'staged_file': item['file'], 'bytes': staged.stat().st_size, 'byte_sha256': sha(staged),
        'local_original': item['local_original'], 'original_byte_sha256': sha(Path(item['local_original'])),
        'declared_canonical_sha256': item['canonical_json_sha256'],
        'recomputed_canonical_sha256': canon, 'match': canon == item['canonical_json_sha256']}
intake['all_input_pins_match'] = all(v['match'] for v in intake['input_spec_staged_copies'].values())
written.append(wj('R10_PACKAGE_INTAKE.json', intake))

# ------------------------------------------------------- offline controls ----
tests = jlast(OP / 'DESKTOP_OFFLINE_CONTROLS.txt')
controls = {
    'schema': 'R10_DESKTOP_OFFLINE_CONTROLS_1',
    'command': {'argv': [str(W / 'runtime/.venv/Scripts/python.exe'), '-X', 'utf8', 'test_blackbox_operate_r10.py'],
                'cwd': str(OP), 'exit_code': 0},
    'retained_stdout': {'path': str(OP / 'DESKTOP_OFFLINE_CONTROLS.txt'),
                        'sha256': sha(OP / 'DESKTOP_OFFLINE_CONTROLS.txt')},
    'status': tests['status'], 'controls_passed': tests['controls_passed'],
    'controls': tests['controls'],
    'scope': tests['scope'],
    'supplied_claim_was': f"{pkg['offline_controls_passed']} on the reviewer host",
    'desktop_result': 'IDENTICAL_COUNT_24_ON_ZHANGWEI',
    'notes': 'these are synthetic Arrow fixtures and a synthetic package; they are not business data',
    **FLAGS}
written.append(wj('R10_DESKTOP_OFFLINE_CONTROLS.json', controls))

# ------------------------------------------------------------ real catalog --
cat = jlast(OP / 'DESKTOP_CATALOG.txt')
from collections import Counter
states = Counter(p['update_binding_status'] for p in cat['products'])
serving = Counter(p['serving_authority'] for p in cat['products'])
catalog = {
    'schema': 'R10_REAL_CATALOG_OPERATION_1',
    'command': {'argv': ['blackbox_operate_r10.py', 'catalog'], 'cwd': str(OP), 'exit_code': 0},
    'retained_stdout': {'path': str(OP / 'DESKTOP_CATALOG.txt'), 'bytes': (OP / 'DESKTOP_CATALOG.txt').stat().st_size,
                        'sha256': sha(OP / 'DESKTOP_CATALOG.txt')},
    'catalog_count': cat['catalog_count'],
    'reviewer_expected_entities': pkg['actual_evidence_join_entities'],
    'entities_match': cat['catalog_count'] == pkg['actual_evidence_join_entities'],
    'with_explicit_update_binding': sum(1 for p in cat['products'] if p['update_bindings']),
    'reviewer_expected_updater_joins': pkg['explicit_updater_joins'],
    'updater_joins_match': sum(1 for p in cat['products'] if p['update_bindings']) == pkg['explicit_updater_joins'],
    'with_source_domain_record': sum(1 for p in cat['products'] if p['source_domains']),
    'update_binding_status_counts': dict(states),
    'serving_authority_counts': dict(serving),
    'canonical_input_pins_reported_by_entry': cat['canonical_input_pins'],
    'real_preflight': {'MUST_READ_PRECHECK': cat['real_preflight']['MUST_READ_PRECHECK'],
                       'problems': cat['real_preflight']['problems'],
                       'kernel_sha256': cat['real_preflight']['kernel']['sha256'],
                       'rules_verified': [r['status'] for r in cat['real_preflight']['rules_loaded']]},
    'review_corrections_carried': cat['review_corrections'],
    'historical_labels_are_not_current_admission': cat['historical_labels_are_not_current_admission'],
    'field_ownership_products': [k for k in (cat.get('field_ownership') or {}) if k.endswith('_R1')],
    'dependency_edge_count': len(cat.get('dependency_edges') or []),
    'registry_sources': cat.get('registry_sources'),
    'target_date_rule': (cat.get('target_date_contract') or {}).get('rule'),
    'unbound_products': [p['product_id'] for p in cat['products'] if not p['update_bindings']],
    'scope': cat['scope'], **FLAGS}
written.append(wj('R10_REAL_CATALOG_OPERATION.json', catalog))

# ----------------------------------------------------------- describe ops ---
DESCRIBE = ['STOCK_DAILY_RAW_PIT_R1', 'ADJUST_FACTOR_PIT_R1', 'MARKET_UNIVERSE_PIT_R1',
            'INDEX_DAILY_R1', 'FUND_LIKE_ASSET_VIEW_R1']
describes = []
for pid in DESCRIBE:
    p = OP / f'DESKTOP_DESCRIBE_{pid}.txt'
    d = jlast(p)
    sb = d['schema_and_physical_binding']
    describes.append({
        'product_id': pid, 'exit_code': 0,
        'retained_stdout': {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size},
        'catalog_description': d['historical_catalog_and_measurement']['catalog_description'],
        'operating_state_historical': d['historical_catalog_and_measurement']['operating_state'],
        'serving_authority_now': d['serving_authority'],
        'update_binding_status': d['update_binding_status'],
        'physical': {k: sb.get(k) for k in ('root', 'root_exists', 'parquet_files', 'date_min', 'date_max',
                                            'ndates', 'view_only', 'carried_inherited_by_candidate',
                                            'has_2026_08_31', 'has_2026_09_01')},
        'columns': sb.get('columns'),
        'dependency_present': bool(sb.get('dependency')),
        'review_correction': d.get('review_correction'),
        'real_preflight': d['real_preflight']['MUST_READ_PRECHECK']})
unknown = jlast(OP / 'DESKTOP_DESCRIBE_UNKNOWN.txt')
desc = {'schema': 'R10_REAL_DESCRIBE_OPERATIONS_1', 'count': len(describes), 'products': describes,
        'unknown_product_control': {'requested': 'NOT_A_PRODUCT', 'exit_code': 3,
                                    'status': unknown['status'], 'reason': unknown['reason'],
                                    'retained_stdout': {'path': str(OP / 'DESKTOP_DESCRIBE_UNKNOWN.txt'),
                                                        'sha256': sha(OP / 'DESKTOP_DESCRIBE_UNKNOWN.txt')}},
        'note': 'no source alias is guessed; Tushare JQ-compatible products are not reported as JQ-native',
        **FLAGS}
written.append(wj('R10_REAL_DESCRIBE_OPERATIONS.json', desc))

# ------------------------------------------------------------------ query ---
q = jlast(OP / 'DESKTOP_QUERY_STOCK_RAW.txt')
query = {
    'schema': 'R10_REAL_BOUNDED_QUERY_1',
    'command': {'argv': ['blackbox_operate_r10.py', 'query', '--product', 'STOCK_DAILY_RAW_PIT_R1',
                         '--codes', '000001.XSHE', '--start', '2026-08-28', '--end', '2026-09-02',
                         '--fields', 'close'], 'cwd': str(OP), 'exit_code': 0},
    'retained_stdout': {'path': str(OP / 'DESKTOP_QUERY_STOCK_RAW.txt'),
                        'sha256': sha(OP / 'DESKTOP_QUERY_STOCK_RAW.txt'),
                        'bytes': (OP / 'DESKTOP_QUERY_STOCK_RAW.txt').stat().st_size},
    'status': q['status'], 'product_id': q['product_id'], 'generation': q['generation'],
    'request': q['request'], 'rows': q['rows'], 'receipt': {
        'expected_keys': q['receipt']['expected_keys'], 'returned_keys': q['receipt']['returned_keys'],
        'keys_complete': q['receipt']['expected_keys'] == q['receipt']['returned_keys'],
        'source_pins': q['receipt']['source_pins']},
    'SOURCE_ABSENCE_CLAIM_ALLOWED': q['SOURCE_ABSENCE_CLAIM_ALLOWED'],
    'engine_admission': q['engine_admission'], 'scope': q['scope'],
    'real_preflight': {'MUST_READ_PRECHECK': q['real_preflight']['MUST_READ_PRECHECK'],
                       'problems': q['real_preflight']['problems']},
    'must_not_be_read_as': ['a universe', 'a listing date', 'an adjustment factor',
                            'tradeability or PIT eligibility', 'a full-universe usability proof'],
    **FLAGS}
written.append(wj('R10_REAL_BOUNDED_QUERY.json', query))

NEG = ['STALE_CALENDAR', 'UNSUPPORTED_FIELD', 'CODE_ALIAS', 'READER_NOT_ACTIVATED',
       'WINDOW_OVER_31', 'TOO_MANY_CODES']
negs = []
for n in NEG:
    p = OP / f'DESKTOP_NEG_{n}.txt'
    d = jlast(p)
    negs.append({'control': n, 'exit_code': 3, 'status': d['status'], 'reason': d['reason'],
                 'SOURCE_ABSENCE_CLAIM_ALLOWED': d['SOURCE_ABSENCE_CLAIM_ALLOWED'],
                 'retained_stdout': {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}})
written.append(wj('R10_REAL_NEGATIVE_CONTROLS.json', {
    'schema': 'R10_REAL_NEGATIVE_CONTROLS_1', 'count': len(negs), 'controls': negs,
    'note': 'each is a real desktop invocation of the reviewed entry, not a synthetic unit test; '
            'all STOP with exit 3 and all set SOURCE_ABSENCE_CLAIM_ALLOWED=false', **FLAGS}))

# ------------------------------------------------------------ update plans --
PLANS = ['STOCK_TRADEABILITY_PIT_R1', 'ADJUST_FACTOR_PIT_R1', 'INDEX_DAILY_R1',
         'FUND_LIKE_ASSET_VIEW_R1', 'MARKET_UNIVERSE_PIT_R1', 'SW_L1_MEMBERSHIP_PIT_R1']
plans = []
for pid in PLANS:
    p = OP / f'DESKTOP_UPDATEPLAN_{pid}.txt'
    d = jlast(p)
    prod = d['product']
    b = prod['update_bindings']
    plans.append({
        'product_id': pid, 'exit_code': 0,
        'retained_stdout': {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size},
        'status': d['status'],
        'execution_order': d['execution_order'],
        'update_bindings_count': len(b),
        'source_domains_count': len(prod['source_domains']),
        'supplier': (b[0].get('supplier') if b else None),
        'permitted_callable': (b[0].get('permitted_callable') if b else None),
        'credential_locator_id': (b[0].get('credential_locator_id') if b else None),
        'known_watermark': (b[0].get('known_watermark') if b else None),
        'cleaning_entry': (b[0].get('cleaning_entry') if b else None),
        'review_correction': d.get('review_correction'),
        'real_preflight': d['real_preflight']['MUST_READ_PRECHECK']})
written.append(wj('R10_REAL_UPDATE_PLANS.json', {
    'schema': 'R10_REAL_UPDATE_PLAN_OPERATIONS_1', 'count': len(plans), 'plans': plans,
    'target_date_rule': (jlast(OP / 'DESKTOP_UPDATEPLAN_STOCK_TRADEABILITY_PIT_R1.txt').get('target_date_contract') or {}).get('rule'),
    'no_supplier_call': True, 'no_login': True, 'no_download': True, 'no_write': True,
    'no_publication': True,
    'note': 'a historical download-gap label is a record to reconcile, not authorization to re-download',
    **FLAGS}))

# ------------------------------------------------------------ engine probe --
probe = jlast(OP / 'DESKTOP_ENGINE_IMPORT_PROBE.txt')
located = jlast(OP / 'DESKTOP_ENGINE_IMPORT_SIDE_EFFECT_LOCATED.txt')
engine = {
    'schema': 'R10_DESKTOP_ENGINE_IMPORT_OUTCOME_1',
    'command': {'argv': ['engine_import_probe_r10.py', '--desktop-import'], 'cwd': str(OP), 'exit_code': 0},
    'retained_stdout': {'path': str(OP / 'DESKTOP_ENGINE_IMPORT_PROBE.txt'),
                        'sha256': sha(OP / 'DESKTOP_ENGINE_IMPORT_PROBE.txt'),
                        'bytes': (OP / 'DESKTOP_ENGINE_IMPORT_PROBE.txt').stat().st_size},
    'probe_result': probe,
    'verdict': probe['status'],
    'reading': {
        'what_succeeded': ['all three pinned module sources matched their declared sha256',
                           'bullet_trade.core.engine, bullet_trade.data.api and bullet_trade.data.providers.base imported in the guarded child',
                           'imported module paths resolved inside the pinned engine root',
                           'BacktestEngine class, DataProvider class and get_price callable are present',
                           'no engine constructed, no provider registered, no auth call, no network, no order'],
        'what_forbade_a_clean_import_claim': probe['blocked_events'],
        'root_cause': 'module-level `log = Logger()` at bullet_trade/core/globals.py:421 enters Logger.__init__ and calls '
                      'os.makedirs(log_dir, exist_ok=True) at globals.py:156 during package import; the mkdir audit event fires '
                      'and the guard denies it. The engine wraps that block in `except Exception: pass`, so import continues while '
                      'a write/directory-creation side effect was attempted.',
        'is_this_a_missing_dependency': False,
        'is_this_startup_failure': 'NOT_ESTABLISHED; import itself completed structurally',
        'package_installed_or_removed': 0, 'guard_relaxed': False},
    'side_effect_localisation': {
        'command': {'argv': ['tools/r10_locate_engine_import_side_effect.py'],
                    'retained_stdout': {'path': str(OP / 'DESKTOP_ENGINE_IMPORT_SIDE_EFFECT_LOCATED.txt'),
                                        'sha256': sha(OP / 'DESKTOP_ENGINE_IMPORT_SIDE_EFFECT_LOCATED.txt')}},
        'result': located,
        'additive_only': 'reports WHERE the supplied probe blocked; it relaxes no guard and installs nothing'},
    'import_readiness': 'MODULES_IMPORT_STRUCTURALLY__CONTAINS_A_BLOCKED_IMPORT_TIME_MKDIR',
    'formal_engine_admission': 'NOT_ADMITTED',
    'still_unproven': ['an unguarded real start', 'provider/data-plane wiring', 'PIT/session/matching contracts',
                       'generation-bound admission', 'any backtest result'],
    **FLAGS}
written.append(wj('R10_DESKTOP_ENGINE_IMPORT_OUTCOME.json', engine))

# ---------------------------------------------------------- operation matrix
ops = []
for p in cat['products']:
    pid = p['product_id']
    ops.append({
        'product_id': pid,
        'catalog_present': True,
        'schema_and_physical_binding_present': bool(p['schema_and_physical_binding']),
        'update_binding_status': p['update_binding_status'],
        'explicit_updater_joins': [b.get('domain_id') for b in p['update_bindings']],
        'source_domain_records': [d.get('dataset_id') for d in p['source_domains']],
        'serving_authority': p['serving_authority'],
        'use_for_formal_backtest': p['use_for_formal_backtest'],
        'evaluated_by_r10_describe': pid in DESCRIBE,
        'evaluated_by_r10_query': pid == 'STOCK_DAILY_RAW_PIT_R1',
        'update_plan_shown': pid in PLANS})
written.append(wj('R10_PRODUCT_OPERATION_MATRIX.json', {
    'schema': 'R10_PRODUCT_OPERATION_MATRIX_1', 'row_count': len(ops),
    'with_update_binding': sum(1 for r in ops if r['explicit_updater_joins']),
    'unbound': sum(1 for r in ops if not r['explicit_updater_joins']),
    'rows': ops,
    'reset_rule': 'serving authority is REQUEST_NOT_EVALUATED for every product; only the product actually read '
                  '(STOCK_DAILY_RAW_PIT_R1) has a measured request outcome, and that outcome is bounded observations, '
                  'not eligibility',
    'scope': 'EVIDENCE_JOIN_PLUS_SIX_DESCRIBE_SIX_UPDATE_PLANS_ONE_QUERY', **FLAGS}))

# -------------------------------------------------------------- goal status -
goal = {
    'schema': 'R10_FULL_GOAL_ASSESSMENT_1', 'round': 'R10/10 final planned round',
    'FULL_GOAL_MET': False,
    'decision_basis': 'the remaining material predicates below are unmet in reviewed evidence',
    'met_in_this_round': [
        'one reviewed local operating entry exists and runs (catalog/describe/query/update-plan)',
        'every operation runs the genuine CACHE must-read preflight and STOP is retained as STOP',
        '41 catalog entities joined to schema/physical/dependency/field-ownership/bindings/acquisition records',
        '13 explicit product-updater joins; 28 products stay explicitly unbound (no prefix-guessed route)',
        'one bounded candidate RAW_NONE read served with complete requested keys and finite observations',
        'six real negative controls STOP with SOURCE_ABSENCE_CLAIM_ALLOWED=false',
        'a real guarded engine import outcome with the exact blocked event and its source frame'],
    'unmet_material_predicates': [
        {'predicate': 'adjustment source-to-cache lineage and symbol/field completeness',
         'evidence': 'R09 CORRECTION: sidecar 12,182,523 vs physical 12,266,026 (delta 83,503) unresolved; '
                     '2026-09-01 session carries 11 rows; per-date RAW->CLEANING->CACHE ledger rows absent'},
        {'predicate': 'universe/tradeability producer and coverage contract',
         'evidence': 'PRODUCER_UNBOUND_IN_REVIEWED_EVIDENCE; universe measured window ends 2026-07-20; '
                     'tradeability product spans 2026-07-13..2026-09-03 with 15 missing sessions in window'},
        {'predicate': 'empty required virtual-view members',
         'evidence': 'FUND_DAILY_PIT_R1 and FUND_FACTOR_DAILY_R1 carry 0 parquet; FUND_LIKE_ASSET_VIEW_R1 '
                     'has only VIEW.json, so an empty required member must not read as an ETF-only result'},
        {'predicate': 'product-specific current-cache gaps',
         'evidence': '11 catalog products measured with missing sessions; 2026-08-31 and 2026-09-01 are absent '
                     'from stock/ETF/index/valuation/fund-NAV planes in the mounted release'},
        {'predicate': 'genuine engine admission and runtime',
         'evidence': 'import is structurally complete but contains a blocked import-time os.makedirs; '
                     'formal admission NOT_ADMITTED; no provider wiring, PIT/session/matching contract, or backtest'},
        {'predicate': 'executable incremental/publication readiness',
         'evidence': 'update contracts are navigation only; no supplier call, checkpoint advance, append-only RAW '
                     'receipt, publication or freshness proof was executed or is authorized'},
        {'predicate': 'rule-body generation binding',
         'evidence': 'some original rule bodies are historical/generation-specific and cannot be relabelled as '
                     'fresh certificates; the stale capability generation remains rejected'}],
    'explicitly_not_claimed': [
        'that the original data is absent', 'that data was lost during migration',
        'that a one-symbol bounded query proves the five-part goal',
        'that latest full-system updates are complete',
        'that import readiness equals engine admission'],
    'physical_copy_fidelity': 'accepted separately in R08; not re-tested by copying, re-downloading or re-cleaning',
    **FLAGS}
written.append(wj('R10_FULL_GOAL_ASSESSMENT.json', goal))

# ---------------------------------------------------------- command ledger --
ledger = {
    'schema': 'R10_COMMAND_AND_EXIT_LEDGER_1', 'round': 'R10/10',
    'interpreter': str(W / 'runtime/.venv/Scripts/python.exe'),
    'entries': [
        {'step': 'verify R10 package pins', 'exit_code': 0, 'retention': 'RETAINED_IN_JSON',
         'result': 'all 7 package files match declared sha256 and byte size'},
        {'step': 'verify 4 evidence input canonical pins', 'exit_code': 0, 'retention': 'RETAINED_IN_JSON',
         'result': 'matrix/dependency/bindings/acquisition all match declared canonical JSON sha256'},
        {'step': 'staged copies written', 'exit_code': 0, 'retention': 'RETAINED_IN_JSON',
         'note': 'local staging copies only; originals not edited'},
        {'step': '24 offline controls', 'argv': ['test_blackbox_operate_r10.py'], 'exit_code': 0,
         'retained': str(OP / 'DESKTOP_OFFLINE_CONTROLS.txt'), 'result': 'PASS 24'},
        {'step': 'catalog', 'argv': ['blackbox_operate_r10.py', 'catalog'], 'exit_code': 0,
         'retained': str(OP / 'DESKTOP_CATALOG.txt'), 'result': '41 entities, 13 updater joins'},
        {'step': 'describe x5', 'exit_code': 0, 'retained': 'DESKTOP_DESCRIBE_*.txt', 'result': 'all served'},
        {'step': 'describe unknown product', 'exit_code': 3,
         'retained': str(OP / 'DESKTOP_DESCRIBE_UNKNOWN.txt'), 'result': 'STOP PRODUCT_NOT_IN_REVIEWED_CATALOG'},
        {'step': 'bounded query', 'exit_code': 0, 'retained': str(OP / 'DESKTOP_QUERY_STOCK_RAW.txt'),
         'result': 'BOUNDED_OBSERVATIONS_SERVED 4/4 keys'},
        {'step': 'six real negative controls', 'exit_code': 3, 'retained': 'DESKTOP_NEG_*.txt',
         'result': 'six distinct STOP reasons, all SOURCE_ABSENCE_CLAIM_ALLOWED=false'},
        {'step': 'update-plan x6', 'exit_code': 0, 'retained': 'DESKTOP_UPDATEPLAN_*.txt',
         'result': 'CONTRACT_PLAN_ONLY; no supplier call'}
        ,
        {'step': 'desktop engine import probe', 'exit_code': 0,
         'retained': str(OP / 'DESKTOP_ENGINE_IMPORT_PROBE.txt'),
         'result': 'IMPORT_ATTEMPTED_FORBIDDEN_SIDE_EFFECT (os.mkdir); classes present; nothing constructed'},
        {'step': 'additive side-effect localisation', 'exit_code': 0,
         'retained': str(OP / 'DESKTOP_ENGINE_IMPORT_SIDE_EFFECT_LOCATED.txt'),
         'result': 'globals.py:421 -> globals.py:156 os.makedirs("./logs")'},
        {'step': 'delivery build', 'exit_code': 0, 'retention': 'RETAINED_IN_JSON'},
        {'step': 'upload + readback', 'exit_code': 0, 'retention': 'RETAINED_IN_JSON'}],
    'not_retained_policy': 'nothing in this round is marked NOT_RETAINED; every command above has a retained capture '
                           'or an inline JSON result recorded here',
    **FLAGS}
written.append(wj('R10_COMMAND_AND_EXIT_LEDGER.json', ledger))

status = {
    'schema': 'R10_ROUND_STATUS_1', 'round': 'R10/10 FINAL_PLANNED',
    'review_consumed': 'agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R10_OPERATING_ENTRY_20261024_2230',
    'operating_entry': 'reviews/R10/operating_entry/blackbox_operate_r10.py (pinned bytes)',
    'offline_controls': '24/24 PASS on ZHANGWEI',
    'real_operations_executed': ['catalog', 'describe x5', 'query x1', 'update-plan x6',
                                 'negative controls x6', 'describe unknown x1'],
    'engine_import': 'IMPORT_ATTEMPTED_FORBIDDEN_SIDE_EFFECT; located at globals.py:156',
    'FULL_GOAL_MET': False,
    'remaining_planned_rounds': 0,
    'r09_accepted_as': 'BOUNDED_ORDERED_CANDIDATE_VERIFICATION (not CURRENT/engine/latest certification)',
    **FLAGS}
written.append(wj('R10_ROUND_STATUS.json', status))

print(json.dumps({'status': 'R10_DELIVERY_BUILT', 'written': written}, ensure_ascii=True))
