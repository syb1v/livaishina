from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core import keyboards as core_keyboards
from bot.database.repository import UserRepository
from config.settings import ADMIN_ID

router = Router()

GREETING = "Привет, это бот-помощник по курсу, выбирай категорию 👇"


async def _greet(message: Message, session: AsyncSession, telegram_id: int) -> None:
    repo = UserRepository(session)
    if not await repo.get_by_telegram_id(telegram_id):
        await repo.create(telegram_id)
    await message.answer(
        GREETING,
        reply_markup=core_keyboards.start_inline_keyboard(telegram_id == ADMIN_ID),
    )


@router.message(CommandStart())
async def start(message: Message, session: AsyncSession) -> None:
    await _greet(message, session, message.from_user.id)
    await message.answer(
        "Кнопка «Меню» внизу экрана всегда вернёт вас сюда 👇",
        reply_markup=core_keyboards.menu_reply_keyboard,
    )


@router.message(F.text == core_keyboards.MENU_BUTTON_TEXT)
async def menu_button(message: Message, session: AsyncSession) -> None:
    await _greet(message, session, message.from_user.id)


@router.callback_query(F.data == "main")
async def back_to_main(call: CallbackQuery, session: AsyncSession) -> None:
    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        GREETING,
        reply_markup=core_keyboards.start_inline_keyboard(call.from_user.id == ADMIN_ID),
    )
