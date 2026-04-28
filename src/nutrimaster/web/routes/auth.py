from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from nutrimaster.auth.service import (
    delete_account_view,
    get_current_user,
    resend_verification_code,
    signup_with_email,
    update_profile_view,
    user_profile_view,
    verify_email_code,
)

router = APIRouter()


@router.post("/api/auth/signup")
async def auth_signup(request: Request):
    return await signup_with_email(request)


@router.post("/api/auth/verify")
async def auth_verify(request: Request):
    return await verify_email_code(request)


@router.post("/api/auth/resend")
async def auth_resend(request: Request):
    return await resend_verification_code(request)


@router.get("/api/user/profile")
async def user_profile(user=Depends(get_current_user)):
    return await user_profile_view(user=user)


@router.put("/api/user/profile")
async def user_profile_update(request: Request, user=Depends(get_current_user)):
    return await update_profile_view(request=request, user=user)


@router.delete("/api/user/account")
async def user_account_delete(user=Depends(get_current_user)):
    return await delete_account_view(user=user)
