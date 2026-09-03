from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Deadline, MessageLog, ScheduleItem, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(self, telegram_id: int) -> User:
        user = User(telegram_id=telegram_id)
        self.session.add(user)
        await self.session.commit()
        return user


class DeadlineRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Deadline]:
        result = await self.session.execute(
            select(Deadline).order_by(Deadline.position, Deadline.due_date)
        )
        return list(result.scalars().all())

    async def replace_all(self, items: list[dict]) -> None:
        await self.session.execute(delete(Deadline))
        self.session.add_all([Deadline(**item) for item in items])
        await self.session.commit()


class ScheduleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[ScheduleItem]:
        result = await self.session.execute(
            select(ScheduleItem).order_by(ScheduleItem.position, ScheduleItem.id)
        )
        return list(result.scalars().all())

    async def replace_all(self, items: list[dict]) -> None:
        await self.session.execute(delete(ScheduleItem))
        self.session.add_all([ScheduleItem(**item) for item in items])
        await self.session.commit()


class StatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def totals(self) -> dict:
        users = await self.session.scalar(select(func.count(User.id)))
        submissions = await self.session.scalar(select(func.count(MessageLog.id)))
        deadlines = await self.session.scalar(select(func.count(Deadline.id)))
        schedule = await self.session.scalar(select(func.count(ScheduleItem.id)))
        return {
            "users": users or 0,
            "submissions": submissions or 0,
            "deadlines": deadlines or 0,
            "schedule": schedule or 0,
        }

    async def submissions_by_day(self, days: int = 14) -> list[tuple]:
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(
                func.date(MessageLog.created_at),
                func.count(MessageLog.id),
            )
            .where(MessageLog.created_at >= since)
            .group_by(func.date(MessageLog.created_at))
            .order_by(func.date(MessageLog.created_at))
        )
        return [(str(row[0]), row[1]) for row in result.all()]

    async def top_users(self, limit: int = 10) -> list[tuple]:
        result = await self.session.execute(
            select(MessageLog.telegram_id, func.count(MessageLog.id))
            .group_by(MessageLog.telegram_id)
            .order_by(func.count(MessageLog.id).desc())
            .limit(limit)
        )
        return [(row[0], row[1]) for row in result.all()]

    async def by_content_type(self) -> list[tuple]:
        result = await self.session.execute(
            select(MessageLog.content_type, func.count(MessageLog.id))
            .group_by(MessageLog.content_type)
            .order_by(func.count(MessageLog.id).desc())
        )
        return [(row[0], row[1]) for row in result.all()]


class MessageLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log(self, telegram_id: int, content_type: str) -> None:
        self.session.add(MessageLog(telegram_id=telegram_id, content_type=content_type))
        await self.session.commit()
