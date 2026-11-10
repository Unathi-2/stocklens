#!/usr/bin/env bash
# StockLens development helper.
#
#   ./scripts/dev.sh            start everything (same as start)
#   ./scripts/dev.sh start      database, migrations, backend, frontend
#   ./scripts/dev.sh stop       stop backend and frontend
#   ./scripts/dev.sh restart    stop, then start
#   ./scripts/dev.sh status     what is running
#   ./scripts/dev.sh logs       last lines of both logs (add "backend" or "frontend" to follow one)
#   ./scripts/dev.sh refresh    download the latest finished trading days into the database

set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN="$ROOT/.run"
BACK_PID="$RUN/backend.pid"
FRONT_PID="$RUN/frontend.pid"
mkdir -p "$RUN"

# Keep runtime files out of git.
if [ -f "$ROOT/.gitignore" ] && ! grep -qx ".run/" "$ROOT/.gitignore"; then
  echo ".run/" >> "$ROOT/.gitignore"
fi

say() { printf '%s\n' "$*"; }
fail() { printf 'Problem: %s\n' "$*" >&2; exit 1; }

is_running() { [ -f "$1" ] && kill -0 "$(cat "$1")" 2>/dev/null; }
answers() { curl -fs -o /dev/null --max-time 2 "$1"; }

wait_for() { # url, seconds, name
  local i
  for i in $(seq 1 "$2"); do
    answers "$1" && return 0
    sleep 1
  done
  return 1
}

ensure_docker() {
  local i
  for i in $(seq 1 30); do
    docker info >/dev/null 2>&1 && return 0
    [ "$i" = 1 ] && say "Waiting for Docker to start..."
    sleep 2
  done
  fail "Docker is not responding. Wait a minute and run this again."
}

start_db() {
  ensure_docker
  say "Starting database..."
  (cd "$ROOT" && docker compose up -d db >/dev/null 2>&1) || fail "Could not start the database. Run: docker compose up -d db"
  local id status i
  id="$(cd "$ROOT" && docker compose ps -q db)"
  for i in $(seq 1 30); do
    status="$(docker inspect -f '{{.State.Health.Status}}' "$id" 2>/dev/null || true)"
    if [ "$status" = "healthy" ]; then say "Database is healthy."; return 0; fi
    sleep 2
  done
  fail "The database did not become healthy. Run: docker compose logs db"
}

ensure_dependencies() {
  if ! python3 -c "import fastapi, sqlalchemy, alembic, psycopg, yfinance" >/dev/null 2>&1; then
    say "Installing backend packages (first run after a rebuild)..."
    (cd "$ROOT/backend" && pip install -q -r requirements.txt) || fail "pip install failed."
  fi
  if [ ! -d "$ROOT/frontend/node_modules" ]; then
    say "Installing frontend packages (first run after a rebuild)..."
    (cd "$ROOT/frontend" && npm install --no-audit --no-fund >/dev/null) || fail "npm install failed."
  fi
}

migrate() {
  say "Applying database migrations..."
  (cd "$ROOT/backend" && alembic upgrade head >"$RUN/migrate.log" 2>&1) \
    || fail "Migration failed. See .run/migrate.log"
}

start_backend() {
  if answers "http://localhost:8000/health"; then say "Backend already running."; return 0; fi
  say "Starting backend..."
  cd "$ROOT/backend" || fail "backend folder not found."
  setsid nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload >"$RUN/backend.log" 2>&1 &
  echo $! > "$BACK_PID"
  cd "$ROOT" || true
  wait_for "http://localhost:8000/health" 40 || fail "Backend did not start. See: ./scripts/dev.sh logs backend"
  say "Backend is up on port 8000."
}

start_frontend() {
  if answers "http://localhost:5173"; then say "Frontend already running."; return 0; fi
  say "Starting frontend..."
  cd "$ROOT/frontend" || fail "frontend folder not found."
  setsid nohup npm run dev >"$RUN/frontend.log" 2>&1 &
  echo $! > "$FRONT_PID"
  cd "$ROOT" || true
  wait_for "http://localhost:5173" 40 || fail "Frontend did not start. See: ./scripts/dev.sh logs frontend"
  say "Frontend is up on port 5173."
}

stop_one() { # pidfile, label, pattern
  if is_running "$1"; then
    kill -- "-$(cat "$1")" 2>/dev/null || kill "$(cat "$1")" 2>/dev/null || true
  fi
  rm -f "$1"
  pkill -f "$3" 2>/dev/null || true   # also catches servers started by hand
  say "Stopped $2."
}

do_stop() {
  stop_one "$BACK_PID" "backend" "uvicorn app.main:app"
  stop_one "$FRONT_PID" "frontend" "vite"
}

do_start() {
  start_db
  ensure_dependencies
  migrate
  start_backend
  start_frontend
  say ""
  say "Ready. In Codespaces open the Ports tab and click the globe next to port 5173."
  say "API docs: add /docs to the address of port 8000."
}

do_status() {
  local db="stopped"
  docker info >/dev/null 2>&1 && [ -n "$(cd "$ROOT" && docker compose ps -q db 2>/dev/null)" ] && db="running"
  say "database : $db"
  say "backend  : $(answers http://localhost:8000/health && echo running || echo stopped)"
  say "frontend : $(answers http://localhost:5173 && echo running || echo stopped)"
}

do_logs() {
  case "${1:-}" in
    backend)  tail -n 40 -f "$RUN/backend.log" ;;
    frontend) tail -n 40 -f "$RUN/frontend.log" ;;
    *)
      for f in backend frontend; do
        say "----- $f -----"
        tail -n 15 "$RUN/$f.log" 2>/dev/null || say "(no log yet)"
      done ;;
  esac
}

do_refresh() {
  start_db
  say "Downloading the latest finished trading days..."
  (cd "$ROOT/backend" && python3 -m app.scripts.ingest --years 1)
}

case "${1:-start}" in
  start)   do_start ;;
  stop)    do_stop ;;
  restart) do_stop; sleep 1; do_start ;;
  status)  do_status ;;
  logs)    do_logs "${2:-}" ;;
  refresh) do_refresh ;;
  *) say "Usage: ./scripts/dev.sh [start|stop|restart|status|logs|refresh]"; exit 1 ;;
esac
