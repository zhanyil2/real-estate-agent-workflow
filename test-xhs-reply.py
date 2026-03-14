#!/usr/bin/env python3
"""
Test XHS comment reply - finds a post with comments and replies to the first one.
Run: python3 test-xhs-reply.py
"""
import json
import urllib.request
import time

MCP_URL = "http://localhost:18060/mcp"

def mcp_call(session_id, method, params=None, req_id=1):
    body = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params:
        body["params"] = params
    req = urllib.request.Request(MCP_URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Mcp-Session-Id": session_id},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

def tools_call(session_id, name, arguments, req_id=1):
    return mcp_call(session_id, "tools/call", {"name": name, "arguments": arguments}, req_id)

# 1. Initialize session (use subprocess curl to avoid urllib 400)
import subprocess
init_body = json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}
})
proc = subprocess.run(
    ["curl", "-s", "-D", "-", "-X", "POST", MCP_URL, "-H", "Content-Type: application/json", "-d", init_body],
    capture_output=True, text=True, timeout=15
)
lines = proc.stdout.split("\n")
session_id = ""
for line in lines:
    if line.lower().startswith("mcp-session-id:"):
        session_id = line.split(":", 1)[1].strip().split("\r")[0]
        break
if not session_id:
    print("Failed to get session. Response:", proc.stdout[:500])
    exit(1)
print(f"Session: {session_id[:20]}...")

# 2. Notify initialized
mcp_call(session_id, "notifications/initialized", {})
time.sleep(0.5)

# 3. List feeds
r = tools_call(session_id, "list_feeds", {}, 2)
txt = r.get("result", {}).get("content", [{}])[0].get("text", "")
feeds = json.loads(txt).get("feeds", [])
print(f"Found {len(feeds)} feeds")

# 4. Get detail for first feed to check comments
f = feeds[0]
fid, token = f["id"], f.get("xsecToken", "")
print(f"Checking feed: {fid} - {f.get('noteCard',{}).get('displayTitle','')[:50]}")

r = tools_call(session_id, "get_feed_detail", {
    "feed_id": fid, "xsec_token": token,
    "load_all_comments": True, "limit": 25
}, 3)

txt = r.get("result", {}).get("content", [{}])[0].get("text", "")
if not txt:
    print("No detail content")
    exit(1)

try:
    d = json.loads(txt)
except json.JSONDecodeError:
    print("Detail response (not JSON):", txt[:300])
    exit(1)

# Find comments - structure may vary
comments = d.get("comments", []) or d.get("commentList", [])
note = d.get("note", {})
if note:
    comments = note.get("comments", []) or note.get("commentList", []) or comments

if not comments:
    print("No comments found. Keys:", list(d.keys()))
    exit(0)

# Get first comment we can reply to (not our own)
for c in comments[:10]:
    cid = c.get("id") or c.get("comment_id")
    content = c.get("content", "") or c.get("text", "")
    user = (c.get("user") or {}).get("nickname", "") or c.get("userName", "")
    print(f"  Comment: id={cid} user={user} content={content[:50]}")

first = comments[0]
cid = first.get("id") or first.get("comment_id")
reply_text = "感谢关注～有需要可以私聊我了解更多～"

# 5. Reply
print(f"\nReplying to comment {cid} with: {reply_text}")
r = tools_call(session_id, "reply_comment_in_feed", {
    "feed_id": fid, "xsec_token": token,
    "comment_id": cid, "content": reply_text
}, 4)

if "error" in r:
    print("Reply error:", r["error"])
else:
    print("Reply sent successfully!")
