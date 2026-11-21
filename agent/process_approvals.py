"""Check Telegram for Approve / Skip taps and post approved drafts to Instagram.

Runs every few minutes from the "Approvals" workflow. Only taps from TELEGRAM_CHAT_ID count.
state/status.json remembers what was already posted or skipped so nothing posts twice.
"""
import json
import os
import pathlib
import sys

from agent import plan, publish_instagram, telegram

STATE = pathlib.Path(__file__).resolve().parent.parent / "state" / "status.json"


def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save(state):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def main():
    chat = str(os.environ["TELEGRAM_CHAT_ID"])
    updates = telegram.get_updates()
    if not updates:
        print("No new taps.")
        return 0
    state = load()
    code = 0
    for u in updates:
        # Confirm each update right away so a crash can never cause a second post.
        telegram.get_updates(offset=u["update_id"] + 1)
        cb = u.get("callback_query")
        if not cb or not cb.get("data"):
            continue
        msg = cb.get("message") or {}
        if str(msg.get("chat", {}).get("id")) != chat:
            print("Ignored a tap from another chat.")
            continue
        action, _, date = cb["data"].partition(":")
        if action not in ("approve", "skip") or not plan.get_row(date):
            telegram.answer_callback(cb["id"], "Unknown button.")
            continue
        telegram.clear_buttons(chat, msg.get("message_id"))
        if date in state:
            telegram.answer_callback(cb["id"], f"Already {state[date]}.")
            continue
        if action == "skip":
            state[date] = "skipped"
            save(state)
            telegram.answer_callback(cb["id"], "Skipped.")
            telegram.send_message(f"Skipped {date}. Nothing was posted.")
            continue
        telegram.answer_callback(cb["id"], "Approved. Posting now...")
        os.environ["POST_DATE"] = date
        os.environ.pop("DRY_RUN", None)
        if publish_instagram.main() == 0:
            state[date] = "published"
        else:
            state[date] = "failed"  # not retried automatically; see the Telegram message
            code = 1
        save(state)
    return code


if __name__ == "__main__":
    sys.exit(main())
