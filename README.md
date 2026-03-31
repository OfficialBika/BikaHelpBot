# BikaHelpBot

Modern modular Telegram group management bot built with:

- aiogram 3.x
- Telethon
- MongoDB
- Redis

## Features

- Modular Miss Rose style structure
- Welcome / clean welcome / welcome preview
- Notes with media support
- Filters with media support
- Warns with auto action
- Bans / mute / unmute
- Force join
- Ticket system with admin panel buttons
- Support admin roles
- Settings panel with multi-page buttons
- Export/import settings
- Full chat backup pack
- Polling + webhook dual mode

## Project Structure

```text
app/
  core/
  keyboards/
  modules/
  services/
  utils/
  config.py
  loader.py
  main.py
```

## Requirements

- Python 3.11+
- MongoDB
- Redis
- Telegram Bot Token
- Telethon API_ID / API_HASH

## Installation

```bash
git clone <your-repo-url>
cd BikaHelpBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Environment

```bash
cp .env.production.example .env
```

Then edit `.env`.

Minimum required:

```env
BOT_TOKEN=your_bot_token
OWNER_ID=your_user_id
MONGODB_URI=mongodb://127.0.0.1:27017
MONGODB_DB_NAME=bika_help_bot
REDIS_URI=redis://127.0.0.1:6379/0
API_ID=123456
API_HASH=your_api_hash
LOG_CHAT_ID=-1001234567890
```

## Run with Polling

```bash
python -m app.main
```

Use:

```env
USE_WEBHOOK=false
```

## Run with Webhook

Use:

```env
USE_WEBHOOK=true
WEBHOOK_HOST=https://your-domain.com
WEBHOOK_PATH=/telegram/webhook
WEBHOOK_SECRET=supersecret
WEB_SERVER_HOST=0.0.0.0
WEB_SERVER_PORT=8080
```

Then start bot:

```bash
python -m app.main
```

Nginx should proxy requests to `127.0.0.1:8080`.

## Docker

```bash
docker compose up --build -d
```

## Systemd

```bash
sudo cp deploy/bikahelpbot.service /etc/systemd/system/bikahelpbot.service
sudo systemctl daemon-reload
sudo systemctl enable bikahelpbot
sudo systemctl start bikahelpbot
sudo systemctl status bikahelpbot
```

## Health Check

```text
/health
/admin
```

## Main Commands

### General
- `/start`
- `/help`
- `/ping`
- `/id`
- `/about`

### Settings
- `/settings`
- `/exportsettings`
- `/importsettings`
- `/exportchat`
- `/importchat`

### Greetings
- `/welcome`
- `/setwelcome`
- `/cleanwelcome`

### Notes
- `/save`
- `/get`
- `/notes`
- `/clear`

### Filters
- `/filter`
- `/filters`
- `/stop`

### Warns
- `/warn`
- `/warns`
- `/resetwarns`
- `/warnlimit`
- `/warnaction`

### Moderation
- `/ban`
- `/unban`
- `/mute`
- `/unmute`
- `/blacklist`
- `/unblacklist`
- `/blacklists`
- `/forcejoin`

### Tickets
- `/ticket`
- `/tickets`
- `/opentickets`
- `/replyticket`
- `/closeticket`

### Support Admin
- `/addsupport`
- `/remsupport`
- `/supports`
- `/issupport`

## Notes

- Redis is required for state-based panels and ticket reply mode.
- MongoDB is required for persistent settings, notes, filters, tickets, warns.
- Bot should be admin in groups for moderation features.
- Delete messages permission is needed for temp cleanup and blacklist cleanup.

## License

Private / custom bot project.
