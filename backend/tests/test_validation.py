from datetime import date

from app.services.market_data import PriceBar
from app.services.validation import validate_bars


def bar(d, o=10.0, h=11.0, l=9.0, c=10.5, adj=10.5, v=100):
    return PriceBar(date=d, open=o, high=h, low=l, close=c, adjusted_close=adj, volume=v)


def test_valid_bars_pass_and_are_sorted():
    clean, rep = validate_bars([bar(date(2026, 1, 3)), bar(date(2026, 1, 2))])
    assert [b.date for b in clean] == [date(2026, 1, 2), date(2026, 1, 3)]
    assert rep.dropped == 0


def test_duplicates_removed():
    clean, rep = validate_bars([bar(date(2026, 1, 2)), bar(date(2026, 1, 2))])
    assert len(clean) == 1 and rep.duplicates == 1


def test_invalid_prices_dropped():
    bad = [bar(date(2026, 1, 2), c=0.0), bar(date(2026, 1, 5), o=float("nan"))]
    clean, rep = validate_bars(bad)
    assert clean == [] and rep.invalid_prices == 2


def test_negative_volume_and_high_below_low_dropped():
    clean, rep = validate_bars(
        [bar(date(2026, 1, 2), v=-5), bar(date(2026, 1, 5), h=8.0, l=9.0)]
    )
    assert clean == [] and rep.negative_volume == 1 and rep.high_below_low == 1


def test_large_gap_reported_not_removed():
    clean, rep = validate_bars([bar(date(2026, 1, 2)), bar(date(2026, 2, 2))])
    assert len(clean) == 2 and len(rep.gaps) == 1
