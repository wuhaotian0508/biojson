#!/usr/bin/env python3
"""
Skill 初始化器 — 从模板创建新 skill 目录

用法:
    python init_skill.py <skill-name> --path <目标目录> [--resources scripts,references]

示例:
    python init_skill.py code-review --path ../skills
    python init_skill.py code-review --path ../skills --resources scripts,references
"""

import argparse
import re
import sys
from pathlib import Path

MAX_NAME_LENGTH = 64
ALLOWED_RESOURCES = {"scripts", "references"}

SKILL_TEMPLATE = """\
---
name: {skill_name}
description: "[TODO] 说明这个 skill 做什么，以及什么时候触发。包含 'Use when...' 触发条件。"
---

# {skill_title}

## 核心流程

1. [TODO] 步骤一
2. [TODO] 步骤二
3. [TODO] 步骤三

## 关键规则

- [TODO] 必须遵守的约束
- [TODO] 输出格式要求
"""


def normalize_name(raw: str) -> str:
    """将任意字符串规范化为小写连字符格式的 skill 名。"""
    name = raw.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    name = re.sub(r"-{2,}", "-", name)
    return name


def title_case(skill_name: str) -> str:
    """连字符名 → Title Case，如 'code-review' → 'Code Review'。"""
    return " ".join(w.capitalize() for w in skill_name.split("-"))


def parse_resources(raw: str) -> list[str]:
    """解析并验证逗号分隔的资源类型。"""
    if not raw:
        return []
    items = [x.strip() for x in raw.split(",") if x.strip()]
    invalid = sorted(set(items) - ALLOWED_RESOURCES)
    if invalid:
        print(f"[错误] 不支持的资源类型: {', '.join(invalid)}")
        print(f"       允许: {', '.join(sorted(ALLOWED_RESOURCES))}")
        sys.exit(1)
    # 去重保序
    seen, result = set(), []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def init_skill(skill_name: str, path: str, resources: list[str]):
    skill_dir = Path(path).resolve() / skill_name

    if skill_dir.exists():
        print(f"[错误] 目录已存在: {skill_dir}")
        return None

    skill_dir.mkdir(parents=True)
    print(f"[OK] 创建目录: {skill_dir}")

    # 写入 skill.md
    content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=title_case(skill_name),
    )
    (skill_dir / "skill.md").write_text(content, encoding="utf-8")
    print("[OK] 创建 skill.md")

    # 创建资源目录
    for res in resources:
        (skill_dir / res).mkdir(exist_ok=True)
        print(f"[OK] 创建 {res}/")

    print(f"\n[完成] skill '{skill_name}' 已初始化于 {skill_dir}")
    print("\n后续步骤:")
    print("1. 编辑 skill.md，完善 description 和正文指令")
    if resources:
        print("2. 在资源目录中添加脚本或参考文档")
    print(f"3. 运行 validate_skill.py 验证: python validate_skill.py {skill_dir}")
    return skill_dir


def main():
    parser = argparse.ArgumentParser(description="创建新 skill 模板目录")
    parser.add_argument("skill_name", help="skill 名称（自动规范化为连字符格式）")
    parser.add_argument("--path", required=True, help="skill 目录的父目录")
    parser.add_argument("--resources", default="", help="逗号分隔: scripts,references")
    args = parser.parse_args()

    name = normalize_name(args.skill_name)
    if not name:
        print("[错误] skill 名称至少包含一个字母或数字")
        sys.exit(1)
    if len(name) > MAX_NAME_LENGTH:
        print(f"[错误] 名称过长 ({len(name)} 字符)，最大 {MAX_NAME_LENGTH}")
        sys.exit(1)
    if name != args.skill_name:
        print(f"[提示] 名称已规范化: '{args.skill_name}' → '{name}'")

    resources = parse_resources(args.resources)

    print(f"初始化 skill: {name}")
    print(f"  路径: {args.path}")
    if resources:
        print(f"  资源: {', '.join(resources)}")
    print()

    result = init_skill(name, args.path, resources)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
