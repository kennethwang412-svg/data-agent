"""
NL2SQL 组件实测：逐步验证 LangChain SQL 链路每个组件的实际输入/输出字段。
基于已验证的 Qwen3-max (ChatTongyi) 模型。

关键导入路径 (langchain 1.2.10 / langchain-classic 1.0.1):
  - create_sql_query_chain -> langchain_classic.chains.sql_database.query
  - SQLDatabase            -> langchain_community.utilities.sql_database
  - QuerySQLDataBaseTool   -> langchain_community.tools.sql_database.tool
  - create_sql_agent       -> langchain_community.agent_toolkits
"""

import os
import json
from pathlib import Path

os.environ["DASHSCOPE_API_KEY"] = "sk-536dbd48b6ea42be995f7b507ba936c3"

SAMPLE_DB = str(Path(__file__).parent / "data" / "sample.db")


# ================================================================
# 测试 1: SQLDatabase 组件 — 连接 & Schema 自省
# ================================================================
def test_sql_database():
    print("=" * 70)
    print("测试 1: SQLDatabase 组件")
    print("=" * 70)

    from langchain_community.utilities import SQLDatabase

    db = SQLDatabase.from_uri(f"sqlite:///{SAMPLE_DB}")

    print(f"[1.1] type(db)          = {type(db).__name__}")
    print(f"[1.2] db.dialect         = {db.dialect}")
    print(f"[1.3] db.table_names     = {db.get_usable_table_names()}")
    print()

    table_info = db.get_table_info()
    print(f"[1.4] db.get_table_info() — type={type(table_info).__name__}, len={len(table_info)}")
    print("--- 内容 ---")
    print(table_info)
    print("--- 结束 ---")
    print()

    result = db.run("SELECT * FROM products LIMIT 3")
    print(f"[1.5] db.run('SELECT ...') — type={type(result).__name__}")
    print(f"      result = {result}")
    print()

    result_with_cols = db.run("SELECT * FROM products LIMIT 3", include_columns=True)
    print(f"[1.6] db.run(..., include_columns=True) — type={type(result_with_cols).__name__}")
    print(f"      result = {result_with_cols}")
    print()

    return db


# ================================================================
# 测试 2: create_sql_query_chain — NL → SQL
# ================================================================
def test_create_sql_query_chain(db):
    print("=" * 70)
    print("测试 2: create_sql_query_chain (NL → SQL)")
    print("=" * 70)

    from langchain_community.chat_models.tongyi import ChatTongyi
    from langchain_classic.chains.sql_database.query import create_sql_query_chain

    llm = ChatTongyi(model="qwen3-max", temperature=0)
    chain = create_sql_query_chain(llm, db)

    print(f"[2.1] chain type = {type(chain).__name__}")

    # 查看 chain 的 input/output schema
    try:
        in_schema = chain.input_schema.model_json_schema()
        print(f"[2.2] input_schema  = {json.dumps(in_schema, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"[2.2] input_schema  = (获取失败: {e})")

    try:
        out_schema = chain.output_schema.model_json_schema()
        print(f"[2.3] output_schema = {json.dumps(out_schema, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"[2.3] output_schema = (获取失败: {e})")
    print()

    # 测试执行
    question = "各个地区的销售总额是多少？"
    print(f"[2.4] invoke 输入: {{'question': '{question}'}}")
    generated_sql = chain.invoke({"question": question})
    print(f"[2.5] invoke 输出:")
    print(f"      type  = {type(generated_sql).__name__}")
    print(f"      value = {repr(generated_sql)}")
    print()

    question2 = "哪个产品类别的订单数量最多？"
    print(f"[2.6] invoke 输入: {{'question': '{question2}'}}")
    generated_sql2 = chain.invoke({"question": question2})
    print(f"[2.7] invoke 输出:")
    print(f"      type  = {type(generated_sql2).__name__}")
    print(f"      value = {repr(generated_sql2)}")
    print()

    return chain, generated_sql


# ================================================================
# 测试 3: QuerySQLDataBaseTool — SQL 执行
# ================================================================
def test_query_tool(db, raw_sql):
    print("=" * 70)
    print("测试 3: QuerySQLDataBaseTool (SQL 执行)")
    print("=" * 70)

    from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool

    tool = QuerySQLDataBaseTool(db=db)

    print(f"[3.1] tool type        = {type(tool).__name__}")
    print(f"[3.2] tool.name        = {tool.name}")
    print(f"[3.3] tool.description = {tool.description[:200]}")
    print()

    # 清理 chain 输出的 SQL (可能包含 markdown 或前缀)
    clean_sql = raw_sql.strip()
    if "SQLQuery:" in clean_sql:
        clean_sql = clean_sql.split("SQLQuery:")[-1].strip()
    if clean_sql.startswith("```"):
        lines = clean_sql.split("\n")
        clean_sql = "\n".join(l for l in lines if not l.strip().startswith("```")).strip()

    print(f"[3.4] invoke 输入: {{'query': '{clean_sql}'}}")
    try:
        result = tool.invoke({"query": clean_sql})
        print(f"[3.5] invoke 输出:")
        print(f"      type  = {type(result).__name__}")
        print(f"      value = {result}")
    except Exception as e:
        print(f"[3.5] invoke 失败: {e}")
        print("      使用备用 SQL 重试...")
        clean_sql = "SELECT c.region, SUM(o.amount) as total_sales FROM orders o JOIN customers c ON o.customer_id = c.id GROUP BY c.region ORDER BY total_sales DESC"
        result = tool.invoke({"query": clean_sql})
        print(f"      备用结果 type = {type(result).__name__}")
        print(f"      备用结果 value = {result}")
    print()

    # 额外测试其他 SQL 工具
    print("[3.6] 其他 SQL 工具:")
    from langchain_community.tools.sql_database.tool import (
        InfoSQLDatabaseTool,
        ListSQLDatabaseTool,
        QuerySQLCheckerTool,
    )

    list_tool = ListSQLDatabaseTool(db=db)
    print(f"  ListSQLDatabaseTool.invoke('') = {list_tool.invoke('')}")

    info_tool = InfoSQLDatabaseTool(db=db)
    print(f"  InfoSQLDatabaseTool.invoke('products') = {info_tool.invoke('products')[:300]}")
    print()

    return tool


# ================================================================
# 测试 4: 完整 Chain 管道 — NL → SQL → 执行 → 自然语言回答
# ================================================================
def test_full_chain(db):
    print("=" * 70)
    print("测试 4: 完整 Chain 管道 (invoke)")
    print("=" * 70)

    from langchain_community.chat_models.tongyi import ChatTongyi
    from langchain_classic.chains.sql_database.query import create_sql_query_chain
    from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    from operator import itemgetter

    llm = ChatTongyi(model="qwen3-max", temperature=0)
    write_query = create_sql_query_chain(llm, db)
    execute_query = QuerySQLDataBaseTool(db=db)

    answer_prompt = PromptTemplate.from_template(
        """根据以下用户问题、对应的SQL查询和SQL执行结果，用中文回答用户的问题。请给出简洁明了的分析。

用户问题: {question}
SQL查询: {query}
SQL执行结果: {result}
回答: """
    )

    chain = (
        RunnablePassthrough.assign(query=write_query)
        .assign(result=itemgetter("query") | execute_query)
        | answer_prompt
        | llm
        | StrOutputParser()
    )

    print(f"[4.1] chain type = {type(chain).__name__}")

    question = "销售额最高的前5个产品是什么？"
    print(f"[4.2] invoke 输入: {{'question': '{question}'}}")
    answer = chain.invoke({"question": question})
    print(f"[4.3] invoke 输出:")
    print(f"      type  = {type(answer).__name__}")
    print(f"      value = {answer}")
    print()

    return chain


# ================================================================
# 测试 5: 分步执行 + 流式输出 (SSE 推送模拟)
# ================================================================
def test_stepwise_stream(db):
    print("=" * 70)
    print("测试 5: 分步执行 + 流式输出 (模拟 SSE)")
    print("=" * 70)

    from langchain_community.chat_models.tongyi import ChatTongyi
    from langchain_classic.chains.sql_database.query import create_sql_query_chain
    from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
    from langchain_core.prompts import PromptTemplate
    from langchain_core.messages import HumanMessage

    llm = ChatTongyi(model="qwen3-max", temperature=0)
    llm_stream = ChatTongyi(model="qwen3-max", temperature=0, streaming=True)
    write_query = create_sql_query_chain(llm, db)
    execute_query = QuerySQLDataBaseTool(db=db)

    answer_prompt = PromptTemplate.from_template(
        """根据以下用户问题、对应的SQL查询和SQL执行结果，用中文回答用户的问题。

用户问题: {question}
SQL查询: {query}
SQL执行结果: {result}
回答: """
    )

    question = "各地区的客户数量分布如何？"
    print(f"[5.1] 输入: question = '{question}'")

    # ---- Step 1: NL → SQL ----
    print("\n--- Step 1: NL → SQL (SSE event: sql) ---")
    sql_raw = write_query.invoke({"question": question})
    print(f"  返回 type  = {type(sql_raw).__name__}")
    print(f"  返回 value = {repr(sql_raw)}")

    clean_sql = sql_raw.strip()
    if "SQLQuery:" in clean_sql:
        clean_sql = clean_sql.split("SQLQuery:")[-1].strip()
    if clean_sql.startswith("```"):
        lines = clean_sql.split("\n")
        clean_sql = "\n".join(l for l in lines if not l.strip().startswith("```")).strip()
    print(f"  清理后 SQL = {clean_sql}")

    # ---- Step 2: 执行 SQL ----
    print("\n--- Step 2: 执行 SQL (SSE event: query_result) ---")
    query_result = execute_query.invoke({"query": clean_sql})
    print(f"  返回 type  = {type(query_result).__name__}")
    print(f"  返回 value = {query_result}")

    # ---- Step 3: 格式化 Prompt ----
    print("\n--- Step 3: 构造 Prompt ---")
    prompt_value = answer_prompt.invoke({
        "question": question,
        "query": clean_sql,
        "result": query_result,
    })
    print(f"  prompt type   = {type(prompt_value).__name__}")
    print(f"  prompt class  = {type(prompt_value).__module__}.{type(prompt_value).__qualname__}")

    # 查看 to_messages() 的输出
    messages = prompt_value.to_messages()
    print(f"  to_messages() = {len(messages)} 条消息")
    for i, m in enumerate(messages):
        print(f"    [{i}] type={type(m).__name__}, content={repr(m.content[:100])}...")

    # 查看 to_string() 的输出
    prompt_str = prompt_value.to_string()
    print(f"  to_string()   = (len={len(prompt_str)}) {prompt_str[:200]}...")

    # ---- Step 4: 流式生成回答 (SSE event: answer) ----
    print("\n--- Step 4: 流式生成回答 (SSE event: answer) ---")
    chunk_count = 0
    full_answer = ""
    for chunk in llm_stream.stream(messages):
        chunk_count += 1
        full_answer += chunk.content
        if chunk_count <= 3:
            print(f"  chunk {chunk_count}:")
            print(f"    type     = {type(chunk).__name__}")
            print(f"    content  = {repr(chunk.content)}")
            print(f"    metadata = {chunk.response_metadata}")
            if hasattr(chunk, "additional_kwargs"):
                print(f"    add_kw   = {chunk.additional_kwargs}")
        elif chunk.response_metadata.get("finish_reason"):
            print(f"  chunk {chunk_count} (finish):")
            print(f"    type     = {type(chunk).__name__}")
            print(f"    content  = {repr(chunk.content)}")
            print(f"    metadata = {chunk.response_metadata}")
    print(f"\n  总 chunk 数: {chunk_count}")
    print(f"  完整回答: {full_answer}")
    print()


# ================================================================
# 测试 6: create_sql_agent (Agent 方式对比)
# ================================================================
def test_sql_agent(db):
    print("=" * 70)
    print("测试 6: create_sql_agent (Agent 方式)")
    print("=" * 70)

    from langchain_community.chat_models.tongyi import ChatTongyi
    from langchain_community.agent_toolkits import create_sql_agent

    llm = ChatTongyi(model="qwen3-max", temperature=0)

    try:
        agent = create_sql_agent(llm, db=db, agent_type="tool-calling", verbose=True)
        print(f"[6.1] agent type = {type(agent).__name__}")

        question = "哪个地区的平均订单金额最高？"
        print(f"[6.2] 输入: {{'input': '{question}'}}")
        result = agent.invoke({"input": question})
        print(f"\n[6.3] 输出 type = {type(result).__name__}")
        print(f"[6.4] 输出 keys = {list(result.keys())}")
        for k, v in result.items():
            v_str = str(v)
            print(f"  {k}: type={type(v).__name__}, len={len(v_str)}, value={v_str[:500]}")
    except Exception as e:
        print(f"[6.x] Agent 执行异常: {type(e).__name__}: {e}")
    print()


if __name__ == "__main__":
    print("🚀 开始 NL2SQL 组件实测\n")

    db = test_sql_database()
    chain, sql = test_create_sql_query_chain(db)
    test_query_tool(db, sql)
    test_full_chain(db)
    test_stepwise_stream(db)
    test_sql_agent(db)

    print("=" * 70)
    print("✅ 全部测试完成")
    print("=" * 70)
