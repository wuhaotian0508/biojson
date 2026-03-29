# Git 分支与合并 常用操作指南

## 目录

1. [日常操作（最常用）](#1-日常操作最常用)
2. [分支基础](#2-分支基础)
3. [合并方式对比](#3-合并方式对比)
4. [Merge 合并](#4-merge-合并)
5. [Rebase 变基](#5-rebase-变基)
6. [解决冲突](#6-解决冲突)
7. [Stash 暂存](#7-stash-暂存)
8. [Force Push](#8-force-push)
9. [常见场景速查](#9-常见场景速查)

---

## 1. 日常操作（最常用）

```bash
# 改了文件后提交并推送
git add .                        # 暂存所有改动
git commit -m "描述你做了什么"     # 提交
git push origin main             # 推送到远程

# 拉取远程最新代码
git pull origin main             # 拉取并合并

# 查看状态
git status                       # 查看哪些文件改了
git log --oneline -10            # 查看最近 10 条提交
git diff                         # 查看未暂存的改动
```

---

## 2. 分支基础

### 什么是分支？

分支就是一条独立的开发线。比如：
- `main`：主分支，稳定代码
- `feature/rag`：开发 RAG 功能的分支
- `pr-review`：学长的 PR 分支

### 基本操作

```bash
# 查看所有分支
git branch           # 本地分支
git branch -a        # 包括远程分支

# 创建新分支
git branch feature/rag

# 切换分支
git checkout feature/rag
# 或者（更推荐）
git switch feature/rag

# 创建并切换（一步到位）
git checkout -b feature/rag
# 或者
git switch -c feature/rag

# 删除分支
git branch -d feature/rag       # 已合并的分支
git branch -D feature/rag       # 强制删除（未合并也删）

# 查看分支图
git log --oneline --graph --all
```

---

## 3. 合并方式对比

Git 有三种主要的合并方式：

| 方式 | 命令 | 历史线 | 适合场景 |
|------|------|--------|----------|
| **Fast-forward** | `git merge --ff-only` | 一条直线 ✅ | 分支没有分叉 |
| **Merge commit** | `git merge` | 有分叉汇合点 | 保留分支历史 |
| **Rebase** | `git rebase` | 一条直线 ✅ | 想要干净的线性历史 |

### 图示对比

**Fast-forward（快进合并）**：
```
合并前：                    合并后：
main: A - B                main: A - B - C - D
              \
feature:       C - D
```

**Merge commit（合并提交）**：
```
合并前：                    合并后：
main: A - B                main: A - B - - - - E (merge commit)
              \                        \       /
feature:       C - D               C - D
```

**Rebase（变基）**：
```
合并前：                    合并后：
main: A - B - E            main: A - B - E - C' - D'
              \
feature:       C - D
```

---

## 4. Merge 合并

### 4.1 Fast-forward merge（推荐，保持直线）

```bash
# 前提：feature 是从 main 最新位置分出来的，main 没有新提交
git checkout main
git merge --ff-only feature/rag
```

如果 main 有新提交（分叉了），`--ff-only` 会报错，这时需要先 rebase。

### 4.2 普通 merge（产生 merge commit）

```bash
git checkout main
git merge feature/rag
# 会自动创建一个 merge commit
```

### 4.3 Squash merge（把多个 commit 合成一个）

```bash
git checkout main
git merge --squash feature/rag
git commit -m "feat: 添加 RAG 功能"
# feature 分支的所有 commit 被压缩成一个
```

---

## 5. Rebase 变基

### 5.1 基本 rebase

把 feature 分支的基底移到 main 的最新位置：

```bash
git checkout feature/rag
git rebase main
# 现在 feature 的 commit 就像是从 main 最新位置开始的
# 然后可以 fast-forward merge
git checkout main
git merge --ff-only feature/rag
```

### 5.2 交互式 rebase（修改/重排/合并 commit）

```bash
git rebase -i HEAD~3   # 修改最近 3 个 commit
```

会打开编辑器：
```
pick abc1234 第一个提交
pick def5678 第二个提交
pick ghi9012 第三个提交
```

可用的操作：
| 命令 | 作用 |
|------|------|
| `pick` | 保留这个 commit |
| `reword` | 保留但修改 commit message |
| `edit` | 暂停让你修改内容 |
| `squash` | 和上一个 commit 合并 |
| `fixup` | 和上一个合并但丢弃 message |
| `drop` | 删除这个 commit |

**交换顺序**：直接调换行的顺序即可。

### 5.3 用脚本自动交互式 rebase

```bash
# 交换最近两个 commit 的顺序
GIT_SEQUENCE_EDITOR="sed -i '1{h;d}; 2{p;x}'" git rebase -i HEAD~2
```

---

## 6. 解决冲突

### 冲突长什么样

```
<<<<<<< HEAD
你的代码
=======
别人的代码
>>>>>>> feature/rag
```

### 解决方法

**方法一：手动编辑**
打开冲突文件，删除 `<<<<<<<`, `=======`, `>>>>>>>` 标记，保留你想要的代码。

**方法二：选择某一方的版本**
```bash
# 选择当前分支的版本（我的）
git checkout --ours 文件名

# 选择合并进来的版本（别人的）
git checkout --theirs 文件名
```

**方法三：批量处理**
```bash
# 所有冲突文件都用我的版本
git checkout --ours .

# 所有冲突文件都用别人的版本
git checkout --theirs .
```

**解决后标记已解决**：
```bash
git add 冲突文件
git merge --continue    # 如果是 merge 冲突
# 或
git rebase --continue   # 如果是 rebase 冲突
```

### ⚠️ ours/theirs 在不同场景下含义不同！

| 场景 | `--ours` | `--theirs` |
|------|----------|------------|
| `git merge` | 当前分支（main） | 合并进来的分支（feature） |
| `git rebase` | rebase 到的基底 | 正在应用的 commit |
| `git stash pop` | 当前分支 | stash 中的内容 |

> 💡 简单记忆：rebase 时 ours/theirs 是**反的**！

---

## 7. Stash 暂存

当你正在写代码，突然需要切分支或拉取代码：

```bash
# 暂存当前改动
git stash                                    # 暂存已跟踪文件的改动
git stash --include-untracked                # 连新文件一起暂存
git stash -m "描述信息"                       # 带描述
git stash --include-untracked -m "描述信息"   # 完整版

# 查看暂存列表
git stash list

# 恢复暂存
git stash pop           # 恢复并删除这条 stash
git stash apply         # 恢复但保留 stash（可以多次使用）
git stash pop stash@{2} # 恢复指定的 stash

# 删除 stash
git stash drop          # 删除最新的 stash
git stash clear         # 清空所有 stash
```

---

## 8. Force Push

### 什么时候需要 force push？

当你用 `rebase` 改写了已经 push 过的历史时，普通 `git push` 会被拒绝。

### 两种 force push

```bash
# 安全版：如果远程有你不知道的新提交，会拒绝
git push --force-with-lease origin main

# 强制版：无条件覆盖远程（慎用！）
git push --force origin main
```

### 危害

| 风险 | 说明 |
|------|------|
| 覆盖别人提交 | 如果别人在你 push 之前推了新 commit，会被覆盖 |
| 别人需要重新同步 | 其他人 `git pull` 会遇到问题 |

### 建议

- 优先用 `--force-with-lease`
- 只在你确定没有人同时在推送时使用
- 个人项目或个人分支可以放心用
- 团队共享分支要**提前通知**

---

## 9. 常见场景速查

### 场景 1：正常开发提交

```bash
git add .
git commit -m "feat: 添加新功能"
git push origin main
```

### 场景 2：拉取远程最新代码

```bash
git pull origin main
# 等同于：
git fetch origin
git merge origin/main
```

### 场景 3：合并别人的 PR（保持直线）

```bash
git stash --include-untracked            # 暂存本地改动
git merge --ff-only pr-review            # 快进合并
git stash pop                            # 恢复本地改动
# 解决可能的冲突后
git add . && git commit && git push
```

### 场景 4：想要干净的线性历史

```bash
# 在 feature 分支上
git rebase main
# 切回 main
git checkout main
git merge --ff-only feature
```

### 场景 5：撤销最近的 commit（保留代码）

```bash
git reset --soft HEAD~1   # 撤销 commit，代码变为已暂存状态
git reset HEAD~1          # 撤销 commit，代码变为未暂存状态
git reset --hard HEAD~1   # 撤销 commit 并丢弃代码（危险！）
```

### 场景 6：查看某个文件的历史

```bash
git log --oneline -- 文件路径
git log -p -- 文件路径          # 带 diff
```

### 场景 7：暂时回到某个旧版本看看

```bash
git checkout abc1234        # 进入 detached HEAD 状态
# 看完了回来
git checkout main
```

---

## 常用命令速查表

| 操作 | 命令 |
|------|------|
| 查看状态 | `git status` |
| 查看历史 | `git log --oneline --graph -20` |
| 添加文件 | `git add .` |
| 提交 | `git commit -m "信息"` |
| 推送 | `git push origin main` |
| 拉取 | `git pull origin main` |
| 暂存 | `git stash --include-untracked` |
| 恢复暂存 | `git stash pop` |
| 查看分支 | `git branch -a` |
| 切换分支 | `git switch 分支名` |
| 合并 | `git merge --ff-only 分支名` |
| 变基 | `git rebase main` |
| 解决冲突后继续 | `git add . && git rebase --continue` |
| 放弃操作 | `git merge --abort` 或 `git rebase --abort` |
