
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
