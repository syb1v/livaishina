from aiogram.types import InlineKeyboardMarkup

from config.settings import ADMIN_ID


def start_inline_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [("📚 Материалы", "materials")],
        [("🏠 Домашки", "homework")],
        [("⏰ Дедлайны", "deadlines")],
        [("❓ Задать вопрос / Отправить домашку", "question")],
    ]
    if is_admin:
        rows.append([( "👥 Ученики", "admin_users")])
    return InlineKeyboardMarkup(
        inline_keyboard=[[{"text": t, "callback_data": d} for t, d in row] for row in rows]
    )


main_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[[{"text": "На главную", "callback_data": "main"}]]
)

__all__ = ["start_inline_keyboard", "main_inline_keyboard", "ADMIN_ID"]
