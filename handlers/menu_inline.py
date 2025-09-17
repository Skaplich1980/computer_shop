# handlers/menu_inline.py — обработчики callback'ов стартового меню
from aiogram import Router, types, F
from keyboards.inline_main import get_inline_main_menu
from handlers.products import show_products, show_cart  # общие функции
router = Router()

@router.callback_query(F.data == "browse_products")
async def cb_browse_products(callback: types.CallbackQuery):
    await show_products(callback.message)
    await callback.answer()

@router.callback_query(F.data == "view_cart")
async def cb_view_cart(callback: types.CallbackQuery):
    await show_cart(callback.message)
    await callback.answer()

# clear_cart есть как callback; важно, чтобы callback_data совпадала: "clear_cart"
