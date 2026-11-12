# Deployment

| Part | Service | Why |
| --- | --- | --- |
| Database | Neon (PostgreSQL) | Free tier, no card needed |
| API | Render (Docker web service) | Free tier, builds from `backend/Dockerfile` |
| Frontend | Vercel | Free tier, builds from `frontend/` |
| Daily data | GitHub Actions | `.github/workflows/refresh-data.yml` |

The free API sleeps after inactivity, so the first request after a pause can take about a minute.

## 1. Database (Neon)
1. Create a project and copy the connection string (`postgresql://...?sslmode=require`).
2. From the Codespace, load the schema and data once:
   ```bash
   cd backend
   export DATABASE_URL='<neon connection string>'
   alembic upgrade head
   python -m app.scripts.seed
   python -m app.scripts.ingest --years 5 --profiles
   ```

## 2. API (Render)
1. New, Blueprint, pick the repo. `render.yaml` defines the service.
2. Set `DATABASE_URL` to the Neon string and `CORS_ORIGINS` to the Vercel address (step 3), for example `https://stocklens.vercel.app`.
3. After deploy, open `https://<service>.onrender.com/health` and `/docs`.

## 3. Frontend (Vercel)
1. Import the repo, set Root Directory to `frontend`.
2. Add the environment variable `VITE_API_BASE_URL` = the Render address, without a trailing slash.
3. Deploy. Then put the Vercel address into `CORS_ORIGINS` on Render if it was not known yet.

## 4. Daily refresh
Repo settings, Secrets and variables, Actions: add `DATABASE_URL` (the Neon string). Run the workflow once from the Actions tab to confirm.

## 5. Forecast evaluation data (phase 10)
The evaluation table is created by a migration. In the backend folder run `alembic revision --autogenerate -m "volatility evaluations"`, commit the new file, and run `alembic upgrade head` (Render does this on every start). The batch job needs a database address, so for the live site run it once against Neon from the Codespace:
```bash
cd backend
export DATABASE_URL='<neon connection string>'
alembic upgrade head
python -m app.scripts.evaluate --symbols NPN AAPL
```
Open a new terminal afterwards so the export does not stay active.
