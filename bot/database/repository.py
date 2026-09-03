from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Deadline, User


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
