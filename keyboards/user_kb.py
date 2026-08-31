from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import urllib.parse

def get_subscription_keyboard(channels: list[dict], bot_username: str = "Girlsfilmbot") -> InlineKeyboardMarkup:
    buttons = []
    for idx, ch in enumerate(channels, 1):
        name = ch.get("name", f"{idx}-kanal")
        url = ch.get("url", "#")

        # To'g'ridan-to'g'ri Telegram kanal havolasini ochadigan inline tugma
        buttons.append([
            InlineKeyboardButton(text=f"📌 {name}", url=url)
        ])
    
    # Obunani tekshirish tugmasi
    buttons.append([
        InlineKeyboardButton(text="Tekshirish 🔄", callback_data="check_subscription")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_share_keyboard(bot_username: str = "Girlsfilmbot", movie_code: str = None) -> InlineKeyboardMarkup:
    bot_link = f"https://t.me/{bot_username}"
    if movie_code:
        share_link = f"https://t.me/{bot_username}?start={movie_code}"
        share_text = f"🍿 Kinoni ko'rish uchun kod: {movie_code}\n\nBotga kiring: {share_link}"
    else:
        share_link = bot_link
        share_text = f"🍿 Eng so'nggi va ajoyib filmlar botimizda:\n\n{bot_link}"

    encoded_text = urllib.parse.quote(share_text)
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(share_link)}&text={encoded_text}"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Do'stlarni taklif qilish",
                    url=share_url
                )
            ]
        ]
    )
