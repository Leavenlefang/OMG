#!/usr/bin/env bash
# install.sh — Set up the nightly cron job for the workflow optimization tool
#
# Usage: bash scripts/install.sh [--hour H] [--minute M] [--remove]
#
# Defaults: runs at 02:00 daily. Pass --hour / --minute to override.
# Pass --remove to uninstall the cron job.

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$REPO_DIR/run_nightly.sh"
LOG="$REPO_DIR/logs/cron.log"
HOUR=2
MINUTE=0
REMOVE=false

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --hour)    HOUR="$2";    shift 2 ;;
        --minute)  MINUTE="$2";  shift 2 ;;
        --remove)  REMOVE=true;  shift   ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--hour H] [--minute M] [--remove]"
            exit 1
            ;;
    esac
done

CRON_ENTRY="$MINUTE $HOUR * * * $SCRIPT >> $LOG 2>&1"
MARKER="# workflow-optimization-tool"

if $REMOVE; then
    echo "Removing cron job..."
    crontab -l 2>/dev/null | grep -v "$MARKER" | crontab - || true
    echo "Done. Cron job removed."
    exit 0
fi

# Make scripts executable
chmod +x "$SCRIPT"
chmod +x "$REPO_DIR/codex_runner.sh"

# Check dependencies
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Please install Python 3." >&2
    exit 1
fi

if ! python3 -c "import yaml" 2>/dev/null; then
    echo "PyYAML not found. Installing..."
    pip install pyyaml
fi

if ! command -v codex &>/dev/null; then
    echo "WARNING: 'codex' CLI not found on PATH."
    echo "  Install it from: https://github.com/openai/codex"
    echo "  Or adjust codex.command in config.yaml to match your binary."
fi

# Check .env
if [[ ! -f "$REPO_DIR/.env" ]]; then
    echo "WARNING: .env not found. Copy .env.example and add your API key:"
    echo "  cp $REPO_DIR/.env.example $REPO_DIR/.env"
    echo "  \$EDITOR $REPO_DIR/.env"
fi

# Install cron job (remove old entry first, then add new one)
echo "Installing cron job: runs at ${HOUR}:$(printf '%02d' $MINUTE) daily..."
mkdir -p "$REPO_DIR/logs"
(crontab -l 2>/dev/null | grep -v "$MARKER"; echo "$CRON_ENTRY $MARKER") | crontab -

echo ""
echo "Cron job installed successfully."
echo "  Schedule : $(printf '%02d' $MINUTE) $(printf '%02d' $HOUR) * * *  (daily at $(printf '%02d' $HOUR):$(printf '%02d' $MINUTE))"
echo "  Script   : $SCRIPT"
echo "  Log      : $LOG"
echo ""
echo "Verify with: crontab -l"
echo "Manual run : python3 $REPO_DIR/orchestrator.py"
echo "Dry run    : python3 $REPO_DIR/orchestrator.py --dry-run"
echo ""

# Print systemd timer alternative
cat <<'EOF'
--- Systemd timer alternative (optional) ---
Create /etc/systemd/system/workflow-opt.service:

  [Unit]
  Description=Daily Workflow Optimization Tool

  [Service]
  Type=oneshot
  ExecStart=/home/user/OMG/run_nightly.sh
  StandardOutput=append:/home/user/OMG/logs/cron.log
  StandardError=append:/home/user/OMG/logs/cron.log

Create /etc/systemd/system/workflow-opt.timer:

  [Unit]
  Description=Run workflow-opt daily at 02:00

  [Timer]
  OnCalendar=*-*-* 02:00:00
  Persistent=true

  [Install]
  WantedBy=timers.target

Then: systemctl daemon-reload && systemctl enable --now workflow-opt.timer
EOF
