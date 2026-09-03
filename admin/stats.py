"""Stats dashboard as a native sqladmin BaseView page."""

from datetime import date, datetime, timedelta

from fastapi import Request
from sqlalchemy import func, select
from sqladmin import BaseView, expose

from bot.database.models import Deadline, MessageLog, ScheduleItem, User
from bot.database.session import SessionMaker

TYPE_LABELS_RU = {
    "text": "Текст",
    "photo": "Фото / скриншот",
    "document": "Документ / файл",
    "video": "Видео",
    "video_note": "Видеокружок",
    "voice": "Голосовое",
    "audio": "Аудио",
    "sticker": "Стикер",
    "animation": "GIF",
}


class StatsAdmin(BaseView):
    name = "Статистика"
    icon = "fa-solid fa-chart-line"

    @expose("/stats", methods=["GET"])
    async def stats_page(self, request: Request):
        async with SessionMaker() as session:
            users_total = await session.scalar(select(func.count(User.id)))

            since = datetime.utcnow() - timedelta(days=14)
            timestamps = (
                (await session.execute(select(MessageLog.created_at).where(MessageLog.created_at >= since)))
                .scalars()
                .all()
            )
            total_in_period = len(timestamps)

            recent_rows = (
                (
                    await session.execute(
                        select(MessageLog).order_by(MessageLog.created_at.desc()).limit(15)
                    )
                )
                .scalars()
                .all()
            )

            by_type_rows = (
                (
                    await session.execute(
                        select(MessageLog.content_type, func.count(MessageLog.id))
                        .group_by(MessageLog.content_type)
                        .order_by(func.count(MessageLog.id).desc())
                    )
                )
                .all()
            )

            deadlines = (
                (await session.execute(select(Deadline).order_by(Deadline.position)))
                .scalars()
                .all()
            )
            schedule_items = (
                (await session.execute(select(ScheduleItem).order_by(ScheduleItem.position)))
                .scalars()
                .all()
            )

        counts: dict[str, int] = {}
        for ts in timestamps:
            key = ts.strftime("%d.%m")
            counts[key] = counts.get(key, 0) + 1
        days = []
        for i in range(13, -1, -1):
            d = datetime.utcnow() - timedelta(days=i)
            key = d.strftime("%d.%m")
            days.append((key, counts.get(key, 0)))
        max_count = max((c for _, c in days), default=0) or 1
        bars = [
            (day, count, "█" * max(round(count / max_count * 30), 1) if count else "")
            for day, count in days
        ]

        today = date.today()
        upcoming = [d for d in deadlines if d.due_date >= today]
        next_dl = min(upcoming, key=lambda d: d.due_date) if upcoming else None

        def _fmt(d: Deadline) -> str:
            months = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
                      "июля", "августа", "сентября", "октября", "ноября", "декабря"]
            return f"{d.due_date.day} {months[d.due_date.month]} — {d.label}"

        ctx = {
            "users_total": users_total or 0,
            "submissions_total": total_in_period,
            "log_rows_total": len(list(timestamps)) + 0,
            "bars": bars,
            "by_type": [
                (TYPE_LABELS_RU.get(t, t), c) for t, c in by_type_rows
            ],
            "recent": [
                {
                    "telegram_id": m.telegram_id,
                    "content_type": TYPE_LABELS_RU.get(m.content_type, m.content_type),
                    "created_at": m.created_at.strftime("%d.%m %H:%M"),
                }
                for m in reversed(recent_rows)
            ],
            "next_deadline": _fmt(next_dl) if next_dl else "нет ближайших",
            "deadlines_count": len(deadlines),
            "schedule_count": len(schedule_items),
        }
        return await self.templates.TemplateResponse(
            request, "stats.html", {**ctx}
        )
