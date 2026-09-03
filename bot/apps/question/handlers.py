"""Mail-mode forwarding.

Students may send ANY message (text, photo, document, video, voice, audio,
sticker, video note) to the bot at ANY time — no mode button required.

The message is copied to the admin chat with a deep-linked header, so the
admin always knows who sent it. Replying to that copy sends the reply back
to the student. Reply-based routing is fully stateless, so restarts of the
bot never break an ongoing conversation.
"""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.core import keyboards as core_keyboards
from bot.database.repository import MessageLogRepository
from config.settings import ADMIN_ID

router = Router()
logger = logging.getLogger(__name__)

QUESTION_INFO_TEXT = (
    "Напишите ваш вопрос или отправьте домашку (фото, файл, видео) прямо в чат — "
    "я передам её Алии и кураторам. Ответ придёт сюда же.\n\n"
    "Отвечаем в течение дня. Нажимать ничего больше не нужно."
)

HEADER_TEMPLATE = "✉️ {name} (id={user_id}) переслал(а) сообщение:\n\n"


def _sender_name(message: Message) -> str:
    user = message.from_user
    parts = [user.first_name or "", user.last_name or ""]
    name = " ".join(p for p in parts if p).strip()
    if not name:
        name = f"@{user.username}" if user.username else "Без имени"
    return name


async def _copy_to_admin(message: Message, session: AsyncSession) -> None:
    header = HEADER_TEMPLATE.format(name=_sender_name(message), user_id=message.from_user.id)
    try:
        await message.send_copy(ADMIN_ID, caption=header)
    except TypeError:
        # content type without caption support (e.g. sticker)
        await message.bot.send_message(ADMIN_ID, header.rstrip())
        await message.send_copy(ADMIN_ID)
    except Exception:
        logger.exception("failed to copy message to admin")
        return
    try:
        await MessageLogRepository(session).log(
            message.from_user.id, message.content_type
        )
    except Exception:
        logger.exception("failed to log submission")


@router.message(Command("question"))
async def question_command(message: Message) -> None:
    await message.answer(QUESTION_INFO_TEXT, reply_markup=core_keyboards.main_inline_keyboard)


@router.callback_query(F.data == "question")
async def question_button(call: CallbackQuery) -> None:
    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(QUESTION_INFO_TEXT, reply_markup=core_keyboards.main_inline_keyboard)


@router.message(F.from_user.id == ADMIN_ID, F.reply_to_message)
async def admin_reply(message: Message) -> None:
    """Admin replies to a copied message -> route the reply to the student."""
    stored_id = None
    if message.reply_to_message.text:
        import re

        match = re.search(r"id=(\d+)", message.reply_to_message.text)
        if match:
            stored_id = int(match.group(1))
    if stored_id is None:
        await message.answer("Не удалось определить получателя: нет ID в исходном сообщении.")
        return
    try:
        await message.send_copy(stored_id)
        await message.answer("Доставлено ✅")
    except Exception:
        logger.exception("failed to deliver admin reply")
        await message.answer("Не удалось доставить сообщение ученику.")


@router.message(F.chat.id == ADMIN_ID, F.text == core_keyboards.MENU_BUTTON_TEXT)
async def admin_menu(message: Message) -> None:
    await message.answer(
        "Меню администратора",
        reply_markup=core_keyboards.menu_reply_keyboard,
    )


@router.message(F.chat.id == ADMIN_ID)
async def admin_chat_noise(message: Message) -> None:
    """Non-reply messages in the admin chat are ignored."""
    return


@router.message()
async def forward_to_admin(message: Message, session: AsyncSession) -> None:
    """Catch-all: every private message from students goes to the admin chat."""
    if message.chat.type != "private":
        return
    await _copy_to_admin(message, session)
    await message.answer(
        "✅ Получено! Алия и кураторы ответят вам в течение дня.",
        reply_markup=core_keyboards.start_inline_keyboard(message.from_user.id == ADMIN_ID),
    )
