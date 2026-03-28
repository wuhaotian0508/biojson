# 当前 Web 设置说明

这份文档解释 biojson 当前 web 的主要结构、配置方式，以及现在这套系统到底是怎么运行的。

---

## 1. 项目位置

web 项目目录：

- `web/`

它是一个 Next.js App Router 项目。

主要文件：

- `web/src/lib/supabase.ts`：Supabase 客户端初始化
- `web/src/lib/UserContext.tsx`：前端本地用户名管理
- `web/src/app/page.tsx`：论文列表页
- `web/src/app/papers/[slug]/page.tsx`：论文详情页服务端取数
- `web/src/app/papers/[slug]/PaperDetail.tsx`：标注交互主界面
- `database/schema.sql`：数据库结构与权限策略

---

## 2. 环境变量

当前 web 依赖：

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

相关文件：

- 示例：`web/.env.local.example`
- 本地实际配置：`web/.env.local`

在 `web/src/lib/supabase.ts` 中，前端通过这些变量创建 Supabase client。

如果缺少这两个变量，代码会报警告：

- `Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY`

---

## 3. 当前“登录”机制是什么

当前项目没有真正接入 Supabase Auth 登录。

现在用的是一个非常轻量的前端本地用户名机制：

- 从 `localStorage` 读取 `biojson_username`
- 保存时也只写回 `localStorage`
- 页面用它判断“当前是否已经登录”

代码位置：

- `web/src/lib/UserContext.tsx`

这套机制的特点：

### 优点

- 简单
- 本地演示方便
- 不用先搭完整认证

### 缺点

- 不是正式身份认证
- 没法可靠追踪谁改了什么
- 换设备或清缓存就没有了
- 与数据库里的 `annotator_id` 设计不一致

---

## 4. 当前数据层设置

数据库结构定义在：

- `database/schema.sql`

当前核心表有 3 张：

### `papers`

存论文：

- 标题、期刊、DOI
- markdown 原文
- 抽取结果 JSON
- 验证结果 JSON
- 状态信息

### `genes`

存拆平后的基因：

- 属于哪篇论文
- 第几个基因
- 基因名
- 基因字段 JSON
- AI 自动验证结果

### `annotations`

存人工标注：

- 标注对应哪个 gene
- 标注的是哪个 field
- 判断正确/错误/修改
- 修正值
- 备注
- 理论上的标注用户 `annotator_id`

---

## 5. 页面如何使用这些数据

### 首页 `web/src/app/page.tsx`

从 `papers` 表读取论文列表，展示：

- 标题
- 期刊
- DOI
- 基因数量
- 状态
- 验证统计

### 详情页数据入口 `web/src/app/papers/[slug]/page.tsx`

按 slug 读取：

1. `papers`
2. `genes`
3. `annotations`

然后把这些数据传给 `PaperDetail.tsx`。

### 标注页面 `web/src/app/papers/[slug]/PaperDetail.tsx`

负责：

- 左侧显示 markdown 原文
- 右侧显示 metadata 与 gene 字段
- 允许用户提交字段级标注
- 保存时直接写 `annotations` 表

---

## 6. 当前保存逻辑的关键问题

虽然 `annotations` 表设计了 `annotator_id`，但前端保存标注时使用的是：

- `annotator_id: null`

这会导致一个核心问题：

- 数据库存了标注内容，
- 但没有把它可靠绑定到真实用户身份。

所以当前系统更像：

- “能提交标注的共享页面”

而不是：

- “可审计、可追踪、按用户区分权限的正式协作系统”。

---

## 7. 当前是否支持实时协作

当前前端没有看到以下逻辑：

- `channel(...)`
- `postgres_changes`
- `subscribe()`

所以现在不是实时协作模式。

现状是：

- 初次进入页面时读取数据库；
- 本人保存后触发一次本地刷新；
- 别人刚提交的标注不会自动推到你页面上。

这意味着：

- **共享是有的**，
- **实时同步没有。**

---

## 8. 推荐你下一步关注什么

如果你要做“多人可追踪标注”，建议重点看：

1. `storage_map.md`：先看数据到底放哪里
2. `data_flow.md`：看页面如何取数和保存
3. `tracking_plan.md`：看如何从现在这套升级成真正可追踪系统