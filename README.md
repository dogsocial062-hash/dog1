# dog1 - AI dog content agent (Petandim)

Drafts one social post a day from `content_plan.csv`, checks it against compliance rules,
and sends it to you on Telegram for review. Step 1 of the build: you approve and post manually.

## How it works

1. A GitHub Actions job runs daily at 9:00 am ET (`.github/workflows/daily.yml`).
2. It finds today's row in `content_plan.csv`.
3. Gemini writes the caption (or video script) and, for image days, the picture.
4. `agent/safety.py` flags banned claims and missing disclosures.
5. The draft and the safety result arrive in your Telegram chat.

## Setup

1. **Telegram bot**: message @BotFather, send `/newbot`, copy the token. Send any message to your new bot,
   then open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy the `chat.id` number.
2. **Gemini key**: create an API key at Google AI Studio.
3. **Add three repo secrets** (Settings > Secrets and variables > Actions):
   `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
4. **Edit `character.md`**: give the dog a name and one detailed written look. Optionally add a
   `character_ref.png` reference image so every post keeps the same dog.
5. **Test**: Actions tab > Daily draft > Run workflow, with `post_date` set to a date in the plan.

## Local dry run (no keys needed)

```bash
DRY_RUN=1 POST_DATE=2026-11-28 python -m agent.run_daily
```

## Rules built into every draft

- The dog is labeled as an AI-generated character and never claims to take Petandim or report results.
- Structure/function language only. No disease, treatment, or income claims.
- Petandim posts carry "independent LifeVantage consultant" and a "talk to your vet" line.
- Always check Petandim posts against LifeVantage's approved claims and the product label.

## Roadmap

- [x] Step 1: daily draft to Telegram (manual posting)
- [ ] Step 2: Approve / Skip buttons and automatic posting through a scheduler API
- [ ] Step 3: HeyGen video on Thursdays
- [ ] Step 4: fully unattended in the cloud
