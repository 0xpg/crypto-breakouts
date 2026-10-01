"""Pure breakout signal and accounting functions."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Config:
    lookbacks: tuple[int, ...] = (10, 20, 40, 80)
    max_age: int = 5
    max_weight: float = 0.025
    cost_bps: float = 10.0
    initial_equity: float = 10_000.0

    def validate(self) -> None:
        if not self.lookbacks or min(self.lookbacks) < 2:
            raise ValueError("lookbacks must contain values >= 2")
        if self.max_age < 1:
            raise ValueError("max_age must be positive")
        if not 0 < self.max_weight <= 1:
            raise ValueError("max_weight must lie in (0, 1]")
        if self.cost_bps < 0 or self.initial_equity <= 0:
            raise ValueError("cost and initial equity must be non-negative/positive")


def fresh_high(close: pd.DataFrame, lookback: int, max_age: int) -> pd.DataFrame:
    """True through ``max_age`` closes after a rolling-high close.

    The rolling window includes the current close. A tied high resets age.
    """
    breakout = close.eq(close.rolling(lookback, min_periods=lookback).max())
    days = pd.DataFrame(
        np.arange(len(close))[:, None], index=close.index, columns=[close.columns[0]]
    ).reindex(columns=close.columns).ffill(axis=1)
    last = days.where(breakout).ffill()
    return (days - last).lt(max_age) & last.notna()


def target_weights(
    close: pd.DataFrame,
    eligible: pd.DataFrame | None = None,
    config: Config = Config(),
) -> pd.DataFrame:
    """Long-only ensemble targets for the next open.

    Each active lookback contributes one equal vote. The combined conviction
    is capped at ``max_weight`` per coin; unused exposure remains cash.
    """
    config.validate()
    votes = sum(
        fresh_high(close, lookback, config.max_age).astype(float)
        for lookback in config.lookbacks
    ) / len(config.lookbacks)
    if eligible is not None:
        votes = votes.where(eligible, 0.0)
    return (votes * config.max_weight).shift(1).fillna(0.0)


def backtest(
    opens: pd.DataFrame,
    close: pd.DataFrame,
    eligible: pd.DataFrame | None = None,
    config: Config = Config(),
) -> pd.DataFrame:
    """Account open-to-open returns with one-way turnover costs."""
    if not opens.index.equals(close.index) or not opens.columns.equals(close.columns):
        raise ValueError("open and close panels must have identical axes")
    weights = target_weights(close, eligible, config)
    asset_return = opens.shift(-1).div(opens).sub(1).fillna(0.0)
    turnover = weights.diff().abs().sum(axis=1)
    turnover.iloc[0] = weights.iloc[0].abs().sum()
    gross = (weights * asset_return).sum(axis=1)
    cost = turnover * config.cost_bps / 10_000
    net = gross - cost
    equity = config.initial_equity * (1 + net).cumprod()
    return pd.DataFrame({
        "gross_return": gross,
        "turnover": turnover,
        "cost": cost,
        "net_return": net,
        "equity": equity,
        "gross_exposure": weights.abs().sum(axis=1),
    })


def summary(daily: pd.DataFrame) -> dict[str, float]:
    net = daily["net_return"]
    years = max(len(net) / 365, 1 / 365)
    peak = daily["equity"].cummax()
    vol = net.std(ddof=1) * np.sqrt(365)
    return {
        "total_return": daily["equity"].iloc[-1] / daily["equity"].iloc[0] - 1,
        "cagr": (daily["equity"].iloc[-1] / daily["equity"].iloc[0]) ** (1 / years) - 1,
        "sharpe": net.mean() * 365 / vol if vol else np.nan,
        "annual_volatility": vol,
        "max_drawdown": (daily["equity"] / peak - 1).min(),
        "annual_turnover": daily["turnover"].mean() * 365,
    }
