"""Minimal Telegram helpers (send text and photos to your chat)."""
import os

import requests


def _api(method):
    return f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/{method}"


def _check(r):
    # Never include the URL in errors: it contains the bot token.
    if not r.ok:
        raise RuntimeError(f"Telegram HTTP {r.status_code}: {r.text[:200]}")


def send_message(text):
    r = requests.post(
        _api("sendMessage"),
        data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": text[:4096]},
        timeout=30,
    )
    _check(r)


def send_photo(path, caption=""):
    with open(path, "rb") as f:
        r = requests.post(
            _api("sendPhoto"),
            data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "caption": caption[:1024]},
            files={"photo": f},
            timeout=60,
        )
    _check(r)
