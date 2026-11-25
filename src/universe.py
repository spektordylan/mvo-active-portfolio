"""
Apply the stock-selection screens and build the returns file.

Run from the repo root:  python src/universe.py

Expects the following in data/raw/
  prices_monthly.csv - date index, one column per ticker plus a benchmark
                       column named 'SPX' (or '^GSPC', renamed on load)
  fundamentals.csv   - columns: ticker, market_cap ($, not millions),
                       avg_volume (shares), price ($)
                       (Bloomberg CUR_MKT_CAP is in $ millions -> multiply by 1e6)

Writes to data/processed/:
  universe.csv - every candidate with its screen flags and 'selected' flag
  returns.csv  - monthly returns for selected stocks + SPX
"""

from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
PROC = Path("data/processed")

MIN_CAP = 2e9             # market cap >= $2bn
MIN_DOLLAR_VOL = 20e6     # avg volume x price >= $20m
MIN_NAMES, MAX_NAMES = 25, 50
N_PRICES = 61             # 60 monthly returns need 61 price points


def load_prices():
    px = pd.read_csv(RAW / "prices_monthly.csv", index_col=0, parse_dates=True)
    return px.rename(columns={"^GSPC": "SPX"})


def screen(prices, fundamentals):
    """Flag each candidate against the three screens, then pick up to MAX_NAMES."""

    f = fundamentals.set_index("ticker").copy()
    stocks = prices.drop(columns="SPX")

    if len(stocks) < N_PRICES:
        print(f"Warning: only {len(stocks)} monthly prices found, expected {N_PRICES}")

    f["dollar_volume"] = f["avg_volume"] * f["price"]
    f["full_history"] = stocks.reindex(columns=f.index).notna().all()
    f["pass_cap"] = f["market_cap"] >= MIN_CAP
    f["pass_volume"] = f["dollar_volume"] >= MIN_DOLLAR_VOL
    f["passed"] = f["full_history"] & f["pass_cap"] & f["pass_volume"]

    # keep the largest passing names
    chosen = f[f["passed"]].sort_values("market_cap", ascending=False).head(MAX_NAMES)
    f["selected"] = f.index.isin(chosen.index)

    if f["selected"].sum() < MIN_NAMES:
        print(f"Warning: only {f['selected'].sum()} names selected, need at least {MIN_NAMES}")
    return f


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    prices = load_prices()
    fundamentals = pd.read_csv(RAW / "fundamentals.csv")

    universe = screen(prices, fundamentals)
    universe.to_csv(PROC / "universe.csv")

    tickers = universe.index[universe["selected"]].tolist()
    returns = prices[tickers + ["SPX"]].pct_change().dropna()
    returns.to_csv(PROC / "returns.csv")

    print(f"{len(fundamentals)} candidates -> {universe['passed'].sum()} passed screens "
          f"-> {len(tickers)} selected")
    print(f"Returns: {returns.shape[0]} months x {returns.shape[1]} series")


if __name__ == "__main__":
    main()