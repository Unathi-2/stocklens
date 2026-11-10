# Statistical methodology

All calculations live in backend/app/analytics as pure functions and are covered by unit tests.

## Prices

Charts show the close. Return measures use the adjusted close, which includes dividends and splits, so they describe total return.

## Returns

Daily log return: r_t = ln(P_t / P_{t-1}). Log returns add over time and are the usual input to volatility models.

Total return over a window: P_end / P_start minus 1, shown as a percentage.

Cumulative return series: P_t / P_start minus 1, shown as a percentage, so every window starts at zero.

## Volatility

Annualised volatility: the sample standard deviation of daily log returns (n minus 1 in the denominator) multiplied by the square root of 252 trading days. It is a historical measure and says nothing certain about the future.

## Moving averages

Simple moving average over n closes: the mean of the latest n closes. Defined only once n closes exist.

Exponential moving average with span n: alpha = 2 / (n + 1), E_t = alpha * P_t + (1 minus alpha) * E_{t-1}, seeded with the first close and shown once n closes exist.

Averages are computed on the full stored history and then trimmed to the requested window, so the first point of a window is already fully warmed up.

## Not yet implemented

Distribution tests (ADF, ARCH LM, Jarque Bera, Ljung Box), drawdown, value at risk and the GARCH family arrive in phases 7 to 9.
