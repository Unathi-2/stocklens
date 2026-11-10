"""Validation of raw price bars before they reach the database.

Pure Python, no database or network code, so it is easy to unit test.
Rules: drop duplicates, drop bars with missing or non positive prices,
drop bars with negative volume, drop bars where high is below low.
Large calendar gaps are reported but not removed.
"""
from dataclasses import dataclass, field
from datetime import timedelta
import math

from app.services.market_data import PriceBar

GAP_DAYS = 7


@dataclass
class ValidationReport:
    received: int = 0
    kept: int = 0
    duplicates: int = 0
    invalid_prices: int = 0
    negative_volume: int = 0
    high_below_low: int = 0
    gaps: list[str] = field(default_factory=list)

    @property
    def dropped(self) -> int:
        return self.received - self.kept


def _bad_number(x: float | None) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x)) or x <= 0


def validate_bars(bars: list[PriceBar]) -> tuple[list[PriceBar], ValidationReport]:
    report = ValidationReport(received=len(bars))
    seen = set()
    clean: list[PriceBar] = []

    for bar in sorted(bars, key=lambda b: b.date):
        if bar.date in seen:
            report.duplicates += 1
            continue
        seen.add(bar.date)

        if any(_bad_number(v) for v in (bar.open, bar.high, bar.low, bar.close, bar.adjusted_close)):
            report.invalid_prices += 1
            continue
        if bar.volume is None or bar.volume < 0:
            report.negative_volume += 1
            continue
        if bar.high < bar.low:
            report.high_below_low += 1
            continue
        clean.append(bar)

    for prev, cur in zip(clean, clean[1:]):
        if cur.date - prev.date > timedelta(days=GAP_DAYS):
            report.gaps.append(f"{prev.date} to {cur.date}")

    report.kept = len(clean)
    return clean, report
