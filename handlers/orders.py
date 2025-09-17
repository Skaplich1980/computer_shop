from aiogram import Router, types, F
from database import get_db_connection

router = Router()

@router.message(F.text == "/orders")
async def show_orders(message: types.Message):
    user_id = message.from_user.id
    conn = await get_db_connection()

    # Получаем все заказы пользователя
    orders = await conn.fetch("""
        SELECT order_id, total_price, created_at
        FROM orders
        WHERE user_id = $1
        ORDER BY created_at DESC
    """, user_id)

    if not orders:
        await message.answer("📭 У вас пока нет заказов.")
        await conn.close()
        return

    text_lines = ["📜 История ваших заказов:\n"]

    for order in orders:
        text_lines.append(
            f"🆔 Заказ №{order['order_id']} от {order['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            f"💰 Сумма: {order['total_price']} руб."
        )

        # Получаем состав заказа
        items = await conn.fetch("""
            SELECT oi.product_code, p.name, oi.quantity, oi.price_per_unit
            FROM order_items oi
            JOIN products p ON p.code = oi.product_code
            WHERE oi.order_id = $1
        """, order["order_id"])

        for code, name, qty, price in items:
            item_sum = qty * price
            text_lines.append(f"   • {name} — {qty} шт. × {price} руб. = {item_sum} руб.")

        text_lines.append("")  # пустая строка между заказами

    await conn.close()

    await message.answer("\n".join(text_lines))
