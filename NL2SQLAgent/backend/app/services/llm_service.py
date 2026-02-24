"""LLM 核心服务：NL→SQL、结果解读、上下文记忆管理。"""
from __future__ import annotations

import os
from collections import defaultdict
from typing import AsyncGenerator

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate

from app.config import settings
from app.prompts.text_to_sql import ANSWER_TEMPLATE, TEXT_TO_SQL_TEMPLATE
from app.services.db_service import clean_generated_sql, get_schema_text

os.environ["DASHSCOPE_API_KEY"] = settings.dashscope_api_key

_conversation_memory: dict[str, list[dict]] = defaultdict(list)


def _get_llm(streaming: bool = False) -> ChatTongyi:
    return ChatTongyi(
        model=settings.llm_model_name,
        temperature=0,
        streaming=streaming,
    )


def _format_history(session_id: str) -> str:
    history = _conversation_memory.get(session_id, [])
    if not history:
        return "（无历史对话）"
    lines = []
    for h in history[-settings.memory_window :]:
        lines.append(f"用户: {h['question']}")
        if h.get("sql"):
            lines.append(f"SQL: {h['sql']}")
        lines.append(f"回答: {h['answer'][:200]}")
    return "\n".join(lines)


def add_to_memory(session_id: str, question: str, sql: str, answer: str) -> None:
    _conversation_memory[session_id].append({
        "question": question,
        "sql": sql,
        "answer": answer,
    })
    if len(_conversation_memory[session_id]) > settings.memory_window * 2:
        _conversation_memory[session_id] = _conversation_memory[session_id][-settings.memory_window:]


def load_memory_from_messages(session_id: str, messages: list) -> None:
    """从数据库消息记录恢复上下文记忆。"""
    _conversation_memory[session_id] = []
    pairs = []
    current_q = None
    for msg in messages:
        if msg.role == "user":
            current_q = msg.content
        elif msg.role == "assistant" and current_q:
            pairs.append({
                "question": current_q,
                "sql": msg.sql_query or "",
                "answer": msg.content or "",
            })
            current_q = None
    _conversation_memory[session_id] = pairs[-settings.memory_window:]


def generate_sql(question: str, session_id: str) -> str:
    """根据自然语言问题生成 SQL。"""
    llm = _get_llm()
    schema = get_schema_text()
    history = _format_history(session_id)

    prompt = PromptTemplate.from_template(TEXT_TO_SQL_TEMPLATE)
    prompt_value = prompt.invoke({
        "schema": schema,
        "history": history,
        "question": question,
    })

    response: AIMessage = llm.invoke(prompt_value.to_messages())
    raw_sql = response.content.strip()
    return clean_generated_sql(raw_sql)


async def stream_answer(
    question: str,
    sql: str,
    query_result: str,
) -> AsyncGenerator[str, None]:
    """流式生成自然语言回答，yield 每个文本 chunk。"""
    llm = _get_llm(streaming=True)
    prompt = PromptTemplate.from_template(ANSWER_TEMPLATE)
    prompt_value = prompt.invoke({
        "question": question,
        "sql": sql,
        "result": query_result,
    })

    for chunk in llm.stream(prompt_value.to_messages()):
        if chunk.content:
            text = chunk.content
            if text.startswith(" ") and not text.startswith("  "):
                text = text[1:]
            if text:
                yield text
        if chunk.response_metadata.get("finish_reason"):
            break
