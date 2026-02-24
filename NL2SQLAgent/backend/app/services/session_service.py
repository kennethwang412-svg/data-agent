from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Message, Session


async def create_session(db: AsyncSession, title: str = "新对话") -> Session:
    session = Session(title=title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(db: AsyncSession) -> list[Session]:
    result = await db.execute(
        select(Session).order_by(Session.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_session(db: AsyncSession, session_id: str) -> Session | None:
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    await db.execute(delete(Message).where(Message.session_id == session_id))
    result = await db.execute(delete(Session).where(Session.id == session_id))
    await db.commit()
    return result.rowcount > 0


async def get_messages(db: AsyncSession, session_id: str) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())


async def add_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    sql_query: str | None = None,
    query_result: str | None = None,
    chart_config: dict | None = None,
) -> Message:
    msg = Message(
        session_id=session_id,
        role=role,
        content=content,
        sql_query=sql_query,
        query_result=query_result,
        chart_config=json.dumps(chart_config, ensure_ascii=False) if chart_config else None,
    )
    db.add(msg)

    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(updated_at=datetime.utcnow())
    )
    await db.commit()
    await db.refresh(msg)
    return msg


async def update_message(
    db: AsyncSession,
    message_id: str,
    content: str | None = None,
    sql_query: str | None = None,
    query_result: str | None = None,
    chart_config: dict | None = None,
) -> None:
    values: dict = {}
    if content is not None:
        values["content"] = content
    if sql_query is not None:
        values["sql_query"] = sql_query
    if query_result is not None:
        values["query_result"] = query_result
    if chart_config is not None:
        values["chart_config"] = json.dumps(chart_config, ensure_ascii=False)
    if values:
        await db.execute(update(Message).where(Message.id == message_id).values(**values))
        await db.commit()
