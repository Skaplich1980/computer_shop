# handlers/help.py
from aiogram import Router, types, F
from aiogram.filters import Command

router = Router()

# Общая функция для отправки справки
async def send_help(target: types.Message | types.CallbackQuery):
    help_text = (
        "📖 Доступные команды и функции бота:\n\n"
        "🔹 /start — регистрация нового пользователя или вход, если вы уже зарегистрированы.\n"
        "🔹 /help — показать эту справку.\n\n"
        "🛍 Работа с товарами:\n"
        "   • /products — показать список доступных товаров с ценами.\n"
        "   • Нажмите на товар, чтобы выбрать его и указать количество для добавления в корзину.\n\n"
        "🛒 Работа с корзиной:\n"
        "   • /cart — показать содержимое корзины: товары, количество, стоимость и общую сумму.\n"
        "   • В корзине доступны кнопки:\n"
        "       🗑 Очистить корзину — удалить все товары.\n"
        "       📦 Отправить заказ — оформить заказ и отправить его в базу данных.\n\n"
        "📜 История заказов:\n"
        "   • /orders — показать список ваших заказов с датой, суммой и составом.\n\n"
        "💡 Также можно пользоваться кнопками главного меню:\n"
        "   📦 Просмотреть товары | 🛒 Моя корзина | 📜 Мои заказы\n"
    )

    # Если вызов из команды
    if isinstance(target, types.Message):
        await target.answer(help_text)
    # Если вызов из callback
    elif isinstance(target, types.CallbackQuery):
        await target.message.answer(help_text)
        await target.answer()

# Хендлер команды /help
@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await send_help(message)

# Хендлер нажатия кнопки "Помощь" в inline‑меню
@router.callback_query(F.data == "help")
async def cb_help(callback: types.CallbackQuery):
    await send_help(callback)
