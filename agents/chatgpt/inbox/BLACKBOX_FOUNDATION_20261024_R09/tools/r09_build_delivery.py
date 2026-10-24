"""Build the R09 delivery from EVIDENCE_INPUTS_R09.json.

Adds no new measurement: every figure below is copied from the recorded inputs
(EVIDENCE_INPUTS_R09.json) which themselves cite path + SHA256.
"""
import hashlib
import json
from pathlib import Path

WORK = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
OUT = WORK / 'r09_delivery'
EV = json.loads((OUT / 'EVIDENCE_INPUTS_R09.json').read_text(encoding='utf-8'))
FLAGS = {'FOUNDATION_ACCEPTANCE': False, 'ORDER_ALLOWED': False,
         'PRODUCTION_CHANGE_AUTHORIZED': False, 'CURRENT_SWITCH_ALLOWED': False,
         'NEW_DATA_ACQUISITION_AUTHORIZED': False, 'SOURCE_ABSENCE_CLAIMS': 0}


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def wj(name, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, indent=1, ensure_ascii=False, default=str) + '\n', encoding='utf-8')
    return {'file': name, 'bytes': p.stat().st_size, 'sha256': sha(p)}


c = EV['desktop_offline_controls']
e = EV['desktop_ordered_entry']
d = EV['desktop_stages_2_4_substituted']
s = EV['successor_build']
L1, L2, L3, L5, L6 = (EV['L1_copied_assets'], EV['L2_classified_assets'], EV['L3_usable_read_requests'],
                      EV['L5_incremental_raw_staging'], EV['L6_publication_and_latest_freshness'])
L4 = EV['L4_formal_engine_admission']
it = EV['four_unresolved_items']

# ---------------------------------------------------------------- controls ---
results = {
    'schema': 'R09_CONTROL_AND_ENTRY_RESULTS_1', 'round': 'R09/10',
    'review_package': {'source': 'agents/chatgpt/reviews/BLACKBOX_FOUNDATION_R09_CONTROL_INTEGRATION_20261024_2100',
                       'stage_pins': EV['review_package_pins'],
                       'all_match': all(v['match'] for v in EV['review_package_pins'].values())},
    'successor_build': s,
    'desktop_offline_controls': {'status': c['status'], 'controls_passed': c['controls_passed'],
                                 'scope': c['scope'], 'supplier_calls': c['supplier_calls'],
                                 'production_writes': c['production_writes'], 'controls': c['controls'],
                                 'interpretation': 'REVIEWED CONTROLS RE-RUN ON DESKTOP; NOT ENGINE ADMISSION'},
    'desktop_ordered_entry': {'status': e['status'], 'error': e.get('error'), 'reason': e.get('reason'),
                              'stage_reached': '1_MUST_READ',
                              'root_cause': EV['stage1_block_root_cause'],
                              'guard_relaxed': False,
                              'stdout_file': EV['desktop_ordered_entry_stdout_path'],
                              'stdout_sha256': EV['desktop_ordered_entry_stdout_sha256']},
    'desktop_stages_2_4_disclosed_substitution': {
        'status': d['status'], 'scope': d['scope'], 'steps': d['steps'],
        'stage1_substituted': d['preflight']['STAGE1_SUBSTITUTED_NOT_EXECUTED'],
        'bounded_read': d['bounded_read'], 'controls': d['controls'],
        'file': EV['desktop_stages_2_4_path'], 'sha256': EV['desktop_stages_2_4_sha256'],
        'not_claimed': ['PASSED_ORDERED_ENTRY', 'ENGINE_ADMISSION', 'CURRENT_SWITCH', 'PUBLICATION']},
    'verdict': {'ordered_entry_on_desktop': 'STOP_AT_STAGE_1', 'stages_2_4_on_desktop': 'EXECUTED_AND_PASSED_IN_DISCLOSED_DIAGNOSTIC',
                'relax_guard_to_proceed': False, 'next_decision_owner': 'REVIEWER (GPT)'},
    **FLAGS}

# ------------------------------------------------------------- six layers ---
layers = [
    {'layer': 'L1_COPIED_ASSETS', 'status': 'PRESENT_AND_PINNED_WITHIN_MANIFEST_SCOPE',
     'figures': {'r08_files_on_disk': L1['r08_manifest_files_on_disk'],
                 'r08_bytes_on_disk': L1['r08_manifest_bytes_on_disk'],
                 'candidate_daily_count': L1['candidate_daily_count'],
                 'parent_daily_count': L1['parent_daily_count'],
                 'inherited_cache_products': L1['inherited_cache_products_count'],
                 'copies_of_inherited_products_created': 0,
                 'r08_artifacts': [{k: a.get(k) for k in ('product', 'rows', 'bytes', 'sha256')} for a in L1['r08_artifacts']]},
     'evidence': [{'path': L1['r08_candidate_manifest'], 'sha256': L1['r08_manifest_sha256'],
                   'bytes': L1['r08_manifest_bytes']}],
     'does_not_prove': ['full product or history coverage', 'that the 51 inherited products are current',
                        'publication', 'engine admission'],
     'borrows_from_other_layer': False},
    {'layer': 'L2_CLASSIFIED_ASSETS', 'status': 'CLASSIFIED_WITH_DECLARED_GAPS',
     'figures': {'canonical_products_classified': L2['canonical_products_classified'],
                 'catalog_rows': L2['catalog_rows'], 'catalog_layer_counts': L2['catalog_layer_counts'],
                 'catalog_status_counts': L2['catalog_status_counts'],
                 'declared_gap_products': {k: {'missing_session_count': v['missing_session_count'],
                                               'max': v['max'], 'expected': v['expected_sessions_in_window'],
                                               'distinct_dates': v['distinct_dates']}
                                           for k, v in L2['per_product'].items() if v['missing_session_count']},
                 'dirty_derived_products': ['MARKET_STRUCTURE_DAILY_R1: SW_UNVERIFIED; PIT_UNIVERSE_UNRESOLVED'],
                 'catalog_reconciliation_status': 'PHYSICAL_PARENT_PRODUCT_ROOTS_ONLY; registry and sidecars remain a separate gate'},
     'evidence': [{'path': L2['coverage_matrix_path'], 'sha256': L2['coverage_matrix_sha256']},
                  {'path': L2['catalog_path'], 'sha256': L2['catalog_sha256']}],
     'does_not_prove': ['usable read requests', 'engine admission', 'publication'],
     'borrows_from_other_layer': False},
    {'layer': 'L3_USABLE_READ_REQUESTS', 'status': 'CANDIDATE_READ_PASS__CURRENT_READ_NOT_SERVED',
     'figures': {'source': L3['served_source'], 'price_path_used': L3['price_path_used'],
                 'factor_path_used': L3['factor_path_used'],
                 'keys_parent': L3['coverage_non_regression']['parent_keys'],
                 'keys_candidate': L3['coverage_non_regression']['candidate_keys'],
                 'lost_keys': L3['coverage_non_regression']['lost_keys'],
                 'lost_close_observations': L3['coverage_non_regression']['lost_field_observation_keys']['close'],
                 'stock_request_rows': L3['stock_request_rows'], 'stock_values': L3['stock_values'],
                 'index_adapter_rows': L3['index_adapter_rows'], 'index_diagnostic_only': True,
                 'current_release_missing_sessions': L3['current_release_missing_sessions_stock']},
     'evidence': [{'path': EV['desktop_stages_2_4_path'], 'sha256': EV['desktop_stages_2_4_sha256']}],
     'does_not_prove': ['that CURRENT serves the two sessions', 'full-universe reads', 'engine admission',
                        'index master/PIT admission'],
     'borrows_from_other_layer': False},
    {'layer': 'L4_FORMAL_ENGINE_ADMISSION', 'status': 'NOT_ADMITTED',
     'figures': {'runtime_verdict': L4['runtime_verdict'], 'missing_packages': L4['missing_packages'],
                 'package_install_status': L4['package_install_status'],
                 'admission_gate_wiring_status': L4['admission_gate_wiring']['status'],
                 'engine_admission_allowed_manifest': L4['engine_admission_allowed_manifest'],
                 'shadow_gate_real_role_result': d['controls']['real_role_reason'],
                 'synthetic_parse_calls': d['controls']['synthetic_parse_calls']},
     'evidence': [{'path': L4['source'], 'sha256': L4['source_sha256']}],
     'does_not_prove': ['anything', 'admission is the blocking layer itself'],
     'borrows_from_other_layer': False},
    {'layer': 'L5_INCREMENTAL_RAW_STAGING', 'status': 'UNITS_PRESENT_AND_PINNED__NO_NEW_ACQUISITION',
     'figures': {'units': {k: {'path': v['chosen_path'], 'rows': v['rows'], 'dates': v['dates'], 'sha256': v['sha256']}
                           for k, v in L5['units_for_20260831_20260901'].items()},
                 'new_units_staged_this_round': 0, 'raw_append_only_preserved': True,
                 'in_place_raw_mutation': False},
     'evidence': [{'path': L5['source'], 'sha256': L5['source_sha256']}],
     'does_not_prove': ['cleaning/cache transform correctness', 'publication', 'any new authorization'],
     'borrows_from_other_layer': False},
    {'layer': 'L6_PUBLICATION_AND_LATEST_FRESHNESS', 'status': 'CURRENT_UNCHANGED__NOT_GLOBALLY_FRESH',
     'figures': {'cache_pointer_sha256': L6['cache_current_pointer']['sha256'],
                 'cleaning_pointer_sha256': L6['cleaning_current_pointer']['sha256'],
                 'cache_release_asof': json.loads(L6['cache_current_pointer']['payload_base64'].encode() and
                                                  __import__('base64').b64decode(L6['cache_current_pointer']['payload_base64']).decode('utf-8-sig'))['asof'],
                 'capability_generation_id': L6['capability_generation_id'],
                 'calendar_authority_max': L6['calendar_authority_max'],
                 'per_domain_watermark': L6['per_domain_watermark'],
                 'seal_content': json.loads(__import__('base64').b64decode(L6['cache_seal_json']['payload_base64']).decode('utf-8-sig')),
                 'publish_gate_live_result': L6['publish_gate_live_result'],
                 'publication_gates': L6['admission_gate']},
     'evidence': [{'path': L6['cache_current_pointer']['path'], 'sha256': L6['cache_current_pointer']['sha256']},
                  {'path': L6['cache_seal_json']['path'], 'sha256': L6['cache_seal_json']['sha256']},
                  {'path': L6['cache_domain_asof_json']['path'], 'sha256': L6['cache_domain_asof_json']['sha256']}],
     'does_not_prove': ['that any single domain is complete', 'that a newer release exists'],
     'borrows_from_other_layer': False}]

matrix = {'schema': 'R09_SIX_LAYER_EVIDENCE_MATRIX_1', 'round': 'R09/10',
          'rule': 'NO_LAYER_BORROWS_ANOTHER_LAYERS_PASS',
          'layer_order': [x['layer'] for x in layers], 'layers': layers,
          'cross_layer_statement': [
              'R08 candidate read PASS (L3) does not upgrade CURRENT (L6).',
              'L1/L2 presence does not upgrade L3 usability.',
              'L3 usability does not upgrade L4 admission.',
              'L5 RAW presence does not upgrade L6 publication.',
              'L4 remains NOT_ADMITTED regardless of any other layer.'],
          'summary_counts': {x['status']: sum(1 for y in layers if y['status'] == x['status']) for x in layers},
          **FLAGS}

# ------------------------------------------------------- four unresolved ----
narrowed = {'schema': 'R09_FOUR_UNRESOLVED_ITEMS_NARROWED_1', 'round': 'R09/10',
            'method': 'existing inventories + exact current-consumer references; no global scan, no re-download',
            'items': {
                'I1': {**it['I1_UNIVERSE_TRADEABILITY_PRODUCER_OWNERSHIP'],
                       'what_is_now_settled': ['both products are ACTIVE catalog rows (L1/STOCK)',
                                               'both are consumed by the resolver name map and by the external evidence agent',
                                               'no local writer exists in the three searched roots',
                                               'content is stale relative to the declared effective asof'],
                       'what_remains_open': ['who produces them (JQ interface or external supplier) and where the receipt lives'],
                       'decision_needed': 'NAME_THE_PRODUCER_INTERFACE; DO_NOT_REBUILD_OR_REDOWNLOAD'},
                'I2': {**it['I2_ADJUST_FACTOR_REFRESH_RECEIPT'],
                       'what_is_now_settled': ['a product-level refresh receipt exists with exact tip RAW source, timestamp and row counts',
                                               'coverage is 3097/3097 sessions with 0 read errors'],
                       'what_remains_open': ['per-date RAW->Cleaning->Cache linkage for the recovered dates',
                                             'what the 12 degraded 2026 dates are and whether they need action'],
                       'decision_needed': 'ACCEPT_PRODUCT_LEVEL_RECEIPT_OR_REQUEST_PER_DATE_LEDGER_ROW'},
                'I3': {**it['I3_SW_L2_L3_ROUTE_GENERATION_AND_CONTENT'],
                       'what_is_now_settled': ['route exists in TIP_COMPILER.inject_sw for L1/L2/L3',
                                               'each CURRENT pointer resolves to an existing release and standard root',
                                               'derived content max == pointer formal_data_asof == 2026-09-24 at all three levels',
                                               'gate_pass true, thin_days 0, 13 partition years each'],
                       'what_remains_open': ['whether the candidate inherits exactly these releases (it inherits by name reference)'],
                       'decision_needed': 'ACCEPT_ROUTE_QUALIFICATION; CANDIDATE_INHERITANCE_STAYS_REFERENCE_ONLY'},
                'I4': {**it['I4_READER_GENERATION_BINDING'],
                       'what_is_now_settled': it['I4_READER_GENERATION_BINDING']['divergence'],
                       'what_remains_open': ['which reader path is authorized as the generation authority'],
                       'decision_needed': 'DECLARE_POINTER_AS_THE_ONLY_GENERATION_AUTHORITY_AND_HAVE_SEAL_CARRY_IT'}},
            'bodies': 'see NARROWING_SOURCE_BODIES.json (byte-exact base64 carriers)',
            **FLAGS}

# -------------------------------------------------------------- manifest ----
wj('R09_CONTROL_AND_ENTRY_RESULTS.json', results)
wj('SIX_LAYER_EVIDENCE_MATRIX.json', matrix)
wj('FOUR_UNRESOLVED_ITEMS_NARROWED.json', narrowed)
wj('NARROWING_SOURCE_BODIES.json', {'schema': 'R09_NARROWING_SOURCE_BODIES_1',
                                    'payload_encoding': 'BASE64_ORIGINAL_BYTES',
                                    'count': len(EV['narrowing_bodies']),
                                    'bodies': EV['narrowing_bodies'], **FLAGS})
print(json.dumps({'status': 'R09_DELIVERY_ARTIFACTS_WRITTEN',
                  'files': sorted(p.name for p in OUT.iterdir() if p.is_file())}, ensure_ascii=True))
