# Git 合并学长 PR 的完整过程记录

> 2026-03-29 实际操作记录

## 背景

- 我的 `main` 分支有自己的开发内容
- 学长提交了一个 PR（`pr-review` 分支），改动了 extractor 模块
- 目标：把学长的 PR 合并进来，**main 保持一条直线**，学长的 commit 在最新位置

## 操作步骤

### 第一步：暂存本地未提交的改动

```bash
git stash --include-untracked -m "backup: local changes before merging"
```

> `--include-untracked` 会把新建的文件也暂存起来，不然 stash 只保存已跟踪文件的改动。

### 第二步：Fast-forward merge 学长的 PR 分支

```bash
git merge --ff-only pr-review
```

> `--ff-only` 确保只做快进合并（不产生 merge commit），保持历史一条线。
> 如果 main 和 pr-review 有分叉，这个命令会失败，需要用 rebase 代替。

结果：
```
Updating cbf0c51..c4d7365
Fast-forward
```

### 第三步：恢复本地改动

```bash
git stash pop
```

结果：5 个 rag 文件有冲突（因为学长也改了 rag 模块）

### 第四步：解决冲突

冲突文件：`rag/README.md`, `rag/config.py`, `rag/generator.py`, `rag/main.py`, `rag/retriever.py`

因为 rag 模块以我的版本为准：
```bash
for f in rag/README.md rag/config.py rag/generator.py rag/main.py rag/retriever.py; do
    git checkout --theirs "$f"   # stash pop 中 theirs = stash 中的版本（我的）
    git add "$f"
done
```

> ⚠️ 注意 `--ours` 和 `--theirs` 的含义：
> - 在 `stash pop` 冲突中：`--ours` = 当前分支，`--theirs` = stash 中的内容
> - 在 `rebase` 冲突中：`--ours` = 正在 rebase 到的基底，`--theirs` = 正在应用的 commit

### 第五步：清理硬编码 API Key

把 `rag/config.py` 和 `ragtry/config.py` 中的明文 API Key 替换为空字符串：
```python
# 修改前
JINA_API_KEY = os.getenv("JINA_API_KEY", "jina_dcf56a89c4724b...")
# 修改后
JINA_API_KEY = os.getenv("JINA_API_KEY", "")
```

### 第六步：提交

```bash
git add -A
# 先把不需要的 backup 目录移出暂存区
git reset HEAD data/backup_20260329_094816/
# 把 backup 加入 .gitignore
echo "data/backup_*/" >> .gitignore

git commit -m "feat: 更新 rag 系统 + 添加验证数据 + 清理 API key"
```

### 第七步：调整 commit 顺序（Rebase）

此时历史是：
```
* 737ab64 我的改动（最新）
* c4d7365 学长的 PR
* cbf0c51 原来的 main
```

我们想要学长的 PR 在最新位置：
```bash
# 交互式 rebase，交换两个 commit 的顺序
GIT_SEQUENCE_EDITOR="sed -i '1{h;d}; 2{p;x}'" git rebase -i cbf0c51
```

这会把 rebase todo 列表中的第 1 行和第 2 行交换。

又遇到冲突，分两轮解决：
```bash
# 第一轮：我的 commit 先应用
git checkout --theirs rag/README.md rag/config.py rag/generator.py rag/main.py rag/retriever.py
git add rag/README.md rag/config.py rag/generator.py rag/main.py rag/retriever.py
GIT_EDITOR=true git rebase --continue

# 第二轮：学长的 commit 叠上去
git checkout --theirs rag/README.md rag/config.py rag/generator.py rag/main.py rag/retriever.py
git add rag/README.md rag/config.py rag/generator.py rag/main.py rag/retriever.py
GIT_EDITOR=true git rebase --continue
```

### 第八步：Force Push

因为 rebase 改写了历史，需要 force push：
```bash
git fetch origin                    # 先更新远程信息
git push --force-with-lease origin main  # 安全的 force push
# 如果 --force-with-lease 因为 stale info 失败：
git push --force origin main
```

### 最终结果

```
* 98f9f3c refactor(extractor): ...  ← 学长的 PR（最新）
* 7587fc5 feat: 更新 rag 系统...    ← 我的改动
* cbf0c51 chore: remove tracked...  ← 原来的 main
```

✅ main 保持一条直线，学长的 PR 在最新位置。

---

## 后续提交

现在一切已经同步，后续正常操作即可：

```bash
git add .
git commit -m "你的提交信息"
git push origin main
```

不需要再 force push 了！
