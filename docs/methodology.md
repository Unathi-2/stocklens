
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

## Volatility models (phase 9)

Every model uses daily log returns in percent, a constant mean and normal errors, estimated by (quasi) maximum likelihood on the same window, so log likelihood, AIC and BIC are comparable. Volatility is annualised with the square root of 252. At least 500 returns are required.

| Model | Variance equation (z is the standardised shock e / sigma) | Source |
|---|---|---|
| sGARCH(1,1) | sigma2 = omega + alpha e2 + beta sigma2 | arch |
| EGARCH(1,1) | ln sigma2 = omega + alpha (abs(z) - sqrt(2/pi)) + gamma z + beta ln sigma2 | arch |
| GJR-GARCH(1,1) | sigma2 = omega + (alpha + gamma I[e < 0]) e2 + beta sigma2 | arch |
| FIGARCH(1,d,1) | fractionally integrated GARCH, hyperbolic decay of shocks | arch |
| APARCH(1,1) | sigma^delta = omega + alpha (abs(e) - gamma e)^delta + beta sigma^delta | arch |
| fGARCH(1,1) | sigma^delta = omega + alpha sigma^delta (abs(z - eta2) - eta1 (z - eta2))^delta + beta sigma^delta | this project |

fGARCH is the family GARCH of Hentschel (1995) in the form with lambda equal to delta (the ALLGARCH submodel in rugarch). Setting eta2 to 0 gives APARCH, delta to 2 with eta2 to 0 gives GJR like asymmetry, and eta1 and eta2 to 0 with delta 2 gives sGARCH. The `arch` package has no fGARCH, so it is estimated here with L-BFGS-B from two starting points (a GARCH like point and the APARCH solution), and standard errors come from a numerical Hessian. Seven parameters are weakly identified on typical equity samples, so the Hessian is often not positive definite and standard errors are then shown as unavailable. Compare fGARCH mainly through its likelihood and criteria.

Comparison measures:
- **AIC and BIC** from the log likelihood and the number of parameters. The AIC gap to the best model is shown, and a gap under about 2 means the data do not separate the models.
- **Persistence**: sGARCH alpha plus beta, GJR alpha plus gamma/2 plus beta, EGARCH beta, APARCH and fGARCH beta plus alpha times the expectation of the shock function under a standard normal (computed by numerical integration). FIGARCH reports its memory parameter d instead.
- **Half life**: ln(0.5) / ln(persistence), when persistence is between 0 and 1.
- **Standardised residual checks**: Ljung Box (10 lags) on residuals and squared residuals, and Jarque Bera. A small p value on squared residuals means volatility clustering is left over.
- **News impact curve**: next day volatility after a shock of -4 to +4 standard deviations, starting from each model's average conditional volatility. The EGARCH gamma follows the `arch` convention, so a negative gamma means falls raise volatility more than rises.
- **Forecasts**: 10 trading days. sGARCH, GJR and FIGARCH use exact (analytic) recursions. EGARCH, APARCH and fGARCH use 5,000 simulated paths with a fixed seed, so repeated requests agree.

Limits: the comparison is in sample. It does not yet rank models by out of sample forecast loss, which needs rolling re estimation. Normal errors understate tail risk, and fat tailed errors (Student t, skewed t) are a natural next step.

## Out of sample forecast evaluation (phase 10)

Run with `python -m app.scripts.evaluate` (about 15 to 60 seconds per stock). Results are stored, and the API computes the losses and tests from the stored forecasts.

**Scheme.** Each of the six models is estimated on the previous 500 daily log returns and re-estimated every 20 trading days. Between re-estimations the parameters stay fixed while the variance recursion runs forward over new returns, so the one day ahead forecast for day t uses returns up to t-1 only. If a re-estimation fails, the previous parameters are reused and the failure is counted. A test checks that changing later returns does not change earlier forecasts. One small exception: `arch` sets the pre sample variance of FIGARCH from the series it is given, which makes FIGARCH forecasts depend very slightly (below 0.05 percent) on later returns inside the same block.

**Realised variance proxies** (daily, in percent squared): the squared close to close log return of the adjusted close, the Parkinson range estimator ln(H/L)^2 / (4 ln 2), and Garman-Klass 0.5 ln(H/L)^2 - (2 ln 2 - 1) ln(C/O)^2. Range proxies miss the overnight gap, so they are multiplied by a constant that equalises their mean to the mean squared return over the evaluation days (the factor is shown). Days with a proxy of zero or below, or a missing forecast, are dropped for all models.

**Losses.** QLIKE = p/h - ln(p/h) - 1 and MSE = (p - h)^2, where h is the variance forecast and p the proxy. Both are robust to noise in an unbiased proxy (Patton, 2011). QLIKE penalises under prediction more than over prediction.

**Diebold Mariano.** Tests equal expected loss against the benchmark (sGARCH). The loss difference series has Newey West variance with floor(n^(1/3)) lags, the statistic is scaled by the Harvey, Leybourne and Newbold correction and compared with a t distribution on n-1 degrees of freedom, two sided. A positive mean difference means the model has the lower loss.

**Model Confidence Set.** Hansen, Lunde and Nason (2011), range statistic T_max with a circular block bootstrap (1,000 draws, block length floor(n^(1/3)), fixed seed). Models are eliminated one at a time while equal predictive ability is rejected at 10 percent. A model is in the set when its MCS p value is at least 0.10. A large set is common with a few years of data and means the models cannot be separated.

Limits: one day ahead variance only (no multi step evaluation), one benchmark for the pairwise tests, normal errors in every model, and results from a single stock and period, so they say little about other stocks or other times.
