from fastapi import APIRouter

from app.authentication.email_auth.endpoints.delete_account import router as delete_account
from app.authentication.email_auth.endpoints.delete_pending_account import (
    router as delete_pending_account,
)
from app.authentication.email_auth.endpoints.me import router as me
from app.authentication.email_auth.endpoints.request_password_reset import (
    router as request_password_reset,
)
from app.authentication.email_auth.endpoints.resend_signup_otp import (
    router as resend_signup_otp,
)
from app.authentication.email_auth.endpoints.sign_in import router as sign_in
from app.authentication.email_auth.endpoints.sign_up import router as sign_up
from app.authentication.email_auth.endpoints.update_password import router as update_password
from app.authentication.email_auth.endpoints.verify_signup_otp import (
    router as verify_signup_otp,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
router.include_router(sign_in)
router.include_router(sign_up)
router.include_router(verify_signup_otp)
router.include_router(resend_signup_otp)
router.include_router(request_password_reset)
router.include_router(update_password)
router.include_router(delete_pending_account)
router.include_router(delete_account)
router.include_router(me)
