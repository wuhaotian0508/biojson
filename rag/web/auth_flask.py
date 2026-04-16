"""
后端认证模块 —— 使用 supabase-py 验证前端传来的 access_token
"""
import os
import logging
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from supabase import create_client
import core.config as config
from web.email_sender import send_verification_code

logger = logging.getLogger(__name__)

# ===== 初始化 Supabase 客户端（用 service_role_key 以便验证任意用户 token） =====
supabase = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_ROLE_KEY)

# ===== 管理员邮箱列表（逗号分隔，从环境变量读取） =====
# 兼容 ADMIN_EMAILS（复数）和 ADMIN_EMAIL（单数）两种写法
_admin_raw = os.getenv("ADMIN_EMAILS") or os.getenv("ADMIN_EMAIL") or ""
ADMIN_EMAILS = set(
    e.strip().lower()
    for e in _admin_raw.split(",")
    if e.strip()
)
logger.info("ADMIN_EMAILS loaded: %s", ADMIN_EMAILS)
print(f"[auth] ADMIN_EMAILS = {ADMIN_EMAILS}")


def login_required(f):
    """装饰器：检查请求中的 Authorization header，验证用户身份"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # 从 header 中取 token
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else ''

        if not token:
            return jsonify({'error': '未登录，请先登录'}), 401

        try:
            # 用 supabase 验证 token，获取用户信息
            user_response = supabase.auth.get_user(token)
            request.user = user_response.user
        except Exception:
            return jsonify({'error': '认证失败，请重新登录'}), 401

        return f(*args, **kwargs)
    return decorated


def user_profile_view():
    """返回当前登录用户的 profile（邮箱、是否管理员、昵称、头像）
    注意：调用此函数前需确保 request.user 已由 login_required 设置。
    昵称和头像优先从 Supabase user_metadata 读取，fallback 到邮箱前缀。
    """
    user = request.user
    email = (user.email or '').lower()
    meta = getattr(user, 'user_metadata', None) or {}

    nickname = meta.get('nickname') or email.split('@')[0] or 'User'
    avatar_url = meta.get('avatar_url')  # base64 data URL 或 None
    is_admin = email in ADMIN_EMAILS

    return jsonify({
        'email': user.email,
        'is_admin': is_admin,
        'nickname': nickname,
        'avatar_url': avatar_url,
    })


def update_profile_view():
    """更新当前用户的 nickname / avatar_url（存入 Supabase user_metadata）"""
    user = request.user
    data = request.get_json() or {}

    nickname = data.get('nickname')
    avatar_url = data.get('avatar_url')

    if nickname is None and avatar_url is None:
        return jsonify({'error': '至少提供 nickname 或 avatar_url'}), 400

    # 构建要更新的 user_metadata（保留原有字段）
    meta = getattr(user, 'user_metadata', None) or {}
    new_meta = dict(meta)
    if nickname is not None:
        new_meta['nickname'] = nickname
    if avatar_url is not None:
        new_meta['avatar_url'] = avatar_url

    try:
        supabase.auth.admin.update_user_by_id(
            user.id,
            {"user_metadata": new_meta}
        )
    except Exception as e:
        logger.error("更新用户 profile 失败: %s", e)
        return jsonify({'error': '更新失败'}), 500

    return jsonify({
        'status': 'ok',
        'nickname': new_meta.get('nickname', ''),
        'avatar_url': new_meta.get('avatar_url'),
    })


def delete_account_view():
    """删除当前用户账号"""
    user = request.user

    try:
        supabase.auth.admin.delete_user(user.id)
    except Exception as e:
        logger.error("删除用户失败: %s", e)
        return jsonify({'error': '删除失败'}), 500

    return jsonify({'status': 'ok'})


def generate_verification_code() -> str:
    """生成 6 位数字验证码"""
    return f"{random.randint(0, 999999):06d}"


def signup_with_email_view():
    """
    注册流程：
    1. 接收 email, password, nickname?, avatar_url?
    2. 生成验证码，通过 admin API 创建用户（未验证状态）
    3. 用 163 SMTP 发送验证码邮件
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    nickname = (data.get("nickname") or "").strip()
    avatar_url = data.get("avatar_url")

    if not email or not password:
        return jsonify({"error": "邮箱和密码不能为空"}), 400

    if len(password) < 6:
        return jsonify({"error": "密码至少 6 位"}), 400

    code = generate_verification_code()
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat() + "Z"

    user_metadata = {
        "verification_code": code,
        "code_expires_at": expires_at,
    }
    if nickname:
        user_metadata["nickname"] = nickname
    if avatar_url:
        user_metadata["avatar_url"] = avatar_url

    try:
        users_resp = supabase.auth.admin.list_users()
        existing_user = None
        for u in users_resp:
            if hasattr(u, 'email') and u.email and u.email.lower() == email:
                existing_user = u
                break

        if existing_user:
            if existing_user.email_confirmed_at:
                return jsonify({"error": "该邮箱已注册，请直接登录"}), 400
            else:
                supabase.auth.admin.update_user_by_id(
                    existing_user.id,
                    {
                        "password": password,
                        "user_metadata": {
                            **(getattr(existing_user, 'user_metadata', None) or {}),
                            **user_metadata,
                        },
                    },
                )
        else:
            supabase.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": False,
                    "user_metadata": user_metadata,
                },
            )
    except Exception as e:
        logger.error("创建用户失败: %s", e)
        error_msg = str(e)
        if "already been registered" in error_msg or "already exists" in error_msg:
            return jsonify({"error": "该邮箱已注册，请直接登录"}), 400
        return jsonify({"error": "注册失败，请稍后再试"}), 500

    sent = send_verification_code(email, code)
    if not sent:
        return jsonify({"error": "验证码邮件发送失败，请稍后再试"}), 500

    return jsonify({"status": "ok", "message": "验证码已发送到您的邮箱"})


def verify_email_code_view():
    """
    验证流程：
    1. 接收 email, code
    2. 查找用户，校验验证码和过期时间
    3. 确认邮箱，清除验证码
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()

    if not email or not code:
        return jsonify({"error": "邮箱和验证码不能为空"}), 400

    try:
        users_resp = supabase.auth.admin.list_users()
        target_user = None
        for u in users_resp:
            if hasattr(u, 'email') and u.email and u.email.lower() == email:
                target_user = u
                break

        if not target_user:
            return jsonify({"error": "用户不存在"}), 400

        meta = getattr(target_user, 'user_metadata', None) or {}
        saved_code = meta.get("verification_code")
        expires_at_str = meta.get("code_expires_at")

        if not saved_code or not expires_at_str:
            return jsonify({"error": "验证码已失效，请重新注册"}), 400

        if code != saved_code:
            return jsonify({"error": "验证码错误"}), 400

        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        now = datetime.utcnow().replace(tzinfo=expires_at.tzinfo)
        if now > expires_at:
            return jsonify({"error": "验证码已过期，请重新发送"}), 400

        clean_meta = dict(meta)
        clean_meta.pop("verification_code", None)
        clean_meta.pop("code_expires_at", None)

        supabase.auth.admin.update_user_by_id(
            target_user.id,
            {
                "email_confirm": True,
                "user_metadata": clean_meta,
            },
        )

    except Exception as e:
        logger.error("验证邮箱失败: %s", e)
        return jsonify({"error": "验证失败，请稍后再试"}), 500

    return jsonify({"status": "ok", "message": "邮箱验证成功"})


def resend_verification_code_view():
    """
    重新发送验证码
    """
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"error": "邮箱不能为空"}), 400

    try:
        users_resp = supabase.auth.admin.list_users()
        target_user = None
        for u in users_resp:
            if hasattr(u, 'email') and u.email and u.email.lower() == email:
                target_user = u
                break

        if not target_user:
            return jsonify({"error": "用户不存在"}), 400

        if target_user.email_confirmed_at:
            return jsonify({"error": "邮箱已验证，请直接登录"}), 400

        code = generate_verification_code()
        expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat() + "Z"

        meta = getattr(target_user, 'user_metadata', None) or {}
        new_meta = dict(meta)
        new_meta["verification_code"] = code
        new_meta["code_expires_at"] = expires_at

        supabase.auth.admin.update_user_by_id(
            target_user.id,
            {"user_metadata": new_meta},
        )

    except Exception as e:
        logger.error("重发验证码失败: %s", e)
        return jsonify({"error": "发送失败，请稍后再试"}), 500

    sent = send_verification_code(email, code)
    if not sent:
        return jsonify({"error": "验证码邮件发送失败，请稍后再试"}), 500

    return jsonify({"status": "ok", "message": "新验证码已发送"})
