#!/usr/bin/env bash
set -e

BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_PORT=${PORT:-10000}

echo "[entrypoint] Starting FastAPI on $BACKEND_HOST:$BACKEND_PORT ..."
python -m uvicorn backend.main:app --host $BACKEND_HOST --port $BACKEND_PORT &

echo "[entrypoint] Waiting for backend..."
sleep 5

echo "[entrypoint] Starting Next.js on port $FRONTEND_PORT ..."
exec npx next start -p $FRONTEND_PORT
