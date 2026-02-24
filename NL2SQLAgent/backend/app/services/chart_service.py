"""图表生成服务：LLM 驱动的图表类型推荐 + ECharts option JSON 生成。"""
from __future__ import annotations

import json
import re
from typing import Any

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage

from app.config import settings
from app.prompts.chart_gen import CHART_GEN_TEMPLATE


def _get_llm() -> ChatTongyi:
    return ChatTongyi(model=settings.llm_model_name, temperature=0)


def _extract_json(text: str) -> dict[str, Any] | None:
    """从 LLM 输出中提取 JSON，处理 markdown 代码块包裹的情况。"""
    cleaned = text.strip()
    code_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
    if code_match:
        cleaned = code_match.group(1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        brace_match = re.search(r"\{[\s\S]*\}", cleaned)
        if brace_match:
            try:
                return json.loads(brace_match.group())
            except json.JSONDecodeError:
                return None
    return None


def generate_chart_config(sql: str, query_result: str) -> dict[str, Any] | None:
    """根据 SQL 和查询结果生成 ECharts 图表配置。"""
    llm = _get_llm()
    prompt_text = CHART_GEN_TEMPLATE.format(sql=sql, result=query_result)
    response = llm.invoke([HumanMessage(content=prompt_text)])

    chart_data = _extract_json(response.content)
    if not chart_data:
        return None

    chart_type = chart_data.get("chart_type", "table")
    if chart_type not in ("bar", "line", "pie", "scatter", "table"):
        chart_type = "table"

    return {
        "chartType": chart_type,
        "title": chart_data.get("title", ""),
        "option": chart_data.get("option", {}),
    }
