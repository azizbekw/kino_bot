import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8523979087:AAEFA-_LA8IQHBqKt17_CqX3Nx71SVrDld8")
DB_PATH = os.getenv("DB_PATH", "kino_bot.db")

# Admin ID lari (vergul bilan ajratilgan)
raw_admins = os.getenv("ADMIN_IDS", "6842846042,2122907163")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in raw_admins.split(",") if admin_id.strip().isdigit()]

# Maxfiy Ombor Kanal ID si (Kinolar doimiy xavfsiz saqlanadigan kanal)
raw_storage = os.getenv("STORAGE_CHANNEL_ID", "-1004248771589").strip()
if raw_storage.isdigit():
    STORAGE_CHANNEL_ID = int(f"-100{raw_storage}")
elif raw_storage.startswith("-100") and raw_storage[4:].isdigit():
    STORAGE_CHANNEL_ID = int(raw_storage)
else:
    STORAGE_CHANNEL_ID = raw_storage

# Default majburiy obuna kanallari
DEFAULT_CHANNELS = [
    {"name": "1-kanal (Mohinur)", "url": "https://t.me/+OCtCGkSJnk00Nzcy", "chat_id": "-1002038097948"},
    {"name": "2-kanal (.)", "url": "https://t.me/+8JahJgfENFEzNmYy", "chat_id": "-1002222128603"},
    {"name": "3-kanal (Mohiy)", "url": "https://t.me/+8jMRKRfVA5g2NGM6", "chat_id": "-1002242671590"},
]
