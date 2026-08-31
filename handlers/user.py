import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ChatJoinRequest
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext

from database import add_user, get_movie_by_code, get_channels
from middlewares.subscription import check_user_subscription, record_user_join_request, mark_user_checked
from keyboards.user_kb import get_subscription_keyboard, get_share_keyboard

router = Router()
logger = logging.getLogger(__name__)

MANDATORY_SUB_TEXT = (
    "Barcha filmlarni va ilovalarni ushbu kanalimizga aʼzo boʻlib koʻrishingiz mumkin ❤️\n\n"
    "Barcha kanallarga aʼzo boʻling va filmni koʻrishingiz mumkin ❤️\n\n"
    "Kanallardan chiqib ketmang ❤️"
)

# Kanalga qo'shilishga so'rov yuborilganda (Join Request)
@router.chat_join_request()
async def on_chat_join_request(event: ChatJoinRequest, bot: Bot):
    user_id = event.from_user.id
    chat_id = str(event.chat.id)

    # Foydalanuvchi so'rov yuborganini saqlaymiz
    record_user_join_request(user_id, chat_id)
    logger.info(f"Join request received: user {user_id} -> chat {chat_id}")

    # So'rovni avtomatik tasdiqlash (auto-approve)
    try:
        await event.approve()
    except Exception as e:
        logger.warning(f"Auto-approve error for {user_id}: {e}")

async def send_movie_to_user(bot: Bot, chat_id: int, movie_data: tuple, code: str):
    _, from_chat_id, message_id = movie_data
    
    bot_info = await bot.get_me()
    bot_username = bot_info.username or "Girlsfilmbot"

    # Kino posti tagiga to'g'ridan-to'g'ri taklif qilish tugmasini biriktirish
    share_kb = get_share_keyboard(bot_username=bot_username, movie_code=code)

    try:
        await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_id=message_id,
            reply_markup=share_kb
        )
    except Exception as e:
        logger.error(f"Error copying movie message: {e}")

# /start komandasi
@router.message(CommandStart())
async def user_start(message: Message, command: CommandObject, bot: Bot, state: FSMContext):
    await state.clear()
    user = message.from_user
    await add_user(user.id, user.username, user.full_name)

    is_subscribed, unsubscribed = await check_user_subscription(bot, user.id)
    bot_info = await bot.get_me()
    bot_username = bot_info.username or "Girlsfilmbot"

    # Start bilan kod kelgan bo'lsa (deep link /start 101)
    code = command.args.strip().lower() if command.args else None

    if not is_subscribed:
        channels = await get_channels()
        kb = get_subscription_keyboard(channels, bot_username)
        if code:
            await state.update_data(pending_code=code)
        await message.answer(MANDATORY_SUB_TEXT, reply_markup=kb)
        return

    # Agar obuna bo'lgan bo'lsa va kod kiritilgan bo'lsa
    if code:
        movie = await get_movie_by_code(code)
        if movie:
            await send_movie_to_user(bot, message.chat.id, movie, code)
            return
        else:
            await message.answer(f"❌ <code>{code}</code> kodli kino topilmadi.", parse_mode="HTML")

    await message.answer(
        f"Salom {user.first_name}! 🍿\n\n"
        "Kino ko'rish uchun kino kodini kiriting (masalan: <code>101</code>):",
        parse_mode="HTML"
    )

# Obunani tekshirish callback button
@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    user_id = callback.from_user.id
    mark_user_checked(user_id)

    is_subscribed, unsubscribed = await check_user_subscription(bot, user_id)

    if not is_subscribed:
        missing_names = ", ".join([ch["name"] for ch in unsubscribed])
        await callback.answer(
            f"❌ Siz hali quyidagi kanallarga a'zo bo'lmadingiz:\n{missing_names}\n\nIltimos, barchasiga a'zo bo'ling!",
            show_alert=True
        )
        return

    await callback.answer("✅ Rahmat! Obuna tasdiqlandi.", show_alert=False)
    try:
        await callback.message.delete()
    except Exception:
        pass

    data = await state.get_data()
    pending_code = data.get("pending_code")

    if pending_code:
        await state.clear()
        movie = await get_movie_by_code(pending_code)
        if movie:
            await send_movie_to_user(bot, callback.message.chat.id, movie, pending_code)
            return

    await callback.message.answer(
        "✅ Barcha kanallarga a'zo bo'ldingiz! 🎉\n\n"
        "Endi ko'rmoqchi bo'lgan kino kodini yuboring (masalan <code>101</code>):",
        parse_mode="HTML"
    )

# Foydalanuvchi matn shaklida kod kiritganda
@router.message(F.text & ~F.text.startswith("/"))
async def handle_movie_code(message: Message, bot: Bot, state: FSMContext):
    code = message.text.strip().lower()
    
    # Admin bo'limi matnlari bo'lsa return
    admin_buttons = [
        "➕ Yangi kino qo'shish", "🗑 Kino o'chirish",
        "📜 Kinolar ro'yxati", "📢 Xabar tarqatish",
        "📢 Kanallar ro'yxati", "📢 Kanallarni boshqarish",
        "📊 Statistika", "Bekor qilish ❌", "Admin 🛠"
    ]
    if code in [btn.lower() for btn in admin_buttons]:
        return

    user_id = message.from_user.id
    await add_user(user_id, message.from_user.username, message.from_user.full_name)

    # Obunani tekshirish
    is_subscribed, unsubscribed = await check_user_subscription(bot, user_id)
    if not is_subscribed:
        channels = await get_channels()
        bot_info = await bot.get_me()
        kb = get_subscription_keyboard(channels, bot_info.username or "Girlsfilmbot")
        await state.update_data(pending_code=code)
        await message.answer(MANDATORY_SUB_TEXT, reply_markup=kb)
        return

    # Kinoni qidirish
    movie = await get_movie_by_code(code)
    if movie:
        await send_movie_to_user(bot, message.chat.id, movie, code)
    else:
        await message.answer(
            f"❌ <code>{code}</code> kodli kino topilmadi.\n\n"
            "Iltimos, kodni to'g'ri kiritganingizni tekshiring.",
            parse_mode="HTML"
        )
