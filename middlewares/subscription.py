import logging
from aiogram import Bot
from database import get_channels, save_join_request_db, get_all_join_requests_db

logger = logging.getLogger(__name__)

# So'rov (Join Request) yuborgan foydalanuvchilar to'plami: (user_id, chat_id)
JOIN_REQUEST_USERS = set()

# Tekshirish tugmasini bosgan foydalanuvchilar
USER_CHECKED_SUB = set()

async def record_user_join_request(user_id: int, chat_id: str):
    cid = str(chat_id)
    JOIN_REQUEST_USERS.add((user_id, cid))
    JOIN_REQUEST_USERS.add((user_id, cid.replace("-100", "")))
    await save_join_request_db(user_id, cid)

async def load_join_requests_from_db():
    try:
        rows = await get_all_join_requests_db()
        for uid, cid in rows:
            cid_str = str(cid)
            JOIN_REQUEST_USERS.add((uid, cid_str))
            JOIN_REQUEST_USERS.add((uid, cid_str.replace("-100", "")))
        logger.info(f"Loaded {len(rows)} join requests from database.")
    except Exception as e:
        logger.error(f"Error loading join requests from database: {e}")

def mark_user_checked(user_id: int):
    USER_CHECKED_SUB.add(user_id)

async def check_user_subscription(bot: Bot, user_id: int) -> tuple[bool, list[dict]]:
    """
    Foydalanuvchi majburiy kanallarga obuna bo'lganligini, Join Request yuborganini yoki Tekshirganini tekshiradi.
    """
    channels = await get_channels()
    if not channels:
        return True, []

    unsubscribed = []

    for ch in channels:
        chat_id = str(ch.get("chat_id", "")).strip()

        if chat_id and chat_id != "0":
            cid = str(chat_id)
            clean_cid = cid.replace("-100", "")
            # 1. Foydalanuvchi kanalga so'rov (Join Request) yuborgan bo'lsa
            if (user_id, cid) in JOIN_REQUEST_USERS or (user_id, clean_cid) in JOIN_REQUEST_USERS:
                continue

            # 2. Real Telegram API member statusini tekshirish
            try:
                member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
                if member.status in ["creator", "administrator", "member", "restricted"]:
                    continue
                else:
                    unsubscribed.append(ch)
            except Exception as e:
                err_msg = str(e).lower()
                # Bot kanalda Admin bo'lmasa yoki chat not found bo'lsa
                if "chat not found" in err_msg or "bot is not a member" in err_msg or "not participant" in err_msg:
                    logger.warning(f"⚠️ '{ch['name']}' ({chat_id}) kanaliga @Girlsfilmbot Admin qilib qo'shilmagan!")
                    if user_id in USER_CHECKED_SUB:
                        continue
                unsubscribed.append(ch)
        else:
            # Chat ID hali biriktirilmagan bo'lsa
            if user_id in USER_CHECKED_SUB:
                continue
            unsubscribed.append(ch)

    if unsubscribed:
        return False, unsubscribed
    return True, []
