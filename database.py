import aiosqlite
import logging
from config import DB_PATH, DEFAULT_CHANNELS, ADMIN_IDS

logger = logging.getLogger(__name__)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Users jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Movies jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                from_chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Channels (Majburiy obuna kanallari) jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                chat_id TEXT DEFAULT ''
            )
        """)

        # Admins jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY
            )
        """)

        # Join Requests jadvali
        await db.execute("""
            CREATE TABLE IF NOT EXISTS join_requests (
                user_id INTEGER,
                chat_id TEXT,
                PRIMARY KEY (user_id, chat_id)
            )
        """)

        # Default admindan qo'shish
        for admin_id in ADMIN_IDS:
            await db.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,))

        # Standart kanallarni kiritish (eski kanallarni yangi 3 tasi bilan almashtirish)
        await db.execute("DELETE FROM channels")
        for ch in DEFAULT_CHANNELS:
            await db.execute(
                "INSERT INTO channels (name, url, chat_id) VALUES (?, ?, ?)",
                (ch["name"], ch["url"], ch["chat_id"])
            )

        await db.commit()
    logger.info("Database initialized successfully.")

# Users
async def add_user(user_id: int, username: str = None, full_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, full_name) 
            VALUES (?, ?, ?) 
            ON CONFLICT(user_id) DO UPDATE SET 
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (user_id, username, full_name)
        )
        await db.commit()

async def get_user_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            res = await cursor.fetchone()
            return res[0] if res else 0

async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

# Admins
async def is_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        return True
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,)) as cursor:
            return (await cursor.fetchone()) is not None

async def add_admin(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
        await db.commit()

# Movies
async def add_movie(code: str, from_chat_id: int, message_id: int) -> bool:
    code = code.strip().lower()
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO movies (code, from_chat_id, message_id) VALUES (?, ?, ?)",
                (code, from_chat_id, message_id)
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

async def get_movie_by_code(code: str):
    code = code.strip().lower()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT code, from_chat_id, message_id FROM movies WHERE code = ?", (code,)
        ) as cursor:
            return await cursor.fetchone()

async def delete_movie_by_code(code: str) -> bool:
    code = code.strip().lower()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM movies WHERE code = ?", (code,))
        await db.commit()
        return cursor.rowcount > 0

async def get_all_movies() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT code, from_chat_id, message_id, created_at FROM movies ORDER BY id DESC") as cursor:
            return await cursor.fetchall()

async def get_movies_count() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM movies") as cursor:
            res = await cursor.fetchone()
            return res[0] if res else 0

# Channels
async def get_channels() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, name, url, chat_id FROM channels") as cursor:
            rows = await cursor.fetchall()
            return [{"id": r[0], "name": r[1], "url": r[2], "chat_id": r[3]} for r in rows]

async def add_channel_db(name: str, url: str, chat_id: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO channels (name, url, chat_id) VALUES (?, ?, ?)",
            (name, url, chat_id)
        )
        await db.commit()

async def delete_channel_db(channel_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        await db.commit()
        return cursor.rowcount > 0

async def update_channel_chat_id(channel_id: int, chat_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "UPDATE channels SET chat_id = ? WHERE id = ?",
            (str(chat_id), channel_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def reset_channels_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels")
        for ch in DEFAULT_CHANNELS:
            await db.execute(
                "INSERT INTO channels (name, url, chat_id) VALUES (?, ?, ?)",
                (ch["name"], ch["url"], ch["chat_id"])
            )
        await db.commit()

async def save_join_request_db(user_id: int, chat_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO join_requests (user_id, chat_id) VALUES (?, ?)",
            (user_id, str(chat_id))
        )
        await db.commit()

async def get_all_join_requests_db() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id, chat_id FROM join_requests") as cursor:
            return await cursor.fetchall()


