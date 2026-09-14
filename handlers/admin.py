import logging
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import STORAGE_CHANNEL_ID
from database import (
    is_admin, add_movie, get_movie_by_code, delete_movie_by_code,
    get_all_movies, get_movies_count, get_user_count, get_all_user_ids,
    get_channels, update_channel_chat_id, add_admin, add_channel_db,
    delete_channel_db, reset_channels_db
)
from states.admin_states import AddMovie, DeleteMovie, AddChannel
from keyboards.admin_kb import (
    get_admin_main_kb, get_cancel_kb, get_confirm_movie_kb
)

router = Router()
logger = logging.getLogger(__name__)

# Admin paneli kirish
@router.message(Command("admin"))
@router.message(F.text == "Admin 🛠")
async def admin_panel_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        # Birinchi foydalanuvchini admin sifatida ro'yxatdan o'tkazish imkoniyati (agar admin bo'lmasa)
        users_cnt = await get_user_count()
        if users_cnt <= 1:
            await add_admin(message.from_user.id)
        else:
            await message.answer("❌ Siz bot admini emassiz.")
            return

    await state.clear()
    users_cnt = await get_user_count()
    movies_cnt = await get_movies_count()
    channels = await get_channels()

    text = (
        "<b>🛠 Admin Paneliga Xush Kelibsiz!</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar</b>: {users_cnt} ta\n"
        f"🎬 <b>Jami kinolar</b>: {movies_cnt} ta\n"
        f"📢 <b>Majburiy kanallar</b>: {len(channels)} ta\n\n"
        "Kerakli bo'limni tanlang 👇"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_kb())

# Bekor qilish
@router.message(F.text == "Bekor qilish ❌")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Amaliyot bekor qilindi.", reply_markup=get_admin_main_kb())

# --- YANGI KINO QO'SHISH ---
@router.message(F.text == "➕ Yangi kino qo'shish")
async def add_movie_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.set_state(AddMovie.waiting_for_code)
    await message.answer(
        "📝 Kino uchun maxsus <b>kod</b> kiriting (masalan: 101, avatar_2, 500):",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )

@router.message(AddMovie.waiting_for_code)
async def process_movie_code(message: Message, state: FSMContext):
    code = message.text.strip().lower()
    if not code:
        await message.answer("❌ Kod bo'sh bo'lishi mumkin emas. Qayta kiriting:")
        return

    # Kod mavjudligini tekshirish
    existing = await get_movie_by_code(code)
    if existing:
        await message.answer(f"⚠️ <code>{code}</code> kodi allaqachon mavjud! Boshqa kod kiriting:", parse_mode="HTML")
        return

    await state.update_data(code=code)
    await state.set_state(AddMovie.waiting_for_media)
    await message.answer(
        f"✅ Kod: <code>{code}</code> qabul qilindi.\n\n"
        "Endi kino xabarini (video, rasm, fayl yoki matn) yuboring yoki forvard qiling 🎬:",
        parse_mode="HTML"
    )

@router.message(AddMovie.waiting_for_media)
async def process_movie_media(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    code = data.get("code")

    chat_id = message.chat.id
    message_id = message.message_id

    # State ga saqlaymiz
    await state.update_data(chat_id=chat_id, message_id=message_id)
    await state.set_state(AddMovie.confirm_save)

    # 1. Preview qilib ko'rsatamiz
    await message.answer("🔍 <b>Kino ko'rinishi (Preview):</b>", parse_mode="HTML")
    try:
        await bot.forward_message(chat_id=chat_id, from_chat_id=chat_id, message_id=message_id)
    except Exception:
        await bot.copy_message(chat_id=chat_id, from_chat_id=chat_id, message_id=message_id)

    # 2. Tasdiqlash va tahrirlash tugmalari
    await message.answer(
        f"📌 <b>Biriktirilayotgan kod</b>: <code>{code}</code>\n\n"
        "Xabar ko'rinishi yuqorida ko'rsatildi. Kinoni bazaga saqlashni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=get_confirm_movie_kb()
    )

# --- TASDIQLASH VA TAHRIRLASH CALLBACKLARI ---
@router.callback_query(F.data == "confirm_add_movie", AddMovie.confirm_save)
async def confirm_add_movie_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    code = data.get("code")
    chat_id = data.get("chat_id")
    message_id = data.get("message_id")

    final_chat_id = chat_id
    final_message_id = message_id

    # Ombor kanaliga (Storage Channel) ko'chirish
    if STORAGE_CHANNEL_ID:
        try:
            copied_msg = await bot.copy_message(
                chat_id=STORAGE_CHANNEL_ID,
                from_chat_id=chat_id,
                message_id=message_id
            )
            final_chat_id = STORAGE_CHANNEL_ID
            final_message_id = copied_msg.message_id
            logger.info(f"Movie '{code}' saved to storage channel {STORAGE_CHANNEL_ID} with msg_id {final_message_id}")
        except Exception as e:
            logger.warning(f"Could not copy movie '{code}' to storage channel {STORAGE_CHANNEL_ID}: {e}")

    success = await add_movie(code=code, from_chat_id=final_chat_id, message_id=final_message_id)

    if success:
        await callback.message.edit_text(
            f"🎉 <b>Kino muvaffaqiyatli saqlandi!</b>\n\n"
            f"🔑 <b>Kino kodi</b>: <code>{code}</code>\n"
            f"📦 <b>Ombor kanaldagi ID</b>: <code>{final_message_id}</code>\n\n"
            "<i>Kino maxfiy Ombor kanaliga doimiy saqlandi. Admin chatidan o'chirilsa ham foydalanuvchilarga yetib boradi!</i>",
            parse_mode="HTML"
        )
        await callback.message.answer("Bosh menyu 👇", reply_markup=get_admin_main_kb())
    else:
        await callback.message.edit_text("❌ Kinoni saqlashda xatolik yuz berdi.", parse_mode="HTML")
        await callback.message.answer("Bosh menyu 👇", reply_markup=get_admin_main_kb())

    await callback.answer()
    await state.clear()

@router.callback_query(F.data == "edit_movie_code", AddMovie.confirm_save)
async def edit_movie_code_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovie.waiting_for_code)
    await callback.message.answer(
        "📝 Yangi kodni kiriting (eski kodingiz o'zgartiriladi):",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "edit_movie_media", AddMovie.confirm_save)
async def edit_movie_media_callback(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    code = data.get("code")
    await state.set_state(AddMovie.waiting_for_media)
    await callback.message.answer(
        f"🔄 <code>{code}</code> kodi uchun yangi kino xabarini (video, rasm, matn) qayta yuboring:",
        parse_mode="HTML",
        reply_markup=get_cancel_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_add_movie", AddMovie.confirm_save)
async def cancel_add_movie_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Kino qo'shish bekor qilindi.")
    await callback.message.answer("Bosh menyu 👇", reply_markup=get_admin_main_kb())
    await callback.answer()

# --- KINO O'CHIRISH ---
@router.message(F.text == "🗑 Kino o'chirish")
async def delete_movie_start(message: Message, state: FSMContext):
    if not await is_admin(message.from_user.id):
        return
    await state.set_state(DeleteMovie.waiting_for_code)
    await message.answer("🗑 O'chiriladigan kino kodini kiriting:", reply_markup=get_cancel_kb())

@router.message(DeleteMovie.waiting_for_code)
async def process_delete_movie(message: Message, state: FSMContext):
    code = message.text.strip().lower()
    success = await delete_movie_by_code(code)

    if success:
        await message.answer(f"✅ <code>{code}</code> kodli kino bazadan o'chirildi!", parse_mode="HTML", reply_markup=get_admin_main_kb())
    else:
        await message.answer(f"❌ <code>{code}</code> kodli kino topilmadi.", parse_mode="HTML", reply_markup=get_admin_main_kb())

    await state.clear()

# --- KINOLAR RO'YXATI ---
@router.message(F.text == "📜 Kinolar ro'yxati")
async def list_movies(message: Message):
    if not await is_admin(message.from_user.id):
        return

    movies = await get_all_movies()
    if not movies:
        await message.answer("📜 Bazada hali hech qanday kino yo'q.")
        return

    text = "<b>📜 Bazadagi kinolar ro'yxati:</b>\n\n"
    for idx, m in enumerate(movies[:30], 1): # Max 30 ta
        code, chat_id, msg_id, created = m
        text += f"{idx}. Kod: <code>{code}</code> (ID: {msg_id})\n"

    if len(movies) > 30:
        text += f"\n<i>...va yana {len(movies) - 30} ta kino bor.</i>"

    await message.answer(text, parse_mode="HTML")

# --- STATISTIKA ---
@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not await is_admin(message.from_user.id):
        return

    users_cnt = await get_user_count()
    movies_cnt = await get_movies_count()
    channels = await get_channels()

    text = (
        "<b>📊 Bot Statistikasi:</b>\n\n"
        f"👤 <b>Foydalanuvchilar</b>: {users_cnt} ta\n"
        f"🎬 <b>Kino medialar</b>: {movies_cnt} ta\n"
        f"📢 <b>Majburiy obuna kanallari</b>: {len(channels)} ta"
    )
    await message.answer(text, parse_mode="HTML")

# --- FORWARD QILINGAN KANAL XABARINI AVTO-ANIQLASH ---
@router.message(F.forward_from_chat)
async def handle_forwarded_channel_msg(message: Message):
    if not await is_admin(message.from_user.id):
        return

    forward_chat = message.forward_from_chat
    if forward_chat.type in ["channel", "supergroup"]:
        chat_id = forward_chat.id
        title = forward_chat.title or "Kanal"
        username = f"@{forward_chat.username}" if forward_chat.username else "Yopiq kanal"

        channels = await get_channels()
        buttons = []
        for ch in channels:
            buttons.append([
                InlineKeyboardButton(
                    text=f"📌 {ch['name']} ga biriktirish (ID: {chat_id})",
                    callback_data=f"link_chat_id_{ch['id']}_{chat_id}"
                )
            ])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            f"📢 <b>Forward qilingan kanal aniqlandi!</b>\n\n"
            f"📌 <b>Nomi</b>: {title}\n"
            f"🆔 <b>Chat ID</b>: <code>{chat_id}</code> ({username})\n\n"
            "Ushbu kanalning <code>chat_id</code> sini majburiy obuna kanallaridan biriga biriktirish uchun quyidagi tugmani bosing:",
            parse_mode="HTML",
            reply_markup=kb
        )

@router.callback_query(F.data.startswith("link_chat_id_"))
async def link_chat_id_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    channel_id = int(parts[3])
    chat_id = parts[4]

    success = await update_channel_chat_id(channel_id, chat_id)
    if success:
        await callback.answer("✅ Kanal Chat ID muvaffaqiyatli biriktirildi!", show_alert=True)
        await callback.message.edit_text(
            f"✅ <b>Kanal Chat ID biriktirildi!</b>\n\n🆔 <code>{chat_id}</code>\n\nEndi bot Telegram API orqali ushbu kanalga obunani 100% real-time avtomatik tekshiradi!",
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Xatolik yuz berdi.", show_alert=True)

# --- KANALLAR RO'YXATI VA BOSHQARUV ---
@router.message(F.text == "📢 Kanallar ro'yxati")
@router.message(F.text == "📢 Kanallarni boshqarish")
async def view_channels(message: Message):
    if not await is_admin(message.from_user.id):
        return

    channels = await get_channels()
    text = "<b>📢 Majburiy Obuna Kanallari Ro'yxati:</b>\n\n"
    buttons = []
    
    if not channels:
        text += "⚠️ Hozirda hech qanday majburiy obuna kanali yo'q.\n\n"
    else:
        for idx, ch in enumerate(channels, 1):
            chat_id = str(ch.get('chat_id', '')).strip()
            status_text = f"✅ Live Check (ID: <code>{chat_id}</code>)" if chat_id and chat_id != '0' else "⚠️ Chat ID biriktirilmagan"
            text += f"{idx}. <b>{ch['name']}</b>: <a href='{ch['url']}'>Havola</a>\n   Holat: {status_text}\n\n"
            buttons.append([
                InlineKeyboardButton(
                    text=f"🗑 {ch['name']} kanalini o'chirish",
                    callback_data=f"del_channel_{ch['id']}"
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            text="🔄 Defolt 3 ta kanalni qayta tiklash",
            callback_data="reset_default_channels"
        )
    ])

    text += (
        "💡 <b>Kanal Chat ID sini avto-biriktirish uchun</b>:\n"
        "Shunchaki ushbu kanaldan 1 ta xabarni botga forvard (forward) qiling!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("del_channel_"))
async def delete_channel_callback(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return

    channel_id = int(callback.data.split("_")[2])
    success = await delete_channel_db(channel_id)
    if success:
        await callback.answer("✅ Kanal o'chirildi!", show_alert=True)
    else:
        await callback.answer("❌ Kanal topilmadi.", show_alert=True)

    # Ro'yxatni yangilash
    channels = await get_channels()
    text = "<b>📢 Majburiy Obuna Kanallari Ro'yxati:</b>\n\n"
    buttons = []
    
    if not channels:
        text += "⚠️ Hozirda hech qanday majburiy obuna kanali yo'q.\n\n"
    else:
        for idx, ch in enumerate(channels, 1):
            chat_id = str(ch.get('chat_id', '')).strip()
            status_text = f"✅ Live Check (ID: <code>{chat_id}</code>)" if chat_id and chat_id != '0' else "⚠️ Chat ID biriktirilmagan"
            text += f"{idx}. <b>{ch['name']}</b>: <a href='{ch['url']}'>Havola</a>\n   Holat: {status_text}\n\n"
            buttons.append([
                InlineKeyboardButton(
                    text=f"🗑 {ch['name']} kanalini o'chirish",
                    callback_data=f"del_channel_{ch['id']}"
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            text="🔄 Defolt 3 ta kanalni qayta tiklash",
            callback_data="reset_default_channels"
        )
    ])

    text += (
        "💡 <b>Kanal Chat ID sini avto-biriktirish uchun</b>:\n"
        "Shunchaki ushbu kanaldan 1 ta xabarni botga forvard (forward) qiling!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "reset_default_channels")
async def reset_channels_callback(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return

    await reset_channels_db()
    await callback.answer("✅ Kanallar defolt 3 ta yangi kanalga qayta tiklandi!", show_alert=True)

    # Ro'yxatni yangilash
    channels = await get_channels()
    text = "<b>📢 Majburiy Obuna Kanallari Ro'yxati:</b>\n\n"
    buttons = []
    for idx, ch in enumerate(channels, 1):
        chat_id = str(ch.get('chat_id', '')).strip()
        status_text = f"✅ Live Check (ID: <code>{chat_id}</code>)" if chat_id and chat_id != '0' else "⚠️ Chat ID biriktirilmagan"
        text += f"{idx}. <b>{ch['name']}</b>: <a href='{ch['url']}'>Havola</a>\n   Holat: {status_text}\n\n"
        buttons.append([
            InlineKeyboardButton(
                text=f"🗑 {ch['name']} kanalini o'chirish",
                callback_data=f"del_channel_{ch['id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔄 Defolt 3 ta kanalni qayta tiklash",
            callback_data="reset_default_channels"
        )
    ])

    text += (
        "💡 <b>Kanal Chat ID sini avto-biriktirish uchun</b>:\n"
        "Shunchaki ushbu kanaldan 1 ta xabarni botga forvard (forward) qiling!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

