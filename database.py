import os
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, select, or_
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///data.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    channel_message_id: Mapped[int] = mapped_column(Integer)
    orig_image_path: Mapped[str] = mapped_column(String)
    current_image_path: Mapped[str] = mapped_column(String)
    caption: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_dirty: Mapped[bool] = mapped_column(Boolean, default=False)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False)


async def init_db():
    os.makedirs("media", exist_ok=True)
    async with engine.begin() as conn:
        # Создаст таблицы, если их ещё нет
        await conn.run_sync(Base.metadata.create_all)


async def create_post_record(
    post_id: str,
    channel_msg_id: int,
    orig_path: str,
    curr_path: str,
    caption: str | None,
    expires_at: datetime
):
    async with async_session() as session:
        post = Post(
            id=post_id,
            channel_message_id=channel_msg_id,
            orig_image_path=orig_path,
            current_image_path=curr_path,
            caption=caption,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            is_dirty=False,
            is_expired=False
        )
        session.add(post)
        await session.commit()


async def get_post_record(post_id: str) -> Post | None:
    async with async_session() as session:
        return await session.get(Post, post_id)


async def update_post_image(post_id: str):
    async with async_session() as session:
        post = await session.get(Post, post_id)
        if post and not post.is_expired:
            post.is_dirty = True
            await session.commit()


async def get_dirty_or_expiring_posts() -> list[Post]:
    async with async_session() as session:
        now = datetime.now(timezone.utc)
        stmt = select(Post).where(
            Post.is_expired == False,
            or_(Post.is_dirty == True, Post.expires_at <= now)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def mark_post_synced(post_id: str):
    async with async_session() as session:
        post = await session.get(Post, post_id)
        if post:
            post.is_dirty = False
            await session.commit()


async def mark_post_expired(post_id: str):
    async with async_session() as session:
        post = await session.get(Post, post_id)
        if post:
            post.is_expired = True
            post.is_dirty = False
            await session.commit()