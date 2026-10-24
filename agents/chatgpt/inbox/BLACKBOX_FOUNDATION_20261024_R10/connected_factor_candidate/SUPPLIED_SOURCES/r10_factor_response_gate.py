"""Pure candidate gate, before concatenation/writing; no SDK, files or admission."""
from __future__ import annotations
import re
import pandas as pd
from r10_factor_input_contract import daily_axis, flatten_factor, require

def request_plan(codes, day, *, fq_arg, batch_size):
    require(isinstance(codes, list) and codes and len(codes) == len(set(codes)), 'INVALID_REQUEST_CODES')
    require(all(isinstance(c, str) and re.fullmatch(r'\d{6}\.(?:XSHE|XSHG)', c) for c in codes),
            'CANONICAL_CODE_REQUIRED')
    require(isinstance(day, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', day), 'EXPLICIT_REQUEST_DAY_REQUIRED')
    daily_axis([day])
    require(fq_arg is None or fq_arg in ('pre', 'post'), 'INVALID_EXPLICIT_FQ_ARGUMENT')
    require(type(batch_size) is int and batch_size > 0, 'INVALID_BATCH_SIZE')
    return {'day': day, 'fq_arg': fq_arg, 'frequency': 'daily', 'fields': ['factor'],
            'batches': [codes[i:i + batch_size] for i in range(0, len(codes), batch_size)]}

def assemble_responses(plan, responses, *, required_fq):
    """Validate explicit planned requests and complete replies before any write.

    This checks a supplied request plan, not historical execution or a market universe.
    Missing/failed/empty batches and missing securities stop the candidate, until an
    independently specified exception contract exists. No value or date is inferred.
    """
    require(isinstance(plan, dict) and 'fq_arg' in plan, 'EXPLICIT_FQ_ARGUMENT_REQUIRED')
    require(required_fq is None or required_fq in ('pre', 'post'), 'INVALID_REQUIRED_FQ')
    require(plan['fq_arg'] == required_fq, 'FQ_ARGUMENT_CONSUMER_CONFLICT')
    require(plan.get('frequency') == 'daily' and plan.get('fields') == ['factor'], 'REQUEST_SHAPE_CONFLICT')
    batches = plan.get('batches')
    require(isinstance(batches, list) and batches, 'REQUEST_BATCH_PLAN_REQUIRED')
    flat = [c for b in batches for c in b] if all(isinstance(b, list) for b in batches) else []
    # Revalidate untrusted plan, rather than trusting a prior builder call.
    request_plan(flat, plan.get('day'), fq_arg=plan['fq_arg'], batch_size=max(1, len(flat)))
    require(all(b for b in batches), 'EMPTY_REQUEST_BATCH')
    require(isinstance(responses, list) and len(responses) == len(batches), 'BATCH_RESPONSE_COUNT_CONFLICT')
    day = daily_axis([plan['day']]).iloc[0]
    parts = []
    for i, (codes, reply) in enumerate(zip(batches, responses)):
        require(isinstance(reply, dict) and reply.get('status') == 'OK', 'BATCH_NOT_SUCCESSFUL')
        require(reply.get('batch_index') == i and reply.get('requested_codes') == codes, 'BATCH_REQUEST_BINDING_CONFLICT')
        frame = reply.get('frame')
        require(isinstance(frame, pd.DataFrame) and not frame.empty, 'EMPTY_BATCH_RESPONSE')
        # Existing validator resets a named time/date index before it is discarded.
        # A bare numeric index remains invalid; no request-day replacement is made.
        out = flatten_factor(frame)
        require(out.date.eq(day).all(), 'RESPONSE_DATE_OUTSIDE_REQUEST')
        require(set(out.code) == set(codes), 'BATCH_SECURITY_COVERAGE_CONFLICT')
        parts.append(out)
    out = flatten_factor(pd.concat(parts, ignore_index=True))
    require(len(out) == len(flat), 'DAY_RESPONSE_KEY_COUNT_CONFLICT')
    return out, {'status': 'OFFLINE_RESPONSE_GATE_PASS', 'rows': len(out),
        'batches_checked': len(batches), 'fq_argument': plan['fq_arg'],
        'consumer_required_fq': required_fq, 'binding_scope': 'SUPPLIED_PLAN_AND_RESPONSES_ONLY',
        'historical_execution_proven': False, 'expected_market_universe_proven': False,
        'date_or_factor_filled': False, 'physical_fq_column_added': False,
        'production_install_authorized': False, 'publication_authorized': False,
        'FOUNDATION_ACCEPTANCE': False, 'NEW_DATA_ACQUISITION_AUTHORIZED': False}
