# menu.py

from aiogram import Router, types, F
from handlers.products import show_products, show_cart
from handlers.orders import show_orders

router = Router()

@router.message(F.text == "📦 Товары")
async def menu_products(message: types.Message):
    await show_products(message)

@router.message(F.text == "🛒 Моя корзина")
async def menu_cart(message: types.Message):
    await show_cart(message)

@router.message(F.text == "📜 Мои заказы")
async def menu_orders(message: types.Message):
    await show_orders(message)

# просмотр корзины
@router.callback_query(F.data == "view_cart")
async def menu_inline_cart(callback: types.CallbackQuery):
    await show_cart(callback)
    await callback.answer()
