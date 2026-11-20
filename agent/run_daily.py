"""Draft today's post and send it to Telegram for review.

Env vars:
  GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID  (required unless DRY_RUN=1)
  POST_DATE   YYYY-MM-DD to draft (default: today in America/New_York)
  DRY_RUN=1   print the prompts and skip all API calls
"""
import datetime as dt
import os
import pathlib
import sys
import zoneinfo

from agent import draft, plan, safety

OUT = pathlib.Path(__file__).resolve().parent.parent / "out"


def today_et():
    return dt.datetime.now(zoneinfo.ZoneInfo("America/New_York")).strftime("%Y-%m-%d")


def main():
    date = os.getenv("POST_DATE") or today_et()
    row = plan.get_row(date)
    if not row:
        msg = f"No post planned for {date}. Nothing to do. (Plan runs 2026-11-23 to 2026-12-22.)"
        print(msg)
        # On a manual run, tell the user in Telegram so a silent result is never confusing.
        if os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch" and os.getenv("TELEGRAM_BOT_TOKEN"):
            from agent import telegram
            telegram.send_message(msg)
        return 0

    print(f"Drafting {row['date']} ({row['day']}) - {row['format']} - {row['pillar']} / {row['intent']}")

    if os.getenv("DRY_RUN") == "1":
        print("\n--- CAPTION PROMPT ---\n" + draft.caption_prompt(row))
        if row["format"] == "image":
            print("\n--- IMAGE PROMPT ---\n" + draft.image_prompt(row))
        return 0

    from agent import telegram

    OUT.mkdir(exist_ok=True)
    caption = draft.write_caption(row)
    issues = safety.check(row, caption)
    (OUT / f"{date}.txt").write_text(caption, encoding="utf-8")

    header = f"Draft for {row['date']} ({row['day']}) - {row['format']} - {row['intent']}"
    if row["format"] == "image":
        img = draft.make_image(row, OUT / f"{date}.png")
        telegram.send_photo(img, header)
    else:
        telegram.send_message(header + "\n(Video: script below. HeyGen render is added in step 3.)")

    telegram.send_message(caption)
    if issues:
        telegram.send_message("SAFETY CHECK FAILED - do not post as is:\n- " + "\n- ".join(issues))
    else:
        telegram.send_message("Safety check passed. Post it manually, or edit first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
