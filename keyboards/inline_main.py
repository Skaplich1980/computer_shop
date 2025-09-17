# keyboards/inline_main.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_inline_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Просмотреть товары", callback_data="browse_products")],
        [InlineKeyboardButton(text="🧺 Моя корзина", callback_data="view_cart")],
        [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])
