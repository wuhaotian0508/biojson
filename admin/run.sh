#!/bin/bash
# Start the BioJSON Admin Panel (port 5501)

# Kill any process using port 5501
lsof -ti:5501 | xargs kill -9 2>/dev/null || true

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[ -f "${BASE_DIR}/.env" ] && set -a && source "${BASE_DIR}/.env" && set +a
cd "${BASE_DIR}" && python -m admin.app