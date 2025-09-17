# cart_store.py — единая точка работы с корзиной
# -------------------------------------------------
# Этот модуль отвечает за хранение корзин пользователей в памяти
# и синхронизацию их с JSON-файлом, чтобы данные не терялись при
# перезапуске бота.
# -------------------------------------------------

import json
import os
from typing import Dict, List, Tuple

# Имя файла, в котором будут храниться все корзины.
# Здесь указан относительный путь — файл будет создан в текущей рабочей директории.
# Если нужно хранить рядом с этим модулем, можно сделать:
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# CART_FILE = os.path.join(BASE_DIR, "cart_store.json")
CART_FILE = "cart_store.json"

# Внутреннее хранилище корзин в памяти (RAM).
# Структура:
# {
#   "123456": [ ["cpu", "Процессор", 2, 10000], ["ram", "Память", 1, 5000] ],
#   "789012": [ ["gpu", "Видеокарта", 1, 30000] ]
# }
# Ключ — user_id в виде строки.
# Значение — список товаров, где каждый товар — список из:
#   [код товара, название, количество, цена за единицу]
_cart: Dict[str, List[Tuple[str, str, int, int]]] = {}


def load_cart():
    """
    Загружает корзины из JSON-файла в память (_cart).
    Вызывается при старте бота, чтобы восстановить данные после перезапуска.
    """
    global _cart
    if os.path.exists(CART_FILE):
        # Если файл существует — читаем его содержимое
        with open(CART_FILE, "r", encoding="utf-8") as f:
            _cart = json.load(f)
    else:
        # Если файла нет — начинаем с пустого словаря
        _cart = {}


def save_cart():
    """
    Сохраняет текущее состояние корзин (_cart) в JSON-файл.
    Вызывается после каждого изменения корзины.
    """
    with open(CART_FILE, "w", encoding="utf-8") as f:
        # ensure_ascii=False — чтобы кириллица сохранялась читаемо
        # indent=2 — для красивого форматирования
        json.dump(_cart, f, ensure_ascii=False, indent=2)


def get_user_cart(user_id: int) -> List[Tuple[str, str, int, int]]:
    """
    Возвращает корзину конкретного пользователя в виде списка кортежей.
    Если корзина пустая — вернёт пустой список.
    """
    # В JSON мы храним списки, но для удобства работы в коде возвращаем кортежи
    return [tuple(x) for x in _cart.get(str(user_id), [])]


def set_user_cart(user_id: int, items: List[Tuple[str, str, int, int]]):
    """
    Полностью заменяет корзину пользователя на переданный список товаров.
    После изменения сразу сохраняет данные в файл.
    """
    # Преобразуем кортежи в списки, чтобы их можно было сериализовать в JSON
    _cart[str(user_id)] = [list(x) for x in items]
    save_cart()


def clear_user_cart(user_id: int):
    """
    Очищает корзину пользователя (делает её пустой).
    """
    _cart[str(user_id)] = []
    save_cart()


def add_item(user_id: int, product_code: str, product_name: str, qty: int, price: int):
    """
    Добавляет товар в корзину пользователя.
    Если товар уже есть — увеличивает количество.
    """
    items = get_user_cart(user_id)
    for i, (code, name, q, p) in enumerate(items):
        if code == product_code:
            # Если товар уже есть — увеличиваем количество
            items[i] = (code, name, q + qty, p)
            set_user_cart(user_id, items)
            return
    # Если товара нет — добавляем новую позицию
    items.append((product_code, product_name, qty, price))
    set_user_cart(user_id, items)

