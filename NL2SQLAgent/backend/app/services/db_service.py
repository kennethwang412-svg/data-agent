"""业务数据库服务：Schema 自省、SQL 安全检查、SQL 执行沙箱。"""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from langchain_community.utilities import SQLDatabase

from app.config import settings

_sql_db: SQLDatabase | None = None

DANGEROUS_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|REPLACE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


def get_sql_database() -> SQLDatabase:
    global _sql_db
    if _sql_db is None:
        _sql_db = SQLDatabase.from_uri(settings.sample_db_uri)
    return _sql_db


def get_table_names() -> list[str]:
    db = get_sql_database()
    return list(db.get_usable_table_names())


def get_schema_text() -> str:
    """返回完整的 DDL + 示例数据文本，用于注入 LLM prompt。"""
    db = get_sql_database()
    return db.get_table_info()


def get_table_details() -> list[dict[str, Any]]:
    """返回结构化的表信息，用于 API 响应。"""
    conn = sqlite3.connect(settings.sample_db_path)
    conn.row_factory = sqlite3.Row
    try:
        tables = []
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        for row in cursor.fetchall():
            table_name = row["name"]
            cols_cursor = conn.execute(f"PRAGMA table_info('{table_name}')")
            columns = [{"name": c["name"], "type": c["type"]} for c in cols_cursor.fetchall()]

            count = conn.execute(f"SELECT COUNT(*) FROM '{table_name}'").fetchone()[0]

            sample_cursor = conn.execute(f"SELECT * FROM '{table_name}' LIMIT 3")
            col_names = [desc[0] for desc in sample_cursor.description]
            sample_rows = [dict(zip(col_names, r)) for r in sample_cursor.fetchall()]

            tables.append({
                "name": table_name,
                "columns": columns,
                "row_count": count,
                "sample_rows": sample_rows,
            })
        return tables
    finally:
        conn.close()


def check_sql_safety(sql: str) -> str | None:
    """检查 SQL 安全性。安全返回 None，危险返回错误描述。"""
    stripped = sql.strip().rstrip(";").strip()
    if DANGEROUS_KEYWORDS.search(stripped):
        return f"SQL 包含危险操作，仅允许 SELECT 查询"
    if not stripped.upper().startswith("SELECT"):
        return f"仅允许 SELECT 查询语句"
    return None


def execute_sql(sql: str) -> str:
    """在 sample.db 上以只读方式执行 SQL，返回结果字符串。"""
    safety_error = check_sql_safety(sql)
    if safety_error:
        raise ValueError(safety_error)

    conn = sqlite3.connect(
        f"file:{settings.sample_db_path}?mode=ro",
        uri=True,
        timeout=settings.sql_timeout,
    )
    try:
        cursor = conn.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(settings.sql_max_rows)

        result_dicts = [dict(zip(columns, row)) for row in rows]
        return json.dumps(result_dicts, ensure_ascii=False, default=str)
    except Exception as e:
        raise ValueError(f"SQL 执行错误: {e}")
    finally:
        conn.close()


def clean_generated_sql(raw: str) -> str:
    """清理 create_sql_query_chain 输出中可能包含的前缀。"""
    sql = raw.strip()
    if "SQLQuery:" in sql:
        sql = sql.split("SQLQuery:")[-1].strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        sql = "\n".join(l for l in lines if not l.strip().startswith("```")).strip()
    sql = sql.rstrip(";").strip() + ";"
    return sql
