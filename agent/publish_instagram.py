"""Publish one approved image post to Instagram (Instagram API with Instagram Login).

Manual only: run the "Publish to Instagram" workflow after you approve the Telegram draft.

Env vars:
  INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_USER_ID   (required unless DRY_RUN=1)
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID        (confirmation message)
  POST_DATE   YYYY-MM-DD to publish (required)
  FORCE=1     publish even if the safety check flags the caption (not recommended)
  DRY_RUN=1   run every check and print what would be sent, but do not call Instagram
"""
import os
import sys
import time

import requests

from agent import draft, plan, safety

HOSTS = ("https://graph.instagram.com/v21.0", "https://graph.facebook.com/v21.0")
RAW = "https://raw.githubusercontent.com/{repo}/main/images/{name}"
SECRETS = ("INSTAGRAM_ACCESS_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")


def scrub(text):
    for var in SECRETS:
        val = os.getenv(var)
        if val:
            text = text.replace(val, "***")
    return text


def fail(msg):
    print(f"::error title=Instagram publish failed::{scrub(msg)[:600]}")
    notify("Instagram post NOT published: " + scrub(msg)[:300])
    return 1


def notify(text):
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"):
        from agent import telegram
        try:
            telegram.send_message(text)
        except Exception as e:  # noqa: BLE001
            print(scrub(f"Telegram notice failed: {e}"))


def call(method, url, **kw):
    r = requests.request(method, url, timeout=60, **kw)
    if not r.ok:
        raise RuntimeError(f"Instagram HTTP {r.status_code}: {scrub(r.text)[:400]}")
    return r.json()


def pick_host(uid, token):
    """Find which Graph host accepts this token (Instagram-login vs Facebook-login tokens)."""
    errors = []
    for host in HOSTS:
        try:
            info = call("GET", f"{host}/{uid}", params={"fields": "username", "access_token": token})
            print(f"Token OK on {host.split('/')[2]} for @{info.get('username', '?')}")
            return host
        except Exception as e:  # noqa: BLE001
            errors.append(f"{host.split('/')[2]}: {e}")
    raise RuntimeError("Token rejected by both hosts. " + " | ".join(errors))


def main():
    date = os.getenv("POST_DATE", "").strip()
    if not date:
        return fail("POST_DATE is required (YYYY-MM-DD).")
    row = plan.get_row(date)
    if not row:
        return fail(f"No post planned for {date}.")
    if row["format"] != "image":
        return fail(f"{date} is a {row['format']} post. Only image posts can be published for now.")

    img = draft.find_image(date)
    if img is None:
        return fail(f"images/{date}.jpg is missing. Add it to the repo first.")
    if img.suffix.lower() not in (".jpg", ".jpeg"):
        return fail("Instagram needs a JPEG. Convert the image to .jpg.")

    caption = draft.get_caption(row)
    issues = safety.check(row, caption)
    if issues and os.getenv("FORCE") != "1":
        return fail("Safety check flagged this post, not publishing: " + "; ".join(issues))

    repo = os.getenv("GITHUB_REPOSITORY", "dogsocial062-hash/dog1")
    image_url = RAW.format(repo=repo, name=img.name)
    print(f"Post {date}: {len(caption)} chars, image {image_url}")

    token, uid = os.getenv("INSTAGRAM_ACCESS_TOKEN", ""), os.getenv("INSTAGRAM_USER_ID", "")
    if os.getenv("DRY_RUN") == "1":
        if token and uid:  # read-only check that the saved secrets work
            try:
                pick_host(uid, token)
            except Exception as e:  # noqa: BLE001
                return fail(f"Token check failed: {e}")
        else:
            print("Secrets not set; skipping token check.")
        print("DRY_RUN: would create a container and publish. Caption:\n" + caption)
        return 0

    if not (token and uid):
        return fail("INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_USER_ID secrets are required.")
    try:
        GRAPH = pick_host(uid, token)
        # The image must be publicly reachable, so check that before asking Instagram to fetch it.
        head = requests.head(image_url, timeout=30, allow_redirects=True)
        if not head.ok:
            return fail(f"Image URL not reachable (HTTP {head.status_code}). Is the commit pushed and the repo public?")

        container = call("POST", f"{GRAPH}/{uid}/media",
                         data={"image_url": image_url, "caption": caption, "access_token": token})["id"]
        for _ in range(10):
            status = call("GET", f"{GRAPH}/{container}",
                          params={"fields": "status_code", "access_token": token}).get("status_code")
            print("Container status:", status)
            if status == "FINISHED":
                break
            if status in ("ERROR", "EXPIRED"):
                return fail(f"Container status {status}.")
            time.sleep(6)
        else:
            return fail("Container not ready after 60 seconds.")

        media_id = call("POST", f"{GRAPH}/{uid}/media_publish",
                        data={"creation_id": container, "access_token": token})["id"]
        try:
            link = call("GET", f"{GRAPH}/{media_id}",
                        params={"fields": "permalink", "access_token": token}).get("permalink", "")
        except Exception:  # noqa: BLE001
            link = ""
    except Exception as e:  # noqa: BLE001
        notify(f"Instagram publish FAILED for {date}.")
        return fail(f"{type(e).__name__}: {e}")

    print("Published", media_id, link)
    notify(f"Published to Instagram: {date}\n{link}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
