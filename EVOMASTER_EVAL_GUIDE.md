# Evomaster 评估使用指南

## 快速开始

### 1. 环境配置

在 `/data/haotianwu/biojson/.env` 中添加以下配置：

```bash
# Notion 配置（必需）
NOTION_API_KEY=your_notion_key
QUESTION_DB_ID=e755b041d920410fa6dd3aa88c421879
RESULT_DB_ID=c7b1b42c0ac14b5f883725f75860860e

# LLM 配置（用于 Judge）
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.gpugeek.com/v1
JUDGE_MODEL=Vendor2/Gemini-3.1-pro

# Evomaster 配置
EVOMASTER_ROOT=/data/haotianwu/Evomaster_fs
EVOMASTER_PLAYGROUND=fs_mv                # 可选: fs_mv, fs_single_sn, fs_debate, FS_MCTS
EVOMASTER_AGENT_NAME=Evomaster-fs_mv      # 在结果中显示的名称
EVOMASTER_TIMEOUT=600                     # 单题超时时间（秒）

# 评测配置
EVAL_VERSION=v3                           # 评测版本标识
NUM_RUNS=1                                # 每题运行次数
MAX_QUESTIONS=0                           # 限制题目数量（0=全部）
AGENT_CONCURRENCY=1                       # Agent 并发数（Evomaster 建议用 1）
JUDGE_CONCURRENCY=3                       # Judge 并发数
```

### 2. 测试 Adapter

在运行完整评估前，先测试 adapter 是否正常工作：

```bash
cd /data/haotianwu/Evomaster_fs
python test_adapter.py
```

这会：
1. 检查 playground 是否正确注册
2. 询问是否运行一个测试问题（可选）

### 3. 运行评估

```bash
cd /data/haotianwu/biojson

# 测试前 5 道题
MAX_QUESTIONS=5 python eval_evomaster.py

# 运行完整评估（50 道题）
python eval_evomaster.py

# 使用不同的 playground
EVOMASTER_PLAYGROUND=fs_single_sn python eval_evomaster.py
```

## 文件说明

### 新增文件

1. **`/data/haotianwu/biojson/eval_evomaster.py`**
   - Evomaster 专用评估脚本
   - 从 Notion 读取题目，调用 Evomaster，评分，写回结果

2. **`/data/haotianwu/Evomaster_fs/test_adapter.py`**
   - 测试脚本，验证 adapter 和 playground 注册是否正常

### 修改文件

1. **`/data/haotianwu/Evomaster_fs/evomaster_nutribench_adapter.py`**
   - 添加了显式导入 playground 模块的逻辑
   - 修复了 playground 注册问题

2. **`/data/haotianwu/Evomaster_fs/playground/*/__init__.py`**
   - 添加了 Playground 类的导出
   - 确保 `from playground.xxx import XXXPlayground` 能正常工作

## 根因修复说明

### 问题

之前 Evomaster 评估出现大量 0 分，根本原因是：

1. **Playground 注册机制失效**
   - `@register_playground` 装饰器只在模块被导入时执行
   - `get_playground_class()` 不会自动导入 playground 模块
   - 导致注册表为空，回退到 `BasePlayground`

2. **返回结构不匹配**
   - `BasePlayground` 使用 `BaseExp`，返回 `{"trajectory", "status", "steps"}`
   - 没有 `final_answer` 字段
   - Adapter 只能从 trajectory 提取，得到投票消息而非答案

### 修复方案

1. **显式导入触发注册**
   ```python
   if agent_name == "fs_mv":
       from playground.fs_mv import FrontierScienceMajorVotePlayground
   ```

2. **完善 `__init__.py` 导出**
   ```python
   from .core.playground import FrontierScienceMajorVotePlayground
   __all__ = ["FrontierScienceMajorVotePlayground"]
   ```

3. **优先提取 `final_answer`**
   ```python
   output = result.get("final_answer", "").strip()
   if not output:
       trajectory = result.get("trajectory")
       if trajectory:
           output = extract_agent_response(trajectory)
   ```

## 可用的 Playground

| Playground | 说明 | 配置 |
|-----------|------|------|
| `fs_mv` | Major-vote (多候选投票) | `EVOMASTER_PLAYGROUND=fs_mv` |
| `fs_single_sn` | Single agent | `EVOMASTER_PLAYGROUND=fs_single_sn` |
| `fs_debate` | Debate (辩论) | `EVOMASTER_PLAYGROUND=fs_debate` |
| `FS_MCTS` | MCTS (蒙特卡洛树搜索) | `EVOMASTER_PLAYGROUND=FS_MCTS` |

## 常见问题

### Q: 如何只测试 Evomaster 而不测试其他 Agent？

A: 使用 `eval_evomaster.py` 脚本，它只调用 Evomaster。

### Q: 评估很慢怎么办？

A: 
- Evomaster 是多 agent 系统，单题可能需要 5-10 分钟
- 建议先用 `MAX_QUESTIONS=5` 测试
- `AGENT_CONCURRENCY=1` 是推荐值，增加并发可能导致资源竞争

### Q: 如何查看详细日志？

A: Evomaster 的运行日志保存在 `/data/haotianwu/Evomaster_fs/runs/` 目录下。

### Q: 如何使用自定义配置文件？

A: 设置 `EVOMASTER_CONFIG=/path/to/config.yaml`

## 评估结果

结果会写入：
1. **Notion 结果数据库** - 实时更新，包含完整评分信息
2. **控制台输出** - 显示进度和最终统计

输出示例：
```
=== Evomaster 评估 ===
Playground: fs_mv
Agent 名称: Evomaster-fs_mv
超时时间: 600s
并发数: Agent=1, Judge=3

读取题目: 50 道
将评测 50 道题目，每题运行 1 次

[Q1] 调用 Evomaster-fs_mv...
[Q1] Agent 回答完成 (1234 字符)
[Q1] 评分中...
[Q1] 得分: 8.5/10
[Q1] 完成

...

=== 评测完成 ===
成功: 50/50
失败: 0/50
平均得分: 7.82
```

## 性能建议

- **首次测试**: `MAX_QUESTIONS=5` 验证流程
- **完整评估**: 预计耗时 4-8 小时（50 题 × 5-10 分钟/题）
- **并发设置**: `AGENT_CONCURRENCY=1` 避免资源竞争
- **超时设置**: 简单题 300s，复杂题 600-1200s
