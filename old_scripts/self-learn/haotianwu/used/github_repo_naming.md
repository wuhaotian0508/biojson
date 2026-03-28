# GitHub 项目起名规范

## 1. 基本规则

| 规则 | 说明 | 示例 |
|------|------|------|
| **全小写** | 仓库名统一使用小写字母 | `my-project` ✅ `My-Project` ❌ |
| **用短横线分隔** | 多个单词之间用 `-`（kebab-case） | `machine-learning-toolkit` ✅ |
| **避免下划线** | GitHub 官方推荐短横线而非下划线 | `my-project` ✅ `my_project` ⚠️ |
| **简短明了** | 名称应简洁，一般 2-4 个单词 | `bio-json` ✅ `my-awesome-biology-json-converter-tool` ❌ |
| **只用字母、数字、短横线** | 避免特殊字符 | `data-pipeline` ✅ `data@pipeline!` ❌ |

## 2. 命名风格

### 2.1 描述功能型（最常见）
直接描述项目做什么：
- `face-detection` — 人脸检测
- `markdown-parser` — Markdown 解析器
- `image-compressor` — 图片压缩工具

### 2.2 领域 + 功能型
前缀表示领域，后缀表示功能：
- `bio-json` — 生物领域的 JSON 工具
- `ml-pipeline` — 机器学习流水线
- `web-crawler` — 网络爬虫

### 2.3 品牌/创意名型
大型项目常用独特名称：
- `pytorch` — Python + Torch
- `pandas` — Panel Data
- `flask` — 轻量（烧瓶的隐喻）
- `numpy` — Numerical Python

### 2.4 缩写型
用简洁缩写：
- `tqdm` — taqaddum（阿拉伯语"进步"）
- `ffmpeg` — Fast Forward MPEG

## 3. 常见命名模式

```
# 工具类
{功能}-{类型}
例: json-parser, file-manager, log-analyzer

# 库/框架
{语言/领域}-{名称}
例: py-utils, react-hooks, go-cache

# API/服务
{服务}-api / {服务}-server
例: weather-api, auth-server

# 学习/教程
{主题}-tutorial / learn-{主题} / {主题}-examples
例: python-tutorial, learn-docker, pytorch-examples

# Awesome 列表
awesome-{主题}
例: awesome-python, awesome-machine-learning

# 配置文件
dotfiles, {工具}-config
例: dotfiles, vim-config, nvim-config
```

## 4. 避免的做法

| ❌ 不推荐 | ✅ 推荐 | 原因 |
|-----------|---------|------|
| `test` / `demo` / `project1` | `bio-data-converter` | 名称无意义 |
| `MyAwesomeProject` | `my-awesome-project` | 不要用驼峰 |
| `final_version_v2_new` | `data-pipeline` | 不要加版本后缀 |
| `asdfgh` | `text-classifier` | 名称应有含义 |
| `john-project` | `sentiment-analyzer` | 避免以人名命名 |

## 5. 好名字的检查清单

- [ ] 名字能让人一眼看出项目做什么？
- [ ] 是否使用了全小写 + 短横线？
- [ ] 长度是否在 2-4 个单词以内？
- [ ] 在 GitHub 上搜索是否已有同名热门项目？（避免混淆）
- [ ] 是否容易拼写和记忆？
- [ ] 是否避免了缩写歧义？

## 6. 实际知名项目的命名参考

| 项目 | 命名逻辑 |
|------|----------|
| `scikit-learn` | Science Kit for Learning |
| `hugging-face/transformers` | 组织名/功能名 |
| `facebookresearch/detectron2` | 组织名/品牌名+版本 |
| `openai/whisper` | 组织名/创意名 |
| `fastapi` | Fast + API，简洁有力 |
| `streamlit` | Stream + Lit，朗朗上口 |

## 7. 总结

> **最佳实践公式：**
>
> `小写字母` + `短横线分隔` + `简短描述功能` = 好的仓库名
>
> 例：`bio-json`、`data-pipeline`、`text-classifier`
