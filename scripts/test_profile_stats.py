import datetime as dt
import unittest
from profile_stats import summarize_activity


def summary(rows, end='2026-11-20'):
    return summarize_activity([(date, count, 0) for date, count in rows], dt.date.fromisoformat(end))


class ActivityStatsTests(unittest.TestCase):
    def test_today_can_still_be_empty(self):
        stats = summary([('2026-11-17', 1), ('2026-11-18', 2), ('2026-11-19', 3), ('2026-11-20', 0)])
        self.assertEqual((stats['current_streak'], stats['longest_streak']), (3, 3))
        self.assertEqual((stats['total'], stats['active'], stats['days'], stats['best_day']), (6, 3, 4, 3))

    def test_two_empty_days_break_current_streak(self):
        stats = summary([('2026-11-17', 2), ('2026-11-18', 1), ('2026-11-19', 0), ('2026-11-20', 0)])
        self.assertEqual((stats['current_streak'], stats['longest_streak']), (0, 2))

    def test_missing_date_breaks_streak(self):
        stats = summary([('2026-11-18', 1), ('2026-11-20', 1)])
        self.assertEqual((stats['current_streak'], stats['longest_streak']), (1, 1))

    def test_twelve_month_window_excludes_old_and_future_counts(self):
        stats = summary([('2025-11-30', 100), ('2025-12-01', 3), ('2026-11-20', 2), ('2026-11-21', 100)])
        self.assertEqual((stats['start'], stats['end'], stats['total']), ('2025-12-01', '2026-11-20', 5))
        self.assertEqual(len(stats['months']), 12)
        self.assertEqual(sum(count for _, count in stats['months']), stats['total'])

    def test_tied_peak_months(self):
        stats = summary([('2026-10-01', 3), ('2026-11-20', 3)])
        self.assertEqual([month for month, count in stats['months'] if count == stats['peak_month']], ['2026-10', '2026-11'])

    def test_zero_activity(self):
        stats = summary([('2026-11-19', 0), ('2026-11-20', 0)])
        self.assertEqual((stats['total'], stats['current_streak'], stats['longest_streak'], stats['peak_month']), (0, 0, 0, 0))

    def test_year_rollover(self):
        stats = summary([('2026-01-02', 1)], '2026-01-02')
        self.assertEqual(stats['start'], '2025-02-01')


if __name__ == '__main__':
    unittest.main()
