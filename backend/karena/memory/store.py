"""Hierarchical conversation memory — short/medium term persistence."""

import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from karena.config import get_settings

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
  pass


class SessionModel(Base):
  __tablename__ = "sessions"
  id = Column(String, primary_key=True)
  user_id = Column(String, nullable=False)
  tenant_id = Column(String, nullable=False)
  created_at = Column(DateTime, nullable=False)


class MessageModel(Base):
  __tablename__ = "messages"
  id = Column(String, primary_key=True)
  session_id = Column(String, nullable=False, index=True)
  role = Column(String, nullable=False)
  content = Column(Text, nullable=False)
  sources_json = Column(Text, default="[]")
  created_at = Column(DateTime, nullable=False)


async def init_db() -> None:
  global _engine, _session_factory
  settings = get_settings()
  _engine = create_async_engine(settings.database_url, echo=settings.debug)
  _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
  async with _engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)


def _now() -> datetime:
  return datetime.now(timezone.utc)


class MemoryStore:
  async def create_session(self, user_id: str, tenant_id: str) -> str:
    session_id = str(uuid.uuid4())
    async with _session_factory() as db:
      db.add(
        SessionModel(
          id=session_id,
          user_id=user_id,
          tenant_id=tenant_id,
          created_at=_now(),
        )
      )
      await db.commit()
    return session_id

  async def add_message(
    self,
    session_id: str,
    role: str,
    content: str,
    *,
    sources: list | None = None,
  ) -> None:
    async with _session_factory() as db:
      db.add(
        MessageModel(
          id=str(uuid.uuid4()),
          session_id=session_id,
          role=role,
          content=content,
          sources_json=json.dumps(sources or []),
          created_at=_now(),
        )
      )
      await db.commit()

  async def get_recent_messages(self, session_id: str, limit: int = 10) -> list[dict]:
    async with _session_factory() as db:
      result = await db.execute(
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.created_at.desc())
        .limit(limit)
      )
      rows = result.scalars().all()
    rows = list(reversed(rows))
    return [
      {
        "role": r.role,
        "content": r.content,
        "sources": json.loads(r.sources_json or "[]"),
      }
      for r in rows
    ]
