# SOP 按钮消失 / 功能异常排查指南

## 问题现象
提问后回答末尾不再弹出「基因编辑器 + 生成 CRISPR 实验方案 SOP」按钮。

## 快速排查流程

### 1. 清除浏览器缓存（最常见原因）
前端静态文件（`app.js`、`style.css`）被浏览器缓存，导致页面使用旧版代码。

**操作：**
- **Chrome/Edge**: `Ctrl+Shift+R`（Mac: `Cmd+Shift+R`）强制刷新
- 或打开 DevTools → Network → 勾选 `Disable cache`，再刷新

### 2. 重启服务器进程
Python 代码改动后需要重启 Flask 进程才能生效。

**操作（SSH 到服务器后）：**
```bash
# 方法一：通过 run.sh 重启（推荐，会自动杀旧进程）
cd /root/code/biojson/rag/web
bash run.sh

# 方法二：手动杀进程再启动
lsof -ti:5000 | xargs kill -9   # 杀掉占用 5000 端口的进程
sleep 1
cd /root/code/biojson/rag/web
export PYTHONUNBUFFERED=1
python -u app.py
```

**如果在 tmux 中运行：**
```bash
# 进入 tmux session
tmux attach -t 0
# Ctrl+C 停掉旧进程，然后：
cd /root/code/biojson/rag/web && bash run.sh
# Ctrl+B 再按 D 脱离 tmux
```

### 3. 确认代码同步到正确位置
服务器上实际运行的代码在 `/root/code/biojson/`（不是 `/code/biojson/`）。

**同步单个文件：**
```bash
sshpass -p '密码' rsync -avz --relative \
  /data/haotianwu/biojson/./rag/path/to/file \
  root@39.108.180.113:/root/code/biojson/
```

**同步整个 rag 目录：**
```bash
sshpass -p '密码' rsync -avz --progress \
  --exclude='__pycache__' --exclude='*.pyc' \
  /data/haotianwu/biojson/rag/ \
  root@39.108.180.113:/root/code/biojson/rag/
```

> 注意：没有 sshpass 可用 expect，见下方示例。

### 4. 检查后端日志
```bash
# SSH 到服务器后查看实时日志
tail -f /tmp/biojson.log

# 或在 tmux 中直接看控制台输出
tmux attach -t 0
```

重点关注：
- `✅ 系统初始化完成` — 确认启动成功
- `Pipeline error` — 查询流程报错
- `extract_gene_names` 相关日志 — 基因检测失败

### 5. 检查前端事件流（浏览器 DevTools）
1. 打开 DevTools → Network → 过滤 `EventStream`
2. 发起一次查询
3. 查看 `/api/query` 的 SSE 事件流，确认是否收到 `genes_available` 事件

**正常流程：**
```
data: {"type": "searching", ...}
data: {"type": "sources", ...}
data: {"type": "text", "data": "..."}   ← 多条
data: {"type": "genes_available", "genes": ["GmFAD2", ...]}   ← 关键！
data: {"type": "done"}
```

如果 `genes_available` 事件缺失，说明后端未检测到基因名。

## 涉及的关键代码路径

| 环节 | 文件 | 关键函数/行 |
|------|------|-------------|
| 基因名正则检测 | `rag/skills/skill_loader.py` | `extract_gene_names()` — 正则 `_GENE_NAME_RE` |
| 生成后触发检测 | `rag/pipeline.py` | `_post_generate()` — 调用 extract 并 yield `genes_available` |
| 前端接收事件 | `rag/web/static/app.js` | `streamQuery()` 中 `data.type === 'genes_available'` 分支 |
| 前端渲染按钮 | `rag/web/static/app.js` | `renderExperimentButton()` — 检查 `state.genesAvailable` |
| SOP 模板 | `rag/skills/crispr_experiment/CRISPR_SpCas9_Gene_Editing_base.txt` | 模板内容（仅影响格式） |
| SOP 样式 | `rag/web/static/style.css` | `.experiment-sop-content` 相关样式（仅影响格式） |

## 按钮显示的前提条件
`renderExperimentButton()` 中的守卫条件（app.js）：
```js
if (!state.genesAvailable || state.experimentRunning || state.experimentDone) return;
```
按钮只在以下情况同时满足时显示：
1. `genesAvailable = true` — 后端发送了 `genes_available` 事件
2. `experimentRunning = false` — 没有正在运行的实验
3. `experimentDone = false` — 实验尚未完成

## 用 expect 代替 sshpass 的示例
本机没有 sshpass 时可用 expect：
```bash
expect -c '
set timeout 60
spawn rsync -avz --progress 本地路径 root@39.108.180.113:远程路径
expect {
    -re "yes/no" { send "yes\r"; exp_continue }
    -re "password:" { send "密码\r"; exp_continue }
    eof
}
'
```
