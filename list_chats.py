"""List recent Telegram chats with their IDs (user account, via MTProto).

Setup:
    pip install telethon
    export TELEGRAM_API_ID=...      # from https://my.telegram.org
    export TELEGRAM_API_HASH=...

Usage:
    python list_chats.py [limit]    # default limit: 30

First run prompts for phone + login code; subsequent runs reuse `tg_user.session`.
"""

import asyncio
import os
import sys

from telethon import TelegramClient


API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = "tg_user"


def _type(dialog) -> str:
    if dialog.is_user:
        return "user"
    if dialog.is_channel:
        return "channel" if not getattr(dialog.entity, "megagroup", False) else "supergroup"
    return "group"


async def main(limit: int) -> None:
    async with TelegramClient(SESSION, API_ID, API_HASH) as client:
        print(f"{'chat_id':>16}  {'type':<10}  name")
        print(f"{'-' * 16}  {'-' * 10}  {'-' * 40}")
        async for dialog in client.iter_dialogs(limit=limit):
            print(f"{dialog.id:>16}  {_type(dialog):<10}  {dialog.name}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    asyncio.run(main(n))
