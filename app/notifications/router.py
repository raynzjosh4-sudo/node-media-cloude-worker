from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.deps import get_current_user_id
from app.notifications.schemas import (
    NotificationItemResponse,
    PaginatedNotifications,
    DeviceTokenRegister,
)
from app.notifications.supabase_client import (
    fetch_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    delete_notification,
    register_device_token,
    unregister_device_token,
)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedNotifications, summary="Get notifications")
async def get_notifications(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(None, description="all, orders, inventory, logistics, security, finance, system, reminders, messages"),
    user_id: str = Depends(get_current_user_id),
):
    items, total = await fetch_notifications(
        user_id=user_id,
        limit=limit,
        offset=offset,
        category=category,
    )
    return PaginatedNotifications(
        data=[NotificationItemResponse(**i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total,
    )


@router.patch("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT, summary="Mark notification as read")
async def read_one(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
):
    updated = await mark_notification_read(notification_id, user_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return None


@router.patch("/read-all", summary="Mark all notifications as read")
async def read_all(user_id: str = Depends(get_current_user_id)):
    count = await mark_all_notifications_read(user_id)
    return {"message": "All notifications marked as read", "updated_count": count}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete notification")
async def remove_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
):
    deleted = await delete_notification(notification_id, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return None


@router.post("/device-token", status_code=status.HTTP_201_CREATED, summary="Register FCM device push token")
async def add_device_token(
    payload: DeviceTokenRegister,
    user_id: str = Depends(get_current_user_id),
):
    saved = await register_device_token(
        user_id=user_id,
        token=payload.token,
        device_type=payload.device_type,
    )
    return {"message": "Device token registered successfully", "token": payload.token}


@router.delete("/device-token", status_code=status.HTTP_204_NO_CONTENT, summary="Unregister FCM device push token")
async def remove_device_token(
    token: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id),
):
    await unregister_device_token(user_id=user_id, token=token)
    return None
