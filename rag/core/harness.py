from pathlib import Path
import os
BASE_DIR=Path(__file__).resolve().parent.parent
SKILLS_DIR=str(BASE_DIR/'skills')
BLOCKED_DIR=str(BASE_DIR/'skills'/'skill-creator')

def check_path(file_path):
    real=os.path.realpath(file_path)
    if not real.startswith(SKILLS_DIR+os.sep) and real != SKILLS_DIR:
        raise PermissionError(f"禁止访问 skills 目录之外的路径: {file_path}")
    if real.startswith(BLOCKED_DIR+os.sep) or real == BLOCKED_DIR:
        raise PermissionError(f"禁止访问 skill-creator: {file_path}")

def check_command(command):
    if 'skill-creator' in command:
        raise PermissionError(f"禁止操作 skill-creator")
    if '..' in command:
        raise PermissionError(f"禁止使用 .. 跳出 skills 目录")

WARNING='（工作目录锁定在 skills/，禁止操作 skill-creator）'