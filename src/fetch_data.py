"""
Download monthly prices, fundamentals, and the S&P 500 via yfinance.

Run once from the repo root:  python src/fetch_data.py
Outputs go to data/raw/ so the rest of the project works from saved files.
"""

from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf

RAW = Path("data/raw")
BENCHMARK = "^GSPC"
N_MONTHS = 60

CANDIDATES = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "AVGO", "ORCL", "ADBE", "CRM",
    "CSCO", "TXN", "QCOM", "INTC", "AMD", "JPM", "BAC", "WFC", "GS", "MS",
    "BLK", "AXP", "C", "V", "MA", "SPGI", "ICE", "CME", "UNH", "JNJ",
    "LLY", "MRK", "ABBV", "AMGN", "GILD", "BMY", "PFE", "TMO", "DHR", "MDT",
    "ABT", "ISRG", "PG", "KO", "PEP", "COST", "WMT", "MCD", "SBUX", "NKE",
    "HD", "LOW", "TGT", "DIS", "CMCSA", "T", "VZ", "XOM", "CVX", "HON",
    "CAT", "DE", "UPS", "LMT", "BA", "MMM", "GE", "NEE", "DUK", "SO",
    "LIN", "SHW", "APD",
]


def month_window(n_months=N_MONTHS):
    """Start/end dates for monthly bars.

    End is the first day of the current month (exclusive), which drops the
    partial current-month bar. Start is n_months + 1 months earlier.
    """
    end = pd.Timestamp(date.today()).replace(day=1)
    start = end - pd.DateOffset(months=n_months + 1)
    return start, end


def fetch_prices(tickers, start, end):
    """Dividend-adjusted monthly closes for tickers + the benchmark."""
    px = yf.download(
        list(tickers) + [BENCHMARK],
        start=start,
        end=end,
        interval="1mo",
        auto_adjust=True,
        progress=False,
    )["Close"]
    return px


def fetch_fundamentals(tickers):
    """Market cap, average volume, price, analyst target, sector (snapshot)."""
    rows = []
    for t in tickers:
        try:
            info = yf.Ticker(t).info
        except Exception:
            info = {}
        rows.append(
            {
                "ticker": t,
                "market_cap": info.get("marketCap"),
                "avg_volume": info.get("averageVolume"),
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "target_mean_price": info.get("targetMeanPrice"),
                "sector": info.get("sector"),
            }
        )
    out = pd.DataFrame(rows)
    out["retrieved"] = date.today().isoformat()
    return out


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    start, end = month_window()
    print(f"Downloading monthly prices {start.date()} -> {end.date()} (exclusive)")

    prices = fetch_prices(CANDIDATES, start, end)
    prices.to_csv(RAW / "prices_monthly.csv")

    print("Downloading fundamentals (one request per ticker, may take a minute)...")
    fundamentals = fetch_fundamentals(CANDIDATES)
    fundamentals.to_csv(RAW / "fundamentals.csv", index=False)

    print(f"Saved {prices.shape[1]} price series and {len(fundamentals)} fundamentals rows to {RAW}/")


if __name__ == "__main__":
    main()