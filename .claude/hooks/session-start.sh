#!/usr/bin/env bash
# SessionStart hook: ensure the project can run its tests/linters in a fresh
# (e.g. Claude Code on the web) session. Installs Python dependencies quietly.
set -euo pipefail
cd "$(dirname "$0")/.."
if command -v pip >/dev/null 2>&1; then
  pip install --quiet -r requirements.txt 2>/dev/null || true
fi
echo "AUTOGENESIS environment ready (run: python -m pytest)"
