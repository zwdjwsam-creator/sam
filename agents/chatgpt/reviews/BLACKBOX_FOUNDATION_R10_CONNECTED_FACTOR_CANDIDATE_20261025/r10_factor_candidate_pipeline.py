"""Connected candidate path: response validation -> history-preserving merge.

No SDK, files, publication, engine or orders. Input authority remains external.
"""
import pandas as pd
from r10_factor_input_contract import flatten_factor, daily_axis, require
from r10_factor_response_gate import assemble_responses
from r10_factor_refresh_assembly import assemble_candidate

def candidate_pipeline(cache, plan, replies, prior_overlap, full_refresh,
                       expected_keys, *, required_fq, dirty_codes=()):
    day, source_receipt = assemble_responses(plan, replies, required_fq=required_fq)
    stages = ['REQUEST_RESPONSES_VALIDATED']
    asof = daily_axis([plan['day']]).iloc[0]
    require(isinstance(prior_overlap, pd.DataFrame), 'PRIOR_OVERLAP_FRAME_REQUIRED')
    if not prior_overlap.empty:
        history = flatten_factor(prior_overlap)
        require(history.date.lt(asof).all(), 'OVERLAP_MUST_PRECEDE_REQUEST_DAY')
        observed = pd.concat([history, day], ignore_index=True)
    else:
        observed = day
    stages.append('OVERLAP_BOUNDARY_VALIDATED')
    dirty = set(dirty_codes)
    require(dirty.issubset(set(day.code)), 'DIRTY_CODE_OUTSIDE_REQUEST_DAY')
    if dirty:
        revised = flatten_factor(full_refresh)
        require(set(revised.code) == dirty, 'REFRESH_CODE_SET_NOT_DIRTY_SET')
        require(revised.date.le(asof).all(), 'REFRESH_AFTER_ASOF')
        tip = revised.loc[revised.date.eq(asof)]
        supplied = day.loc[day.code.isin(dirty)]
        joined = tip.merge(supplied, on=['date','code'], how='outer',
                          suffixes=('_refresh','_reply'), indicator=True, validate='one_to_one')
        require(joined['_merge'].eq('both').all(), 'DIRTY_REQUEST_DAY_KEYS_CONFLICT')
        require(joined.factor_refresh.eq(joined.factor_reply).all(), 'DIRTY_REQUEST_DAY_VALUES_CONFLICT')
    else:
        require(full_refresh is None, 'UNDECLARED_FULL_REFRESH_INPUT')
        revised = None
    stages.append('DIRTY_DAY_BOUNDARY_VALIDATED')
    result, merge_receipt = assemble_candidate(cache, observed, revised,
        expected_keys, plan['day'], dirty)
    stages += ['HISTORY_PRESERVING_MERGE_PASSED', 'PUBLICATION_NOT_AUTHORIZED']
    return result, {'status': 'CONNECTED_OFFLINE_CANDIDATE_PASS', 'stages': stages,
        'source_gate': source_receipt, 'merge_gate': merge_receipt,
        'historical_input_authority_proven': False, 'expected_market_universe_proven': False,
        'production_integrated': False, 'publication_authorized': False,
        'FOUNDATION_ACCEPTANCE': False, 'FORMAL_ENGINE_ADMISSION': False,
        'NEW_DATA_ACQUISITION_AUTHORIZED': False, 'CURRENT_SWITCH_ALLOWED': False,
        'ORDER_ALLOWED': False}
