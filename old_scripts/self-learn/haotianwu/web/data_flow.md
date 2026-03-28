# Web 数据流说明

这份文档解释当前 web 页面中，数据是怎么从数据库进入页面、再从页面写回数据库的。

---

## 1. 首页数据流

文件：`web/src/app/page.tsx`

首页会从 Supabase `papers` 表读取：

- `id`
- `slug`
- `title`
- `journal`
- `doi`
- `gene_count`
- `status`
- `verification_report`

然后把它们显示成论文列表。

### 结论

- 首页看到的论文信息来自数据库 `papers`
- 不是本地文件直接渲染

---

## 2. 论文详情页数据流

文件：`web/src/app/papers/[slug]/page.tsx`

进入某篇论文详情页时，会依次读取：

1. `papers`：根据 `slug` 找到论文
2. `genes`：根据 `paper.id` 找到该论文的所有基因
3. `annotations`：根据 `gene_ids` 找到这些基因已有的人工标注

然后把这三部分数据一起传给：

- `PaperDetail.tsx`

### 结论

进入详情页时，页面上看到的内容由三层组成：

- 论文主信息：`papers`
- 基因信息：`genes`
- 人工标注：`annotations`

---

## 3. 左侧原文来自哪里

在 `PaperDetail.tsx` 中，左侧 markdown 原文来自：

- `paper.md_content`

也就是说，原文内容已经提前存到了 `papers` 表里。

不是页面临时去读 `md/processed/*.md` 文件。

### 结论

- 页面读的是数据库缓存后的 markdown 文本
- 不是直接读仓库里的 md 文件

---

## 4. 右侧基因和字段来自哪里

在 `PaperDetail.tsx` 中：

- gene 卡片来自 `genes`
- 单个字段内容来自 `gene.gene_data`
- AI 验证结果来自 `gene.auto_verification`
- 验证统计来自 `gene.auto_stats`

所以用户在右侧看到的基因字段，不是前端写死的，而是数据库里每条 gene 的 JSON 数据。

---

## 5. 标注是怎么保存的

在 `PaperDetail.tsx` 中，用户点“正确 / 错误 / 修改”后，会把标注写入：

- Supabase `annotations` 表

保存的主要字段包括：

- `gene_id`
- `field_name`
- `expert_verdict`
- `corrected_value`
- `comment`
- `annotator_id`

但当前前端实际传的是：

- `annotator_id: null`

### 这意味着

- 标注内容在存
- 但“是谁改的”没有可靠落地

---

## 6. 保存后页面怎么更新

字段标注保存成功后，前端会调用 `refreshAnnotations()`：

- 再次从 `annotations` 表拉取当前论文所有 gene 的标注

所以当前刷新逻辑是：

- **保存后主动重拉**

而不是：

- **数据库变了就自动推送**

---

## 7. 为什么别人改了你这里不会立刻出现

因为当前代码没有 Realtime 订阅。

也就是没有：

- 监听 `annotations` 表变化
- 收到变化后自动更新界面

因此现状是：

1. 别人把标注写进数据库；
2. 数据库里已经有了；
3. 但你当前页面不会自动知道；
4. 你刷新页面或重新拉取后才看得到。

---

## 8. Metadata 标注目前是什么状态

在 `PaperDetail.tsx` 里，metadata 区域目前有：

- Title
- Journal
- DOI

这些操作现在主要保存在组件本地状态 `metaAnnotations` 中。

也就是说当前 metadata 标注：

- 页面里有交互
- 但还没有像 gene field annotation 一样正式入库

这也是当前系统需要后续补齐的地方之一。