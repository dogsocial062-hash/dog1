"""Print the chat ID(s) of people who messaged the bot (the ID is not a secret)."""
import os

import requests

r = requests.get(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/getUpdates",
                 params={"allowed_updates": '["message"]'}, timeout=30)
if not r.ok:
    raise SystemExit(f"Telegram HTTP {r.status_code}: {r.text[:200]}")
seen = {}
for u in r.json().get("result", []):
    c = (u.get("message") or {}).get("chat") or {}
    if c.get("type") == "private":
        seen[c["id"]] = c.get("first_name", "")
if not seen:
    print("::error title=No messages found::Open your bot in Telegram, send it any message, then run this again.")
for cid, name in seen.items():
    print(f"::notice title=Your chat ID::{cid} ({name})")
me = requests.get(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/getMe", timeout=30).json()
print(f"::notice title=Bot::@{me.get('result', {}).get('username')} (id {me.get('result', {}).get('id')})")
