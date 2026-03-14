#!/bin/bash
# Apply cookies.json to xiaohongshu-mcp and restart
# Usage: ./apply-xhs-cookies.sh [path/to/cookies.json]
COOKIES="${1:-cookies.json}"
DEST="/root/xiaohongshu-mcp/cookies.json"

[[ -f "$COOKIES" ]] || { echo "File not found: $COOKIES"; exit 1; }

# Validate JSON
python3 -c "import json; json.load(open('$COOKIES'))" || { echo "Invalid JSON"; exit 1; }

sudo cp "$COOKIES" "$DEST" && sudo systemctl restart xhs-mcp
echo "Done. Cookies applied, xhs-mcp restarted."
