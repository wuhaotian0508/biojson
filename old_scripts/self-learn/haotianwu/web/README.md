# BioJSON Web 文档总览

这个目录用于记录 biojson 项目 web 端的当前实现、数据存放位置、协作标注现状，以及后续要做的用户追踪方案。

## 你最关心的结论

1. **当前“用户名”** 主要保存在浏览器本地 `localStorage`，不是正式认证系统。
2. **论文、基因、标注数据** 存在 **Supabase** 数据库中。
3. **别人的标注** 也存在 Supabase，但当前前端 **没有实时订阅**，所以不是实时回传。
4. **数据库设计本身支持按用户追踪**，因为 `annotations` 表里有 `annotator_id`。
5. **当前前端实现还没有把本地用户名真正绑定为数据库里的真实用户身份**，所以“按用户名可靠追踪”还没有完全落地。

## 建议阅读顺序

1. `storage_map.md`：先看“网站和用户信息都存哪里”
2. `web_setup.md`：再看当前 web 的整体设置
3. `data_flow.md`：再看页面如何读写数据
4. `tracking_plan.md`：最后看为什么现在还不能完整追踪，以及应该怎么改

## 对应代码位置

- Supabase 客户端：`web/src/lib/supabase.ts`
- 本地用户名：`web/src/lib/UserContext.tsx`
- 首页论文列表：`web/src/app/page.tsx`
- 论文详情数据读取：`web/src/app/papers/[slug]/page.tsx`
- 标注主界面：`web/src/app/papers/[slug]/PaperDetail.tsx`
- 数据库结构：`database/schema.sql`