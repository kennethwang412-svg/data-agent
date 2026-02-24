from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------- Session ----------

class SessionCreate(BaseModel):
    title: str = "新对话"


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------- Message ----------

class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sql_query: Optional[str] = None
    query_result: Optional[str] = None
    chart_config: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionDetailResponse(BaseModel):
    session: SessionResponse
    messages: list[MessageResponse]


# ---------- Chat ----------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


# ---------- Chart ----------

class ChartConfig(BaseModel):
    chart_type: str = Field(..., description="bar | line | pie | scatter | table")
    title: str = ""
    option: dict[str, Any] = Field(default_factory=dict)


# ---------- Database Info ----------

class ColumnInfo(BaseModel):
    name: str
    type: str


class TableInfo(BaseModel):
    name: str
    columns: list[ColumnInfo]
    row_count: int = 0
    sample_rows: list[dict[str, Any]] = Field(default_factory=list)


class DatabaseInfoResponse(BaseModel):
    dialect: str
    tables: list[TableInfo]
    raw_schema: str
