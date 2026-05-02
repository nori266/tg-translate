import os


BOT_TOKEN: str = os.environ["BOT_TOKEN"]

CHAR_THRESHOLD: int = int(os.environ.get("CHAR_THRESHOLD", "280"))

_raw_ids = os.environ["GROUP_CHAT_IDS"]  # required — raises KeyError if missing
GROUP_CHAT_IDS: list[int] = [int(i.strip()) for i in _raw_ids.split(",")]
