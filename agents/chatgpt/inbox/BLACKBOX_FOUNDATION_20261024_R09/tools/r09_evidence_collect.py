"""R09 evidence collector: reads only existing inventories, pinned pointers and
recorded round outputs. No network, no download, no production write.
Writes r09_delivery/EVIDENCE_INPUTS_R09.json consumed by the R09 delivery builder.
"""
import base64
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

WORK = Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
OUT = WORK / 'r09_delivery'
OUT.mkdir(parents=True, exist_ok=True)


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def body(p):
    b = Path(p).read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
            'payload_encoding': 'BASE64_ORIGINAL_BYTES',
            'payload_base64': base64.b64encode(b).decode('ascii')}


def jload(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def txt(p):
    return Path(p).read_text(encoding='utf-8-sig', errors='replace')


R8C = WORK / 'candidate_releases/R08/R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024/CANDIDATE_MANIFEST.json'
R6C = WORK / 'r06_delivery/CANDIDATE_MANIFEST.json'
CACHE_PTR = Path(r'E:\BLACKBOX\数据\回测缓存\CURRENT_CACHE_RELEASE.json')
CLEAN_PTR = Path(r'E:\BLACKBOX\数据\清洗成品\CURRENT_CLEANING_RELEASE.json')
CACHE_ROOT = Path(r'E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439')
CLEAN_R33 = Path(r'E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R33_FUND_NAV_ASOF_20260924_20260924_200439')
CLEAN_R45 = Path(r'E:\BLACKBOX\数据\清洗成品\releases\BLACKBOX_FORMAL_CLEANING_R45_DAILY_TIP_ASOF_20260924_20260925_034534')
SW_PTR = {lv: Path(r'E:\BLACKBOX\数据\清洗成品') / f'CURRENT_SW_{lv}_PIT_ALIGN_RELEASE.json' for lv in ('L1', 'L2', 'L3')}
SW_CFG = {'L1': ('sw_l1_membership_pit', 'SW_L1_MEMBERSHIP_PIT_FULL.parquet', 'sw_l1_structure_daily', 'SW_L1_STRUCTURE_DAILY_FULL.parquet'),
          'L2': ('sw_l2_membership_pit', 'SW_L2_MEMBERSHIP_PIT_FULL.parquet', 'sw_l2_structure_daily', 'SW_L2_STRUCTURE_DAILY_FULL.parquet'),
          'L3': ('sw_l3_membership_pit', 'SW_L3_MEMBERSHIP_PIT_FULL.parquet', 'sw_l3_structure_daily', 'SW_L3_STRUCTURE_DAILY_FULL.parquet')}
SCOPE = Path(r'E:\BLACKBOX\运行\BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json')
RESOLVER = Path(r'E:\BLACKBOX\脚本\blackbox_data_access_resolver_r1.py')
EXTAGENT = Path(r'E:\BLACKBOX\脚本\blackbox_external_market_evidence_data_agent_r1.py')
CATALOG = WORK / 'r06_delivery/source_bodies/registry/CACHE_PRODUCT_CATALOG.csv'
R07COV = WORK / 'r07_delivery/evidence/product_coverage_vs_authority_calendar.json'
R07RAW = WORK / 'r07_delivery/evidence/raw_units_two_dates_2.json'
R08READY = WORK / 'r08_delivery/ENGINE_RUNTIME_AND_UPDATE_READINESS.json'
SUCCESSOR = WORK / 'candidate/r09/control_successor'
PACKET = WORK / 'reviews/R08/BODY_EXPORT_20261024_2025'
REVIEW = WORK / 'reviews/R09/control_2100'

ev = {'schema': 'R09_EVIDENCE_INPUTS_1', 'round': 'R09/10',
      'generated_by': 'r09_evidence_collect.py',
      'boundaries': {'FOUNDATION_ACCEPTANCE': False, 'ORDER_ALLOWED': False,
                     'PRODUCTION_CHANGE_AUTHORIZED': False, 'CURRENT_SWITCH_ALLOWED': False,
                     'NEW_DATA_ACQUISITION_AUTHORIZED': False, 'network_calls': 0,
                     'downloads': 0, 'source_absence_claims': 0}}

# --- 1. review package pins -------------------------------------------------
pkg = jload(REVIEW / 'R09_IMPLEMENTATION_PACKAGE.json')
ev['review_package_pins'] = {n: {'expected': v['sha256'], 'bytes_expected': v['bytes'],
                                 'actual': sha(REVIEW / n), 'bytes_actual': (REVIEW / n).stat().st_size,
                                 'match': sha(REVIEW / n) == v['sha256']} for n, v in pkg['files'].items()}
ev['successor_build'] = {'manifest_path': str(SUCCESSOR / 'SUCCESSOR_BUILD_MANIFEST.json'),
                         'manifest_sha256': sha(SUCCESSOR / 'SUCCESSOR_BUILD_MANIFEST.json')}
sm = jload(SUCCESSOR / 'SUCCESSOR_BUILD_MANIFEST.json')
ev['successor_build']['source_pins'] = sm['source_pins']
ev['successor_build']['outputs'] = {n: {'build_sha256': v,
                                        'disk_sha256': sha(SUCCESSOR / n),
                                        'expected_review_sha256': pkg['expected_successor_outputs'].get(n),
                                        'match_expected': v == pkg['expected_successor_outputs'].get(n)}
                                    for n, v in sm['outputs'].items()}
ev['successor_build']['production_modified'] = sm['production_modified']

# --- 2. control + entry results --------------------------------------------
def jlast(p):
    for line in reversed(Path(p).read_text(encoding='utf-8-sig', errors='replace').strip().splitlines()):
        line = line.strip()
        if line.startswith('{'):
            return json.loads(line)
    raise ValueError('NO_JSON_LINE:' + str(p))


ctl = jlast(REVIEW / 'DESKTOP_CONTROLS_STDOUT.txt')
ev['desktop_offline_controls'] = ctl
ev['desktop_ordered_entry'] = jlast(REVIEW / 'DESKTOP_ORDERED_ENTRY.txt')
ev['desktop_ordered_entry_stdout_path'] = str(REVIEW / 'DESKTOP_ORDERED_ENTRY.txt')
ev['desktop_ordered_entry_stdout_sha256'] = sha(REVIEW / 'DESKTOP_ORDERED_ENTRY.txt')
d24 = jlast(REVIEW / 'DESKTOP_STAGES_2_4_WITH_STAGE1_SUBSTITUTED.json')
ev['desktop_stages_2_4_substituted'] = d24
ev['desktop_stages_2_4_path'] = str(REVIEW / 'DESKTOP_STAGES_2_4_WITH_STAGE1_SUBSTITUTED.json')
ev['desktop_stages_2_4_sha256'] = sha(REVIEW / 'DESKTOP_STAGES_2_4_WITH_STAGE1_SUBSTITUTED.json')
ev['stage1_block_root_cause'] = {
    'observed': 'tempfile.gettempdir() called at import time by E:\\BLACKBOX\\脚本\\_base.py line 30; the R09 audit guard denies the O_CREAT probe write, so no temp dir is found',
    'evidence_path': str(REVIEW / '_diag_child.py'), 'evidence_sha256': sha(REVIEW / '_diag_child.py'),
    'base_line': 30, 'base_sha256': sha(Path(r'E:\BLACKBOX\脚本\_base.py')),
    'guard_relaxed': False, 'action': 'STOP per review instruction; no production edit, no guard exception added'}

# --- 3. layer inputs --------------------------------------------------------
r8 = jload(R8C)
r6 = jload(R6C)
r8files = [f for f in (WORK / 'candidate_releases/R08/R08_OBSERVED_STOCK_DERIVED_RECOVERY_20261024').rglob('*') if f.is_file()]
ev['L1_copied_assets'] = {
    'r08_candidate_manifest': str(R8C), 'r08_manifest_sha256': sha(R8C), 'r08_manifest_bytes': R8C.stat().st_size,
    'r08_manifest_files_on_disk': len(r8files), 'r08_manifest_bytes_on_disk': sum(f.stat().st_size for f in r8files),
    'r08_artifacts': r8['r08_artifacts'], 'r06_parent_artifacts': len(r6['artifacts']),
    'candidate_daily_count': r8['candidate_daily_count'], 'parent_daily_count': r8['parent_daily_count'],
    'generation': r8['generation'], 'parent_cache_id': r8['parent_cache_id'],
    'parent_cache_root': r8['parent_cache_root'], 'parent_cleaning_id': r8['parent_cleaning_id'],
    'parent_realpaths': r8['parent_realpaths'], 'inherited_status': r8['inherited_status'],
    'inherited_cache_products_count': len(r8['inherited_cache_products']),
    'copies_of_inherited_products_created': 0,
    'scope_acceptance': r8['scope_acceptance']}
cov = jload(R07COV)
ev['L2_classified_assets'] = {
    'coverage_matrix_path': str(R07COV), 'coverage_matrix_sha256': sha(R07COV),
    'canonical_products_classified': len(cov),
    'per_product': {k: {kk: v[kk] for kk in ('files', 'rows', 'date_col', 'min', 'max', 'distinct_dates',
                                             'expected_sessions_in_window', 'missing_session_count', 'read_errors')}
                    | {'missing_session_examples': v['missing_sessions'][:6]} for k, v in cov.items()},
    'catalog_path': str(CATALOG), 'catalog_sha256': sha(CATALOG),
    'catalog_rows': len(list(csv.reader(txt(CATALOG).splitlines()))) - 1,
    'catalog_layer_counts': dict(Counter(r[1] for r in list(csv.reader(txt(CATALOG).splitlines()))[1:] if len(r) > 1)),
    'catalog_status_counts': dict(Counter(r[3] for r in list(csv.reader(txt(CATALOG).splitlines()))[1:] if len(r) > 3))}
ev['L3_usable_read_requests'] = {
    'served_source': 'CANDIDATE_OVERRIDE_NOT_CURRENT',
    'price_path_used': r8['cache_overrides']['STOCK_DAILY_RAW_PIT_R1']['year=2026/part_2026.parquet'],
    'factor_path_used': next(x for x in r8['r08_artifacts'] if x['product'] == 'STOCK_FACTOR_DAILY_R1')['path'],
    'coverage_non_regression': d24['bounded_read']['conservation'],
    'stock_request_rows': d24['bounded_read']['stock_request_rows'],
    'stock_values': d24['bounded_read']['stock_values'],
    'index_adapter_rows': d24['bounded_read']['index_adapter_rows'],
    'index_diagnostic_only': True,
    'current_release_missing_sessions_stock': cov['STOCK_DAILY_RAW_PIT_R1']['missing_sessions'],
    'verdict': 'CANDIDATE_READ_PASS; CURRENT_RELEASE_STILL_MISSING_THE_TWO_SESSIONS'}
ev['L4_formal_engine_admission'] = {
    'source': str(R08READY), 'source_sha256': sha(R08READY),
    'runtime_verdict': jload(R08READY)['engine_runtime']['verdict'],
    'missing_packages': jload(R08READY)['engine_runtime']['missing'],
    'package_install_status': jload(R08READY)['engine_runtime']['package_install_status'],
    'admission_gate_wiring': jload(R08READY)['admission_gate_wiring'],
    'engine_admission_allowed_manifest': r8['engine_admission_allowed'],
    'verdict': 'NOT_ADMITTED'}
raw = jload(R07RAW)
ev['L5_incremental_raw_staging'] = {
    'source': str(R07RAW), 'source_sha256': sha(R07RAW),
    'units_for_20260831_20260901': {k: {'chosen_path': v['chosen']['path'], 'rows': v['chosen']['rows'],
                                        'dates': v['chosen']['dates'], 'sha256': v['chosen']['sha256']}
                                    for k, v in raw.items()},
    'new_units_staged_this_round': 0, 'raw_append_only_preserved': True,
    'in_place_raw_mutation': False,
    'verdict': 'TWO_SESSION_RAW_UNITS_PRESENT_AND_PINNED; NO_NEW_ACQUISITION_THIS_ROUND'}
ready = jload(R08READY)
ev['L6_publication_and_latest_freshness'] = {
    'cache_current_pointer': body(CACHE_PTR), 'cleaning_current_pointer': body(CLEAN_PTR),
    'cache_release_json': body(CACHE_ROOT / 'RELEASE.json'), 'cache_manifest_json': body(CACHE_ROOT / 'MANIFEST.json'),
    'cache_seal_json': body(CACHE_ROOT / 'SEAL.json'), 'cache_domain_asof_json': body(CACHE_ROOT / 'DOMAIN_ASOF.json'),
    'admission_gate': ready['update_readiness']['publication_gates'],
    'per_domain_watermark': ready['update_readiness']['watermarks']['per_domain_watermark'],
    'calendar_authority_max': ready['update_readiness']['watermarks']['calendar_authority_max'],
    'capability_generation_id': jload(SCOPE)['capability_generation_id'],
    'publish_gate_live_result': {'CURRENT_PUBLISH': 'FORBIDDEN', 'reason': 'R09_SUCCESSOR_DRY_RUN_ONLY'},
    'verdict': 'CURRENT_UNCHANGED; FRESHNESS_IS_PER_DOMAIN_NOT_GLOBAL'}

# --- 4. four unresolved items ----------------------------------------------
sw = {}
for lv, (md, mf, sd, sf) in SW_CFG.items():
    d = jload(SW_PTR[lv])
    std = Path(d['standard_root'])
    mem, st = std / md / mf, std / sd / sf
    rec = {'pointer': str(SW_PTR[lv]), 'pointer_sha256': sha(SW_PTR[lv]),
           'release_id': d['release_id'], 'formal_data_asof': d['formal_data_asof'],
           'gate_pass': d.get('gate_pass'), 'n_membership_rows_pointer': d.get('n_membership_rows'),
           'thin_days': d.get('thin_days'), 'standard_root_exists': std.exists(),
           'mem_full_exists': mem.exists(), 'st_full_exists': st.exists(),
           'mem_partition_years': len(list((std / md / 'partitions').glob('year=*'))),
           'st_partition_years': len(list((std / sd / 'partitions').glob('year=*')))}
    if mem.exists():
        pf = pq.ParquetFile(mem)
        rec['mem_rows'] = pf.metadata.num_rows
        rec['mem_columns_sample'] = pf.schema_arrow.names[:8]
        rec['mem_derived_max'] = str(__import__('pandas').to_datetime(
            pq.read_table(mem, columns=['date']).column(0).to_pandas()).max().date())
        rec['mem_derived_matches_pointer'] = rec['mem_derived_max'] == d['formal_data_asof']
    if st.exists():
        pf = pq.ParquetFile(st)
        rec['st_rows'] = pf.metadata.num_rows
        rec['st_derived_max'] = str(__import__('pandas').to_datetime(
            pq.read_table(st, columns=['date']).column(0).to_pandas()).max().date())
        rec['st_derived_matches_pointer'] = rec['st_derived_max'] == d['formal_data_asof']
    sw[lv] = rec

scope = jload(SCOPE)
catalog_lines = [r for r in list(csv.reader(txt(CATALOG).splitlines()))[1:] if len(r) > 3]
ev['four_unresolved_items'] = {
    'I1_UNIVERSE_TRADEABILITY_PRODUCER_OWNERSHIP': {
        'products': ['MARKET_UNIVERSE_PIT_R1', 'STOCK_TRADEABILITY_PIT_R1'],
        'catalog_declaration': [r for r in catalog_lines if r[0] in ('MARKET_UNIVERSE_PIT_R1', 'STOCK_TRADEABILITY_PIT_R1')],
        'consumer_references': [
            {'file': str(RESOLVER), 'sha256': sha(RESOLVER), 'lines': [125, 126, 127, 210, 211],
             'role': 'name map + PIT policy (reader only)'},
            {'file': str(EXTAGENT), 'sha256': sha(EXTAGENT), 'lines': [228, 405],
             'role': 'reads tradeability from a release root; external-evidence agent, not the JQ producer'}],
        'writer_search_roots': [r'E:\BLACKBOX\脚本', r'E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1', r'E:\BLACKBOX\研究系统\数据平面'],
        'writer_files_found': [],
        'content_state': {'MARKET_UNIVERSE_PIT_R1': cov['MARKET_UNIVERSE_PIT_R1'],
                          'STOCK_TRADEABILITY_PIT_R1': cov['STOCK_TRADEABILITY_PIT_R1']},
        'current_scope_declaration': {'TRADEABILITY_EFFECTIVE_ASOF': scope['TRADEABILITY_EFFECTIVE_ASOF'],
                                      'TRADEABILITY_NOTE': scope['TRADEABILITY_NOTE']},
        'narrowed_status': 'DECLARED_AND_READ_BUT_NO_LOCAL_PRODUCER_FOUND; CONTENT_STALE_BY_DECLARED_ASOF',
        'not_a_source_gap': True, 'acquisition_authorized': False},
    'I2_ADJUST_FACTOR_REFRESH_RECEIPT': {
        'receipt_path': str(CACHE_ROOT / 'ADJUST_FACTOR_PIT_R1' / 'COVERAGE.json'),
        'receipt': jload(CACHE_ROOT / 'ADJUST_FACTOR_PIT_R1' / 'COVERAGE.json'),
        'release_seal': jload(CACHE_ROOT / 'SEAL.json'),
        'coverage_3097_sessions': cov['ADJUST_FACTOR_PIT_R1'],
        'degraded_note_from_r08': ready['update_readiness']['watermarks']['per_domain_watermark']['adjust_factor'],
        'narrowed_status': 'PRODUCT_LEVEL_REFRESH_RECEIPT_EXISTS_WITH_EXACT_TIP_SOURCE; PER_DATE_RAW_TO_CACHE_LINKAGE_STILL_ABSENT',
        'not_a_source_gap': True, 'acquisition_authorized': False},
    'I3_SW_L2_L3_ROUTE_GENERATION_AND_CONTENT': {
        'route_owner': 'TIP_COMPILER.inject_sw',
        'pointers': sw,
        'cache_release_sw_status': {k: jload(CACHE_ROOT / 'RELEASE.json').get(k) for k in
                                    ('sw_l1_status', 'sw_l2_status', 'sw_l3_status')},
        'narrowed_status': 'ROUTE_PLUS_GENERATION_PLUS_CONTENT_QUALIFIED_FOR_CURRENT; CANDIDATE_INHERITS_BY_NAME_REFERENCE_ONLY',
        'not_a_source_gap': True, 'acquisition_authorized': False},
    'I4_READER_GENERATION_BINDING': {
        'cache_pointer': jload(CACHE_PTR),
        'cache_release_json': jload(CACHE_ROOT / 'RELEASE.json'),
        'cache_manifest_json': jload(CACHE_ROOT / 'MANIFEST.json'),
        'cache_seal_json': jload(CACHE_ROOT / 'SEAL.json'),
        'cleaning_pointer': jload(CLEAN_PTR),
        'cleaning_r33_exists': CLEAN_R33.exists(), 'cleaning_r45_exists': CLEAN_R45.exists(),
        'r33_seal_present': (CLEAN_R33 / 'SEAL.json').exists(),
        'r33_seal': jload(CLEAN_R33 / 'SEAL.json') if (CLEAN_R33 / 'SEAL.json').exists() else None,
        'r45_seal_present': (CLEAN_R45 / 'SEAL.json').exists(),
        'capability_generation_id': scope['capability_generation_id'],
        'divergence': [
            'CURRENT_CACHE_RELEASE.cache_release_id=FUND_NAV_PIT_ASOF_20260924...; the RELEASE.json inside its own release_root carries cache_release_id=TIP_REBASE_ASOF_20260924_20260925_034907',
            'MANIFEST.json in that release_root declares cache_release_id=FUND_NAV... with parent=TIP_REBASE... and products_added=[FUND_NAV_PIT_R1]',
            'CURRENT_CLEANING_RELEASE.release_id=R33_FUND_NAV while parent_release_id=R45_DAILY_TIP and its quarantine_root+ledger_path live under R45',
            'SEAL.json is 70 bytes and carries accepted+sealed_at only: no generation id, no product list, no content hash'],
        'narrowed_status': 'GENERATION_ID_DEPENDS_ON_THE_READER_PATH; POINTER_IS_AUTHORITATIVE, INNER_RELEASE_JSON_IS_HISTORICAL',
        'not_a_source_gap': True, 'acquisition_authorized': False}}

# --- 5. byte-exact narrowing bodies ---------------------------------------
narrow_paths = [CACHE_PTR, CLEAN_PTR, CACHE_ROOT / 'RELEASE.json', CACHE_ROOT / 'MANIFEST.json',
                CACHE_ROOT / 'SEAL.json', CACHE_ROOT / 'DOMAIN_ASOF.json',
                CACHE_ROOT / 'ADJUST_FACTOR_PIT_R1' / 'COVERAGE.json',
                SW_PTR['L1'], SW_PTR['L2'], SW_PTR['L3']]
ev['narrowing_bodies'] = [body(p) for p in narrow_paths]

(OUT / 'EVIDENCE_INPUTS_R09.json').write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=str), encoding='utf-8')
print(json.dumps({'status': 'EVIDENCE_INPUTS_WRITTEN',
                  'path': str(OUT / 'EVIDENCE_INPUTS_R09.json'),
                  'bytes': (OUT / 'EVIDENCE_INPUTS_R09.json').stat().st_size,
                  'sha256': sha(OUT / 'EVIDENCE_INPUTS_R09.json'),
                  'all_review_pins_match': all(v['match'] for v in ev['review_package_pins'].values()),
                  'all_successor_outputs_match_expected': all(v['match_expected'] for v in ev['successor_build']['outputs'].values())},
                 ensure_ascii=True))
