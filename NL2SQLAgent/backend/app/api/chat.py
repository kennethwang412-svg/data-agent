import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.models.database import async_session, get_db
from app.models.schemas import ChatRequest
from app.services import chart_service, db_service, llm_service, session_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/{session_id}")
async def chat(
    session_id: str,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await session_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await session_service.get_messages(db, session_id)
    llm_service.load_memory_from_messages(session_id, messages)

    user_msg = await session_service.add_message(
        db, session_id, role="user", content=body.message
    )

    ai_msg = await session_service.add_message(
        db, session_id, role="assistant", content=""
    )

    if session.title == "新对话":
        new_title = body.message[:30] + ("..." if len(body.message) > 30 else "")
        from sqlalchemy import update as sql_update
        from app.models.database import Session as SessionModel
        await db.execute(
            sql_update(SessionModel).where(SessionModel.id == session_id).values(title=new_title)
        )
        await db.commit()

    ai_msg_id = ai_msg.id

    async def event_stream() -> AsyncGenerator[dict, None]:
        full_answer = ""
        generated_sql = ""
        query_result = ""
        chart_config = None

        try:
            generated_sql = llm_service.generate_sql(body.message, session_id)
            yield {"event": "sql", "data": generated_sql}

            safety_err = db_service.check_sql_safety(generated_sql)
            if safety_err:
                yield {"event": "error", "data": safety_err}
                yield {"event": "done", "data": ""}
                return

            try:
                query_result = db_service.execute_sql(generated_sql)
            except ValueError as e:
                yield {"event": "error", "data": str(e)}
                yield {"event": "done", "data": ""}
                return

            yield {"event": "query_result", "data": query_result}

            answer_buffer = ""
            async for chunk_text in llm_service.stream_answer(
                body.message, generated_sql, query_result
            ):
                full_answer += chunk_text
                answer_buffer += chunk_text
                while "\n" in answer_buffer:
                    line, answer_buffer = answer_buffer.split("\n", 1)
                    yield {"event": "answer", "data": line + "\n"}
            if answer_buffer:
                yield {"event": "answer", "data": answer_buffer}

            try:
                chart_config = chart_service.generate_chart_config(
                    generated_sql, query_result
                )
                if chart_config:
                    yield {
                        "event": "chart",
                        "data": json.dumps(chart_config, ensure_ascii=False),
                    }
            except Exception as e:
                logger.warning(f"Chart generation failed: {e}")

            llm_service.add_to_memory(
                session_id, body.message, generated_sql, full_answer
            )

        except Exception as e:
            logger.exception("Chat processing error")
            yield {"event": "error", "data": f"处理出错: {str(e)}"}

        finally:
            try:
                async with async_session() as persist_db:
                    await session_service.update_message(
                        persist_db,
                        ai_msg_id,
                        content=full_answer,
                        sql_query=generated_sql,
                        query_result=query_result,
                        chart_config=chart_config,
                    )
            except Exception as e:
                logger.error(f"Failed to persist message: {e}")

            yield {"event": "done", "data": ""}

    return EventSourceResponse(event_stream())
