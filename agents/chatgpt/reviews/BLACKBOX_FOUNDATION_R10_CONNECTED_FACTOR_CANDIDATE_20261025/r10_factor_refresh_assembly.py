"""Pure candidate assembly; no acquisition, disk write or publication."""
import pandas as pd
from r10_factor_input_contract import flatten_factor, require
from r10_factor_candidate_merge import candidate_merge


def assemble_candidate(cache, overlap, full_refresh, expected_keys, asof, dirty_codes=()):
    """Retain non-dirty observed overlap while replacing dirty complete histories.

    Inputs must already have separate source/date/basis authority. No such
    authority is created here; the return is never a production admission.
    """
    observed = flatten_factor(overlap)
    dirty = set(dirty_codes)
    if dirty:
        revised = flatten_factor(full_refresh)
        require(set(revised.code) == dirty, 'REFRESH_CODE_SET_NOT_DIRTY_SET')
        fresh = pd.concat([observed.loc[~observed.code.isin(dirty)], revised], ignore_index=True)
    else:
        require(full_refresh is None, 'UNDECLARED_FULL_REFRESH_INPUT')
        fresh = observed
    return candidate_merge(cache, fresh, expected_keys, asof, dirty)
