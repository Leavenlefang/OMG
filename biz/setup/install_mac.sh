#!/usr/bin/env bash
# install_mac.sh — Install the daily brief as a macOS launchd job
#
# Usage:
#   bash biz/setup/install_mac.sh           # installs at 07:00 daily
#   bash biz/setup/install_mac.sh --hour 8  # installs at 08:00 daily
#   bash biz/setup/install_mac.sh --remove  # uninstalls

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LABEL="com.omg.daily-brief"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
HOUR=7
REMOVE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --hour)   HOUR="$2"; shift 2 ;;
        --remove) REMOVE=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if $REMOVE; then
    launchctl unload "$PLIST" 2>/dev/null || true
    rm -f "$PLIST"
    echo "✅ Daily brief uninstalled."
    exit 0
fi

# Check Python
PYTHON=$(command -v python3 || echo "")
if [[ -z "$PYTHON" ]]; then
    echo "ERROR: python3 not found." >&2
    exit 1
fi

# Check PyYAML
if ! "$PYTHON" -c "import yaml" 2>/dev/null; then
    echo "Installing PyYAML..."
    pip3 install pyyaml
fi

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$REPO_DIR/biz/data"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON}</string>
        <string>${REPO_DIR}/biz/run_daily.py</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>${HOUR}</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>${REPO_DIR}/biz/data/daily.log</string>

    <key>StandardErrorPath</key>
    <string>${REPO_DIR}/biz/data/daily.log</string>

    <key>WorkingDirectory</key>
    <string>${REPO_DIR}</string>

    <!-- Run even if the scheduled time was missed (e.g. Mac was asleep) -->
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

# Load it
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo ""
echo "✅ Daily brief installed!"
echo "   Runs at: ${HOUR}:00 every morning"
echo "   Log:     ${REPO_DIR}/biz/data/daily.log"
echo ""
echo "Test it now:"
echo "   python3 ${REPO_DIR}/biz/run_daily.py --preview"
echo ""
echo "To uninstall:"
echo "   bash ${REPO_DIR}/biz/setup/install_mac.sh --remove"
