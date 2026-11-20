"""Compliance checks run on every draft before it reaches Telegram.

These are guardrails, not legal advice. Always check Petandim posts against
LifeVantage's approved claims and the product label.
"""
import re

# Disease / treatment claims and income claims are never allowed.
BANNED_PATTERNS = [
    r"\bcure[sd]?\b", r"\btreat(ed|ing|ment)\b", r"\bto treat\b",  # the noun "treats" (dog treats) is allowed
    r"\bprevent(s|ed|ing)?\b",
    r"\bheal(s|ed|ing)?\b", r"\bdiagnos\w*", r"\barthritis\b", r"\bcancer\b",
    r"\btumou?r\b", r"\bdiabet\w*", r"\bkidney (disease|failure)\b",
    r"\bclinically proven\b", r"\bguarantee[sd]?\b", r"\bmiracle\b",
    r"\bincome\b", r"\bearn(ing|ings)?\b", r"\bpassive income\b", r"\bget paid\b",
]

AI_LABEL = re.compile(r"\bAI\b|AI-generated", re.IGNORECASE)
CONSULTANT_LINE = re.compile(r"independent\s+LifeVantage\s+consultant", re.IGNORECASE)


def check(row, caption):
    """Return a list of problems. Empty list means the draft passed."""
    issues = []
    text = f"{row.get('hook', '')} {caption}"

    for pattern in BANNED_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            issues.append(f"Banned word or claim: '{m.group(0)}'")

    if not AI_LABEL.search(caption):
        issues.append("Caption is missing the AI label (e.g. 'AI-generated dog').")

    if row.get("intent") == "Promote":
        if not CONSULTANT_LINE.search(caption):
            issues.append("Petandim post is missing 'independent LifeVantage consultant'.")
        if "ask your vet" not in caption.lower() and "talk to your vet" not in caption.lower():
            issues.append("Petandim post should say to ask or talk to your vet.")

    return issues
