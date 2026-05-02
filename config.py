import os


BOT_TOKEN: str = os.environ["BOT_TOKEN"]

CHAR_THRESHOLD: int = 280

_raw_ids = os.environ.get("GROUP_CHAT_IDS", "")
GROUP_CHAT_IDS: list[int] = [int(i.strip()) for i in _raw_ids.split(",") if i.strip()]
