# BioJSON 重新部署（Redeploy）完整指南

> 当你修改了代码（前端页面、后端逻辑、数据库数据等）后，需要重新部署让线上版本同步更新。
> 本指南覆盖：**Vercel 首次配置**、**前端重新部署**、**Supabase 数据重新导入**、**常见问题排查**。

---

## 📋 目录

1. [整体架构理解](#1-整体架构理解)
2. [Vercel 首次配置清单（必看）](#2-vercel-首次配置清单必看)
3. [日常 Redeploy 操作](#3-日常-redeploy-操作)
4. [Supabase 数据重新导入](#4-supabase-数据重新导入)
5. [完整 Redeploy 流程](#5-完整-redeploy-流程)
6. [常见问题排查](#6-常见问题排查)

---

## 1. 整体架构理解

```
┌──────────────────────────────────────────────────────────────┐
│                  你的本地服务器                                │
│              /data/haotianwu/biojson                          │
│                                                              │
│  ① bash scripts/run.sh                                      │
│     → 调用 Claude API（需要 OPENAI_API_KEY）                 │
│     → 从论文 MD 提取 JSON + 验证报告                          │
│                                                              │
│  ② python scripts/import_to_supabase.py                     │
│     → 把 JSON + MD + 报告上传到 Supabase 云数据库             │
│     → 需要 SUPABASE_SERVICE_ROLE_KEY                         │
└──────────────────────┬───────────────────────────────────────┘
                       │ 数据存到了云数据库
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                    Supabase 云数据库                           │
│         （数据已经在这里，随时可被前端读取）                     │
└──────────────────────┬───────────────────────────────────────┘
                       │ 前端只「读取」数据
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                 Vercel（前端网页）                              │
│                                                              │
│  只需要两个环境变量：                                          │
│    NEXT_PUBLIC_SUPABASE_URL     → 数据库地址                  │
│    NEXT_PUBLIC_SUPABASE_ANON_KEY → 只读公钥                   │
│                                                              │
│  ❌ 不需要 Claude API Key（不做 AI 提取，提取在本地完成）       │
│  ❌ 不需要 SERVICE_ROLE_KEY（不写数据库，导入在本地完成）        │
└──────────────────────────────────────────────────────────────┘
```

**关键结论：** Vercel 上跑的前端只是一个展示面板，从 Supabase 读数据显示。所有 AI 提取和数据导入都在本地完成。

---

## 2. Vercel 首次配置清单（必看）

> ⚠️ **你 Vercel 上有 3 个重复项目**（biojson-2yhf、生物信息素、biojson-pgdv），都关联了同一个 GitHub 仓库。建议只保留一个，删掉其他的，避免混乱。
> 删除方法：项目 Settings → 最底部 Advanced → Delete Project

### 2.1 Build and Deployment 设置

打开 Vercel Dashboard → 你的项目 → **Settings → Build and Deployment**

| 设置项 | 正确值 | 说明 |
|--------|--------|------|
| **Framework Preset** | **Next.js** | ⚠️ 不能选 Other！否则 Vercel 不知道怎么构建 |
| **Build Command** | 留空（不要 Override） | 默认使用 `npm run build` 或 `next build` |
| **Output Directory** | 留空（不要 Override） | 默认 Next.js default |
| **Install Command** | 留空（不要 Override） | 默认 `npm install` |
| **Root Directory** | **`web`** | ⚠️ 必须填！Next.js 代码在 web/ 子目录里 |
| **Node.js Version** | `22.x` 或 `24.x`（都行） | |

> 每个设置项修改后都要点对应区块右下角的 **Save** 按钮！

### 2.2 Environment Variables 设置

打开 Vercel Dashboard → 你的项目 → **Settings → Environment Variables**

**只需要添加这 2 个变量：**

| Key | Value | 来源 |
|-----|-------|------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://vqcfjnwyxvayygxtaons.supabase.co` | Supabase Dashboard → Settings → API → URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZxY2Zqbnd5eHZheXlneHRhb25zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MDE0ODQsImV4cCI6MjA4OTM3NzQ4NH0.0oErR07B644NmWX2ck48po9LQNVXgpxlQkXT8Y1aquI` | Supabase Dashboard → Settings → API → anon public key |

Environment 选 **All Environments**（Production + Preview + Development 都勾上）。

**以下变量 ❌ 不要 ❌ 添加到 Vercel：**
- `OPENAI_API_KEY` — 这是本地跑 Pipeline 用的
- `SUPABASE_SERVICE_ROLE_KEY` — 这是管理员密钥，暴露在前端会有安全风险
- 所有 `FALLBACK_*` 变量

> 这些值也记录在本地 `.env` 文件中，方便查阅（`.env` 不会上传 GitHub）。

### 2.3 Git 设置

打开 Vercel Dashboard → 你的项目 → **Settings → Git**

确认关联的是正确的 GitHub 仓库：`wuhaotian0508/biojson`，Production Branch 为 `main`。

### 2.4 配置完成后 Redeploy

1. 进入 **Deployments** 标签页
2. 找到最近一次部署，点击右侧的 **⋮**（三个点）
3. 选择 **Redeploy**
4. 等待 1-2 分钟，状态变为 **Ready**（绿色）即成功
5. 点击部署的域名访问，确认页面正常显示

---

## 3. 日常 Redeploy 操作

### 什么时候需要 Redeploy？

| 修改内容 | 需要做什么 |
|---------|-----------|
| 修改了 `web/` 下的前端代码 | git push 自动触发 Vercel 部署 |
| 修改了 Vercel 上的环境变量 | 手动 Redeploy |
| 重新跑了 Pipeline，生成新 JSON | 只需重新导入 Supabase，不需要 Redeploy |
| 修改了数据库 Schema | Supabase 执行 SQL + 可能需要重新导入 |

### 方式一：推送代码自动触发（最常用 ✅）

```bash
cd /data/haotianwu/biojson
git add .
git commit -m "fix: 更新论文详情页样式"
git push
# Vercel 自动开始构建部署，1-2 分钟完成
```

### 方式二：Vercel Dashboard 手动触发

1. 打开 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击你的项目 → **Deployments**
3. 最近部署 → **⋮** → **Redeploy**

### 方式三：Vercel CLI

```bash
cd /data/haotianwu/biojson/web
npx vercel --prod    # 部署到生产环境
```

---

## 4. Supabase 数据重新导入

当你重新跑了 Pipeline 生成新数据后：

```bash
cd /data/haotianwu/biojson

# 确认 .env 中有 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY
python scripts/import_to_supabase.py
```

导入完成后，**不需要 Redeploy Vercel**。前端是实时从 Supabase 读数据的，刷新页面即可看到（ISR 缓存最多等 60 秒）。

---

## 5. 完整 Redeploy 流程

当你做了全面修改（代码 + 数据都改了），按以下顺序：

```bash
# Step 1: 重跑 Pipeline（如果有新论文）
bash scripts/run.sh              # 增量模式
# 或
bash scripts/run.sh rerun        # 强制全部重跑

# Step 2: 导入数据到 Supabase
python scripts/import_to_supabase.py

# Step 3: 本地测试（可选）
bash scripts/dev.sh --kill       # 杀掉旧进程后启动
# 浏览器打开 http://localhost:3000 检查

# Step 4: 推送代码（自动触发 Vercel 部署）
git add .
git commit -m "update: 新增论文数据 + 前端优化"
git push

# Step 5: 等 1-2 分钟，到 Vercel Dashboard 确认部署成功
```

### 流程图

```
修改代码 / 新增论文
        │
        ├── 有新论文要提取？
        │       │
        │       ▼
        │   bash scripts/run.sh
        │       │
        │       ▼
        │   python scripts/import_to_supabase.py
        │       │
        │       ▼
        │   （数据已更新到 Supabase，刷新网页即可看到）
        │
        ├── 修改了前端代码？
        │       │
        │       ▼
        │   git add . && git commit && git push
        │       │
        │       ▼
        │   Vercel 自动部署（1-2 分钟）
        │       │
        │       ▼
        │   ✅ 线上更新完成
        │
        └── 只改了 Vercel 环境变量？
                │
                ▼
            Vercel Dashboard → Deployments → Redeploy
```

---

## 6. 常见问题排查

### Q1: 访问网站显示 404

**检查清单（按顺序排查）：**

1. **Root Directory 是否设为 `web`？**
   - Settings → Build and Deployment → Root Directory → 填 `web` → Save

2. **Framework Preset 是否选了 Next.js？**
   - Settings → Build and Deployment → Framework Preset → 选 `Next.js`（不是 Other！）→ Save

3. **构建是否成功？**
   - Deployments → 点击最近部署 → 查看 Build Logs
   - 如果状态是 Error（红色），看日志找错误原因

4. **是否 Redeploy 了？**
   - 修改设置后必须 Redeploy 才会生效

5. **是否配置了环境变量？**
   - Settings → Environment Variables → 确认有 `NEXT_PUBLIC_SUPABASE_URL` 和 `NEXT_PUBLIC_SUPABASE_ANON_KEY`

6. **是否访问了正确的域名？**
   - 你有 3 个项目，确认访问的是你配置好的那个项目的域名

### Q2: 本地 `bash scripts/dev.sh` 报 lock 错误

```
⨯ Unable to acquire lock at web/.next/dev/lock
```

说明之前有 next dev 进程没关掉。解决方法：

```bash
# 方式一：用 --kill 参数自动杀旧进程
bash scripts/dev.sh --kill

# 方式二：手动杀掉
kill -9 $(lsof -ti :3000) 2>/dev/null
rm -f web/.next/dev/lock
bash scripts/dev.sh
```

### Q3: Vercel 构建报错 TypeScript 错误

先在本地测试构建：

```bash
cd web
npm run build
```

如果本地也报错，先修复 TypeScript 错误再推送。

### Q4: 数据导入成功但网页看不到

- 按 `Ctrl + Shift + R` 强制刷新