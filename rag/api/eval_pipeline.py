"""
NutriBench 自动评测管线。

运行示例：
  EVAL_VERSION=v3 AGENT_CONCURRENCY=3 JUDGE_CONCURRENCY=3 python eval_pipeline.py
"""

from __future__ import annotations

import asyncio
import os
import re
import time
from typing import Any, Callable

import dotenv
from notion_client import Client as NotionClient
from openai import AsyncOpenAI


dotenv.load_dotenv(".env.local")
dotenv.load_dotenv()


# ===== 配置 =====

QUESTION_DB_ID = os.getenv("QUESTION_DB_ID") or os.getenv("NOTION_DATABASE_ID", "e755b041d920410fa6dd3aa88c421879")
RESULT_DB_ID = os.getenv("RESULT_DB_ID", "c7b1b42c0ac14b5f883725f75860860e")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.gpugeek.com/v1")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "Vendor2/Gemini-3.1-pro")
EVAL_VERSION = os.getenv("EVAL_VERSION", "v3")

NUM_RUNS = int(os.getenv("NUM_RUNS", "1"))
MAX_RUBRICS = int(os.getenv("MAX_RUBRICS", "5"))
AGENT_CONCURRENCY = int(os.getenv("AGENT_CONCURRENCY", "3"))
JUDGE_CONCURRENCY = int(os.getenv("JUDGE_CONCURRENCY", "3"))
NOTION_CONCURRENCY = int(os.getenv("NOTION_CONCURRENCY", "3"))

NOTION_TEXT_CHUNK = 2000
NOTION_MAX_RICH_TEXT_BLOCKS = 100


def require_env(name: str) -> str:
    """
    读取必填环境变量，若未设置则立即抛出异常。
    用于在程序启动阶段就暴露配置缺失问题，避免运行到一半才报错。

    参数:
        name: 环境变量名称

    返回:
        该环境变量的值（非空字符串）

    抛出:
        RuntimeError: 当环境变量未设置或为空时
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少环境变量 {name}")
    return value


NOTION_API_KEY = require_env("NOTION_API_KEY")
LLM_API_KEY = require_env("LLM_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


AGENT_MODELS = [
    {
        "id": "Vendor2/Claude-4.5-Sonnet",
        "short": "Claude-4.5-Sonnet@gpugeek",
        "base_url": LLM_BASE_URL,
        "api_key": LLM_API_KEY,
    },
    {
        "id": "Vendor2/GPT-5.4",
        "short": "GPT-5.4@gpugeek",
        "base_url": LLM_BASE_URL,
        "api_key": LLM_API_KEY,
    },
]

if OPENROUTER_API_KEY:
    AGENT_MODELS.append(
        {
            "id": "anthropic/claude-sonnet-4.5",
            "short": "Claude-4.5-Sonnet@openrouter",
            "base_url": OPENROUTER_BASE_URL,
            "api_key": OPENROUTER_API_KEY,
        }
    )
else:
    print("WARN: OPENROUTER_API_KEY 未设置，跳过 OpenRouter 对比模型")


notion = NotionClient(auth=NOTION_API_KEY)
judge_client = AsyncOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
agent_clients: dict[str, AsyncOpenAI] = {}


# ===== Notion 读写 =====

def resolve_data_source_id(database_id: str) -> str:
    """
    获取 Notion 数据库关联的第一个 data_source ID。
    Notion AI Connected Database 需要通过 data_source_id 才能用
    data_sources.query() 接口分页读取数据，而不是普通的 databases.query()。

    参数:
        database_id: Notion 数据库 ID

    返回:
        data_source ID 字符串

    抛出:
        RuntimeError: 数据库没有关联 data_source 时（说明该数据库不是 AI Connected Database）
    """
    db = notion.databases.retrieve(database_id=database_id)
    sources = db.get("data_sources") or []
    if not sources:
        raise RuntimeError(f"数据库 {database_id} 没有 data_source")
    return sources[0]["id"]


def fetch_questions() -> list[dict[str, Any]]:
    """
    从 Notion 题库数据库中读取所有有效题目。
    使用分页循环遍历全部记录（每次最多 100 条），
    过滤掉没有正文的题目（防止空题目进入评测流程）。

    返回:
        题目字典列表，每个字典由 parse_question() 构造，
        包含编号、标题、正文、难度、采分点等字段。
    """
    questions = []
    data_source_id = resolve_data_source_id(QUESTION_DB_ID)
    start_cursor = None  # Notion 分页游标，None 表示从第一页开始

    while True:
        kwargs: dict[str, Any] = {"data_source_id": data_source_id, "page_size": 100}
        if start_cursor:
            kwargs["start_cursor"] = start_cursor  # 传入游标继续翻页

        response = notion.data_sources.query(**kwargs)
        for page in response["results"]:
            question = parse_question(page)
            # 跳过正文为空的题目（可能是占位行或未填写完整的题目）
            if question["正文"]:
                questions.append(question)

        # has_more=False 表示已到最后一页
        if not response.get("has_more"):
            break
        start_cursor = response.get("next_cursor")

    print(f"读取题目: {len(questions)} 道")
    return questions


def parse_question(page: dict[str, Any]) -> dict[str, Any]:
    """
    将 Notion 页面原始数据解析为评测用的题目字典。
    Notion API 返回的属性结构较复杂（嵌套 rich_text/select 等），
    这里统一提取为扁平的 Python 字典，方便后续逻辑使用。

    采分点从 "采分点1-描述" 到 "采分点{MAX_RUBRICS}-描述" 依次读取，
    跳过描述为空的项（允许题目只有部分采分点）。

    参数:
        page: Notion API 返回的单个页面对象（包含 id 和 properties）

    返回:
        题目字典，字段包括：
        - page_id: Notion 页面 ID（写入结果时用于关联）
        - 编号: 题目唯一编号
        - 标题/正文/参考答案: 题目内容
        - 难度/领域/小类: 分类标签
        - 采分点: [{"描述": str, "满分": float}, ...] 评分标准列表
    """
    props = page["properties"]
    rubrics = []

    # 动态读取最多 MAX_RUBRICS 个采分点，有描述才加入列表
    for i in range(1, MAX_RUBRICS + 1):
        desc = get_text(props, f"采分点{i}-描述")
        score = props.get(f"采分点{i}-分值", {}).get("number")
        if desc:
            rubrics.append({"描述": desc, "满分": float(score or 0)})

    return {
        "page_id": page["id"],
        "编号": props.get("题目编号", {}).get("unique_id", {}).get("number", 0),
        "标题": get_title(props, "题目标题"),
        "正文": get_text(props, "题目正文"),
        "难度": get_select(props, "难度等级"),
        "领域": get_select(props, "领域大类"),
        "小类": get_text(props, "领域小类"),
        "参考答案": get_text(props, "参考答案"),
        "采分点": rubrics,
    }


def write_result(question: dict[str, Any], agent_name: str, run: int, agent_output: str, judge: dict[str, Any]) -> None:
    """
    将单次评测结果写入 Notion 结果数据库。
    每条记录对应一个"题目 × 模型 × 运行轮次"的评测结果，
    包含 Agent 原始输出、各采分点得分、总分和得分率。

    Name 字段格式: "{版本}|NB-{编号}|{模型}|Run{轮次}"，便于在 Notion 中筛选和排序。

    参数:
        question:     题目字典（来自 parse_question）
        agent_name:   模型短名称（如 "Claude-4.5-Sonnet@gpugeek"）
        run:          当前运行轮次（1 到 NUM_RUNS）
        agent_output: Agent 返回的原始文本答案
        judge:        评分字典，包含 scores（各采分点得分列表）和 reasoning（评分理由）
    """
    scores = judge["scores"]
    max_total = sum(r["满分"] for r in question["采分点"])  # 题目总满分
    total = round(sum(scores), 4)                           # Agent 实际得分
    rate = round(total / max_total, 4) if max_total else 0  # 得分率（0~1）

    # 构建 Notion 属性字典，key 必须与结果数据库的列名完全匹配
    properties: dict[str, Any] = {
        "Name": title_prop(f"{EVAL_VERSION}|NB-{question['编号']}|{agent_name}|Run{run}"),
        "题目编号": {"number": question["编号"]},
        "题目标题": rich_text_prop(question["标题"]),
        "Agent名称": select_prop(agent_name),
        "运行轮次": select_prop(f"Run{run}"),
        "版本": rich_text_prop(EVAL_VERSION),
        "Agent原始输出": rich_text_prop(agent_output),
        "总分": {"number": total},
        "满分": {"number": max_total},
        "得分率": {"number": rate},
        "评分模型": select_prop(short_model_name(JUDGE_MODEL)),
        "评分原始输出": rich_text_prop(judge["reasoning"]),
    }
    # 难度和领域字段仅在题目有值时才设置，避免 Notion 创建空 select 选项
    if question["难度"]:
        properties["难度等级"] = select_prop(question["难度"])
    if question["领域"]:
        properties["领域大类"] = select_prop(question["领域"])

    # 逐项写入各采分点得分列（最多 MAX_RUBRICS 项）
    for i, score in enumerate(scores[:MAX_RUBRICS], start=1):
        properties[f"采分点{i}-得分"] = {"number": score}

    # 同步写入，出错时自动重试（Notion API 偶尔会限流或超时）
    retry_sync(
        lambda: notion.pages.create(parent={"database_id": RESULT_DB_ID}, properties=properties),
        label="Notion 写入",
    )


# ===== LLM 调用 =====

def agent_client(model: dict[str, str]) -> AsyncOpenAI:
    """
    获取或创建指定模型的异步 OpenAI 客户端。
    使用全局字典缓存客户端实例，避免重复创建连接。

    参数:
        model: 模型配置字典，包含 short（唯一标识）、base_url、api_key

    返回:
        AsyncOpenAI 客户端实例
    """
    key = model["short"]
    if key not in agent_clients:
        agent_clients[key] = AsyncOpenAI(base_url=model["base_url"], api_key=model["api_key"])
    return agent_clients[key]


async def call_agent(model: dict[str, str], question_text: str) -> dict[str, Any]:
    """
    调用 Agent 模型回答题目。
    使用 system prompt 设定角色（植物营养科学专家），
    要求提供具体标识符（Gene ID、KEGG、PMID）以便评分时检查可追溯性。

    参数:
        model:         模型配置字典
        question_text: 题目正文

    返回:
        {"ok": bool, "output": str, "error": str}
        - ok=True 时 output 包含答案文本
        - ok=False 时 error 包含错误信息
    """
    try:
        response = await retry_async(
            lambda: agent_client(model).chat.completions.create(
                model=model["id"],
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一个植物营养科学领域的专家级AI助手。"
                            "请根据你的知识，尽可能全面、准确、有理有据地回答以下问题。"
                            "如果涉及基因、通路、文献，请提供具体的标识符（如Gene ID、KEGG编号、PMID等）。"
                        ),
                    },
                    {"role": "user", "content": question_text},
                ],
                max_tokens=16384,  # 允许较长回答（约 12k 中文字符）
                temperature=0.3,   # 低温度保证答案稳定性，减少随机性
            ),
            label=f"Agent {model['short']}",
        )
        output = response.choices[0].message.content or ""
        if not output.strip():
            return {"ok": False, "error": "Agent 返回空内容", "output": ""}
        return {"ok": True, "output": output}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "output": ""}


async def call_judge(question: dict[str, Any], agent_output: str) -> dict[str, Any]:
    """
    调用评分模型对 Agent 答案进行打分。
    根据题目的采分点逐项评分，返回各项得分和评分理由。

    参数:
        question:     题目字典（包含采分点、参考答案等）
        agent_output: Agent 返回的答案文本

    返回:
        {"ok": bool, "scores": list[float], "reasoning": str, "raw": str, "error": str}
        - scores: 各采分点得分列表（与 question["采分点"] 顺序对应）
        - reasoning: 评分理由（去掉最后两行 SCORES/VERDICT 后的文本）
        - raw: 评分模型原始输出（用于调试）
    """
    try:
        prompt = build_judge_prompt(question, agent_output)
        response = await retry_async(
            lambda: judge_client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=16384,
                temperature=0.1,  # 极低温度保证评分一致性
            ),
            label="Judge",
        )
        raw = (response.choices[0].message.content or "").strip()
        scores, reasoning = parse_judge_scores(raw, question["采分点"])
        return {"ok": True, "scores": scores, "reasoning": reasoning, "raw": raw}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "scores": [], "reasoning": "", "raw": ""}


def build_judge_prompt(question: dict[str, Any], agent_output: str) -> str:
    """
    构建评分 prompt。
    使用英文 prompt 以提升评分模型的理解准确性（大部分 LLM 在英文上表现更好），
    但保留中文题目和答案原文。要求模型在最后两行输出结构化的分数列表和总分。

    参数:
        question:     题目字典
        agent_output: Agent 答案

    返回:
        完整的评分 prompt 字符串
    """
    rubrics = question["采分点"]
    max_total = sum(r["满分"] for r in rubrics)
    rubric_lines = "\n".join(
        f"{i}. ({r['满分']} points) {r['描述']}"
        for i, r in enumerate(rubrics, start=1)
    )
    reference = question.get("参考答案", "")
    ref_section = f"\n***\n\nThe reference answer:\n{reference}\n" if reference else ""

    return f"""You are grading a 植物营养科学 (plant nutrition science) exam answer written in Chinese.

You will be given the problem, a reference answer, a rubric, and the student's attempted answer. The rubric has {len(rubrics)} item(s) and totals up to {max_total} points.

Evaluate the attempted answer against the provided rubric. Pay close attention to detail and grade it strictly, but fairly. Only evaluate against the rubric. Per-item scores can be decimals. Give 0 if the item is not addressed, partial credit if partially addressed, full marks only if fully addressed per the rubric description. If the answer cites non-existent papers, gene IDs, or database entries, deduct on the traceability-related item(s).

***

The problem:
{question["正文"]}
{ref_section}
***

The rubric:
{rubric_lines}

***

The attempted answer:
{agent_output}

***

Explain your reasoning for each rubric item.

Then, on the LAST TWO LINES of your response, output EXACTLY this format and nothing else after them:
SCORES: [<num>, <num>, ...]
VERDICT: <total>"""


def parse_judge_scores(raw: str, rubrics: list[dict[str, Any]]) -> tuple[list[float], str]:
    """
    从评分模型的原始输出中提取分数列表和评分理由。
    使用正则表达式匹配最后两行的 SCORES 和 VERDICT，
    将前面的文本作为 reasoning 返回。

    参数:
        raw:     评分模型原始输出
        rubrics: 采分点列表（用于确定期望的分数个数）

    返回:
        (scores, reasoning) 元组
        - scores: 各采分点得分列表（若解析失败则全部填 0）
        - reasoning: 评分理由文本（去掉最后两行）
    """
    match = re.search(r"^SCORES\s*:\s*\[([^\]]*)\]\s*$", raw, flags=re.MULTILINE)
    if not match:
        raise ValueError("Judge 输出缺少 SCORES 行")

    # 提取方括号内的所有数字（支持负数和小数）
    numbers = re.findall(r"-?\d+(?:\.\d+)?", match.group(1))
    if len(numbers) != len(rubrics):
        raise ValueError(f"Judge 返回 {len(numbers)} 个分数，期望 {len(rubrics)} 个")

    # 将分数限制在 [0, 满分] 范围内，防止评分模型输出异常值
    scores = []
    for number, rubric in zip(numbers, rubrics):
        score = float(number)
        scores.append(min(max(score, 0.0), float(rubric["满分"])))

    # reasoning 是去掉最后两行（SCORES 和 VERDICT）后的文本
    return scores, raw[: match.start()].strip()


# ===== 并发控制与重试 =====

def retry_sync(func: Callable[[], Any], label: str = "操作", max_retries: int = 3) -> Any:
    """
    同步函数重试包装器。
    用于 Notion API 等可能偶发失败的操作，自动重试最多 max_retries 次。

    参数:
        func:        要执行的函数（无参数）
        label:       操作描述（用于日志）
        max_retries: 最大重试次数

    返回:
        func() 的返回值

    抛出:
        最后一次重试失败时的异常
    """
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as exc:
            if attempt == max_retries:
                print(f"{label} 失败（已重试 {max_retries} 次）: {exc}")
                raise
            print(f"{label} 失败（第 {attempt} 次尝试），1秒后重试: {exc}")
            time.sleep(1)


async def retry_async(func: Callable[[], Any], label: str = "操作", max_retries: int = 3) -> Any:
    """
    异步函数重试包装器。
    用于 LLM API 调用等可能因网络波动或限流失败的操作。

    参数:
        func:        要执行的异步函数（无参数）
        label:       操作描述（用于日志）
        max_retries: 最大重试次数

    返回:
        await func() 的返回值

    抛出:
        最后一次重试失败时的异常
    """
    for attempt in range(1, max_retries + 1):
        try:
            return await func()
        except Exception as exc:
            if attempt == max_retries:
                print(f"{label} 失败（已重试 {max_retries} 次）: {exc}")
                raise
            print(f"{label} 失败（第 {attempt} 次尝试），1秒后重试: {exc}")
            await asyncio.sleep(1)


# ===== 主流程 =====

async def process_one(
    question: dict[str, Any],
    model: dict[str, str],
    run: int,
    agent_sem: asyncio.Semaphore,
    judge_sem: asyncio.Semaphore,
    notion_sem: asyncio.Semaphore,
) -> dict[str, Any]:
    """
    处理单个评测任务（一道题 × 一个模型 × 一轮运行）。
    按顺序执行：Agent 回答 → Judge 评分 → Notion 写入，
    每个阶段使用信号量控制并发数，避免 API 限流或资源耗尽。

    参数:
        question:   题目字典
        model:      模型配置字典
        run:        运行轮次（1 到 NUM_RUNS）
        agent_sem:  Agent 调用并发控制信号量
        judge_sem:  Judge 评分并发控制信号量
        notion_sem: Notion 写入并发控制信号量

    返回:
        结果字典，包含 ok（是否成功）、score（得分）、error（错误信息）等字段
    """
    base = {"question": question["编号"], "agent": model["short"], "run": run}
    max_total = sum(r["满分"] for r in question["采分点"])

    # 前置检查：题目必须有有效采分点
    if not question["采分点"] or max_total <= 0:
        return {**base, "ok": False, "error": "题目缺少有效采分点"}

    # 阶段 1: Agent 回答（受 agent_sem 限制并发数）
    async with agent_sem:
        agent = await call_agent(model, question["正文"])
    if not agent["ok"]:
        return {**base, "ok": False, "error": f"Agent 调用失败: {agent['error']}"}

    # 阶段 2: Judge 评分（受 judge_sem 限制并发数）
    async with judge_sem:
        judge = await call_judge(question, agent["output"])
    if not judge["ok"]:
        return {**base, "ok": False, "error": f"Judge 评分失败: {judge['error']}"}

    # 阶段 3: Notion 写入（受 notion_sem 限制并发数）
    # write_result 是同步函数，用 asyncio.to_thread 转为异步执行
    try:
        async with notion_sem:
            await asyncio.to_thread(write_result, question, model["short"], run, agent["output"], judge)
    except Exception as exc:
        return {**base, "ok": False, "error": f"Notion 写入失败: {exc}"}

    return {**base, "ok": True, "score": sum(judge["scores"]), "max_score": max_total}


async def run_evaluation() -> None:
    """
    评测主流程入口。
    从 Notion 读取题目，为每个"题目 × 模型 × 轮次"组合创建异步任务，
    使用 asyncio.as_completed 并发执行并实时输出进度。

    流程:
    1. 读取题目列表
    2. 创建所有评测任务（题目数 × 模型数 × 运行轮次）
    3. 并发执行，实时打印每个任务的结果
    4. 输出汇总统计和结果库链接
    """
    print("=" * 60)
    print("NutriBench 自动评测管线")
    print("=" * 60)

    # 从 Notion 读取题目（同步操作，在主线程执行）
    questions = fetch_questions()
    if not questions:
        print("没有找到任何题目，请检查 Notion 数据库")
        return

    # 计算总任务数并打印配置信息
    total = len(questions) * len(AGENT_MODELS) * NUM_RUNS
    print(f"版本: {EVAL_VERSION}")
    print(f"计划评测: {len(questions)} 题 x {len(AGENT_MODELS)} 模型 x {NUM_RUNS} 轮 = {total} 次")
    print(f"并发: agent={AGENT_CONCURRENCY}, judge={JUDGE_CONCURRENCY}, notion={NOTION_CONCURRENCY}")
    print()

    # 创建信号量控制各阶段并发数
    agent_sem = asyncio.Semaphore(AGENT_CONCURRENCY)
    judge_sem = asyncio.Semaphore(JUDGE_CONCURRENCY)
    notion_sem = asyncio.Semaphore(NOTION_CONCURRENCY)

    # 生成所有任务（笛卡尔积：题目 × 模型 × 轮次）
    tasks = [
        process_one(q, model, run, agent_sem, judge_sem, notion_sem)
        for q in questions
        for model in AGENT_MODELS
        for run in range(1, NUM_RUNS + 1)
    ]

    # 并发执行并实时输出进度
    ok = failed = 0
    for i, future in enumerate(asyncio.as_completed(tasks), start=1):
        result = await future
        prefix = f"[{i}/{total}] NB-{result['question']} {result['agent']} Run{result['run']}"
        if result["ok"]:
            ok += 1
            print(f"{prefix} OK {result['score']:.4g}/{result['max_score']:.4g}")
        else:
            failed += 1
            print(f"{prefix} FAIL {result['error']}")

    # 输出汇总统计
    print("=" * 60)
    print(f"完成: 成功 {ok} 条，失败 {failed} 条")
    print(f"结果库: https://www.notion.so/{RESULT_DB_ID.replace('-', '')}")
    print("=" * 60)


# ===== 小工具 =====

async def retry_async(fn: Callable[[], Any], label: str, attempts: int = 3) -> Any:
    """
    异步函数重试包装器（指数退避版本）。
    每次重试前等待 2^(attempt-1) 秒（1s, 2s, 4s...），
    适合应对 API 限流或临时网络故障。

    注意：此函数与前面定义的 retry_async 功能相同但实现略有不同，
    这里使用指数退避策略，前面使用固定 1 秒延迟。

    参数:
        fn:       要执行的异步函数（无参数）
        label:    操作描述（用于错误信息）
        attempts: 最大尝试次数

    返回:
        await fn() 的返回值

    抛出:
        RuntimeError: 所有重试均失败时，包含最后一次的错误信息
    """
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                await asyncio.sleep(2 ** (attempt - 1))  # 指数退避：1s, 2s, 4s...
    raise RuntimeError(f"{label} 重试 {attempts} 次失败: {last_error}")


def retry_sync(fn: Callable[[], Any], label: str, attempts: int = 3) -> Any:
    """
    同步函数重试包装器（指数退避版本）。
    与 retry_async 类似，但用于同步函数（如 Notion API 调用）。

    参数:
        fn:       要执行的函数（无参数）
        label:    操作描述（用于错误信息）
        attempts: 最大尝试次数

    返回:
        fn() 的返回值

    抛出:
        RuntimeError: 所有重试均失败时，包含最后一次的错误信息
    """
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            if attempt < attempts:
                time.sleep(2 ** (attempt - 1))  # 指数退避：1s, 2s, 4s...
    raise RuntimeError(f"{label} 重试 {attempts} 次失败: {last_error}")


def get_text(props: dict[str, Any], key: str) -> str:
    """
    从 Notion 属性中提取 rich_text 类型字段的纯文本。
    Notion rich_text 是数组，每个元素包含 plain_text 字段，
    这里将所有片段拼接为完整字符串。

    参数:
        props: Notion 页面的 properties 字典
        key:   属性名称

    返回:
        拼接后的纯文本字符串（若字段不存在则返回空字符串）
    """
    return "".join(item.get("plain_text", "") for item in props.get(key, {}).get("rich_text", []))


def get_title(props: dict[str, Any], key: str) -> str:
    """
    从 Notion 属性中提取 title 类型字段的纯文本。
    title 类型与 rich_text 结构类似，但字段名为 "title" 而非 "rich_text"。

    参数:
        props: Notion 页面的 properties 字典
        key:   属性名称

    返回:
        拼接后的纯文本字符串（若字段不存在则返回空字符串）
    """
    return "".join(item.get("plain_text", "") for item in props.get(key, {}).get("title", []))


def get_select(props: dict[str, Any], key: str) -> str:
    """
    从 Notion 属性中提取 select 类型字段的选项名称。
    select 类型存储为 {"select": {"name": "选项名"}}。

    参数:
        props: Notion 页面的 properties 字典
        key:   属性名称

    返回:
        选项名称字符串（若未选择则返回空字符串）
    """
    selected = props.get(key, {}).get("select")
    return selected["name"] if selected else ""


def chunks(text: Any) -> list[dict[str, Any]]:
    """
    将长文本切分为 Notion API 可接受的 rich_text 块列表。
    Notion API 限制：
    - 单个 rich_text 块最多 2000 字符
    - 单个属性最多 100 个 rich_text 块

    超出限制时自动截断并添加 [TRUNCATED] 标记。

    参数:
        text: 任意类型的文本（会转为字符串）

    返回:
        Notion rich_text 块列表，格式: [{"text": {"content": "..."}}, ...]
    """
    value = str(text or "")
    if not value:
        return [{"text": {"content": ""}}]

    # 按 2000 字符切分
    pieces = [value[i : i + NOTION_TEXT_CHUNK] for i in range(0, len(value), NOTION_TEXT_CHUNK)]

    # 若超过 100 块，截断并标记
    if len(pieces) > NOTION_MAX_RICH_TEXT_BLOCKS:
        pieces = pieces[:NOTION_MAX_RICH_TEXT_BLOCKS]
        pieces[-1] = pieces[-1][:1900] + "\n\n[TRUNCATED]"  # 最后一块留 100 字符给标记

    return [{"text": {"content": piece}} for piece in pieces]


def rich_text_prop(text: Any) -> dict[str, Any]:
    """
    构造 Notion rich_text 属性格式。
    将任意文本转为 Notion API 接受的 rich_text 属性值。

    参数:
        text: 文本内容（会通过 chunks() 自动切分和截断）

    返回:
        Notion rich_text 属性字典，格式: {"rich_text": [...]}
    """
    return {"rich_text": chunks(text)}


def title_prop(text: str) -> dict[str, Any]:
    """
    构造 Notion title 属性格式。
    Title 是 Notion 数据库的主键字段，有 2000 字符的单块上限，
    这里截取前 2000 字符防止超限。

    参数:
        text: 标题文本

    返回:
        Notion title 属性字典，格式: {"title": [...]}
    """
    return {"title": chunks(str(text)[:NOTION_TEXT_CHUNK])}


def select_prop(name: str) -> dict[str, Any]:
    """
    构造 Notion select 属性格式。
    若 name 在数据库中不存在，Notion 会自动创建该选项。

    参数:
        name: 选项名称

    返回:
        Notion select 属性字典，格式: {"select": {"name": "..."}}
    """
    return {"select": {"name": name}}


def short_model_name(model: str) -> str:
    """
    将完整模型 ID 转为简短显示名称。
    用于 Notion 中的 select 字段，避免名称过长影响可读性。
    未在映射表中的模型 ID，取最后一个 "/" 后的部分。

    参数:
        model: 完整模型 ID（如 "Vendor2/Claude-4.5-Sonnet"）

    返回:
        简短名称（如 "Claude-4.5-Sonnet"）
    """
    return {
        "Vendor2/Claude-4.5-Sonnet": "Claude-4.5-Sonnet",
        "Vendor2/GPT-5.4": "GPT-5.4",
        "Vendor2/Gemini-3.1-pro": "Gemini-3.1-pro",
    }.get(model, model.split("/")[-1])


async def close_clients() -> None:
    """
    关闭所有 AsyncOpenAI 客户端连接。
    在程序退出前调用，确保底层 HTTP 连接池被正常释放，
    避免 "Unclosed client session" 等异步资源泄漏警告。
    """
    await judge_client.close()
    for client in agent_clients.values():
        await client.close()


async def main() -> None:
    """
    程序主入口。
    确保无论评测是否成功，都会在退出前关闭所有 HTTP 客户端连接。
    """
    try:
        await run_evaluation()
    finally:
        await close_clients()  # 无论是否出错都要关闭连接


if __name__ == "__main__":
    asyncio.run(main())
