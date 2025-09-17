# main.py
import asyncio
import logging
import importlib
import pkgutil
from aiogram import Bot, Dispatcher # Bot — класс, который представляет нашего Telegram-бота и умеет отправлять/получать сообщения.
# Dispatcher — объект, который управляет обработкой входящих апдейтов (сообщений, команд, нажатий кнопок).
from config import BOT_TOKEN # Импортируем токен бота из файла config.py
# Это нужно, чтобы при первом запуске бот сам подготовил БД
# импорт всех хендлеров сразу
import handlers
from cart_store import load_cart

logging.basicConfig(level=logging.INFO) # Настраиваем логирование так, чтобы в консоль выводились все сообщения уровня INFO и выше.
# на этапе тестирования чтобы видеть все сообщения

async def on_shutdown():
    logging.info("Бот остановлен. Закрываем соединения...")

async def on_startup(): # функция выполняется при старте бота
    # Создание таблиц временно отключено
    load_cart() # загрузка корзины
    return

async def main():
    dp = Dispatcher()  # Создаём объект Dispatcher, который будет управлять всеми хендлерами и обработкой событий.
    bot = Bot(token=BOT_TOKEN) # Создаём объект Bot, передавая ему токен

    # Автоматический импорт всех модулей из пакета handlers
    for _, module_name, _ in pkgutil.iter_modules(handlers.__path__):
        module = importlib.import_module(f"handlers.{module_name}")
        if hasattr(module, "router"):
            dp.include_router(module.router)

    await on_startup() # Подготовительные действия (сейчас ничего не делает)
    try:
        await dp.start_polling(bot) # Запускаем «долгий опрос» (long polling) Telegram API
        # Бот начинает получать апдейты (сообщения, команды, нажатия кнопок) и передавать их в хендлеры.
    finally:
        await on_shutdown()

if __name__ == "__main__":
    asyncio.run(main()) # Запускаем асинхронную функцию main() через asyncio.run()