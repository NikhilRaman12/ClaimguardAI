#!/usr/bin/env bash
set -euo pipefail

export USE_MONGO="${USE_MONGO:-false}"
export SECRET_KEY="${SECRET_KEY:-local-development-secret-key}"

cd "$(dirname "$0")/../backend"
uvicorn app.main:app --reload --port 8000
