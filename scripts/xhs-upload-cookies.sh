#!/bin/bash
# 上传 cookies.json 到服务器并重启 XHS MCP
# 用法: ./xhs-upload-cookies.sh [cookies.json] [user@host]
COOKIES="${1:-cookies.json}"
SERVER="${2:-root@localhost}"
[[ -f "$COOKIES" ]] || { echo "文件不存在: $COOKIES"; exit 1; }
scp "$COOKIES" "$SERVER:/root/xiaohongshu-mcp/cookies.json" && ssh "$SERVER" "systemctl restart xhs-mcp"
echo "Done"
