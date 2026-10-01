# Crypto Breakouts

Configurable Python backtester for long-only crypto breakout strategies.

This is a backtesting tool, not a live trading bot or investment advice.

## Default rule

At each daily close:

1. Mark a breakout when the close equals its rolling 10, 20, 40, or 80-day high.
2. Keep each rule active while that high is fewer than five closes old; a new high resets the clock.
3. Average the four binary states and multiply by a 2.5% per-coin cap.
4. Fill the target at the next open and leave unused capital in cash.
5. Charge 10 bps per unit of one-way turnover.

The engine is long-only and leaves unused exposure in cash.

## Data contract

Provide a long CSV with one row per UTC date and contract:

| Column | Meaning |
|---|---|
| `date` | UTC daily session |
| `symbol` | Stable contract identifier |
| `open` | Next-open execution and marking price |
| `close` | Breakout signal price |
| `eligible` | Optional point-in-time universe membership |

Use `eligible` to supply any point-in-time universe rule. If omitted, every observed symbol is eligible.

## Run

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/run_backtest.py data/panel.csv
```

Every strategy parameter is configurable. For example:

```powershell
python scripts/run_backtest.py data/panel.csv `
  --lookbacks 20 40 80 `
  --max-age 3 `
  --max-weight 0.01 `
  --cost-bps 15 `
  --initial-equity 25000
```

Run `python scripts/run_backtest.py --help` for the complete interface.

The runner writes `results/daily.csv` and prints total return, CAGR, Sharpe, annual volatility, maximum drawdown, and turnover.

## Repository map

| Path | Purpose |
|---|---|
| `engine.py` | Pure breakout, target, accounting, and summary functions |
| `scripts/run_backtest.py` | CSV-to-results command-line runner |
| `tests/test_engine.py` | Synthetic freshness, timing, cost, and causality checks |

## Known limits

- Funding, spread, impact, liquidation, margin tiers, and venue failure are excluded.
- Daily opens cannot model intraday execution or liquidation paths.
- Flat costs do not model capacity.
- Results vary materially by year and market-cap bucket.
- Adjacent lookbacks are correlated views of one feature, not four independent strategies.
