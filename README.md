# tg-translate

A Telegram bot that translates between English and Russian (EN↔RU) using Google Translate.

## Modes of operation

### 1. Discovery mode (no `GROUP_CHAT_IDS` set)

When `GROUP_CHAT_IDS` is not configured, the bot logs the `chat_id`, name, and type of every chat it receives a message from. Use this to find the numeric IDs you need before switching to normal mode.

```
INFO  Received message from chat_id=-1001234567890 name='My Group' type=supergroup
```

### 2. Group auto-translate mode

Once `GROUP_CHAT_IDS` is set, the bot monitors the listed group chats and automatically replies with a translation whenever a message exceeds `CHAR_THRESHOLD` characters (default: 280). Only EN and RU are supported; other languages are ignored.

- EN text → replied with RU translation
- RU text → replied with EN translation

### 3. `/translate` command

In a configured group, reply to any message with `/translate` to get an on-demand translation of that message. If used without a reply, the bot translates the most recent message it has seen in that chat.

### 4. Inline mode

From any chat, type `@botname <text>` to translate text inline before sending it. The bot detects the dominant script:

- Cyrillic-dominant → translates to EN
- Otherwise → translates to RU

The result is offered as a sendable message showing the original and translation together.

Note: Telegram limits inline query text to **256 characters**. Longer input is truncated by Telegram before it reaches the bot. For longer text, send it as a normal message in a configured group or use `/translate`.

---

## Setup

### Prerequisites

- Python 3.13+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- For inline mode, enable inline queries in BotFather

### Install dependencies

```bash
pip install -r requirements.txt
```

### Environment variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | Yes | Telegram bot token from BotFather |
| `GROUP_CHAT_IDS` | No | Comma-separated list of group chat IDs to monitor (omit to run in discovery mode) |

### Run locally

```bash
BOT_TOKEN=xxx python bot.py
```

With specific groups:

```bash
BOT_TOKEN=xxx GROUP_CHAT_IDS=-1001234567890,-1009876543210 python bot.py
```

### Deploy to Heroku (or similar)

The `Procfile` defines a `worker` dyno:

```
worker: python bot.py
```

Set `BOT_TOKEN` and optionally `GROUP_CHAT_IDS` as config vars.

---

## Finding chat IDs

Use `list_chats.py` to list recent chats from your personal Telegram account via MTProto:

```bash
export TELEGRAM_API_ID=...   # from https://my.telegram.org
export TELEGRAM_API_HASH=...
python list_chats.py         # lists 30 most recent chats
python list_chats.py 50      # lists 50 most recent chats
```

The first run will prompt for your phone number and a login code. Subsequent runs reuse the saved `tg_user.session` file.
