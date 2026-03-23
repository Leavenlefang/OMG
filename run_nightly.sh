#!/usr/bin/env bash
# run_nightly.sh — Entry point invoked by cron / systemd timer
#
# This script changes to the repo directory, sources the .env file,
# and delegates everything to orchestrator.py.
#
# Cron example (runs daily at 02:00):
#   0 2 * * * /home/user/OMG/run_nightly.sh >> /home/user/OMG/logs/cron.log 2>&1

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Load environment variables (API keys, etc.)
if [[ -f ".env" ]]; then
    set -o allexport
    # shellcheck disable=SC1091
    source ".env"
    set +o allexport
fi

# Ensure log directory exists
mkdir -p logs

# Run orchestrator
echo "[$(date '+%Y-%m-%d %H:%M:%S')] run_nightly.sh starting"
python3 orchestrator.py
EXIT_CODE=$?
echo "[$(date '+%Y-%m-%d %H:%M:%S')] run_nightly.sh finished (exit $EXIT_CODE)"

exit $EXIT_CODE
