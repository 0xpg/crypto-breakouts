.PHONY: test backtest

test:
	python -m unittest discover -s tests -v

backtest:
	python scripts/run_backtest.py data/panel.csv
