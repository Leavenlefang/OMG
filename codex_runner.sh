#!/usr/bin/env bash
# codex_runner.sh — Thin wrapper around the Codex CLI
#
# Usage: codex_runner.sh <model> <prompt_file>
#
# Reads the prompt from <prompt_file> and passes it to the codex CLI.
# Stdout = generated code  |  Stderr = codex logs/errors
#
# To swap out the AI CLI, edit only this file.

set -euo pipefail

MODEL="${1:?Usage: codex_runner.sh <model> <prompt_file>}"
PROMPT_FILE="${2:?Usage: codex_runner.sh <model> <prompt_file>}"

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "ERROR: prompt file not found: $PROMPT_FILE" >&2
    exit 1
fi

# Load .env from repo root if present (for OPENAI_API_KEY, etc.)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$REPO_DIR/.env" ]]; then
    # shellcheck disable=SC1091
    set -o allexport
    source "$REPO_DIR/.env"
    set +o allexport
fi

PROMPT="$(cat "$PROMPT_FILE")"

# --- Codex CLI invocation ---
# The codex CLI (https://github.com/openai/codex) accepts a prompt via stdin
# or as a positional argument. Adjust the flags to match your installed version.
#
# Common invocation styles:
#   codex --model o4-mini "prompt..."
#   codex chat -q "prompt..."
#
# We use: codex --model <model> "<prompt>" and capture stdout.

exec codex --model "$MODEL" "$PROMPT"
