import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core import keyboards as core_keyboards
from bot.database.repository import DeadlineRepository

router = Router()
logger = logging.getLogger(__name__)

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

FALLBACK_TEXT = "Дедлайны пока не заданы."


def format_deadlines(deadlines) -> str:
    lines = []
    for d in deadlines:
        lines.append(f"• {d.due_date.day} {MONTHS_RU[d.due_date.month]} — {d.label}")
    return "\n".join(lines)


@router.callback_query(F.data == "deadlines")
async def deadlines(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    repo = DeadlineRepository(session)
    items = await repo.get_all()
    text = format_deadlines(items) if items else FALLBACK_TEXT
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(text, reply_markup=core_keyboards.main_inline_keyboard)
