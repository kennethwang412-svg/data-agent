from fastapi import APIRouter

from app.models.schemas import ColumnInfo, DatabaseInfoResponse, TableInfo
from app.services import db_service

router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("/tables", response_model=DatabaseInfoResponse)
async def get_tables():
    details = db_service.get_table_details()
    tables = [
        TableInfo(
            name=t["name"],
            columns=[ColumnInfo(**c) for c in t["columns"]],
            row_count=t["row_count"],
            sample_rows=t["sample_rows"],
        )
        for t in details
    ]
    return DatabaseInfoResponse(
        dialect="sqlite",
        tables=tables,
        raw_schema=db_service.get_schema_text(),
    )
