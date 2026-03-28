# BioJSON

BioJSON 当前的正式主线是 `extractor/`：把植物营养代谢相关论文的 Markdown 文本做预处理、LLM 结构化提取、字段级验证，并输出可复查的 JSON 与报告。

`rag/` 目录仍保留，但现在明确视为**实验模块**，不属于主流水线，也不会直接消费 `extractor/output/*.json`。

## Mainline

主线目录只看 `extractor/`：

```text
extractor/
├── input/          # 待处理 Markdown
├── output/         # 最终 verified JSON
├── reports/        # extraction / verification 报告
├── prompts/        # Prompt 与 Schema
├── extract.py      # 提取阶段
├── verify.py       # 验证阶段
├── pipeline.py     # 编排入口
├── text_utils.py   # 纯文本清洗 + 显式 LLM section 过滤
├── token_tracker.py
└── run.sh          # 推荐运行入口
```

## Quick Start

1. 安装依赖

```bash
pip install openai python-dotenv pytest
```

2. 配置根目录 `.env`

```env
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
MODEL=Vendor2/Claude-4.6-opus

FALLBACK_API_KEY=
FALLBACK_BASE_URL=
FALLBACK_MODEL=
```

3. 把待处理论文放进 `extractor/input/`

4. 运行主流水线

```bash
bash extractor/run.sh
```

常用命令：

```bash
bash extractor/run.sh pipeline
bash extractor/run.sh pipeline-test
bash extractor/run.sh pipeline-test 3
bash extractor/run.sh pipeline-test keyword
bash extractor/run.sh rerun
python -m extractor.pipeline --workers 5
```

## Outputs

- `extractor/output/*_verified.json`: 最终修正后的结构化结果
- `extractor/reports/<paper>/extraction.json`: 原始提取结果
- `extractor/reports/<paper>/verification.json`: 字段级验证报告
- `extractor/reports/token-usage/*.json`: token 用量报告

流水线重跑时会明确区分：

- `processed`: 本次真正执行并产出结果
- `skipped`: 已有 verified 结果，未重复处理
- `failed`: 本次执行失败

## Experimental Modules

`rag/` 是单独的实验目录，用于基于 `data/*.json` 的检索问答。

当前约束：

- 它不是 `extractor` 的一部分
- 它不读取 `extractor/output/*.json`
- 它需要单独配置 `JINA_API_KEY`
- 若将来要接入主线，必须先做 schema 适配，而不是直接混用

实验模块说明见 [`rag/README.md`](./rag/README.md)。

## Verification

项目最基本的回归检查：

```bash
pytest -q
python -m compileall extractor rag
```
