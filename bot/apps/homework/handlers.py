from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.core import keyboards as core_keyboards

router = Router()


@router.callback_query(F.data == "homework")
async def homework(call: CallbackQuery) -> None:
    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        "Инструкция по домашкам появится позже. А пока просто отправьте работу "
        "через «Задать вопрос / Отправить домашку».",
        reply_markup=core_keyboards.main_inline_keyboard,
    )
