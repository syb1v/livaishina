"""Stats dashboard and schedule text helpers for the admin panel."""

import math
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from admin.templates import render
from bot.database.models import Deadline, MessageLog, ScheduleItem, User
from bot.database.session import SessionMaker

router = APIRouter()

MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля",
    5: "мая", 6: "июня", 7: "июля", 8: "августа",
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря",
}

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


def format_deadlines_ru(deadlines: list[Deadline]) -> str:
    lines = []
    for d in deadlines:
        lines.append(f"{d.due_date.day} {MONTHS_RU[d.due_date.month]} — {d.label}")
    return "\n".join(lines)


def next_deadline(deadlines: list[Deadline]) -> Deadline | None:
    today = date.today()
    upcoming = [d for d in deadlines if d.due_date >= today]
    return min(upcoming, key=lambda d: d.due_date) if upcoming else None


@router.get("/admin/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    from sqladmin import Admin

    app = request.app
    admin: Admin = app.state.admin if hasattr(app, "state") and hasattr(app.state, "admin") else None

    async with SessionMaker() as session:
        users_total = (await session.execute(select(User).order_by(User.id))).scalars().all()
        log_count = await session.scalar(
            select(MessageLog.id).order_by(MessageLog.id.desc()).limit(1)
        )
        recent = (
            (
                await session.execute(
                    select(MessageLog)
                    .order_by(MessageLog.created_at.desc())
                    .limit(15)
                )
            )
            .scalars()
            .all()
        )
        by_day = (
            (
                await session.execute(
                    select(
                        MessageLog.created_at,
                    )
                )
            )
            .scalars()
            .all()
        )

    # group by day (last 14 days)
    counts: dict[str, int] = {}
    for ts in by_day:
        key = ts.strftime("%Y-%m-%d")
        counts[key] = counts.get(key, 0) + 1
    days = []
    for i in range(13, -1, -1):
        d = datetime.utcnow() - timedelta(days=i)
        key = d.strftime("%Y-%m-%d")
        days.append((key, counts.get(key, 0)))

    max_count = max((c for _, c in days), default=0) or 1
    bars = [
        (label[5:], count, "█" * round(count / max_count * 30))
        for label, count in days
    ]

    by_type: dict[str, int] = {}
    for m in recent:
        by_type[m.content_type] = by_type.get(m.content_type, 0) + 1

    total_submissions = sum(counts.values())

    ctx = {
        "request": request,
        "users_total": len(list(users_total)),
        "submissions_total": total_submissions,
        "log_rows": log_count or 0,
        "bars": bars,
        "by_type": [
            (TYPE_LABELS_RU.get(t, t), c) for t, c in sorted(
                by_type.items(), key=lambda kv: -kv[1]
            )
        ],
        "recent": [
            {
                "telegram_id": m.telegram_id,
                "content_type": TYPE_LABELS_RU.get(m.content_type, m.content_type),
                "created_at": m.created_at.strftime("%d.%m %H:%M"),
            }
            for m in reversed(recent)
        ],
    }

    return render(request, "stats.html", ctx)
