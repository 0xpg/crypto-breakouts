from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import Config, backtest, fresh_high, target_weights  # noqa: E402


class TestBreakouts(unittest.TestCase):
    def setUp(self):
        self.dates = pd.date_range("2024-01-01", periods=10, freq="D")
        self.close = pd.DataFrame(
            {"A": [1, 2, 1.5, 1.4, 1.3, 3, 2.5, 2.4, 4, 3.5]},
            index=self.dates,
        )

    def test_freshness_and_reset(self):
        state = fresh_high(self.close, lookback=2, max_age=2)["A"].tolist()
        self.assertEqual(state, [False, True, True, False, False, True, True, False, True, True])

    def test_signal_is_traded_next_day(self):
        cfg = Config(lookbacks=(2,), max_age=1, max_weight=.025)
        weights = target_weights(self.close, config=cfg)
        self.assertEqual(weights.loc[self.dates[1], "A"], 0)
        self.assertEqual(weights.loc[self.dates[2], "A"], .025)

    def test_cost_is_one_way_turnover(self):
        cfg = Config(lookbacks=(2,), max_age=1, max_weight=.025, cost_bps=10)
        opens = pd.DataFrame(100.0, index=self.dates, columns=["A"])
        result = backtest(opens, self.close, config=cfg)
        self.assertAlmostEqual(result.loc[self.dates[2], "cost"], .025 * .001)

    def test_future_close_does_not_change_past_target(self):
        cfg = Config(lookbacks=(2,), max_age=2)
        before = target_weights(self.close, config=cfg)
        changed = self.close.copy()
        changed.iloc[-1] = 1_000
        after = target_weights(changed, config=cfg)
        pd.testing.assert_frame_equal(before.iloc[:-1], after.iloc[:-1])


if __name__ == "__main__":
    unittest.main()
