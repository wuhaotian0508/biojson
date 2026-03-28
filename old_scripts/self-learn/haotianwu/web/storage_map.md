# 网站和用户信息存放位置总表

这份文档专门回答一个问题：**网站相关信息、用户相关信息、标注数据，现在分别存在哪里？**

---

## 一张表先看懂

| 信息类型 | 当前存放位置 | 代码/配置位置 | 是否共享 | 是否能追踪到具体用户 |
|---|---|---|---|---|
| 前端用户名 | 浏览器 `localStorage` | `web/src/lib/UserContext.tsx` | 否 | 否 |
| Supabase 连接配置 | 本地环境变量 | `web/.env.local`、`web/.env.local.example`、`web/src/lib/supabase.ts` | 否 | 不适用 |
| 论文数据 | Supabase `papers` 表 | `database/schema.sql` | 是 | 不适用 |
| 基因数据 | Supabase `genes` 表 | `database/schema.sql` | 是 | 不适用 |
| 人工标注 | Supabase `annotations` 表 | `database/schema.sql` | 是 | 当前不可靠 |
| 标注归属用户 | 理论上在 `annotations.annotator_id` | `database/schema.sql` | 是 | 设计上支持，当前前端未正确接入 |
| 标注时间 | `annotations.created_at` / `updated_at` | `database/schema.sql` | 是 | 只能追踪到记录时间 |

---

## 1. 网站配置存在哪里

### 1.1 Web 项目代码

网站主代码在：

- `web/`

这是一个 Next.js 项目。

### 1.2 Supabase 连接配置

Supabase 连接依赖两个前端环境变量：

- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

相关文件：

- 示例：`web/.env.local.example`
- 本地实际配置：`web/.env.local`
- 客户端初始化：`web/src/lib/supabase.ts`

也就是说，**网站连接哪个数据库**，主要由这几个环境变量决定。

---

## 2. 用户信息存在哪里

### 2.1 当前前端“用户名”

当前 web 页面里的用户名，存在浏览器本地：

- 存储位置：`localStorage`
- key：`biojson_username`
- 代码：`web/src/lib/UserContext.tsx`

这意味着：

1. 这个用户名只是在当前浏览器里记住；
2. 换电脑、换浏览器、清缓存后就会丢；
3. 它不是 Supabase Auth 的正式登录用户；
4. 它不能天然代表数据库层面的真实身份。

### 2.2 数据库里用于标注用户身份的字段

`database/schema.sql` 里，`annotations` 表定义了：

- `annotator_id UUID REFERENCES auth.users(id)`

这说明数据库原本是按 **Supabase Auth 用户** 来设计的。

也就是说，从设计上讲，系统本来想记录：

- 哪个真实用户做了这条标注。

但是当前前端在 `PaperDetail.tsx` 里保存标注时，传的是：

- `annotator_id: null`

所以现在的现状是：

- 页面里有“本地用户名”概念；
- 数据库里也有“真实标注用户字段”；
- **但这两个目前没有真正打通。**

---

## 3. 论文和标注数据存在哪里

### 3.1 论文数据：`papers`

存在 Supabase 的 `papers` 表。

包含内容主要有：

- `slug`
- `title`
- `journal`
- `doi`
- `md_content`
- `extraction_json`
- `verified_json`
- `verification_report`
- `status`

### 3.2 基因数据：`genes`

存在 Supabase 的 `genes` 表。

主要内容有：

- `paper_id`
- `gene_index`
- `gene_name`
- `gene_data`
- `auto_verification`
- `auto_stats`

### 3.3 人工标注数据：`annotations`

存在 Supabase 的 `annotations` 表。

主要内容有：

- `gene_id`
- `field_name`
- `expert_verdict`
- `corrected_value`
- `comment`
- `annotator_id`
- `created_at`
- `updated_at`

这张表才是“谁对哪个字段做了什么人工判断”的核心位置。

---

## 4. 别人的标注存在哪里

**别人的标注也存在同一个 Supabase `annotations` 表里。**

不是存在：

- 别人的浏览器里
- 你的本地电脑里

而是存在共享数据库里。

所以理论上：

- 只要你的页面重新读取 `annotations` 表，
- 你就能看到别人已经提交到数据库的标注。

但当前代码里没有 Realtime 订阅，所以：

- **能共享，不等于能实时同步。**

---

## 5. 当前能不能按用户名追踪改动

### 简短答案

**现在不能可靠追踪到“每个用户名下的改动”。**

### 原因

1. 当前用户名只是 `localStorage` 里的字符串；
2. 保存标注时没有把它转成正式数据库用户 ID；
3. `annotations` 表虽然有 `annotator_id`，但当前前端没有正确写入；
4. 当前也没有独立历史表去记录“这条标注被谁改过几次”。

### 现阶段你能确定的

- 标注内容存进了数据库；
- 标注时间字段存在；
- 数据库设计支持未来按用户追踪；
- 但当前前端实现还没有真正闭环。

---

## 6. 如果你需要真正追踪，后面要做什么

至少要补两层：

### 第一层：真实用户身份

接入 Supabase Auth，并在保存时写入：

- `annotator_id = auth.uid()`

### 第二层：历史记录

新增一张历史表，例如：

- `annotation_history`

专门记录：

- 谁改了
- 改了哪个字段
- 旧值是什么
- 新值是什么
- 什么时间改的

这样才能从“当前状态”升级到“完整追踪”。