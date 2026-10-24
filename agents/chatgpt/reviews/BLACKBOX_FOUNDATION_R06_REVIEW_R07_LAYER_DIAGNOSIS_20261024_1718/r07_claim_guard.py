"""GPT claim boundary: a consumer miss never proves source absence.

Supplement to the existing BLACKBOX diagnosis rules; not a replacement for them.
Inputs are evidence references/hashes, not assertions inferred from filenames.
"""

# No new source-absence receipt has been reviewed/approved by GPT for this task.
# Only a later GPT-authored contract may pin a reviewed receipt here.
APPROVED_SOURCE_ABSENCE_RECEIPTS=frozenset()


def decide(evidence):
    found = evidence.get('source_rows_found', 0) > 0 or bool(evidence.get('source_file_hash_verified'))
    common = {'SOURCE_ABSENCE_CLAIM_ALLOWED':False, 'REDOWNLOAD_ALLOWED':False,
              'MIGRATION_LOSS_PROVEN':False, 'evidence_scope':evidence.get('scope')}
    if found:
        if evidence.get('raw_scope_complete') is True and evidence.get('clean_serves_request') is False:
            code='RAW_COMPLETE_CLEANING_MISSING'
        elif evidence.get('clean_scope_complete') is True and evidence.get('cache_serves_request') is False:
            code='CLEANING_COMPLETE_CACHE_MISSING'
        elif evidence.get('reader_predicate_error'):
            code='READER_DATE_SLICE_MISSING'
        else:
            code='UNKNOWN_STOP'
        return {**common,'classification':code,'action':'REPAIR_IMPORT_INDEX_OR_BINDING; PRESERVE_SOURCE'}
    if evidence.get('r9_content_verified_for_entity'):
        return {**common,'classification':'UNKNOWN_STOP',
                'action':'TRACE_PATH_ALIAS_OR_POST_ACCEPTANCE_CHANGE; DO_NOT_ATTRIBUTE_TO_MIGRATION'}
    closure = evidence.get('search_closure') or {}
    required = ('all_required_layers_searched','all_authorized_roots_accounted',
                'historical_releases_searched','aliases_and_views_resolved',
                'time_field_semantics_verified','universe_and_frequency_verified',
                'no_search_errors','no_unresolved_locations','scope_and_expected_presence_proven')
    closed = all(closure.get(k) is True for k in required)
    prior = evidence.get('existing_diagnoser') or {}
    certified = (prior.get('classification')=='SOURCE_MISSING'
                 and prior.get('completed') is True and bool(prior.get('receipt_path'))
                 and prior.get('receipt_sha256') in APPROVED_SOURCE_ABSENCE_RECEIPTS)
    allowed = closed and certified and not evidence.get('conflicting_positive_evidence')
    return {**common,'classification':'SOURCE_MISSING' if allowed else 'UNKNOWN_STOP',
            'SOURCE_ABSENCE_CLAIM_ALLOWED':allowed,
            'REDOWNLOAD_ALLOWED':bool(allowed and evidence.get('explicit_acquisition_contract')
                 and evidence.get('current_entitlement_verified') and not evidence.get('policy_excluded')),
            'action':'REGISTER_SCOPED_SOURCE_ABSENCE' if allowed else 'COMPLETE_EVIDENCE_CLOSURE; NO_ABSENCE_CLAIM'}


def assert_download_allowed(evidence):
    result=decide(evidence)
    if not result['REDOWNLOAD_ALLOWED']:
        raise ValueError('DOWNLOAD_BLOCKED_WITHOUT_COMPLETE_SCOPED_DIAGNOSIS')
    return result
