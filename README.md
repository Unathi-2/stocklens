# StockLens

StockLens is an interactive financial analytics platform for exploring JSE and US equities, studying return behaviour and downside risk, and comparing statistical volatility models. It is built as a data science portfolio project with an emphasis on transparent methodology and reproducible evaluation.

**Live application:** https://stocklens-rouge.vercel.app  
**Source code:** https://github.com/Unathi-2/stocklens

StockLens is for education and research. It does not trade, provide personalised investment advice, or tell users what to buy.

## What it does

- Explore JSE and US equities through market views, stock search, profiles, and interactive price charts.
- Inspect daily returns, distributional properties, stationarity, serial dependence, and ARCH effects.
- Compare risk measures including drawdown, annualised volatility, Sharpe and Sortino ratios, historical and parametric VaR, and expected shortfall.
- Fit and inspect six conditional volatility specifications: sGARCH, EGARCH, GJR GARCH, FIGARCH, APARCH, and a project implementation of fGARCH.
- Compare one day ahead out of sample variance forecasts with QLIKE and mean squared error.
- Inspect Diebold Mariano comparisons against an sGARCH benchmark and Model Confidence Set results.

## What makes the project useful

The goal is to make the reasoning behind an analytical result inspectable, not to present a model score without context.

- JSE and US market coverage in one application.
- Statistical tests are accompanied by their hypotheses and interpretations.
- Forecast models are compared on a chronological out of sample evaluation, rather than only on the data used to fit them.
- Forecast losses, variance proxies, model failures, non convergence counts, and evaluation settings are retained with the stored run.
- The methodology and known limitations are documented in the repository.

## Forecast evaluation at a glance

The current evaluation compares six volatility models using rolling estimation. By default, models are estimated on 500 prior daily log returns and re estimated every 20 trading days. Forecasts are evaluated against squared return, Parkinson, and Garman Klass realised variance proxies.

The evaluation reports QLIKE and mean squared error, model ranks, Diebold Mariano tests, and a Model Confidence Set at a 10% significance level. Range based proxies are rescaled to match the mean squared return proxy over the evaluation period. The selected proxy, scale factor, sample size, dates, model failures, and convergence information are exposed to help users interpret the results.

These comparisons are not proof that one model will perform best in the future. Results depend on the ticker, evaluation period, proxy, estimation settings, and assumptions. The current setup uses one day ahead forecasts and normal innovations. See [the methodology](docs/methodology.md) for details and limitations.

## Technology

| Layer | Tools |
| --- | --- |
| Frontend | React, TypeScript, Tailwind CSS, Lightweight Charts |
| API | FastAPI, Pydantic |
| Data layer | PostgreSQL, SQLAlchemy, Alembic |
| Analytics | Python, NumPy, pandas, SciPy, statsmodels, arch |
| Delivery | Docker, GitHub Actions, Vercel, Render |

## Run locally in GitHub Codespaces

1. Open this repository in a Codespace.
2. Start the development environment:

   ```bash
   ./scripts/dev.sh
   ```

3. Open the forwarded frontend port 5173. The app should report that the API is online.

The helper starts the database, applies migrations, and launches the backend and frontend. For manual startup, start PostgreSQL with `docker compose up -d db`, then run the backend from `backend/` with `uvicorn app.main:app --reload` and the frontend from `frontend/` with `npm run dev`.

Run the backend test suite with:

```bash
cd backend
pytest -q
```

Build the frontend with:

```bash
cd frontend
npm install
npm run build
```

For setup details, see [the development guide](docs/development.md) and [deployment guide](docs/deployment.md).

## Reproduce the rolling forecast evaluation

After the database is populated and migrations are current, run the evaluation from the backend directory:

```bash
python -m app.scripts.evaluate --symbols NPN AAPL
```

Replace the symbols with companies available in your database. The default uses a 500 return estimation window and refits every 20 trading days. For a shorter development run, you can set the options explicitly, for example:

```bash
python -m app.scripts.evaluate --symbols NPN --window 300 --refit-every 40
```

The evaluation stores the forecasts and diagnostics in the database. It can take time because each model is repeatedly re estimated. The app does not fabricate evaluation results when no stored run exists.

## Project documentation

- [Product definition](docs/product.md), goals, intended users, and non goals.
- [Architecture](docs/architecture.md), application boundaries and component responsibilities.
- [Data pipeline](docs/data-pipeline.md), ingestion and refresh process.
- [Statistical methodology](docs/methodology.md), formulas, tests, model assumptions, and evaluation limitations.
- [Research case study](docs/case-study.md), research question, experimental design, and interpretation guide.
- [Roadmap](docs/roadmap.md), completed work and planned extensions.

## Roadmap

The deployed application includes market data ingestion, stock analytics, risk measures, volatility models, and an out of sample evaluation workflow. Planned extensions include broader machine learning and deep learning volatility benchmarks, watchlists, paper portfolios, and additional operational hardening. The roadmap tracks these separately from the features available today.

## Disclaimer

StockLens is an educational analytics tool. Historical estimates and model forecasts are uncertain and are not financial advice.
