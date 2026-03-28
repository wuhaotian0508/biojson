# BioJSON 前端（web）提交与发布指南

> 本指南专门说明：当你只修改 `web/` 前端代码时，应该如何本地检查、提交 Git commit、推送到 GitHub，并让 Vercel 自动更新线上网页。

---

## 📋 目录

1. [什么时候使用这份指南](#1-什么时候使用这份指南)
2. [先强制关闭 3000 端口（如有需要）](#2-先强制关闭-3000-端口如有需要)
3. [web commit 标准流程](#3-web-commit-标准流程)
4. [推荐的 commit message 写法](#4-推荐的-commit-message-写法)
5. [提交前检查清单](#5-提交前检查清单)
6. [常见问题](#6-常见问题)

---

## 1. 什么时候使用这份指南

当你修改的是以下内容时，适合使用这份 `web commit` 指南：

- `web/src/app/` 页面代码
- `web/src/components/` 组件代码
- `web/src/lib/` 前端工具函数或类型定义
- `web/src/app/globals.css` 等样式文件
- `web/package.json`、`web/next.config.ts` 等前端配置

也就是说：**只要你主要改的是前端展示层，就按这份流程来做。**

---

## 2. 先强制关闭 3000 端口（如有需要）

如果你本地开发时发现 3000 端口被占用，或者 Next.js 启动时报 lock 错误，可以先执行以下命令。

### 方法一：直接强制杀掉 3000 端口（最直接）

```bash
kill -9 $(lsof -ti :3000) 2>/dev/null
rm -f /data/haotianwu/biojson/web/.next/dev/lock
```

### 方法二：使用项目自带脚本（更推荐）

```bash
cd /data/haotianwu/biojson
bash scripts/dev.sh --kill
```

> 推荐优先使用 `bash scripts/dev.sh --kill`，因为这是项目内已经约定好的方式。

---

## 3. web commit 标准流程

以下是最常用、最稳妥的前端提交流程。

### 3.1 进入项目根目录

```bash
cd /data/haotianwu/biojson
```

### 3.2 查看当前改了哪些文件

```bash
git status
```

如果你只想提交前端相关改动，应优先确认改动主要集中在：

- `web/`
- 少量相关文档（比如 `self-learn/`）

### 3.3 本地启动前端检查

```bash
cd /data/haotianwu/biojson
bash scripts/dev.sh --kill
```

然后打开浏览器访问：

```text
http://localhost:3000
```

确认页面样式、交互、数据展示都正常。

### 3.4 可选：先做一次生产构建检查

```bash
cd /data/haotianwu/biojson/web
npm run build
```

这一步很重要，因为有些代码本地 `dev` 能跑，但 `build` 时会报 TypeScript 或 ESLint 错误。

### 3.5 添加要提交的文件

#### 方式一：只添加前端目录（推荐）

```bash
cd /data/haotianwu/biojson
git add web
```

#### 方式二：前端 + 指定文档一起提交

```bash
cd /data/haotianwu/biojson
git add web self-learn/web_commit_guide.md
```

#### 方式三：如果你非常确定所有修改都应该提交

```bash
git add .
```

> ⚠️ 一般不建议无脑 `git add .`，因为容易把不想提交的文件一起加进去。

### 3.6 再次确认提交内容

```bash
git status
```

必要时可用：

```bash
git diff --cached
```

查看这次 commit 实际会提交什么。

### 3.7 提交 commit

```bash
git commit -m "fix: 修复论文列表页显示问题"
```

### 3.8 推送到 GitHub

```bash
git push
```

推送后，如果 Vercel 已正确连接 GitHub 仓库，通常会自动开始部署。

---

## 4. 推荐的 commit message 写法

为了后面看提交历史更清楚，建议 commit message 带上类型前缀。

### 常见前缀

- `feat:` 新功能
- `fix:` 修复 bug
- `style:` 样式调整
- `refactor:` 重构代码但不改变功能
- `docs:` 文档更新
- `chore:` 杂项维护

### 示例

```bash
git commit -m "feat: 新增论文详情页基因信息展示"
git commit -m "fix: 修复首页论文列表不刷新的问题"
git commit -m "style: 调整 Header 和卡片间距"
git commit -m "refactor: 拆分 PaperDetail 组件逻辑"
git commit -m "docs: 新增 web commit 使用指南"
```

如果这次修改比较综合，也可以写得稍微完整一点：

```bash
git commit -m "fix: 修复 Supabase 数据更新后前端未及时展示的问题"
```

---

## 5. 提交前检查清单

在 `git commit` 之前，建议你快速检查下面几项：

- [ ] 本地页面能正常打开（`http://localhost:3000`）
- [ ] 没有 3000 端口冲突
- [ ] `npm run build` 能通过（至少在重要修改后跑一次）
- [ ] 没把 `.env`、密钥、临时文件加进 commit
- [ ] `git status` 中的文件确实都是你想提交的
- [ ] commit message 能说明这次改了什么

---

## 6. 常见问题

### Q1: 3000 端口被占用怎么办？

```bash
kill -9 $(lsof -ti :3000) 2>/dev/null
rm -f /data/haotianwu/biojson/web/.next/dev/lock
```

或者：

```bash
cd /data/haotianwu/biojson
bash scripts/dev.sh --kill
```

---

### Q2: 我只想提交前端，不想把别的文件带上去

用下面这种方式：

```bash
git add web
git status
git commit -m "fix: 修复前端页面问题"
```

如果还想一起提交某篇文档，就单独加那篇：

```bash
git add web self-learn/web_commit_guide.md
```

---

### Q3: push 之后 Vercel 没更新怎么办？

先检查：

1. 这次是不是确实 push 成功了
2. Vercel 项目是否绑定了正确仓库
3. Vercel 的 Root Directory 是否设置为 `web`
4. Deployments 页面里是否出现新的部署记录

如果还是没更新，可以到 Vercel Dashboard 手动点：

**Deployments → 最近一次部署右侧 `⋮` → Redeploy**

---

### Q4: 本地正常，但线上构建失败怎么办？

先在本地执行：

```bash
cd /data/haotianwu/biojson/web
npm run build
```

如果本地 build 失败，先修复本地错误再 `git push`。

---

## 一套最常用的命令模板

```bash
cd /data/haotianwu/biojson

# 关闭旧的开发进程
bash scripts/dev.sh --kill

# 看看改了什么
git status

# 只提交前端
git add web

# 如果还要加文档
# git add web self-learn/web_commit_guide.md

# 再确认一遍
git status

# 提交
git commit -m "fix: 修复前端页面显示问题"

# 推送
git push
```

---

## 结论

以后只要你改的是前端页面，就记住这条主线：

**先本地跑通 → 再 `git add web` → 写清楚 commit message → `git push` → 看 Vercel 自动部署。**

这样会比每次 `git add .` 更安全，也更适合长期维护项目。