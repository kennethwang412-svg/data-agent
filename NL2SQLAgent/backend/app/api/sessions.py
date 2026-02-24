import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.schemas import (
    MessageResponse,
    SessionCreate,
    SessionDetailResponse,
    SessionResponse,
)
from app.services import session_service

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _msg_to_response(msg) -> MessageResponse:
    chart = None
    if msg.chart_config:
        try:
            chart = json.loads(msg.chart_config)
        except (json.JSONDecodeError, TypeError):
            chart = None
    return MessageResponse(
        id=msg.id,
        session_id=msg.session_id,
        role=msg.role,
        content=msg.content or "",
        sql_query=msg.sql_query,
        query_result=msg.query_result,
        chart_config=chart,
        created_at=msg.created_at,
    )


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
):
    session = await session_service.create_session(db, body.title)
    return session


@router.get("", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    return await session_service.list_sessions(db)


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    session = await session_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await session_service.get_messages(db, session_id)
    return SessionDetailResponse(
        session=SessionResponse.model_validate(session),
        messages=[_msg_to_response(m) for m in messages],
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await session_service.delete_session(db, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
