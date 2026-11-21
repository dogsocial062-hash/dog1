"""Minimal Telegram helpers (send text and photos to your chat)."""
import json
import os

import requests


def _api(method):
    return f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/{method}"


def _check(r):
    # Never include the URL in errors: it contains the bot token.
    if not r.ok:
        raise RuntimeError(f"Telegram HTTP {r.status_code}: {r.text[:200]}")


def send_message(text, buttons=None):
    """Send text. buttons = [[(label, callback_data), ...]] adds tap buttons under the message."""
    data = {"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": text[:4096]}
    if buttons:
        data["reply_markup"] = json.dumps(
            {"inline_keyboard": [[{"text": t, "callback_data": c} for t, c in row] for row in buttons]})
    r = requests.post(_api("sendMessage"), data=data, timeout=30)
    _check(r)


def get_updates(offset=None):
    params = {"timeout": 0, "allowed_updates": json.dumps(["callback_query"])}
    if offset is not None:
        params["offset"] = offset
    r = requests.get(_api("getUpdates"), params=params, timeout=30)
    _check(r)
    return r.json().get("result", [])


def answer_callback(callback_id, text=""):
    requests.post(_api("answerCallbackQuery"),
                  data={"callback_query_id": callback_id, "text": text[:200]}, timeout=30)


def clear_buttons(chat_id, message_id):
    requests.post(_api("editMessageReplyMarkup"),
                  data={"chat_id": chat_id, "message_id": message_id,
                        "reply_markup": json.dumps({"inline_keyboard": []})}, timeout=30)


def send_photo(path, caption=""):
    with open(path, "rb") as f:
        r = requests.post(
            _api("sendPhoto"),
            data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "caption": caption[:1024]},
            files={"photo": f},
            timeout=60,
        )
    _check(r)
