# Web 运作原理超简化教程

## 核心概念

### 1. Web 的三个角色

```
用户浏览器  ←→  Web服务器  ←→  数据库(Supabase)
   |                            |
   显示页面                      存数据/取数据
```

### 2. 数据流向

```
┌─────────────────────────────────────────────────────────────┐
│                        用户访问流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 用户打开浏览器，访问网址                                 │
│     ↓                                                       │
│  2. 浏览器向服务器请求页面                                   │
│     ↓                                                       │
│  3. 服务器返回 HTML + CSS + JavaScript                      │
│     ↓                                                       │
│  4. JavaScript 在浏览器中运行                               │
│     ↓                                                       │
│  5. JavaScript 直接连接 Supabase 获取/保存数据              │
│     ↓                                                       │
│  6. JavaScript 更新页面显示                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. 关键技术

| 技术 | 作用 | 生活比喻 |
|------|------|----------|
| HTML | 页面结构 | 房子的框架 |
| CSS | 样式/美观 | 装修和家具 |
| JavaScript | 交互逻辑 | 房子里的管家 |
| Supabase | 数据库 | 仓库 |

### 4. 与 Supabase 交互的核心代码

```javascript
// 连接 Supabase
const supabase = createClient(URL, KEY)

// 读取数据 (GET)
const { data } = await supabase.from('papers').select('*')

// 写入数据 (POST/INSERT)
await supabase.from('annotations').insert({ field: 'value' })

// 更新数据 (PUT/UPDATE)
await supabase.from('papers').update({ status: 'done' }).eq('id', 123)
```

## 文件说明

- `index.html` - 主页面（结构）
- `style.css` - 样式（美观）
- `app.js` - 交互逻辑（功能）
- `supabase-client.js` - Supabase连接（数据库操作）

## 运行方法

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 Supabase URL 和 KEY

# 2. 启动简单服务器
python3 -m http.server 8000

# 3. 浏览器访问
open http://localhost:8000
```
