#!/bin/bash
# Vercel 构建脚本：将前端静态文件复制到 public/ 目录

set -e

echo "=== Building NutriMaster frontend for Vercel ==="

# 清理 & 创建目录
rm -rf public
mkdir -p public/static public/admin/static

# ---- 主站前端（rag/web/static/） ----
cp rag/web/static/index.html public/
cp rag/web/static/app.js     public/static/
cp rag/web/static/style.css  public/static/
cp rag/web/static/auth.js    public/static/
cp rag/web/static/marked.min.js   public/static/
cp rag/web/static/supabase.min.js public/static/

# 复制图片（logo 等）
for f in rag/web/static/*.png; do
  [ -f "$f" ] && cp "$f" public/static/
done

# ---- Admin 面板（admin/static/） ----
cp admin/static/index.html  public/admin/
cp admin/static/admin.js    public/admin/static/
cp admin/static/style.css   public/admin/static/

echo "=== Build complete: public/ ==="
ls -la public/
ls -la public/static/
ls -la public/admin/static/
