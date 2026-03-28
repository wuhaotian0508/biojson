# BioJSON RAG (Experimental)

`rag/` 是一个实验性的检索问答模块，不属于 BioJSON 的正式主流水线。

它当前基于 `data/*.json` 构建向量索引，再通过 Jina 检索与 LLM 生成回答。它和 `extractor/` 的 schema 目前**没有打通**，所以不能直接拿 `extractor/output/*.json` 当输入。

## Requirements

至少需要这些环境变量：

```env
JINA_API_KEY=your-jina-key
OPENAI_API_KEY=your-llm-key
OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
MODEL=gpt-4o
```

如果缺少 `JINA_API_KEY`，`JinaRetriever` 会直接报错，而不是使用任何内置默认值。

## Usage

交互模式：

```bash
python rag/main.py
```

单次查询：

```bash
python rag/main.py -q "植物中DREB转录因子如何调控抗旱性？"
```

Web 实验界面：

```bash
cd rag/web
bash run.sh
```

## Scope Boundary

这个目录当前只做实验，不承担主产品职责：

- 不由 `extractor/run.sh` 调起
- 不参与主 README 的运行路径
- 不保证和 `extractor` 输出兼容

如果后续要把它升级为正式模块，应先完成 schema 对齐和入口整合。
