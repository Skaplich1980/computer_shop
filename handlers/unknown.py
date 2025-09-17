from aiogram import Router, types
from aiogram.filters import Command

router = Router()

# Ловим все сообщения, которые начинаются с "/" (команды), но не обрабатываются другими хендлерами
@router.message(lambda message: message.text and message.text.startswith("/"))
async def unknown_command(message: types.Message):
    await message.answer("❌ Такой команды нет. Введите /help, чтобы посмотреть список доступных команд.")