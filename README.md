# Rose Bika Bot

Modern Miss Rose style modular Telegram group help bot.

## Stack
- Python 3.11+
- aiogram 3.x
- Telethon (optional raw Telegram layer)
- MongoDB (optional)
- Redis (optional)
- FastAPI webhook support (optional)

## Quick start
1. Create virtual environment
2. Install dependencies
3. Copy `.env.example` to `.env`
4. Fill required values
5. Run:

```bash
python -m app.main
```

## Notes
- Bot can run with **only BOT_TOKEN** for basic commands.
- Mongo, Redis, and Telethon are optional and safely skipped when not configured.
- This is a clean starter structure for expanding admin, greetings, warns, filters, notes, tickets, and force-join features.
