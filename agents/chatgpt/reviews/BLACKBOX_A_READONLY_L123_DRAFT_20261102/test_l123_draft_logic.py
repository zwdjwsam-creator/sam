import copy
import unittest
from l123_draft_logic import candidate, profile_flags


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.kw = dict(code='002270.XSHE', instrument_type='stock',
                       listing_date='2026-09-28', execution_date='2026-10-09',
                       sessions=['2026-09-28', '2026-09-29', '2026-09-30',
                                 '2026-10-08', '2026-10-09', '2026-10-12'],
                       calendar_start='2026-09-28', calendar_end='2026-10-12',
                       master_valid=True)

    def label(self, **changes):
        return candidate(**(self.kw | changes))

    def test_fifth_session_is_no_limit_candidate(self):
        self.assertEqual(self.label(), 'NO_LIMIT_CANDIDATE')

    def test_sixth_is_candidate_only(self):
        self.assertEqual(self.label(execution_date='2026-10-12'), 'LIMITED_CANDIDATE_PENDING_EXCEPTIONS')

    def test_missing_master_never_defaults_limited(self):
        self.assertEqual(self.label(master_valid=False), 'UNKNOWN_MASTER')

    def test_missing_listing_date(self):
        self.assertEqual(self.label(listing_date=None), 'UNKNOWN_LISTING_DATE')

    def test_cdr_excluded_even_without_master(self):
        self.assertEqual(self.label(code='689009.XSHG', master_valid=False), 'EXCLUDED_CDR')

    def test_nonstock(self):
        self.assertEqual(self.label(instrument_type='etf'), 'EXCLUDED_NON_ORDINARY')

    def test_undated_name_risk_does_not_certify_exception(self):
        self.assertEqual(self.label(name_risk=True), 'UNKNOWN_NAME_RISK')

    def test_explicit_no_limit_exception(self):
        self.assertEqual(self.label(exception='NO_LIMIT'), 'NO_LIMIT_CANDIDATE')

    def test_unsupported_exception(self):
        self.assertEqual(self.label(exception='RELISTING_UNDATED'), 'UNKNOWN_EXCEPTION')

    def test_old_listing_insufficient_calendar(self):
        self.assertEqual(self.label(listing_date='2000-01-01'), 'UNKNOWN_CALENDAR')

    def test_old_listing_five_preceding_covered_sessions(self):
        self.assertEqual(self.label(listing_date='2000-01-01', execution_date='2026-10-12'), 'LIMITED_CANDIDATE_PENDING_EXCEPTIONS')

    def test_future_listing(self):
        self.assertEqual(self.label(listing_date='2026-10-12'), 'UNKNOWN_CALENDAR')

    def test_listing_on_unlisted_session(self):
        self.assertEqual(self.label(listing_date='2026-10-01'), 'UNKNOWN_LISTING_SESSION')

    def test_execution_outside_calendar(self):
        self.assertEqual(self.label(execution_date='2026-10-28'), 'UNKNOWN_CALENDAR')

    def test_duplicate_calendar(self):
        self.assertEqual(self.label(sessions=self.kw['sessions'] * 2), 'UNKNOWN_CALENDAR')


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(paused=0, open=17.87, high_limit=19.82, low_limit=16.22,
                        volume=14076869., money=254286654.36)

    def test_sample(self):
        self.assertEqual(profile_flags(self.row), [])

    def test_null_is_not_silently_removed(self):
        r = self.row | {'open': None}
        self.assertIn('open:NULL', profile_flags(r))

    def test_nan(self):
        self.assertIn('money:NON_FINITE', profile_flags(self.row | {'money': float('nan')}))

    def test_infinity(self):
        self.assertIn('high_limit:NON_FINITE', profile_flags(self.row | {'high_limit': float('inf')}))

    def test_boolean_is_not_numeric_status(self):
        self.assertIn('paused:NON_NUMERIC', profile_flags(self.row | {'paused': False}))

    def test_string_is_not_coerced(self):
        self.assertIn('volume:NON_NUMERIC', profile_flags(self.row | {'volume': '1'}))

    def test_reversed_limits(self):
        self.assertIn('UPPER_NOT_ABOVE_LOWER', profile_flags(self.row | {'high_limit': 1.}))

    def test_paused_does_not_trigger_open_bounds_flag(self):
        self.assertNotIn('UNPAUSED_OPEN_OUTSIDE_OBSERVED_BOUNDS', profile_flags(self.row | {'paused': 1, 'open': 1.}))

    def test_zero_volume_retained_and_flagged(self):
        self.assertIn('volume:ZERO', profile_flags(self.row | {'volume': 0.}))

    def test_arbitrary_large_value_not_called_regime(self):
        self.assertEqual(profile_flags(self.row | {'high_limit': 1e200}), [])

    def test_inputs_unchanged(self):
        before = copy.deepcopy(self.row)
        profile_flags(self.row)
        self.assertEqual(self.row, before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
