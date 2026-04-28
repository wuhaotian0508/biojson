"""
后端认证模块 —— FastAPI Depends 版
使用 supabase-py 验证前端传来的 access_token
"""
import os
import asyncio
import logging
import random
import threading
import hashlib
import hmac
from datetime import datetime, timedelta
from types import SimpleNamespace

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from supabase import create_client
from nutrimaster.auth.email import send_verification_code
from nutrimaster.config.settings import Settings

logger = logging.getLogger(__name__)

_SETTINGS = Settings.from_env()
_CODE_SALT = os.getenv("AUTH_CODE_SALT") or _SETTINGS.supabase_service_role_key
_VERIFY_ATTEMPT_LOCK = threading.Lock()
_VERIFY_ATTEMPTS: dict[str, dict] = {}
_MAX_VERIFY_ATTEMPTS = 5
_VERIFY_LOCK_MINUTES = 15

# ===== 初始化 Supabase 客户端（用 service_role_key 以便验证任意用户 token） =====
supabase = create_client(_SETTINGS.supabase_url, _SETTINGS.supabase_service_role_key)

# ===== 管理员邮箱列表（逗号分隔，从环境变量读取） =====
_admin_raw = os.getenv("ADMIN_EMAILS") or os.getenv("ADMIN_EMAIL") or ""
ADMIN_EMAILS = set(
    e.strip().lower()
    for e in _admin_raw.split(",")
    if e.strip()
)
logger.info("ADMIN_EMAILS loaded: %d entries", len(ADMIN_EMAILS))


def _as_bool_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _dev_auth_user():
    email = os.getenv("NUTRIMASTER_DEV_AUTH_EMAIL", "dev@example.com")
    nickname = os.getenv("NUTRIMASTER_DEV_AUTH_NICKNAME") or email.split("@")[0] or "dev"
    return SimpleNamespace(
        id=os.getenv("NUTRIMASTER_DEV_AUTH_USER_ID", "dev-user"),
        email=email,
        user_metadata={"nickname": nickname, "avatar_url": None},
    )


async def get_current_user(request: Request):
    """FastAPI 依赖：从 Authorization header 提取并验证 Supabase token"""
    if _as_bool_env("NUTRIMASTER_DEV_AUTH_BYPASS"):
        logger.warning("NUTRIMASTER_DEV_AUTH_BYPASS is enabled; Supabase auth is bypassed")
        return _dev_auth_user()

    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else ""

    if not token:
        raise HTTPException(status_code=401, detail="未登录，请先登录")

    try:
        user_response = await asyncio.to_thread(supabase.auth.get_user, token)
        return user_response.user
    except Exception:
        raise HTTPException(status_code=401, detail="认证失败，请重新登录")


async def user_profile_view(user):
    """返回当前登录用户的 profile"""
    email = (user.email or "").lower()
    meta = getattr(user, "user_metadata", None) or {}

    nickname = meta.get("nickname") or email.split("@")[0] or "User"
    avatar_url = meta.get("avatar_url")
    is_admin = email in ADMIN_EMAILS

    return JSONResponse({
        "email": user.email,
        "is_admin": is_admin,
        "nickname": nickname,
        "avatar_url": avatar_url,
    })


async def update_profile_view(request: Request, user):
    """更新当前用户的 nickname / avatar_url"""
    data = await request.json()

    nickname = data.get("nickname")
    avatar_url = data.get("avatar_url")

    if nickname is None and avatar_url is None:
        raise HTTPException(status_code=400, detail="至少提供 nickname 或 avatar_url")

    meta = getattr(user, "user_metadata", None) or {}
    new_meta = dict(meta)
    if nickname is not None:
        new_meta["nickname"] = nickname
    if avatar_url is not None:
        new_meta["avatar_url"] = avatar_url

    try:
        await asyncio.to_thread(
            supabase.auth.admin.update_user_by_id,
            user.id,
            {"user_metadata": new_meta},
        )
    except Exception as e:
        logger.error("更新用户 profile 失败: %s", e)
        raise HTTPException(status_code=500, detail="更新失败")

    return JSONResponse({
        "status": "ok",
        "nickname": new_meta.get("nickname", ""),
        "avatar_url": new_meta.get("avatar_url"),
    })


async def delete_account_view(user):
    """删除当前用户账号"""
    try:
        await asyncio.to_thread(supabase.auth.admin.delete_user, user.id)
    except Exception as e:
        logger.error("删除用户失败: %s", e)
        raise HTTPException(status_code=500, detail="删除失败")

    return JSONResponse({"status": "ok"})


def generate_verification_code() -> str:
    """生成 6 位数字验证码"""
    return f"{random.randint(0, 999999):06d}"


def _hash_verification_code(email: str, code: str) -> str:
    """对验证码做带邮箱作用域的哈希，避免明文落库。"""
    payload = f"{email.lower()}:{code}".encode("utf-8")
    return hmac.new(_CODE_SALT.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def _public_auth_message() -> str:
    """统一对外文案，避免泄露账号状态。"""
    return "如果邮箱可用，验证码已发送，请查收邮箱"


def _cleanup_verify_attempts(now: datetime) -> None:
    expired = [
        email for email, state in _VERIFY_ATTEMPTS.items()
        if state.get("lock_until") and state["lock_until"] <= now
    ]
    for email in expired:
        _VERIFY_ATTEMPTS.pop(email, None)


def _ensure_not_locked(email: str) -> None:
    now = datetime.utcnow()
    with _VERIFY_ATTEMPT_LOCK:
        _cleanup_verify_attempts(now)
        state = _VERIFY_ATTEMPTS.get(email)
        lock_until = state.get("lock_until") if state else None
        if lock_until and lock_until > now:
            raise HTTPException(status_code=429, detail="验证码尝试次数过多，请稍后再试")


def _record_verify_failure(email: str) -> None:
    now = datetime.utcnow()
    with _VERIFY_ATTEMPT_LOCK:
        _cleanup_verify_attempts(now)
        state = _VERIFY_ATTEMPTS.setdefault(email, {"count": 0, "lock_until": None})
        state["count"] += 1
        if state["count"] >= _MAX_VERIFY_ATTEMPTS:
            state["lock_until"] = now + timedelta(minutes=_VERIFY_LOCK_MINUTES)


def _clear_verify_failures(email: str) -> None:
    with _VERIFY_ATTEMPT_LOCK:
        _VERIFY_ATTEMPTS.pop(email, None)


async def signup_with_email(request: Request):
    """
    注册流程：
    1. 接收 email, password, nickname?, avatar_url?
    2. 生成验证码，通过 admin API 创建用户（未验证状态）
    3. 用 163 SMTP 发送验证码邮件
    """
    data = await request.json()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    nickname = (data.get("nickname") or "").strip()
    avatar_url = data.get("avatar_url")

    if not email or not password:
        raise HTTPException(status_code=400, detail="邮箱和密码不能为空")

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")

    code = generate_verification_code()
    code_hash = _hash_verification_code(email, code)
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat() + "Z"

    # 构建 user_metadata
    user_metadata = {
        "verification_code_hash": code_hash,
        "code_expires_at": expires_at,
    }
    if nickname:
        user_metadata["nickname"] = nickname
    if avatar_url:
        user_metadata["avatar_url"] = avatar_url

    try:
        # 先尝试查找已有用户（可能之前注册过但未验证）
        users_resp = await asyncio.to_thread(
            supabase.auth.admin.list_users,
        )
        existing_user = None
        for u in users_resp:
            if hasattr(u, 'email') and u.email and u.email.lower() == email:
                existing_user = u
                break

        if existing_user:
            # 用户已存在
            if existing_user.email_confirmed_at:
                logger.info("Signup requested for existing confirmed email: %s", email)
            else:
                # 未验证 → 只更新验证码，不覆盖原密码，避免未验证账号被他人接管
                await asyncio.to_thread(
                    supabase.auth.admin.update_user_by_id,
                    existing_user.id,
                    {
                        "user_metadata": {
                            **(getattr(existing_user, 'user_metadata', None) or {}),
                            **user_metadata,
                        },
                    },
                )
                return JSONResponse({
                    "status": "ok",
                    "message": _public_auth_message(),
                    "password_updated": False,
                })
        if not existing_user:
            # 新用户 → 创建
            await asyncio.to_thread(
                supabase.auth.admin.create_user,
                {
                    "email": email,
                    "password": password,
                    "email_confirm": False,
                    "user_metadata": user_metadata,
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("创建用户失败: %s", e)
        raise HTTPException(status_code=500, detail="注册失败，请稍后再试")

    # 发送验证码邮件
    sent = await asyncio.to_thread(send_verification_code, email, code)
    if not sent:
        raise HTTPException(status_code=500, detail="验证码邮件发送失败，请稍后再试")

    return JSONResponse({
        "status": "ok",
        "message": _public_auth_message(),
        "password_updated": True,
    })


async def verify_email_code(request: Request):
    """
    验证流程：
    1. 接收 email, code
    2. 查找用户，校验验证码和过期时间
    3. 确认邮箱，清除验证码
    """
    data = await request.json()
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()

    if not email or not code:
        raise HTTPException(status_code=400, detail="邮箱和验证码不能为空")

    _ensure_not_locked(email)

    try:
        # 查找用户
        users_resp = await asyncio.to_thread(
            supabase.auth.admin.list_users,
        )
        target_user = None
        for u in users_resp:
            if hasattr(u, 'email') and u.email and u.email.lower() == email:
                target_user = u
                break

        if not target_user:
            _record_verify_failure(email)
            raise HTTPException(status_code=400, detail="验证码错误或已失效")

        meta = getattr(target_user, 'user_metadata', None) or {}
        saved_code_hash = meta.get("verification_code_hash")
        expires_at_str = meta.get("code_expires_at")

        if not saved_code_hash or not expires_at_str:
            _record_verify_failure(email)
            raise HTTPException(status_code=400, detail="验证码错误或已失效")

        # 校验验证码
        expected_hash = _hash_verification_code(email, code)
        if not hmac.compare_digest(expected_hash, saved_code_hash):
            _record_verify_failure(email)
            raise HTTPException(status_code=400, detail="验证码错误或已失效")

        # 校验过期时间
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        now = datetime.utcnow().replace(tzinfo=expires_at.tzinfo)
        if now > expires_at:
            _record_verify_failure(email)
            raise HTTPException(status_code=400, detail="验证码错误或已失效")

        # 验证成功：确认邮箱 + 清除验证码
        clean_meta = dict(meta)
        clean_meta.pop("verification_code_hash", None)
        clean_meta.pop("code_expires_at", None)

        await asyncio.to_thread(
            supabase.auth.admin.update_user_by_id,
            target_user.id,
            {
                "email_confirm": True,
                "user_metadata": clean_meta,
            },
        )
        _clear_verify_failures(email)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("验证邮箱失败: %s", e)
        raise HTTPException(status_code=500, detail="验证失败，请稍后再试")

    return JSONResponse({"status": "ok", "message": "邮箱验证成功"})


async def resend_verification_code(request: Request):
    """
    重新发送验证码：
    1. 接收 email
    2. 生成新验证码，更新 user_metadata
    3. 发送新验证码邮件
    """
    data = await request.json()
    email = (data.get("email") or "").strip().lower()

    if not email:
        raise HTTPException(status_code=400, detail="邮箱不能为空")

    try:
        users_resp = await asyncio.to_thread(
            supabase.auth.admin.list_users,
        )
        target_user = None
        for u in users_resp:
            if hasattr(u, 'email') and u.email and u.email.lower() == email:
                target_user = u
                break

        if not target_user:
            return JSONResponse({"status": "ok", "message": _public_auth_message()})

        if target_user.email_confirmed_at:
            return JSONResponse({"status": "ok", "message": _public_auth_message()})

        code = generate_verification_code()
        code_hash = _hash_verification_code(email, code)
        expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat() + "Z"

        meta = getattr(target_user, 'user_metadata', None) or {}
        new_meta = dict(meta)
        new_meta["verification_code_hash"] = code_hash
        new_meta["code_expires_at"] = expires_at

        await asyncio.to_thread(
            supabase.auth.admin.update_user_by_id,
            target_user.id,
            {"user_metadata": new_meta},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("重发验证码失败: %s", e)
        raise HTTPException(status_code=500, detail="发送失败，请稍后再试")

    sent = await asyncio.to_thread(send_verification_code, email, code)
    if not sent:
        raise HTTPException(status_code=500, detail="验证码邮件发送失败，请稍后再试")

    return JSONResponse({"status": "ok", "message": _public_auth_message()})
