"""Debug script to test ilinkai API calls"""
import json
import subprocess
import sys
import time
import random
import os

BOT_TOKEN = "93ce2a55ab54@im.bot:0600001b85c77c7845abfab549157923d42eeb"
WECHAT_USER_ID = "o9cq805lfrS-OgQ59AIP9tamh3Jw@im.wechat"
CONTEXT_TOKEN_FILE = r"C:\Users\Administrator\.openclaw\openclaw-weixin\accounts\93ce2a55ab54-im-bot.context-tokens.json"
ILINK_BASE_URL = "https://ilinkai.weixin.qq.com"

# Load contextToken
with open(CONTEXT_TOKEN_FILE, "r", encoding="utf-8") as f:
    tokens = json.load(f)
ct = tokens.get(WECHAT_USER_ID, "")
print(f"contextToken: len={len(ct)}, first50={repr(ct[:50])}")

# Generate client_id
hexc = "0123456789abcdef"
cid = "openclaw-weixin:" + str(int(time.time() * 1000)) + "-" + "".join(random.choices(hexc, k=8))

# Build message body WITH base_info (like OpenClaw does)
body = {
    "base_info": {
        "channel_version": "2026.5.19",
        "bot_agent": "OpenClaw",
    },
    "msg": {
        "from_user_id": "",
        "to_user_id": WECHAT_USER_ID,
        "client_id": cid,
        "message_type": 3,  # BOT
        "message_state": 2,  # FINISH
        "context_token": ct,
        "item_list": [
            {"type": 1, "text_item": {"text": "debug test: Hello from Python direct API call!"}}
        ],
    }
}

json_body = json.dumps(body, ensure_ascii=False)
print(f"\n=== Sending text message ===")
print(f"Body length: {len(json_body)}")

cmd = [
    "curl", "-s", "-k", "-v",
    "-X", "POST",
    f"{ILINK_BASE_URL}/ilink/bot/sendmessage",
    "-H", "Content-Type: application/json",
    "-H", "AuthorizationType: ilink_bot_token",
    "-H", f"Authorization: Bearer {BOT_TOKEN}",
    "-H", "iLink-App-Id: wxb11d9224a8d8f9d0",
    "-d", json_body,
]

result = subprocess.run(cmd, capture_output=True, timeout=30)
stdout = result.stdout.decode("utf-8", errors="replace")
stderr = result.stderr.decode("utf-8", errors="replace")

print(f"\nSTDOUT:\n{stdout}")
print(f"\nSTDERR (curl verbose):\n{stderr}")

# Parse response
try:
    resp = json.loads(stdout)
    print(f"\nParsed response: {json.dumps(resp, indent=2, ensure_ascii=False)}")
    print(f"ret code: {resp.get('ret', 'NOT FOUND')}")
except:
    print("Failed to parse response as JSON")

# Also test getupdates to see current state
print(f"\n\n=== Testing getupdates ===")
cmd2 = [
    "curl", "-s", "-k", "-v",
    "-X", "POST",
    f"{ILINK_BASE_URL}/ilink/bot/getupdates",
    "-H", "Content-Type: application/json",
    "-H", "AuthorizationType: ilink_bot_token",
    "-H", f"Authorization: Bearer {BOT_TOKEN}",
    "-H", "iLink-App-Id: wxb11d9224a8d8f9d0",
    "-d", json.dumps({"timeout": 5}),
]
result2 = subprocess.run(cmd2, capture_output=True, timeout=30)
stdout2 = result2.stdout.decode("utf-8", errors="replace")
stderr2 = result2.stderr.decode("utf-8", errors="replace")
print(f"\nSTDOUT:\n{stdout2[:2000]}")
print(f"\nSTDERR:\n{stderr2[:1000]}")
