from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = str(BASE_DIR / 'skills')
USER_SKILLS_DIR = str(BASE_DIR / 'user_skills')

# skill-creator 目录：允许读取（Agent 需要读指令），禁止写入（防止篡改）
SKILL_CREATOR_DIR = str(BASE_DIR / 'skills' / 'skill-creator')


def check_path(file_path, *, write=False, user_id=None):
    """检查文件路径是否在允许范围内。

    允许的读取范围: skills/ + user_skills/<当前用户>/
    允许的写入范围: skills/（排除 skill-creator）+ user_skills/<当前用户>/
    用户隔离: user_skills/ 下的路径必须匹配 user_id
    """
    real = os.path.realpath(file_path)

    # 检查是否在 skills/ 下
    in_skills = real.startswith(SKILLS_DIR + os.sep) or real == SKILLS_DIR

    # 检查是否在 user_skills/ 下（需要用户隔离）
    in_user_skills = real.startswith(USER_SKILLS_DIR + os.sep) or real == USER_SKILLS_DIR

    if not in_skills and not in_user_skills:
        raise PermissionError(f"禁止访问 skills/user_skills 目录之外的路径: {file_path}")

    # 用户隔离：user_skills/ 下的路径必须属于当前用户
    if in_user_skills:
        if not user_id:
            raise PermissionError(f"访问 user_skills 需要用户身份: {file_path}")
        user_dir = os.path.join(USER_SKILLS_DIR, user_id)
        if not (real.startswith(user_dir + os.sep) or real == user_dir):
            raise PermissionError(f"禁止访问其他用户的 skills: {file_path}")

    # skill-creator: 允许读，禁止写
    in_creator = real.startswith(SKILL_CREATOR_DIR + os.sep) or real == SKILL_CREATOR_DIR
    if in_creator and write:
        raise PermissionError(f"禁止写入 skill-creator 目录: {file_path}")


def check_command(command):
    if '..' in command:
        raise PermissionError(f"禁止使用 .. 跳出目录")


WARNING = '（工作目录锁定在 skills/ 和 user_skills/，skill-creator 目录只读）'
