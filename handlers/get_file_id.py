# handlers/get_file_id.py
from aiogram import Router, types, F

router = Router()

@router.message(F.photo)
async def get_file_id(message: types.Message):
    """
    Ловит фото, берёт file_id в максимальном качестве и отправляет его как чистый текст.
    """
    file_id = message.photo[-1].file_id
    await message.answer(file_id)  # отправляем только код, без <code>...</code>
