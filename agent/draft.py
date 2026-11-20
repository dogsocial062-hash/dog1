"""Write the caption (or video script) and generate the image with Gemini."""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT_MODEL = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")


def _read(name, default=""):
    p = ROOT / name
    return p.read_text(encoding="utf-8").strip() if p.exists() else default


def caption_prompt(row):
    character = _read("character.md", "A friendly AI-generated dog.")
    is_video = row["format"] == "video"
    kind = "a 30-45 second video script (spoken lines plus an on-screen text line)" if is_video else "an Instagram/Facebook caption"
    promo = row["intent"] == "Promote"
    rules = [
        "The dog is an AI-generated character. Say so plainly (e.g. 'AI-generated dog').",
        "The dog never says it took Petandim or got results. It is a host, not a patient.",
        "Never use cure, prevent, heal or 'treat' as a medical verb, and never name any disease (the noun 'treats' for snacks is fine). No income or earnings talk.",
        "Health tips end with 'ask your vet'.",
        "Keep the dog's voice warm, funny and short. 2-4 short paragraphs for a caption.",
        "End with exactly one call to action. Add 3-5 relevant hashtags.",
    ]
    if promo:
        rules += [
            "This is a Petandim post. Use only 'supports' / 'helps maintain' language, from the product label.",
            "Include the exact line: 'Posted by an independent LifeVantage consultant.'",
            "Include a line telling readers to talk to their vet first.",
        ]
    return (
        f"You write social media posts for this character:\n{character}\n\n"
        f"Write {kind}.\n"
        f"Date: {row['date']} ({row['day']}). Pillar: {row['pillar']}. Intent: {row['intent']}.\n"
        f"Hook angle: {row['hook']}\n"
        f"Core idea and call to action: {row['idea_cta']}\n\n"
        "Rules:\n- " + "\n- ".join(rules) + "\n\nReturn only the post text."
    )


def image_prompt(row):
    character = _read("character.md", "A friendly AI-generated dog.")
    return (
        f"Square 1:1 social media image. Character: {character}\n"
        f"Scene: {row['asset']}. Mood matches this hook: \"{row['hook']}\".\n"
        "Bright, clean, friendly style. Keep the dog's look identical to the reference. "
        "No real people, no brand logos, no medical imagery, no pills or product claims. "
        "If text appears in the image, keep it to a few short, correctly spelled words."
    )


_CLIENT = None


def _client():
    # Keep one client alive for the whole run. Creating it inline lets Python
    # clean it up before the request is sent ("client has been closed").
    global _CLIENT
    if _CLIENT is None:
        from google import genai
        _CLIENT = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _CLIENT


def write_caption(row):
    resp = _client().models.generate_content(model=TEXT_MODEL, contents=caption_prompt(row))
    return resp.text.strip()


def make_image(row, out_path):
    from google.genai import types
    contents = [image_prompt(row)]
    ref = ROOT / "character_ref.png"
    if ref.exists():
        contents.append(types.Part.from_bytes(data=ref.read_bytes(), mime_type="image/png"))
    resp = _client().models.generate_content(model=IMAGE_MODEL, contents=contents)
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            pathlib.Path(out_path).write_bytes(part.inline_data.data)
            return out_path
    raise RuntimeError("Gemini returned no image. Check the model name and quota.")
