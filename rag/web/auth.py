"""
后端认证模块 —— 使用 supabase-py 验证前端传来的 access_token
"""
import os
import logging
from functools import wraps
from flask import request, jsonify
from supabase import create_client
import config

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
