#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [ -x ".venv/Scripts/pocket-tts.exe" ]; then
  exec .venv/Scripts/pocket-tts.exe app
fi

if [ -x ".venv/bin/pocket-tts" ]; then
  exec .venv/bin/pocket-tts app
fi

if command -v uvx >/dev/null 2>&1; then
  exec uvx --from 'pocket-tts[desktop]' pocket-tts app
fi

exec pocket-tts app
