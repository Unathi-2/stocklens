
## Statistical analysis (phase 7)

Everything below uses daily log returns in percent, computed from adjusted closes, over the selected window. At least 60 returns are required. Tests use a 5% significance level and report the statistic, the p value and a plain reading. A small p value is evidence against the null hypothesis. A large one only means the data do not contradict it.

| Test | Applied to | Null hypothesis | Typical reading for equities |
|---|---|---|---|
| Augmented Dickey Fuller | Log prices | Unit root, not stationary | Not rejected: prices are non stationary |
| Augmented Dickey Fuller | Returns | Unit root, not stationary | Rejected: returns are stationary |
| ARCH LM (5 lags) | Demeaned returns | No ARCH effects | Often rejected: volatility clusters |
| Jarque Bera | Returns | Normal (skewness 0, excess kurtosis 0) | Rejected: fat tails |
| Ljung Box (10 lags) | Returns | No autocorrelation | Often not rejected |
| Ljung Box (10 lags) | Squared returns | No autocorrelation | Often rejected: volatility clustering |

The ADF regression includes a constant and chooses the lag length by AIC. Critical values at 1%, 5% and 10% are reported.

Skewness and excess kurtosis are moment estimators, so a normal distribution has 0 for both.

Correlograms show the autocorrelation function (ACF) of returns and squared returns and the partial autocorrelation function (PACF) of returns, up to 30 lags (fewer for short windows). The dashed band is plus or minus 1.96 divided by the square root of n.

The Q-Q plot compares standardised sorted returns with standard normal quantiles at plotting positions (i minus 0.5) divided by n.

Statsmodels and SciPy provide the test implementations. The unit tests check them on simulated data with known properties: white noise, a random walk, GARCH(1,1) data and Student t data.

## Risk measures (phase 8)

Prices are adjusted closes. Volatility uses daily log returns scaled by the square root of 252, as on the Performance tab. VaR, expected shortfall, Sharpe and Sortino use simple daily returns, because a loss is measured on the value of the position. VaR and ES are reported as positive percentages of the position, over one day.

- **Drawdown**: percentage below the running peak. The worst drawdown reports its peak, trough and recovery date (or not yet recovered), the current drawdown and the longest run of days below a previous peak.
- **Annualised return**: compound rate from first to last price over the elapsed calendar years.
- **Sharpe**: mean daily excess return divided by the standard deviation of daily returns, times the square root of 252. The daily risk free rate is the compound daily equivalent of the annual rate supplied.
- **Sortino**: mean daily excess return divided by the downside deviation, the root mean square of negative excess returns, times the square root of 252.
- **Calmar**: annualised return divided by the absolute maximum drawdown.
- **VaR**: historical (empirical quantile), normal (sample mean and standard deviation) and Cornish-Fisher (normal quantile adjusted for sample skewness and excess kurtosis). 95% and 99% levels.
- **Expected shortfall**: historical (mean of returns at or beyond the historical VaR) and normal (closed form).
- **Kupiec backtest**: each day's historical VaR uses only the previous 250 returns. The proportion of failures test compares the violation rate with 1 minus the confidence level, using a likelihood ratio statistic with one degree of freedom. Needs more than 350 returns.
- **Rolling volatility**: 21 and 63 trading day windows.
- **GARCH(1,1)**: constant mean, normal errors, maximum likelihood through the arch package, on percent log returns. Reports omega, alpha, beta with standard errors, persistence (alpha plus beta), the half life of a shock, the long run volatility when persistence is below 1, log likelihood, AIC, BIC and the conditional volatility path. Needs at least 500 returns.

These describe the past window shown. Other GARCH family models, fat tailed errors and forecasts belong to phase 9.
