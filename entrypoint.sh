#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/venv/bin:$PATH"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${PORT:-10000}"

echo "[entrypoint] Starting FastAPI on ${BACKEND_HOST}:${BACKEND_PORT} ..."
# Use the virtualenv's python specifically to ensure consistency
/opt/venv/bin/python -m uvicorn backend.main:app --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" &
BACK_PID=$!

echo "[entrypoint] Waiting for backend /health ..."
for i in {1..60}; do
  if curl -fsS "http://${BACKEND_HOST}:${BACKEND_PORT}/health" >/dev/null 2>&1; then
    echo "[entrypoint] Backend is ready."
    break
  fi
  if ! kill -0 "${BACK_PID}" 2>/dev/null; then
    echo "[entrypoint] Backend process exited unexpectedly."
    wait "${BACK_PID}" || true
    exit 1
  fi
  sleep 1
done

echo "[entrypoint] Starting Next.js on port ${FRONTEND_PORT} ..."
sleep 5
exec npx next start -p "${FRONTEND_PORT}"
