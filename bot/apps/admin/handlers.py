from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User

router = Router()


@router.callback_query(F.data == "admin_users")
async def admin_users(call: CallbackQuery, session: AsyncSession) -> None:
    result = await session.execute(select(User.telegram_id).order_by(User.id))
    ids = result.scalars().all()

    lines = [f"Учеников: {len(ids)}"]
    lines += [f"• <a href='tg://user?id={tid}'>{tid}</a>" for tid in ids]

    await call.answer()
    await call.message.answer("\n".join(lines), disable_web_page_preview=True)
