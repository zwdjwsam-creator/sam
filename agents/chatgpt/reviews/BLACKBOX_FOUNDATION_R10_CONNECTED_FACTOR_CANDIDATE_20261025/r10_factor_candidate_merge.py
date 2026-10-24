"""Offline merge guard only. No source access, business writes or admission."""
from __future__ import annotations
import pandas as pd
from r10_factor_input_contract import flatten_factor, daily_axis, require


def keys(frame):
    return set(zip(frame.date, frame.code))


def candidate_merge(cache, incoming, expected_keys, asof, dirty_codes=()):
    """Expected keys must be supplied by a separately verified scope contract.

    This function does not create a universe/calendar grid, choose factor bases,
    prove provenance or publish anything. It checks only its explicit inputs.
    """
    old, new = flatten_factor(cache), flatten_factor(incoming)
    require(isinstance(expected_keys, pd.DataFrame) and
            set(expected_keys.columns) == {'date', 'code'}, 'EXPLICIT_EXPECTED_KEYS_REQUIRED')
    expected = flatten_factor(expected_keys.assign(factor=1.0))
    end = daily_axis([asof]).iloc[0]
    require(expected.date.le(end).all(), 'EXPECTED_KEYS_AFTER_ASOF')
    require(new.date.le(end).all(), 'INCOMING_AFTER_ASOF')
    dirty = set(dirty_codes)
    require(dirty.issubset(set(old.code)), 'DIRTY_CODES_OUTSIDE_PARENT')
    new_keys = keys(new)
    # A changed factor basis cannot stop before the parent's tip for that code.
    require(not (old.code.isin(dirty) & old.date.gt(end)).any(),
            'REVISION_END_BEFORE_PARENT_TIP')
    # Full-code replacement must never discard older observations.
    replaced = old.code.isin(dirty) & old.date.le(end)
    require(keys(old.loc[replaced]).issubset(new_keys), 'DIRTY_HISTORY_KEY_REGRESSION')
    common = old.merge(new, on=['date', 'code'], suffixes=('_old', '_new'),
                       validate='one_to_one')
    conflicts = common.factor_old.ne(common.factor_new)
    require(common.loc[conflicts, 'code'].isin(dirty).all(),
            'VALUE_CONFLICT_REQUIRES_REVISION_CONTRACT')
    # Every already-present key is retained. Equal shared observations need no override.
    kept = old.loc[~replaced]
    kept_keys = keys(kept)
    additions = new.loc[[k not in kept_keys for k in zip(new.date, new.code)]]
    out = flatten_factor(pd.concat([kept, additions], ignore_index=True))
    require(keys(old).issubset(keys(out)), 'PARENT_KEY_REGRESSION')
    require(keys(expected).issubset(keys(out)), 'REQUEST_KEYS_NOT_SERVED')
    return out, {'status': 'OFFLINE_CANDIDATE_INPUTS_CHECKED',
                 'expected_keys_checked': len(expected),
                 'source_absence_claim_allowed': False, 'provenance_proven': False,
                 'calendar_or_universe_authority_proven': False,
                 'publication_authorized': False, 'FOUNDATION_ACCEPTANCE': False}
