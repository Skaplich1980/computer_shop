# main_menu.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Товары")],
            [KeyboardButton(text="🛒 Моя корзина")],
            [KeyboardButton(text="📜 Мои заказы")]
        ],
        resize_keyboard=True
    )
