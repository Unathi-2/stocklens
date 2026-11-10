"""yfinance implementation of MarketDataProvider.

yfinance is an unofficial wrapper around Yahoo Finance. It is fine for
prototyping, but check the terms of use before making the app public and
keep the provider interface so a licensed source can replace it.
"""
from datetime import date, timedelta

from app.services.market_data import MarketDataProvider, PriceBar, SymbolMatch


class YFinanceProvider(MarketDataProvider):
    def search_symbols(self, query: str) -> list[SymbolMatch]:
        import yfinance as yf

        results = yf.Search(query, max_results=10).quotes
        return [
            SymbolMatch(symbol=q["symbol"], name=q.get("shortname", ""), exchange=q.get("exchDisp", ""))
            for q in results
            if "symbol" in q
        ]

    def get_history(self, symbol: str, start: date, end: date) -> list[PriceBar]:
        import yfinance as yf

        # auto_adjust=False keeps Close raw and gives a separate Adj Close column.
        # yfinance treats end as exclusive, so add one day.
        df = yf.Ticker(symbol).history(
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            auto_adjust=False,
        )
        bars: list[PriceBar] = []
        for ts, row in df.iterrows():
            bars.append(
                PriceBar(
                    date=ts.date(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    adjusted_close=float(row.get("Adj Close", row["Close"])),
                    volume=int(row["Volume"]) if row["Volume"] == row["Volume"] else 0,
                )
            )
        return bars

    def get_profile(self, symbol: str) -> dict:
        import yfinance as yf

        info = yf.Ticker(symbol).info or {}
        return {
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "country": info.get("country"),
            "currency": info.get("currency"),
            "market_cap": info.get("marketCap"),
        }
