# handlers/products.py
# Компактный каталог с кнопками "Подробнее" и "🛒" для добавления в корзину

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from database import get_db_connection
from keyboards.inline_main import *
from html import escape
import cart_store

router = Router()

# ------------------------------
# FSM для добавления товара в корзину
# ------------------------------
class AddToCart(StatesGroup):
    waiting_for_quantity = State()
    selected_product_code = State()
    selected_product_name = State()
    selected_product_price = State()


# ------------------------------
# /products — компактный список товаров
# ------------------------------
@router.message(F.text == "/products")
async def show_products(event: types.Message | types.CallbackQuery):
    conn = await get_db_connection()
    rows = await conn.fetch("SELECT code, name, price FROM products ORDER BY name")
    await conn.close()

    if not rows:
        text = "❌ Товары пока не добавлены."
        reply_markup = get_inline_main_menu()
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, reply_markup=reply_markup)
        else:
            await event.answer(text, reply_markup=reply_markup)
        return

    lines = []
    kb = InlineKeyboardMarkup(inline_keyboard=[])

    for row in rows:
        name_html = escape(row["name"])
        lines.append(f"{name_html} — {row['price']} руб.")
        kb.inline_keyboard.append([
            InlineKeyboardButton(text=name_html, callback_data=f"details_{row['code']}"),
            InlineKeyboardButton(text="🛒", callback_data=f"add_{row['code']}")
        ])

    kb.inline_keyboard.append(get_back_to_main_button())
    text = "\n".join(lines)

    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    else:
        await event.reply(text, parse_mode="HTML", reply_markup=kb)


# ------------------------------
# Callback: показать карточку товара с фото
# ------------------------------
@router.callback_query(F.data.startswith("details_"))
async def product_details(callback: types.CallbackQuery):
    product_code = callback.data.split("_", 1)[1]

    conn = await get_db_connection()
    product = await conn.fetchrow(
        "SELECT code, name, price, image_file_id FROM products WHERE code = $1",
        product_code
    )
    await conn.close()

    if not product:
        await callback.message.answer("❌ Товар не найден.", reply_markup=get_inline_main_menu())
        await callback.answer()
        return

    name_html = escape(product["name"])
    caption = f"<b>{name_html}</b>\n💰 Цена: {product['price']} руб."
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_{product['code']}")]
    ])
    kb.inline_keyboard.append(get_back_to_main_button())

    if product["image_file_id"]:
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=product["image_file_id"],
                caption=caption,
                parse_mode="HTML"
            ),
            reply_markup=kb
        )
    else:
        await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=kb)

    await callback.answer()


# ------------------------------
# Callback: начать добавление в корзину
# ------------------------------
@router.callback_query(F.data.startswith("add_"))
async def add_to_cart_start(callback: types.CallbackQuery, state: FSMContext):
    product_code = callback.data.split("_", 1)[1]

    conn = await get_db_connection()
    product = await conn.fetchrow(
        "SELECT code, name, price FROM products WHERE code = $1",
        product_code
    )
    await conn.close()

    if not product:
        await callback.message.answer("❌ Товар не найден.", reply_markup=get_inline_main_menu())
        await callback.answer()
        return

    await state.update_data(
        selected_product_code=product["code"],
        selected_product_name=product["name"],
        selected_product_price=product["price"]
    )

    await callback.message.answer(f"Сколько «{product['name']}» вы хотите добавить?")
    await state.set_state(AddToCart.waiting_for_quantity)
    await callback.answer()


# ------------------------------
# FSM: получение количества и добавление в корзину
# ------------------------------
@router.message(AddToCart.waiting_for_quantity)
async def get_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text.strip())
        if quantity <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Пожалуйста, введите положительное число")
        return

    data = await state.get_data()
    cart_store.add_item(
        message.from_user.id,
        data["selected_product_code"],
        data["selected_product_name"],
        quantity,
        data["selected_product_price"]
    )

    await message.answer(
        f"✅ Добавлено {quantity} шт. {data['selected_product_name']} в корзину",
        reply_markup=get_inline_main_menu()
    )
    await state.clear()


# ------------------------------
# Показ содержимого корзины (универсально для Message и CallbackQuery)
# ------------------------------
async def show_cart(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    items = cart_store.get_user_cart(user_id)

    if not items:
        text = "🛒 Ваша корзина пуста."
        reply_markup = get_inline_main_menu()
        if isinstance(event, types.CallbackQuery):
            await event.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await event.reply(text, parse_mode="HTML", reply_markup=reply_markup)
        return

    lines = ["🛒 <b>Ваша корзина:</b>"]
    total_sum = 0
    for idx, (code, name, qty, price) in enumerate(items, start=1):
        item_sum = qty * price
        total_sum += item_sum
        lines.append(f"{idx}. {escape(name)} — {qty} шт. ({item_sum} руб.)")
    lines.append(f"\n💰 <b>Итого: {total_sum} руб.</b>")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="📦 Отправить заказ", callback_data="send_order")],
            get_back_to_main_button()
        ]
    )

    text = "\n".join(lines)
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    else:
        await event.reply(text, parse_mode="HTML", reply_markup=markup)


# ------------------------------
# Callback: очистка корзины
# ------------------------------
@router.callback_query(F.data == "clear_cart")
async def clear_cart_callback(callback: types.CallbackQuery):
    cart_store.clear_user_cart(callback.from_user.id)
    await callback.message.edit_text("✅ Корзина очищена", reply_markup=get_inline_main_menu())
    await callback.answer()


# ------------------------------
# Callback: отправка заказа в БД
# ------------------------------
@router.callback_query(F.data == "send_order")
async def send_order(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    items = cart_store.get_user_cart(user_id)

    # Если корзина пуста — редактируем текущее сообщение
    if not items:
        await callback.message.edit_text(
            "❌ Ваша корзина пуста.",
            parse_mode="HTML",
            reply_markup=get_inline_main_menu()
        )
        await callback.answer()
        return

    conn = await get_db_connection()
    try:
        # Добавляем пользователя в таблицу users (если нет)
        await conn.execute("""
            INSERT INTO users (user_id, username, first_name, last_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id, callback.from_user.username, callback.from_user.first_name, callback.from_user.last_name)

        total_sum = sum(qty * price for _, _, qty, price in items)

        # Создаём заказ
        order_row = await conn.fetchrow(
            "INSERT INTO orders (user_id, total_price) VALUES ($1, $2) RETURNING order_id",
            user_id, total_sum
        )
        order_id = order_row["order_id"]

        # Добавляем позиции заказа
        for product_code, _, qty, price in items:
            await conn.execute(
                "INSERT INTO order_items (order_id, product_code, quantity, price_per_unit) VALUES ($1, $2, $3, $4)",
                order_id, product_code, qty, price
            )
    finally:
        await conn.close()

    # Очищаем корзину
    cart_store.clear_user_cart(user_id)

    # Редактируем текущее сообщение, а не отправляем новое
    await callback.message.edit_text(
        f"✅ Заказ №{order_id} успешно отправлен!",
        parse_mode="HTML",
        reply_markup=get_inline_main_menu()
    )
    await callback.answer()
