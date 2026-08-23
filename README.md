# Telegram Keyword Tracker

A personal Telegram monitoring tool that scans all incoming messages across your groups, channels, and chats for configured keywords, then sends real-time notifications with links to the original messages.

## How it works

Two components run in a single process:

- **Listener** — logs into your personal Telegram account via MTProto (Telethon), silently reads every incoming message
- **Bot** — a separate @BotFather bot you interact with for keyword management and that delivers notifications to you

When a message contains a tracked keyword, the Bot sends you a notification like:

```
🔔 Keyword matched: **PS5**

💬 Chat: Gaming Deals
👤 From: DealBot @dealbot
📝 "PS5 Digital Edition por apenas R$2.999! Corre que..."
🔗 https://t.me/gamingdeals/12345
```

## Setup

### 1. Get `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`

1. Go to https://my.telegram.org
2. Log in with your phone number (the same account the Listener will use)
3. Click **"API development tools"**
4. Fill in the form:
   - **App title**: anything (e.g., "Keyword Tracker")
   - **Short name**: anything (e.g., "kwtracker")
   - **Platform**: "Other"
5. Click **Create application**
6. Copy your **App api_id** (a number) and **App api_hash** (a hex string)

### 2. Create the Bot and get `TELEGRAM_BOT_TOKEN`

1. Open Telegram and message **@BotFather**
2. Send `/newbot`
3. Choose a display name (e.g., "Keyword Tracker")
4. Choose a username ending in `bot` (e.g., `my_keyword_tracker_bot`)
5. BotFather replies with a token like `7123456789:AAH...` — copy it

### 3. Get your `TELEGRAM_OWNER_ID`

1. Open Telegram and message **@userinfobot**
2. Send it any message
3. It replies with your **Id** — a number like `123456789` — copy it

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_BOT_TOKEN=7123456789:AAH_your_token_here
TELEGRAM_OWNER_ID=123456789
```

### 5. Install and run

```bash
pip install -r requirements.txt
python -m src.main
```

On first run, Telethon prompts in the terminal:

1. **"Please enter your phone"** → your phone number with country code (e.g., `+5511999999999`)
2. **"Please enter the code"** → the code Telegram sends to your app
3. **"Two-step verification password"** → only if you have 2FA enabled

After authentication, a session file is saved in `data/` — you won't be asked again.

### Docker (alternative)

```bash
docker compose up -d
```

First run requires interactive terminal for phone auth:

```bash
docker compose run --rm tracker
```

After the session is created, restart with `docker compose up -d`.

## Usage

Message your bot in Telegram:

| Command | Description |
|---------|-------------|
| `/add <phrase>` | Track a keyword or exact phrase |
| `/remove <phrase>` | Stop tracking a keyword |
| `/list` | Show all active keywords |
| `/status` | Check if the listener is connected |
| `/help` | Command reference |

### Examples

```
/add PS5
/add iPhone 15 Pro
/add good deal
```

Keywords are matched as whole words/phrases, case-insensitive. "PS5" matches "New PS5 available!" but not "PS50" or "GPS5".

## Features

- **Whole-word/phrase matching** — no false positives from partial matches
- **Scans everything** — groups, channels, private chats, bot messages, media captions
- **Edited message detection** — catches keywords added in edits, marked with [Edited]
- **Combined notifications** — multiple keywords in one message = one notification
- **Message links** — direct links for public and private groups/channels
- **Keywords persisted in SQLite** — survive restarts

## Project structure

```
src/
├── main.py         Entry point, starts both clients
├── config.py       Environment configuration
├── database.py     SQLite keyword storage
├── service.py      Matching, notifications
├── bot.py          Bot command handlers
└── listener.py     MTProto message handlers + disconnect monitor
```
