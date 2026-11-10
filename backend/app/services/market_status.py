"""Open or closed status per exchange.

Weekends and normal trading hours are handled. Public holidays are not,
so the response says so explicitly.
"""
from datetime import datetime, time
from zoneinfo import ZoneInfo

from app.schemas.stock import ExchangeStatusOut

SESSIONS = {
    "JSE": ("Africa/Johannesburg", time(9, 0), time(17, 0)),
    "NYSE": ("America/New_York", time(9, 30), time(16, 0)),
    "NASDAQ": ("America/New_York", time(9, 30), time(16, 0)),
}
NOTE = "Based on weekday trading hours. Public holidays are not accounted for."


def exchange_status(now_utc: datetime | None = None) -> list[ExchangeStatusOut]:
    now_utc = now_utc or datetime.now(ZoneInfo("UTC"))
    out = []
    for name, (tz, opens, closes) in SESSIONS.items():
        local = now_utc.astimezone(ZoneInfo(tz))
        is_open = local.weekday() < 5 and opens <= local.time() < closes
        out.append(
            ExchangeStatusOut(
                exchange=name,
                is_open=is_open,
                local_time=local.strftime("%Y-%m-%d %H:%M %Z"),
                opens=opens.strftime("%H:%M"),
                closes=closes.strftime("%H:%M"),
                note=NOTE,
            )
        )
    return out
