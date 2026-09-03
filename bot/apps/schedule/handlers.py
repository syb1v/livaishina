from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core import keyboards as core_keyboards
from bot.database.repository import ScheduleRepository

router = Router()

FALLBACK_TEXT = "Расписание пока не задано."


@router.callback_query(F.data == "schedule")
async def schedule(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    repo = ScheduleRepository(session)
    items = await repo.get_all()
    text = "\n".join(f"• {item.label}" for item in items) if items else FALLBACK_TEXT
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(text, reply_markup=core_keyboards.main_inline_keyboard)
