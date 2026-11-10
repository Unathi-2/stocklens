# Development guide

## Every time you open or restart the Codespace

    ./scripts/dev.sh

This starts the database, applies migrations, then starts the backend (port 8000) and the frontend (port 5173) in the background and waits until both answer. Open the Ports tab and click the globe next to 5173.

## Other commands

| Command | What it does |
|---|---|
| ./scripts/dev.sh status | Shows what is running |
| ./scripts/dev.sh restart | Stops and starts everything |
| ./scripts/dev.sh stop | Stops the backend and frontend |
| ./scripts/dev.sh logs | Last lines of both logs |
| ./scripts/dev.sh logs backend | Follow the backend log (Ctrl+C to leave) |
| ./scripts/dev.sh refresh | Download the latest finished trading days |

Logs are in .run/ and are not committed.

## When something is wrong

1. The page says "API offline": run ./scripts/dev.sh status, then ./scripts/dev.sh restart.
2. The script says the database is not healthy: run docker compose logs db.
3. A port is already in use: ./scripts/dev.sh stop, then start again.
4. Packages missing after a container rebuild: the script reinstalls them on the next start.

## Saving Codespace hours

Stop the Codespace when you finish (Command palette, "Codespaces: Stop Current Codespace"). Everything in the repo and the database volume is kept. Run ./scripts/dev.sh when you come back.

## Keeping data current

Prices are stored daily closes. Run ./scripts/dev.sh refresh once a day, after markets close, to add the newest finished days.
