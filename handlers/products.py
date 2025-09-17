# handlers/products.py
# Модуль отвечает за работу с товарами, корзиной и оформлением заказа

from aiogram import Router, types, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from database import get_db_connection
from cart_store import get_user_cart, add_item, clear_user_cart  # функции для работы с корзиной
from keyboards.inline_main import get_inline_main_menu

router = Router()

# ------------------------------
# FSM (Finite State Machine) для добавления товара в корзину
# ------------------------------
class AddToCart(StatesGroup):
    waiting_for_quantity = State()  # Ожидание ввода количества
    selected_product_code = State()  # Код выбранного товара
    selected_product_name = State()  # Название выбранного товара
    selected_product_price = State() # Цена выбранного товара

# ------------------------------
# Команда /products — показать список товаров
# ------------------------------
@router.message(F.text == "/products")
async def show_products(message: types.Message):
    """
    Выводит список товаров из БД с кнопками для добавления в корзину.
    """
    conn = await get_db_connection()
    rows = await conn.fetch("SELECT code, name, price, image_file_id FROM products ORDER BY name")
    await conn.close()

    if not rows:
        await message.answer("❌ Товары пока не добавлены.")
        return

    # Формируем inline-клавиатуру с товарами
    for row in rows:
        # Кнопка для добавления в корзину
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"Добавить в корзину — {row['price']} руб.",
                    callback_data=f"product_{row['code']}"
                )]
            ]
        )

        caption = f"<b>{row['name']}</b>\n💰 Цена: {row['price']} руб."

        if row["image_file_id"]:
            # Отправляем фото с подписью и кнопкой
            await message.answer_photo(
                photo=row["image_file_id"],
                caption=caption,
                reply_markup=markup
            )
        else:
            # Если фото нет — отправляем только текст
            await message.answer(caption, reply_markup=markup)

# ------------------------------
# Callback: выбор товара из списка
# ------------------------------
@router.callback_query(F.data.startswith("product_"))
async def product_selected(callback: types.CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие на товар, запрашивает количество.
    """
    product_code = callback.data.split("_", 1)[1]

    conn = await get_db_connection()
    product = await conn.fetchrow("SELECT code, name, price FROM products WHERE code = $1", product_code)
    await conn.close()

    if not product:
        await callback.message.answer("❌ Товар не найден.")
        await callback.answer()
        return

    # Сохраняем данные о товаре в FSM
    await state.update_data(
        selected_product_code=product["code"],
        selected_product_name=product["name"],
        selected_product_price=product["price"]
    )

    await callback.message.answer(f"Сколько {product['name']} вы хотите добавить?")
    await state.set_state(AddToCart.waiting_for_quantity)  # Переходим в состояние ожидания количества
    await callback.answer()

# ------------------------------
# FSM: получение количества и добавление в корзину
# ------------------------------
@router.message(AddToCart.waiting_for_quantity)
async def get_quantity(message: types.Message, state: FSMContext):
    """
    Получает количество товара от пользователя, проверяет корректность ввода,
    добавляет товар в корзину.
    """
    try:
        quantity = int(message.text.strip())  # Преобразуем в число, убираем пробелы
        if quantity <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Пожалуйста, введите положительное число")
        return

    data = await state.get_data()
    product_code = data["selected_product_code"]
    product_name = data["selected_product_name"]
    product_price = data["selected_product_price"]

    user_id = message.from_user.id

    # Добавляем товар в корзину через cart_store
    add_item(user_id, product_code, product_name, quantity, product_price)

    # Отправляем подтверждение и показываем главное меню
    await message.answer(
        f"✅ Добавлено {quantity} шт. {product_name} в корзину",
        reply_markup=get_inline_main_menu()
    )
    await state.clear()  # Сбрасываем состояние FSM

# ------------------------------
# Команда /cart — показать содержимое корзины
# ------------------------------
@router.message(F.text == "/cart")
async def show_cart(message: types.Message):
    """
    Показывает содержимое корзины пользователя.
    """
    user_id = message.from_user.id
    items = get_user_cart(user_id)

    if not items:
        await message.answer("🛒 Ваша корзина пуста.", reply_markup=get_inline_main_menu())
        return

    text_lines = ["🛒 Ваша корзина:"]
    total_sum = 0
    for idx, (code, name, qty, price) in enumerate(items, start=1):
        item_sum = qty * price
        total_sum += item_sum
        text_lines.append(f"{idx}. {name} — {qty} шт. ({item_sum} руб.)")

    text_lines.append(f"\n💰 Общая сумма: {total_sum} руб.")

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")],
            [InlineKeyboardButton(text="📦 Отправить заказ", callback_data="send_order")]
        ]
    )

    await message.answer("\n".join(text_lines), reply_markup=markup)

# ------------------------------
# Callback: очистка корзины
# ------------------------------
@router.callback_query(F.data == "clear_cart")
async def clear_cart_callback(callback: types.CallbackQuery):
    """
    Очищает корзину пользователя.
    """
    user_id = callback.from_user.id
    clear_user_cart(user_id)
    await callback.message.answer("✅ Корзина очищена", reply_markup=get_inline_main_menu())
    await callback.answer()

# ------------------------------
# Callback: отправка заказа в БД
# ------------------------------
@router.callback_query(F.data == "send_order")
async def send_order(callback: types.CallbackQuery):
    """
    Отправляет заказ в базу данных PostgreSQL и очищает корзину.
    """
    user_id = callback.from_user.id
    items = get_user_cart(user_id)

    if not items:
        await callback.message.answer("❌ Ваша корзина пуста.")
        await callback.answer()
        return

    conn = await get_db_connection()

    # Регистрируем пользователя в БД, если его нет
    await conn.execute("""
        INSERT INTO users (user_id, username, first_name, last_name)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id) DO NOTHING
    """, user_id, callback.from_user.username, callback.from_user.first_name, callback.from_user.last_name)

    # Считаем общую сумму заказа
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

    await conn.close()

    # Очищаем корзину
    clear_user_cart(user_id)

    await callback.message.answer(f"✅ Заказ №{order_id} успешно отправлен!", reply_markup=get_inline_main_menu())
    await callback.answer()
