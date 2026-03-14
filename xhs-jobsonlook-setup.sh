#!/bin/bash
# jobsonlook xhs-mcp setup - run: bash xhs-jobsonlook-setup.sh
set -e
COOKIE='a1=19cde2b6e95yb5ijk2uz3ywzfe85cfmq6y3fmsuk230000210186; web_session=0400698f68ca2a56648da0f3813b4b119e4731; id_token=VjEAANWvxA6zTTVqZHStfK8lENzoH6m5bpJBCwaTaco7E/VPO+UP2p+dZuvVHm09ZcboUbMMBbz6TYDqcHHKDcocwpU1Wn8gUBZJk/+tHrXSUvy8DzTPJ3A7M91nDX7+ao38F1XR; webId=9ff78b54b2f4ed3fd668057a03acd802; sec_poison_id=37e42b4b-695a-490a-92ae-5fa14514cf90; xsecappid=xhs-pc-web; gid=yjSfdJDY80KyyjSfdJDKdvM7j2vD23VTJ7uqqTJvEuidYiq82Si6A6888Jy8yYK8j80W2SSW; websectiga=f3d8eaee8a8c63016320d94a1bd00562d516a5417bc43a032a80cbf70f07d5c0'
if ! command -v uvx 2>/dev/null; then pip install uv; fi
if ! command -v npx 2>/dev/null; then echo "Need Node.js"; exit 1; fi
printf '[Unit]\nDescription=XHS MCP jobsonlook\nAfter=network.target\n\n[Service]\nEnvironment=XHS_COOKIE=%s\nExecStart=npx --yes mcp-proxy --port 18060 --shell -- uvx --from jobson-xhs-mcp xhs-mcp\nRestart=always\n\n[Install]\nWantedBy=multi-user.target\n' "$COOKIE" | sudo tee /etc/systemd/system/xhs-mcp-jobsonlook.service
echo "Done. Run: sudo systemctl stop xhs-mcp && sudo systemctl enable --now xhs-mcp-jobsonlook"
