#!/bin/bash
# Redeploy the site and Worker after new trace data or model changes.
# Run from the repo root: ./scripts/deploy.sh
set -e

cd "$(dirname "$0")/.."
source .venv/bin/activate

echo "==> exporting site data"
python scripts/export_site_data.py
python scripts/export_detector_weights.py

echo "==> deploying Worker"
(cd web/worker && npx wrangler deploy)

echo "==> freezing site"
(cd web && WORKER_BASE_URL="https://agent-red-teamer-api.bhuvism003.workers.dev" python freeze.py)

echo "==> deploying Pages"
(cd web && npx wrangler pages deploy build --project-name=agent-red-teamer)

echo "==> done"
