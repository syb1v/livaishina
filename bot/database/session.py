from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config.settings import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

SessionMaker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
