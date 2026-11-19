from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.core.deps import require_admin
from app.admin.schemas import (
    CategoryCreateRequest,
    SupplierActionResponse,
    RoleUpdateRequest,
    PotentialSupplierItem,
)
from app.admin.supabase_client import (
    fetch_potential_suppliers,
    set_user_role,
    insert_category,
    fetch_users,
)
from app.profile.supabase_client import fetch_user, fetch_business
from app.services.email_service import (
    build_supplier_status_email_html,
    create_in_app_notification,
    send_order_email,
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ─────────────────────────────────────────────────────────────
# 1. Supplier Approvals & Management
# ─────────────────────────────────────────────────────────────

@router.get(
    "/supplier-applications",
    response_model=list[PotentialSupplierItem],
    summary="List potential suppliers (users who filled business profile)",
)
async def list_supplier_applications(
    admin_user: dict = Depends(require_admin),
):
    """
    Returns users with role='customer' and their business details for admin review.
    """
    return await fetch_potential_suppliers()


async def _notify_supplier_status_change(user_id: str, is_approved: bool):
    try:
        user = await fetch_user(user_id)
        if not user:
            return
        email = user.get("email")
        full_name = user.get("full_name") or "Valued Partner"
        
        # 1. In-App Notification
        title = "Supplier Account Approved!" if is_approved else "Supplier Status Revoked"
        body = (
            "Congratulations! Your supplier application was confirmed by administration. You can now post and manage products."
            if is_approved
            else "Your supplier privileges have been revoked by administration."
        )
        await create_in_app_notification(
            user_id=user_id,
            title=title,
            body=body,
            category="account",
            metadata={"role": "supplier" if is_approved else "customer"},
        )

        # 2. Email Notification
        if email:
            html = build_supplier_status_email_html(
                recipient_name=full_name,
                user_id=user_id,
                is_approved=is_approved,
            )
            subj = "N.O.D.E. Supplier Account Approved" if is_approved else "N.O.D.E. Supplier Privileges Update"
            await send_order_email(
                recipient=email,
                subject=subj,
                html_content=html,
            )
    except Exception as e:
        print(f"Error sending supplier status notification: {e}")


@router.post(
    "/suppliers/{user_id}/approve",
    response_model=SupplierActionResponse,
    summary="Approve user as a verified supplier",
)
async def approve_supplier(
    user_id: str,
    background_tasks: BackgroundTasks,
    admin_user: dict = Depends(require_admin),
):
    """
    Elevates a user's role to 'supplier' so they can post and manage products.
    """
    updated = await set_user_role(user_id=user_id, new_role="supplier")
    background_tasks.add_task(_notify_supplier_status_change, user_id=user_id, is_approved=True)
    return SupplierActionResponse(
        user_id=user_id,
        role="supplier",
        message="User successfully approved and elevated to supplier status.",
    )


@router.post(
    "/suppliers/{user_id}/revoke",
    response_model=SupplierActionResponse,
    summary="Revoke supplier status from a user",
)
async def revoke_supplier(
    user_id: str,
    background_tasks: BackgroundTasks,
    admin_user: dict = Depends(require_admin),
):
    """
    Reverts a supplier's role back to 'customer'.
    """
    updated = await set_user_role(user_id=user_id, new_role="customer")
    background_tasks.add_task(_notify_supplier_status_change, user_id=user_id, is_approved=False)
    return SupplierActionResponse(
        user_id=user_id,
        role="customer",
        message="Supplier privileges revoked. User reverted to customer status.",
    )


# ─────────────────────────────────────────────────────────────
# 2. Category Management
# ─────────────────────────────────────────────────────────────

@router.post(
    "/categories",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product category",
)
async def create_category(
    payload: CategoryCreateRequest,
    admin_user: dict = Depends(require_admin),
):
    """
    Create a new root or child category in categories_table.
    """
    return await insert_category(
        name=payload.name,
        parent_id=payload.parent_id,
        image_url=payload.image_url,
        level=payload.level,
    )


# ─────────────────────────────────────────────────────────────
# 3. User & Role Management
# ─────────────────────────────────────────────────────────────

@router.get("/users", summary="List registered users")
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role: customer, supplier, admin"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin_user: dict = Depends(require_admin),
):
    """List all registered platform users."""
    return await fetch_users(role=role, limit=limit, offset=offset)


@router.patch("/users/{user_id}/role", summary="Directly change a user's role")
async def change_user_role(
    user_id: str,
    payload: RoleUpdateRequest,
    admin_user: dict = Depends(require_admin),
):
    """Manually update any user's role."""
    allowed = ("customer", "supplier", "admin")
    if payload.role.lower() not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(allowed)}",
        )
    return await set_user_role(user_id=user_id, new_role=payload.role.lower())
