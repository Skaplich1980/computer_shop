# cart_store.py — единая точка работы с корзиной
# -------------------------------------------------
# Этот модуль отвечает за хранение корзин пользователей в памяти
# и синхронизацию их с JSON-файлом, чтобы данные не терялись при
# перезапуске бота.
# -------------------------------------------------

import sys
print("[CART] module key in sys.modules:", __name__)

import json
import os
import threading
from typing import Dict, List, Tuple

# Фиксируем путь к файлу рядом с модулем (чтобы не зависеть от CWD)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CART_FILE = os.path.join(BASE_DIR, "cart_store.json")

# Потокобезопасность на случай параллельных хендлеров
_LOCK = threading.RLock()

# Внутреннее хранилище корзин в памяти (RAM).
# Ключ — user_id (str). Значение — список: [код, название, кол-во, цена]
_cart: Dict[str, List[Tuple[str, str, int, int]]] = {}


def load_cart() -> None:
    """Загружает корзины из JSON-файла в память (_cart)."""
    global _cart
    with _LOCK:
        if os.path.exists(CART_FILE):
            try:
                with open(CART_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # safety: убедимся, что структура валидна
                if isinstance(data, dict):
                    _cart = {str(k): list(v) for k, v in data.items()}
                else:
                    _cart = {}
            except Exception:
                # В проде можно добавить логирование
                _cart = {}
        else:
            _cart = {}


def save_cart() -> None:
    """Сохраняет текущее состояние корзин (_cart) в JSON-файл."""
    with _LOCK:
        tmp_file = CART_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(_cart, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, CART_FILE)  # атомарная запись


def get_user_cart(user_id: int) -> List[Tuple[str, str, int, int]]:
    """Возвращает корзину пользователя. Пустой список, если нет."""
    with _LOCK:
        data = [tuple(x) for x in _cart.get(str(user_id), [])]
        print(f"[CART] get_user_cart user={user_id} items={len(data)} file={CART_FILE}")
        return data


def set_user_cart(user_id: int, items: List[Tuple[str, str, int, int]]) -> None:
    """Полностью заменяет корзину пользователя и сохраняет на диск."""
    with _LOCK:
        _cart[str(user_id)] = [list(x) for x in items]
    save_cart()


def clear_user_cart(user_id: int) -> None:
    """Очищает корзину пользователя и сохраняет на диск."""
    with _LOCK:
        _cart[str(user_id)] = []
    save_cart()

def add_item(user_id: int, product_code: str, product_name: str, qty: int, price: int) -> None:
    """Добавляет товар в корзину пользователя, увеличивает количество если позиция уже есть."""
    with _LOCK:
        print(f"[CART] add_item user={user_id} code={product_code} qty={qty} before={len(_cart.get(str(user_id), []))}")
        items = [tuple(x) for x in _cart.get(str(user_id), [])]
        for i, (code, name, q, p) in enumerate(items):
            if code == product_code:
                items[i] = (code, name, q + qty, p)
                _cart[str(user_id)] = [list(x) for x in items]
                save_cart()
                print(f"[CART] add_item updated, after={len(items)}")
                return
        items.append((product_code, product_name, qty, price))
        _cart[str(user_id)] = [list(x) for x in items]
    save_cart()
    print(f"[CART] add_item appended, after={len(items)}")


# Загружаем корзины при импорте модуля
load_cart()
