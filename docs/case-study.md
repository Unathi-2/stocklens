# StockLens research case study

## Project question

How do common conditional volatility models compare when forecasting the next trading day's variance for JSE and US equities, and how sensitive are the rankings to the realised variance proxy used for evaluation?

This is a model comparison exercise, not a claim that one model is universally best. The appropriate model can vary by asset, sample period, market regime, and evaluation loss.

## Why volatility modelling matters

Return variance changes over time. Periods of large price movements can cluster, and negative and positive shocks may have different relationships with future volatility. A useful comparison therefore needs more than fitting a model and reporting an in sample information criterion. It should examine forecasts on observations not used to estimate the model and report uncertainty in the comparison.

## Current experimental design

### Data and response

StockLens stores daily equity price history for supported JSE and US listings. The volatility workflow computes daily log returns from adjusted closing prices and expresses returns in percentage units. The rolling evaluation uses three realised variance proxies:

1. Squared close to close log return.
2. Parkinson range estimator based on the daily high and low.
3. Garman Klass range estimator based on the daily open, high, low, and close.

The two range estimators do not fully capture overnight gaps. StockLens therefore rescales each range proxy to match the mean squared return proxy over the evaluation sample. The scale factor is reported with the results. This is a practical comparability adjustment, not a claim that the proxies become identical.

### Models

The current out of sample comparison includes six conditional variance specifications:

- sGARCH(1,1)
- EGARCH(1,1)
- GJR GARCH(1,1)
- FIGARCH(1,d,1)
- APARCH(1,1)
- A project implementation of fGARCH

The default evaluation uses a 500 return estimation window and re estimates every 20 trading days. Parameters are held fixed between refits while the variance recursion generates one day ahead forecasts. If a model refit fails, the previous successful parameters are reused where available and the failure is counted.

### Evaluation

For each model, the application reports:

- Mean QLIKE and mean squared error, with model ranks.
- Diebold Mariano comparisons against sGARCH.
- Model Confidence Set p values and membership at the configured significance level.
- Forecast counts, model refit failures, and non convergence counts.
- The selected variance proxy, scaling factor, and evaluation dates.

QLIKE and mean squared error summarise different aspects of forecast performance. Diebold Mariano results test equal expected loss against the chosen benchmark, while the Model Confidence Set identifies models that cannot be distinguished from the best performing set at the chosen level. Neither procedure guarantees future performance.

## Reproducing the evaluation

With the database running, migrations applied, and price history ingested, run from the `backend/` directory:

```bash
python -m app.scripts.evaluate --symbols NPN AAPL
```

Use symbols that exist in your local database. The default settings use a 500 return estimation window and a 20 trading day refit interval. A shorter configuration can be used for development:

```bash
python -m app.scripts.evaluate --symbols NPN --window 300 --refit-every 40
```

The resulting forecasts and diagnostics are stored in the database and exposed through the stock forecast evaluation endpoint. Reproduction depends on the price data available at the time of the run and the package versions in the environment.

## How to interpret the results responsibly

- Prefer conclusions that are consistent across several evaluation proxies and a range of stocks.
- Check the number of usable forecast days and the model failure and non convergence counts before comparing ranks.
- Treat small ranking differences cautiously. Statistical uncertainty can mean that several models remain in the Model Confidence Set.
- Do not equate a low average loss on one historical period with a reliable investment signal.
- Inspect data coverage and the chosen date range. A single ticker or period cannot support broad claims about an entire market.

## Current limitations

The current evaluation has several explicit limits:

- It focuses on one day ahead variance forecasts.
- It uses normal innovations in the six model specifications.
- Diebold Mariano comparisons use sGARCH as the benchmark.
- The Model Confidence Set uses a circular block bootstrap with 1,000 draws and a fixed random seed.
- The realised variance proxies are imperfect and the range proxies require scaling.
- The initial results are asset and period specific. A broader empirical conclusion requires repeated evaluation across more securities and distinct market regimes.
- Machine learning and deep learning benchmarks, including HAR, boosting, LSTM, and hybrid models, are planned extensions and are not included in the current six model comparison.

These limitations define the next research steps: expand the asset and period evaluation, test alternative innovation distributions, add carefully validated machine learning baselines, and compare stability across regimes before making broader claims.

## Related documentation

- [Methodology and formulas](methodology.md)
- [Development guide](development.md)
- [Roadmap](roadmap.md)
- [Project README](../README.md)
