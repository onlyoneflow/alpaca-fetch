#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
mkdir -p "$HOME/.local/bin"
ln -sf "$ROOT/alpaca_fetch.py" "$HOME/.local/bin/alpaca-fetch"
chmod +x "$ROOT/alpaca_fetch.py"

MARKER='alpaca-fetch fastfetch'
if ! grep -Fq "$MARKER" "$HOME/.zshrc" 2>/dev/null; then
  cat >> "$HOME/.zshrc" <<'EOF'

# Rotating inline alpaca photo + fastfetch system summary.
if [[ -o interactive && -z "$TMUX" && -z "$SSH_CONNECTION" && -x "$(command -v alpaca-fetch 2>/dev/null)" ]]; then
  alpaca-fetch fastfetch
fi
EOF
fi

printf '%s\n' 'Warming the alpaca cache (up to 20 images)...'
"$HOME/.local/bin/alpaca-fetch" refresh
printf '%s\n' 'Installed. Start a new terminal or run: source ~/.zshrc'
