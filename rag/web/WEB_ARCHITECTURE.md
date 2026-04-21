
# rag/web/ 架构文档

> 最后更新: 2026-04-15

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | **FastAPI** (Python, async) |
| 前端 | 原生 HTML/CSS/JS（无框架） |
| 流式通信 | **SSE** (Server-Sent Events)，前端通过 `fetch` + `ReadableStream.getReader()` 手动解析 |
| Markdown 渲染 | `marked.min.js` (本地托管) |
| XSS 防护 | `DOMPurify` (`purify.min.js`) |
| 认证 | Supabase Auth (`supabase.min.js`) + 自定义 JWT 校验 |

---

## 文件结构

```
rag/web/
├── app.py                 # FastAPI 主应用，所有 API 路由
├── auth.py                # 认证中间件 (get_current_user, JWT 校验)
├── auth_flask.py          # Flask 认证 (备用/旧版)
├── email_sender.py        # 邮件发送
├── run.sh                 # 开发模式启动脚本
├── run_prod.sh            # 生产模式启动脚本
├── static/
│   ├── index.html         # 单页面入口
│   ├── app.js             # 核心前端逻辑 (~1900行)
│   ├── auth.js            # 认证 UI 逻辑 (登录/注册)
│   ├── style.css          # 全部样式
│   ├── marked.min.js      # Markdown 渲染库
│   ├── purify.min.js      # DOMPurify
│   └── supabase.min.js    # Supabase SDK
```

---

## 后端 API 路由 (`app.py`)

| 路由 | 方法 | 说明 | 返回类型 |
|---|---|---|---|
| `/` | GET | 首页 (index.html) | HTML |
| `/static/...` | GET | 静态资源 | File |
| `/api/query` | POST | **主聊天接口** | SSE Stream |
| `/api/sop/extract` | POST | SOP: 提取基因 + NCBI 验证 | SSE Stream |
| `/api/sop/run` | POST | SOP: 执行实验方案生成 | SSE Stream |
| `/api/personal-lib/...` | 多种 | 个人知识库管理 (上传/列表/删除/重命名) | JSON |
| `/api/skills/...` | 多种 | Skills 管理 (CRUD) | JSON |
| `/api/tools` | GET | 获取可用 Tools 列表 | JSON |

### SSE 事件格式

所有 SSE 接口使用 `_sse(payload)` 序列化：
```
data: {"type": "...", "data": "..."}\n\n
```

`/api/query` 发出的事件类型：

| type | 含义 | data |
|---|---|---|
| `tools_enabled` | 可用工具列表 | `{tools: [...]}` |
| `skill_selected` | 命中的 Skill | `{data: "skill_name"}` |
| `tool_call` | 工具调用开始 | `{tool, args}` |
| `tool_result` | 工具调用完成 | `{tool}` |
| `searching` | 搜索状态文案 | `{data: "正在搜索..."}` |
| `sources` | 参考文献列表 | `{data: [...]}` |
| `text` | **流式回答文本片段** | `{data: "..."}` |
| `genes_available` | 检测到可编辑基因 | `{genes: ["GmFAD2",...]}` |
| `done` | 流结束 | `{}` |
| `error` | 错误 | `{data: "msg"}` 或 `{msg: "pipeline error"}` |
| `experiment_start` | SOP 实验开始 | `{genes: [...]}` |
| `progress` | SOP 进度 | 进度详情 |
| `result` | SOP 结果 | `{sops: [...]}` |

---

## 前端架构 (`app.js`)

### 国际化 (i18n)

- 双语支持: `zh` / `en`
- `I18N` 对象存储所有翻译
- `t(key)` 函数获取翻译
- `applyLanguage()` 批量更新 DOM 中 `data-i18n` 和 `data-i18n-placeholder` 属性
- 语言偏好存储在 `localStorage('lang')`

### 全局状态

```js
let isQuerying = false;              // 是否正在生成
let currentAbortController = null;   // 用于中断 SSE 流的 AbortController
let currentStreamMsgId = null;       // 正在流式生成的消息 ID
let userHasScrolled = false;         // 用户是否手动向上滚动
let conversationHistory = [];        // 本地历史 [{id, title, messages, timestamp}]
let currentSessionId = null;         // 当前对话 session ID
let hasStartedConversation = false;  // 是否已开始对话（控制欢迎页显示）
let isDeepSearch = false;            // 深度搜索开关
let usePersonal = false;             // 个人知识库开关
const assistantTurnState = new Map(); // 每条 assistant 消息的状态
```

### 核心流程

```
用户输入 → handleSend()
  ├── 正在生成中？→ abortCurrentStream() 终止
  └── 发送请求：
      ├── addMessage('user', query)         # 添加用户消息气泡
      ├── setSendBtnToStop()                # 按钮变红色 ■
      ├── addMessage('assistant', loading)  # 添加加载占位
      └── streamQuery(query, messageId)     # 开始流式请求
          ├── fetch('/api/query', {signal})
          ├── reader.read() 循环
          │   ├── text 事件 → answerText += data → updateMessage(formatAnswer)
          │   ├── sources 事件 → 缓存引用
          │   ├── done 事件 → 最终渲染 + 参考文献 + 实验按钮
          │   └── 其他事件 → 更新工具调用 UI
          └── 结束 → setSendBtnToSend()
```

### 消息 DOM 结构

```
.message.message-assistant
├── .message-avatar          # 🧬 头像
└── .message-body
    └── .message-content
        ├── .tool-calls-summary  # 工具调用折叠区（可展开）
        ├── .assistant-answer    # 主回答区（流式更新目标）
        └── .assistant-extras    # 参考文献、实验按钮、SOP UI
```

关键设计：`.assistant-answer` 和 `.assistant-extras` 分离，避免流式更新覆盖附加 UI。

### 智能滚动机制

- `smartScroll()`: 仅在 `userHasScrolled === false` 时自动滚到底部
- scroll 监听: 距离底部 >80px → `userHasScrolled = true`
- 用户发消息时: `userHasScrolled = false`（重置）
- 生成中向上滚动: 出现 "↓ 回到底部" 悬浮按钮，点击回到底部

### 生成终止机制

- 生成中发送按钮变为红色 ■ (`.stop-mode`)，带脉冲动画
- 点击 → `abortCurrentStream()`:
  1. 保存已有的部分回答到历史
  2. 清理 loading spinner
  3. 渲染已有内容 + "已停止生成" 提示
  4. 折叠工具调用 UI
  5. 追加已获取的参考文献
  6. `AbortController.abort()` 终止 fetch 请求
  7. 重置按钮状态

### 关键函数速查

| 函数 | 行号(约) | 说明 |
|---|---|---|
| `abortCurrentStream()` | ~332 | 终止生成，保存部分回答 |
| `smartScroll()` | ~385 | 智能滚动 |
| `setSendBtnToStop/Send()` | ~404 | 切换按钮状态 |
| `setupEventListeners()` | ~453 | 初始化所有事件监听 |
| `startNewChat()` | ~690 | 新建对话 |
| `handleSend()` | ~717 | 处理发送/停止 |
| `streamQuery()` | ~805 | 流式请求核心 |
| `streamExperiment()` | ~971 | SOP 实验流程 |
| `addMessage()` | ~1287 | 添加消息气泡 |
| `updateMessage()` | ~1324 | 更新消息内容（只改 .assistant-answer） |
| `getMessageRegions()` | ~1434 | 获取消息三区域 DOM |
| `formatAnswer()` | ~1450+ | marked + DOMPurify 渲染 |
| `renderReferences()` | ~1500+ | 渲染参考文献 |
| `renderExperimentButton()` | ~1460+ | 渲染实验设计按钮 |
| `saveToHistory()` | - | 保存到 localStorage |
| `loadHistory()` | - | 加载历史列表 |

### 历史记录

- 存储在 `localStorage`
- 结构: `[{id, title, messages: [{query, answerText, sources, timestamp}], timestamp}]`
- 多轮对话通过 `buildHistory()` 发送给后端（保留第 1 轮 + 最近 2 轮）

---

## CSS 关键布局 (`style.css`)

```
.app-container (flex row)
├── .sidebar (240px 宽, 可折叠)
│   ├── .sidebar-header (logo)
│   ├── #history-list (历史列表)
│   └── .knowledge-base (知识库入口)
└── .main-content (flex: 1)
    └── .content-wrapper (flex column, position: relative)
        ├── .app-header (固定头部)
        ├── #welcome-section (欢迎页, 首次显示)
        ├── #chat-container (flex: 1, overflow-y: auto, 消息容器)
        ├── #scroll-to-bottom-btn (absolute 定位悬浮按钮)
        ├── .input-section (固定底部输入区)
        │   └── .input-container
        │       ├── textarea#query-input
        │       └── .input-actions
        │           ├── #personal-btn
        │           ├── #depth-btn
        │           └── #send-btn (.send-btn / .send-btn.stop-mode)
        └── #scene-intro (场景卡片, 首次显示)
```

### 重要 CSS 类

| 类名 | 作用 |
|---|---|
| `.send-btn.stop-mode` | 红色脉冲停止按钮 |
| `.generation-stopped` | "已停止生成" 提示样式 |
| `.scroll-to-bottom-btn` / `.visible` | 回到底部悬浮按钮 |
| `.search-progress` + `.search-spinner` | 搜索中加载动画 |
| `.tool-calls-summary` | 工具调用折叠摘要 |
| `.message-user` / `.message-assistant` | 用户/助手消息气泡 |

---

## 认证流程

1. 页面加载 → `initAuth()` 检查 `localStorage` 中的 token
2. 无 token → 显示登录/注册覆盖层
3. 登录成功 → 存储 access_token → 隐藏覆盖层
4. API 请求 → `Authorization: Bearer <token>` header
5. 401 响应 → 重新显示登录覆盖层

---

## 修改指南

### 添加新的 SSE 事件类型
1. 后端 `app.py` 的 `generate()` 中 `yield _sse({"type": "new_type", ...})`
2. 前端 `app.js` 的 `streamQuery()` 中添加 `else if (data.type === 'new_type')` 分支

### 添加新的 UI 文案
1. `app.js` 的 `I18N.zh` 和 `I18N.en` 中各添加一条
2. 使用 `t('key.name')` 获取

### 修改消息渲染
- 主回答内容: 修改 `formatAnswer()` 或 `updateMessage()`
- 附加内容 (参考文献等): 修改对应的 render 函数，内容插入 `.assistant-extras`
- 注意: `updateMessage()` 只替换 `.assistant-answer`，不会覆盖 `.assistant-extras`
