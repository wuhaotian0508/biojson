"""
SOP 纯文本 → Markdown 格式转换器

将 experiment_design.py 生成的纯文本 SOP 转为合法 Markdown，
使前端 marked.parse() 能正确渲染标题、表格、列表等结构。
"""
from __future__ import annotations

import re


# ------------------------------------------------------------------
# 行级模式识别
# ------------------------------------------------------------------

_META_RE = re.compile(
    r'^(物种|适用物种|系统|转化策略|验证策略|流程覆盖|文件版本)\s*[：:]\s*(.+)$'
)

_STEP_RE = re.compile(r'^(Step\s+\d+)\s*[：:]\s*(.+)$')

_H3_RE = re.compile(r'^(\d+\.\d+)\s+(.+)$')

_H4_NUM_RE = re.compile(r'^(\d+\.\d+\.\d+)\s+(.+)$')

_H4_LETTER_RE = re.compile(r'^（[A-Z]）(.+)$')

_DAY_RE = re.compile(r'^(Day\s+[\d\-]+\s*(?:至\s*Day\s*\d+)?)\s*[-–—]\s*(.+)$')

# 流程图行：只匹配 │ ▼ 【】 等纯流程符号，不匹配 → （→ 也出现在普通文本中）
_FLOW_CHAR_RE = re.compile(r'[│▼▲【】]')

_HR_RE = re.compile(r'^_{5,}$')

_SUB_BULLET_RE = re.compile(r'^o\t(.+)$')

_CALLOUT_RE = re.compile(
    r'^(注意|推荐|关键提示|决策节点|转化效率参考|命名规则|判断标准|原则)[：:]\s*(.+)$'
)

_LABEL_RE = re.compile(
    r'^(试剂|操作|材料|菌株|大豆品种|种子处理|目的|PCR条件|PCR程序|保存|参考方案'
    r'|小麦品种|水稻品种|番茄品种|玉米品种|烟草品种|拟南芥品种|植物品种)[：:]\s*(.*)$'
)

_SECTION_CANDIDATES = {
    '总体流程概览', '附录', '参考文献', '参考资源',
}


def _is_list_item(line: str) -> bool:
    """判断是否为列表项（• / o / N. 开头 + tab）"""
    if line.startswith('•'):
        return True
    if re.match(r'^o\t', line):
        return True
    if re.match(r'^\d+\.\t', line):
        return True
    return False


def _is_table_row(line: str) -> bool:
    """判断是否为真正的表格行（含 tab，且不是列表项）"""
    if '\t' not in line:
        return False
    if _is_list_item(line):
        return False
    parts = [p.strip() for p in line.split('\t')]
    non_empty = [p for p in parts if p]
    return len(non_empty) >= 2


def _make_table_row(line: str) -> str:
    parts = [p.strip() for p in line.split('\t')]
    return '| ' + ' | '.join(p if p else ' ' for p in parts) + ' |'


def _make_table_separator(line: str) -> str:
    parts = line.split('\t')
    return '| ' + ' | '.join('---' for _ in parts) + ' |'


def _close_block(out: list[str], in_flow: bool, in_table: bool) -> tuple[bool, bool]:
    """关闭当前打开的代码块/表格"""
    if in_flow:
        out.append('```')
    return False, False


# ------------------------------------------------------------------
# 主转换函数
# ------------------------------------------------------------------

def format_sop_to_markdown(text: str) -> str:
    """
    将纯文本 SOP 转为 Markdown 格式。

    参数:
        text: experiment_design.py 输出的纯文本 SOP

    返回:
        Markdown 格式字符串
    """
    lines = text.split('\n')
    out: list[str] = []

    in_flow = False
    in_table = False
    title_done = False

    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        # ---- 空行 ----
        if not stripped:
            if in_flow:
                out.append('```')
                in_flow = False
            in_table = False
            out.append('')
            i += 1
            continue

        # ---- 分隔线 ----
        if _HR_RE.match(stripped):
            if in_flow:
                out.append('```')
                in_flow = False
            in_table = False
            out.append('---')
            i += 1
            continue

        # ---- 标题（第一行） ----
        if not title_done:
            out.append(f'# {stripped}')
            title_done = True
            i += 1
            continue

        # ---- 在流程图内：保持在代码块中，直到空行/分隔线 ----
        if in_flow:
            # 流程图中的 Step 行也属于流程图内容
            out.append(stripped)
            i += 1
            continue

        # ---- 元数据行 ----
        m = _META_RE.match(stripped)
        if m:
            in_table = False
            out.append(f'**{m.group(1)}：** {m.group(2)}')
            i += 1
            continue

        # ---- Step 标题 → ## ----
        m = _STEP_RE.match(stripped)
        if m:
            in_table = False
            out.append('')
            out.append(f'## {m.group(1)}：{m.group(2)}')
            i += 1
            continue

        # ---- 独立节标题 ----
        if stripped in _SECTION_CANDIDATES:
            in_table = False
            out.append('')
            out.append(f'## {stripped}')
            i += 1
            continue

        # ---- 带"附录"前缀的标题 ----
        if stripped.startswith('附录') and len(stripped) < 40:
            in_table = False
            out.append('')
            out.append(f'## {stripped}')
            i += 1
            continue

        # ---- 四级数字标题 N.N.N ----
        m = _H4_NUM_RE.match(stripped)
        if m:
            in_table = False
            out.append(f'#### {m.group(1)} {m.group(2)}')
            i += 1
            continue

        # ---- 三级数字标题 N.N ----
        m = _H3_RE.match(stripped)
        if m:
            in_table = False
            out.append(f'### {m.group(1)} {m.group(2)}')
            i += 1
            continue

        # ---- （A）/（B）标题 ----
        m = _H4_LETTER_RE.match(stripped)
        if m:
            out.append(f'#### {stripped}')
            i += 1
            continue

        # ---- Day N 标题 ----
        m = _DAY_RE.match(stripped)
        if m:
            out.append(f'#### {m.group(1)} — {m.group(2)}')
            i += 1
            continue

        # ---- 强调标签（注意：、推荐：等）→ blockquote（优先于流程图检测） ----
        m = _CALLOUT_RE.match(stripped)
        if m:
            out.append(f'> **{m.group(1)}：** {m.group(2)}')
            i += 1
            continue

        # ---- 标签行（试剂：、操作：等，优先于流程图检测） ----
        m = _LABEL_RE.match(stripped)
        if m:
            rest = m.group(2)
            if rest:
                out.append(f'**{m.group(1)}：** {rest}')
            else:
                out.append(f'**{m.group(1)}：**')
            i += 1
            continue

        # ---- 子项 o\ttext（优先于表格检测） ----
        m = _SUB_BULLET_RE.match(stripped)
        if m:
            out.append(f'  - {m.group(1)}')
            i += 1
            continue

        # ---- 圆点列表 •\ttext ----
        if stripped.startswith('•'):
            text_after = stripped.lstrip('•').strip()
            out.append(f'- {text_after}')
            i += 1
            continue

        # ---- 带 tab 的编号列表 N.\ttext ----
        num_m = re.match(r'^(\d+)\.\t(.+)$', stripped)
        if num_m:
            out.append(f'{num_m.group(1)}. {num_m.group(2)}')
            i += 1
            continue

        # ---- 流程图行（纯流程符号） ----
        if _FLOW_CHAR_RE.search(stripped):
            if in_table:
                in_table = False
            out.append('```')
            in_flow = True
            out.append(stripped)
            i += 1
            continue

        # ---- 表格行 ----
        if _is_table_row(stripped):
            if not in_table:
                out.append(_make_table_row(stripped))
                out.append(_make_table_separator(stripped))
                in_table = True
            else:
                out.append(_make_table_row(stripped))
            i += 1
            continue

        # 如果之前在表格模式，结束表格
        if in_table:
            in_table = False

        # ---- 普通行 ----
        out.append(stripped)
        i += 1

    # 收尾
    if in_flow:
        out.append('```')

    return '\n'.join(out)
