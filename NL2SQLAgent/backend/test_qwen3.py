"""测试 Qwen3 模型接入：基础调用、流式输出、函数调用"""

import os
os.environ["DASHSCOPE_API_KEY"] = "sk-536dbd48b6ea42be995f7b507ba936c3"

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool


# ========== 测试 1: 基础调用 ==========
def test_basic():
    print("=" * 60)
    print("测试 1: 基础调用")
    print("=" * 60)
    llm = ChatTongyi(model="qwen3-max")
    messages = [
        SystemMessage(content="你是一个数据分析助手，请用中文简洁回答。"),
        HumanMessage(content="你好，请介绍一下你自己"),
    ]
    response = llm.invoke(messages)
    print(f"type: {type(response).__name__}")
    print(f"content: {response.content}")
    print(f"response_metadata: {response.response_metadata}")
    print(f"id: {response.id}")
    if hasattr(response, "additional_kwargs"):
        print(f"additional_kwargs: {response.additional_kwargs}")
    print()


# ========== 测试 2: 流式输出 ==========
def test_streaming():
    print("=" * 60)
    print("测试 2: 流式输出")
    print("=" * 60)
    llm = ChatTongyi(model="qwen3-max", streaming=True)
    messages = [
        SystemMessage(content="你是一个数据分析助手。"),
        HumanMessage(content="用一句话解释什么是 SQL"),
    ]

    print("逐 chunk 输出:")
    chunk_count = 0
    for chunk in llm.stream(messages):
        chunk_count += 1
        print(f"  chunk {chunk_count}: "
              f"type={type(chunk).__name__}, "
              f"content='{chunk.content}', "
              f"response_metadata={chunk.response_metadata}")
    print(f"总共 {chunk_count} 个 chunk")
    print()


# ========== 测试 3: 函数调用 (Tool Calling) ==========
@tool
def query_sales_by_region(region: str) -> str:
    """查询指定地区的销售总额。参数 region 是地区名称，如华东、华南。"""
    mock_data = {"华东": "128500", "华南": "95200", "华北": "87600"}
    return mock_data.get(region, "未找到该地区数据")


@tool
def query_monthly_trend(year: int) -> str:
    """查询指定年份的月度销售趋势数据。"""
    return f"{year}年月度销售: 1月42300, 2月38900, 3月55600..."


def test_tool_calling():
    print("=" * 60)
    print("测试 3: 函数调用 (Tool Calling)")
    print("=" * 60)
    llm = ChatTongyi(model="qwen3-max")
    llm_with_tools = llm.bind_tools([query_sales_by_region, query_monthly_trend])

    response = llm_with_tools.invoke("帮我查一下华东地区的销售总额")
    print(f"type: {type(response).__name__}")
    print(f"content: '{response.content}'")
    print(f"tool_calls: {response.tool_calls}")
    print(f"additional_kwargs: {response.additional_kwargs}")
    print(f"response_metadata: {response.response_metadata}")
    print()


if __name__ == "__main__":
    test_basic()
    test_streaming()
    test_tool_calling()
