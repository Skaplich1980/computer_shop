# start.py

from aiogram import Router, types
from aiogram.filters import CommandStart
from database import get_db_connection
from keyboards.main_menu import get_main_menu  # импортируем меню
from keyboards.inline_main import get_inline_main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    # Регистрируем пользователя в БД, если его нет
    conn = await get_db_connection()

    user_exists = await conn.fetchval(
        "SELECT 1 FROM users WHERE user_id = $1",
        message.from_user.id
    )

    if not user_exists:
        await conn.execute('''
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES ($1, $2, $3, $4)
        ''',
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            message.from_user.last_name
        )
        text = f"👋 Привет, {message.from_user.first_name}! 🎉\nВы успешно зарегистрированы в системе."
    else:
        text = f"С возвращением, {message.from_user.first_name}! ✅\nВы уже зарегистрированы."

    await conn.close()

    # Отправляем сообщение с главным меню 1 вариант main_menu
    # await message.answer(
    #     text + "\n\nВыберите действие из меню ниже:",
    #     reply_markup=get_main_menu()
    # )
    # Отправляем сообщение с главным меню 2 вариант inline_menu
    await message.answer(
        text + "\n\nДобро пожаловать в магазин компьютерных комплектующих! Выберите действие:",
        reply_markup=get_inline_main_menu()
    )