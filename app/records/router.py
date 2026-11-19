from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.deps import get_current_user_id
from app.records.schemas import RecordCreate, RecordResponse, PaginatedRecords
from app.records.supabase_client import (
    fetch_user_records,
    fetch_record_by_id,
    upsert_record,
    delete_record,
)

router = APIRouter(prefix="/api/v1/records", tags=["records"])


@router.get("", response_model=PaginatedRecords, summary="List user financial records")
async def list_records(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    is_archived: Optional[bool] = Query(None),
    user_id: str = Depends(get_current_user_id),
):
    rows, total = await fetch_user_records(
        user_id=user_id,
        limit=limit,
        offset=offset,
        is_archived=is_archived,
    )
    items = [RecordResponse(**r) for r in rows]
    return PaginatedRecords(
        data=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.get("/{record_id}", response_model=RecordResponse, summary="Get single record")
async def get_record(
    record_id: str,
    user_id: str = Depends(get_current_user_id),
):
    row = await fetch_record_by_id(record_id, user_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return RecordResponse(**row)


@router.post("", response_model=RecordResponse, status_code=status.HTTP_201_CREATED, summary="Create/save record")
async def create_record(
    payload: RecordCreate,
    user_id: str = Depends(get_current_user_id),
):
    row = await upsert_record(user_id, payload.model_dump())
    return RecordResponse(**row)


@router.put("/{record_id}", response_model=RecordResponse, summary="Update record")
async def update_record(
    record_id: str,
    payload: RecordCreate,
    user_id: str = Depends(get_current_user_id),
):
    data = payload.model_dump()
    data["id"] = record_id
    row = await upsert_record(user_id, data)
    return RecordResponse(**row)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete record")
async def remove_record(
    record_id: str,
    user_id: str = Depends(get_current_user_id),
):
    deleted = await delete_record(record_id, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return None
