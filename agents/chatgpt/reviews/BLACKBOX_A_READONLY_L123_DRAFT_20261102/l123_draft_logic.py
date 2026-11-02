"""Pure review prototype. No native launcher, filesystem reader or admission API."""
from bisect import bisect_left
from datetime import date, timedelta
import math


def candidate(*, code, instrument_type, listing_date, execution_date,
              sessions, calendar_start, calendar_end, master_valid,
              exception=None, name_risk=False):
    """Candidate labels only; caller must bind all input identities separately.

    calendar_start/end are explicit reviewed coverage bounds, not inferred from
    the first and last session. No result of this function admits trading.
    """
    if code == '689009.XSHG':
        return 'EXCLUDED_CDR'
    if not master_valid or not instrument_type:
        return 'UNKNOWN_MASTER'
    if instrument_type != 'stock':
        return 'EXCLUDED_NON_ORDINARY'
    if exception == 'NO_LIMIT':
        return 'NO_LIMIT_CANDIDATE'
    if exception not in (None, 'NO_LIMIT'):
        return 'UNKNOWN_EXCEPTION'
    if name_risk:
        return 'UNKNOWN_NAME_RISK'
    if not listing_date:
        return 'UNKNOWN_LISTING_DATE'
    try:
        listing = date.fromisoformat(listing_date)
        execution = date.fromisoformat(execution_date)
        start, end = date.fromisoformat(calendar_start), date.fromisoformat(calendar_end)
        days = [date.fromisoformat(d) for d in sessions]
    except (ValueError, TypeError):
        return 'UNKNOWN_CALENDAR'
    if days != sorted(set(days)) or not days or days[0] < start or days[-1] > end:
        return 'UNKNOWN_CALENDAR'
    if listing > execution or execution < start or execution > end or execution not in days:
        return 'UNKNOWN_CALENDAR'
    if listing < start:
        # An earlier listing is not automatically established as older than five
        # sessions: only five explicitly covered preceding sessions suffice.
        preceding = bisect_left(days, execution)
        if preceding < 5:
            return 'UNKNOWN_CALENDAR'
        return 'LIMITED_CANDIDATE_PENDING_EXCEPTIONS'
    if listing not in days:
        return 'UNKNOWN_LISTING_SESSION'
    ordinal = bisect_left(days, execution) - bisect_left(days, listing) + 1
    if 1 <= ordinal <= 5:
        return 'NO_LIMIT_CANDIDATE'
    return 'LIMITED_CANDIDATE_PENDING_EXCEPTIONS'


def number_state(value):
    if value is None:
        return 'NULL'
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 'NON_NUMERIC'
    if not math.isfinite(value):
        return 'NON_FINITE'
    return 'FINITE'


def profile_flags(row):
    """No mutation, filtering, tolerance, magnitude cutoff or regime inference."""
    fields = ('paused', 'open', 'high_limit', 'low_limit', 'volume', 'money')
    states = {f: number_state(row.get(f)) for f in fields}
    flags = [f + ':' + s for f, s in states.items() if s != 'FINITE']
    good = lambda *fs: all(states[f] == 'FINITE' for f in fs)
    if good('paused') and row['paused'] not in (0, 1):
        flags.append('STATUS_OUTSIDE_0_1')
    if good('high_limit', 'low_limit') and row['high_limit'] <= row['low_limit']:
        flags.append('UPPER_NOT_ABOVE_LOWER')
    if good('paused', 'open', 'high_limit', 'low_limit') and row['paused'] == 0:
        if not row['low_limit'] <= row['open'] <= row['high_limit']:
            flags.append('UNPAUSED_OPEN_OUTSIDE_OBSERVED_BOUNDS')
    for f in fields[1:]:
        if good(f) and row[f] <= 0:
            flags.append(f + (':ZERO' if row[f] == 0 else ':NEGATIVE'))
    return flags
