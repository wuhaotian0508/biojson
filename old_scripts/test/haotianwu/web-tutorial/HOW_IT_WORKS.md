# Web 与 Supabase 交互详解

## 一、Web 基本原理

### 1.1 什么是 Web？

Web 就是 **浏览器** 和 **服务器** 之间的对话。

```
┌─────────┐                  ┌─────────┐
│ 浏览器  │  ←→  发送请求  →  │ 服务器  │
│ (你看到的) │  ←→  返回页面  →  │ (运行代码) │
└─────────┘                  └─────────┘
```

### 1.2 三个核心技术

| 技术 | 全称 | 作用 | 例子 |
|------|------|------|------|
| **HTML** | HyperText Markup Language | 页面骨架 | `<h1>标题</h1>` |
| **CSS** | Cascading Style Sheets | 页面样式 | `color: red;` |
| **JavaScript** | - | 页面行为 | `alert('你好!')` |

### 1.3 文件分工

```
index.html  →  定义页面有什么内容（结构）
style.css   →  定义页面长什么样（样式）
app.js      →  定义页面怎么动（交互）
```

---

## 二、数据流向图解

### 2.1 完整流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户打开网页                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  浏览器下载 index.html                                            │
│  浏览器下载 style.css                                             │
│  浏览器下载 app.js                                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  JavaScript 开始运行                                             │
│  1. 读取 Supabase 配置                                            │
│  2. 创建 Supabase 客户端                                         │
│  3. 发送请求：GET /papers                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Supabase 云端数据库                           │
│  接收请求 → 查询数据 → 返回 JSON                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  JavaScript 收到数据                                             │
│  1. 解析 JSON                                                    │
│  2. 生成 HTML                                                    │
│  3. 插入到页面                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    用户看到论文列表                              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 保存标注时的流程

```
用户选择评分 "好"
      ↓
JavaScript 监听到 change 事件
      ↓
收集数据：gene_id, field_name, verdict, username
      ↓
发送请求：POST /field_annotations
      ↓
Supabase 保存到数据库
      ↓
返回成功/失败
      ↓
JavaScript 显示提示消息
```

---

## 三、Supabase 交互详解

### 3.1 什么是 Supabase？

Supabase = 开源的 Firebase 替代品
- 提供**云数据库**（基于 PostgreSQL）
- 提供**实时订阅**
- 提供**身份验证**
- 提供**存储**服务

### 3.2 连接 Supabase

```javascript
// 第一步：导入 Supabase 库
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>

// 第二步：创建客户端
const supabase = window.supabase.createClient(
    'https://你的项目.supabase.co',  // URL
    '你的匿名密钥'                     // Key
)
```

### 3.3 CRUD 操作

#### CREATE（创建/插入）
```javascript
await supabase
    .from('field_annotations')      // 表名
    .insert({                        // 要插入的数据
        gene_id: '123',
        field_name: 'Gene_Name',
        verdict: 'good',
        annotator_name: '张三'
    })
```

#### READ（读取/查询）
```javascript
const { data } = await supabase
    .from('papers')                  // 表名
    .select('*')                     // 选择所有列
    .eq('status', 'completed')       // 条件：status = 'completed'
    .order('created_at', { ascending: false })  // 排序
```

#### UPDATE（更新）
```javascript
await supabase
    .from('papers')
    .update({ status: 'in_review' }) // 要更新的字段
    .eq('id', 123)                   // 条件：id = 123
```

#### DELETE（删除）
```javascript
await supabase
    .from('annotations')
    .eq('id', 456)                   // 条件：id = 456
    .delete()                        // 删除
```

---

## 四、代码运行顺序

### 4.1 index.html 的执行顺序

```html
<!DOCTYPE html>
<html>
<head>
    <!-- 1. 先加载样式 -->
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <!-- 2. 渲染 HTML 结构 -->
    <div id="papersList"></div>

    <!-- 3. 加载外部库 -->
    <script src="supabase 库"></script>

    <!-- 4. 加载我们的代码（按顺序）-->
    <script src="supabase-client.js"></script>
    <script src="app.js"></script>
</body>
</html>
```

### 4.2 app.js 的执行顺序

```
1. 等待 DOM 加载完成 (DOMContentLoaded)
      ↓
2. 检查 localStorage 中是否有用户信息
      ↓
3. 调用 initSupabase() 初始化数据库连接
      ↓
4. 调用 fetchPapers() 从 Supabase 获取数据
      ↓
5. 调用 renderPapersList() 渲染到页面
      ↓
6. 等待用户交互（点击、输入等）
```

---

## 五、关键概念对比

| 概念 | 传统 Web | 本项目 |
|------|----------|--------|
| **服务器** | 需要写后端代码 | 无需后端，直接连 Supabase |
| **数据库** | MySQL/PostgreSQL | Supabase (也是 PostgreSQL) |
| **API** | 需要 REST/GraphQL | Supabase 自动生成 |
| **认证** | 需要自己实现 | Supabase Auth（本例用简化版） |
| **实时性** | 需要 WebSocket | Supabase Realtime |

---

## 六、常见问题

### Q1: 为什么不需要后端服务器？
A: Supabase 提供了**直接从浏览器访问数据库**的能力。但这需要注意安全：
- 使用 **anon key**（匿名密钥）而非 service key
- 在 Supabase 后台设置 **Row Level Security** (RLS)

### Q2: 数据存在哪里？
A: 数据存在 Supabase 的云端服务器，你可以在 Supabase 控制台查看。

### Q3: 用户数据存在哪里？
A: 本例使用 `localStorage` 存储用户名，这只是演示。生产环境应该用 Supabase Auth。

### Q4: 如何调试？
A: 按 F12 打开浏览器开发者工具：
- **Console**：看 `console.log` 输出
- **Network**：看网络请求
- **Application**：看 localStorage

---

## 七、学习路径建议

1. **第一步**：先理解 HTML/CSS/JS 基础语法
2. **第二步**：学习 `fetch()` 和 `async/await`
3. **第三步**：学习 Supabase 查询语法
4. **第四步**：了解 React（本项目的 web 文件夹使用）

## 八、与原项目对比

| 特性 | 简化版 (test/) | 原项目 (web/) |
|------|----------------|---------------|
| 框架 | 纯 JavaScript | Next.js + React |
| 构建 | 无需构建 | 需要编译 |
| 类型 | 无类型 | TypeScript |
| 样式 | 原生 CSS | Tailwind CSS |
| 复杂度 | ~300 行 | ~1000+ 行 |

简化版适合学习原理，原项目适合生产使用。
