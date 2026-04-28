#!/usr/bin/env python3
"""
Skill 验证器 — 检查 skill 目录结构和 frontmatter 是否合法

用法:
    python validate_skill.py <skill-directory>

示例:
    python validate_skill.py ../skills/code-review
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

MAX_NAME_LENGTH = 64
ALLOWED_RESOURCE_DIRS = {"scripts", "references"}
PLACEHOLDER_MARKERS = ("[todo", "todo:")


def _extract_frontmatter(content: str) -> str | None:
    """提取 --- ... --- 之间的 frontmatter 文本。"""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


def _parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    """解析 frontmatter，优先用 PyYAML，无则降级到简化解析。"""
    if yaml is not None:
        try:
            fm = yaml.safe_load(text)
        except yaml.YAMLError as e:
            return None, f"YAML 解析失败: {e}"
        if not isinstance(fm, dict):
            return None, "frontmatter 必须是字典格式"
        return fm, None

    # 简化解析: 逐行 key: value
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if not key:
            continue
        # 去引号
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        result[key] = value
    return result, None


def validate_skill(skill_path: str | Path) -> tuple[bool, str]:
    """
    验证 skill 目录结构。

    返回 (is_valid, message)。
    """
    skill_path = Path(skill_path).resolve()

    if not skill_path.is_dir():
        return False, f"路径不是目录: {skill_path}"

    skill_md = skill_path / "skill.md"
    if not skill_md.exists():
        return False, "缺少 skill.md 文件"

    try:
        content = skill_md.read_text(encoding="utf-8")
    except OSError as e:
        return False, f"无法读取 skill.md: {e}"

    # 解析 frontmatter
    fm_text = _extract_frontmatter(content)
    if fm_text is None:
        return False, "skill.md 缺少 frontmatter（需要以 --- 开头）"

    fm, error = _parse_frontmatter(fm_text)
    if error:
        return False, error

    # 必填字段
    if "name" not in fm:
        return False, "frontmatter 缺少 'name' 字段"
    if "description" not in fm:
        return False, "frontmatter 缺少 'description' 字段"

    # 验证 name
    name = str(fm["name"]).strip()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        return False, f"name '{name}' 格式不对（需小写字母+数字+连字符）"
    if len(name) > MAX_NAME_LENGTH:
        return False, f"name 过长 ({len(name)} 字符)，最大 {MAX_NAME_LENGTH}"
    if name != skill_path.name:
        return False, f"name '{name}' 与目录名 '{skill_path.name}' 不一致"

    # 验证 description
    desc = str(fm["description"]).strip()
    if not desc:
        return False, "description 不能为空"
    if any(m in desc.lower() for m in PLACEHOLDER_MARKERS):
        return False, "description 仍包含 TODO 占位符，请替换为实际内容"
    if len(desc) > 1024:
        return False, f"description 过长 ({len(desc)} 字符)，最大 1024"

    # 验证目录中没有多余文件
    for child in skill_path.iterdir():
        if child.name == "skill.md":
            continue
        if child.is_dir() and child.name in ALLOWED_RESOURCE_DIRS:
            continue
        return False, f"skill 根目录中有意外文件: {child.name}（只允许 skill.md、scripts/、references/）"

    return True, "验证通过！"


def main():
    if len(sys.argv) != 2:
        print("用法: python validate_skill.py <skill-directory>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(f"{'[OK]' if valid else '[错误]'} {message}")
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
