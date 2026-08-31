from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Yangi kino qo'shish"),
                KeyboardButton(text="🗑 Kino o'chirish")
            ],
            [
                KeyboardButton(text="📜 Kinolar ro'yxati"),
                KeyboardButton(text="📢 Kanallar ro'yxati")
            ],
            [
                KeyboardButton(text="📊 Statistika")
            ]
        ],
        resize_keyboard=True
    )

def get_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Bekor qilish ❌")]
        ],
        resize_keyboard=True
    )

def get_confirm_movie_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash va saqlash", callback_data="confirm_add_movie")
            ],
            [
                InlineKeyboardButton(text="✏️ Kodni tahrirlash", callback_data="edit_movie_code"),
                InlineKeyboardButton(text="🔄 Mediani almashtirish", callback_data="edit_movie_media")
            ],
            [
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_add_movie")
            ]
        ]
    )
