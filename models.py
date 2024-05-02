from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True,
                                          nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    salary: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2),
                                            nullable=False)
    promotion_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)    


engine = create_async_engine("sqlite+aiosqlite:///db.sqlite3", echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def delete_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
