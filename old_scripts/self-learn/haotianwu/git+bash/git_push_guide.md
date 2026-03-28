# 将 biojson 项目推送到 GitHub 仓库指南

> 本指南将帮助你将 `/data/haotianwu/biojson` 项目推送到 GitHub 上的 `wuhaotian0508/biojson` 仓库。
> 前提条件：GitHub SSH 密钥已配置完成。

---

## 第一步：在 GitHub 上创建远程仓库

1. 打开浏览器，登录 [GitHub](https://github.com)
2. 点击右上角 **"+"** → **"New repository"**
3. 填写仓库信息：
   - **Repository name**: `biojson`
   - **Description**（可选）: 简单描述项目
   - **Visibility**: 选择 `Public`（公开）或 `Private`（私有）
   - ⚠️ **不要勾选** "Add a README file"、".gitignore" 或 "Choose a license"（保持空仓库，避免后续合并冲突）
4. 点击 **"Create repository"**

---

## 第二步：在本地初始化 Git 仓库并推送

打开终端，依次执行以下命令：

### 2.1 进入项目目录

```bash
cd /data/haotianwu/biojson
```

### 2.2 配置 Git 用户信息（仅对该仓库生效）

```bash
git config --global user.name "wuhaotian0508"
git config --global user.email "wuhaotian0508@sjtu.edu.cn"
```

> 💡 如果只想对当前仓库设置（不影响全局），把 `--global` 去掉即可。但需要先执行 `git init` 之后才能用局部配置。

### 2.3 初始化 Git 仓库

```bash
git init
```

这会在 `biojson/` 目录下创建一个 `.git/` 隐藏文件夹，标志着这个目录已经成为一个 Git 仓库。

### 2.4 将所有文件添加到暂存区

```bash
git add .
```

> 💡 `.gitignore` 文件中已经配置了忽略规则（如 `.env`、`__pycache__/`、`/self-learn/` 等），所以这些文件不会被添加到暂存区。

### 2.5 查看暂存区状态（可选，建议检查）

```bash
git status
```

确认将要提交的文件列表是否正确。你应该看到类似以下内容：

```
new file:   .gitignore
new file:   configs/nutri_plant.json
new file:   configs/nutri_plant.txt
new file:   scripts/md_to_json.py
...
```

> ⚠️ 注意：`self-learn/` 目录已被 `.gitignore` 忽略，不会出现在列表中。如果你希望也把 `self-learn/` 提交上去，需要先修改 `.gitignore`，将 `/self-learn/` 那一行删除或注释掉。

### 2.6 提交到本地仓库

```bash
git commit -m "Initial commit: biojson project"
```

### 2.7 重命名默认分支为 main（可选但推荐）

```bash
git branch -M main
```

> GitHub 默认主分支名为 `main`，而 `git init` 默认创建的可能是 `master`。执行此命令统一为 `main`。

### 2.8 添加远程仓库（使用 SSH 地址）

```bash
git remote add origin git@github.com:wuhaotian0508/biojson.git
```

### 2.9 推送到 GitHub

```bash
git push -u origin main
```

> `-u` 参数会将本地 `main` 分支与远程 `origin/main` 分支关联，之后再推送只需 `git push` 即可。

---

## 完整命令速查（可直接复制执行）

```bash
cd /data/haotianwu/biojson

# 配置用户信息
git config --global user.name "wuhaotian0508"
git config --global user.email "wuhaotian0508@sjtu.edu.cn"

# 初始化并提交
git init
git add .
git status          # 检查一下要提交的文件
git commit -m "Initial commit: biojson project"

# 关联远程仓库并推送
git branch -M main
git remote add origin git@github.com:wuhaotian0508/biojson.git
git push -u origin main
```

---

## 后续日常使用

当你修改了代码后，想要再次推送更新到 GitHub：

```bash
cd /data/haotianwu/biojson

# 查看哪些文件被修改了
git status

# 添加修改的文件到暂存区
git add .
# 或者只添加特定文件：git add scripts/md_to_json.py

# 提交
git commit -m "描述你做了什么修改"

# 推送
git push
```

---

## 多人协作时，作为仓库维护者的你该怎么做

这一节是**专门写给 `wuhaotian0508` 的**。

如果这个仓库后面要和 `scarlettLi` 一起协作，建议你不要把 GitHub 只当成“自己备份代码的地方”，而是把它当成你们两个人共同开发的中心仓库。

你的角色更适合是：

- **主仓库维护者**
- **`main` 分支管理者**
- **Pull Request 审查和合并人**

也就是说：

- 你负责维护 `wuhaotian0508/biojson`
- `scarlettLi` 在自己的功能分支上开发
- 她开发完后提 PR
- 你检查无误后再合并到 `main`

这样会比两个人都直接往 `main` 里推送安全很多。

### 1. 先把 `scarlettLi` 加为仓库协作者

在 GitHub 仓库页面中操作：

1. 进入 `wuhaotian0508/biojson`
2. 点击 **Settings**
3. 找到 **Collaborators** 或 **Manage access**
4. 点击 **Add people**
5. 输入 `scarlettLi`
6. 发送邀请，等待对方接受

完成后，`scarlettLi` 就可以向这个仓库推送她自己的分支。

### 2. 你自己尽量也不要直接在 `main` 上长期开发

即使你是仓库拥有者，也建议你养成下面的习惯：

```bash
git checkout main
git pull origin main
git checkout -b feature/wuhaotian-xxx
```

也就是说：

- `main` 只保留稳定版本
- 你自己的新功能也尽量在分支里写
- 写完后再合并回 `main`

这样以后如果你们同时改同一个模块，会更容易排查和回滚。

### 3. 每次开始工作前，先同步最新代码

你在本地开始改代码前，建议先执行：

```bash
cd /data/haotianwu/biojson
git checkout main
git pull origin main
```

这样可以避免你基于旧版本开发。

### 4. 当 `scarlettLi` 提交 PR 后，你该怎么处理

推荐流程：

1. 打开 GitHub 上的 Pull Request
2. 看她改了哪些文件
3. 看改动是否和任务一致
4. 确认没有误删、误改、临时文件
5. 没问题后点击 **Merge pull request**

如果你想先在本地看看她的分支，也可以：

```bash
git fetch origin
git checkout -b review-scarlettLi origin/feature/scarlettLi-xxx
```

检查完后再切回主分支：

```bash
git checkout main
git pull origin main
```

### 5. 合并后，你要提醒双方同步

PR 合并完成后，你自己和 `scarlettLi` 都应该执行：

```bash
git checkout main
git pull origin main
```

这样双方本地代码才会保持一致。

### 6. 你们两个人最推荐的协作模式

对于现在这个项目，最推荐你采用：

```text
wuhaotian0508 管主仓库和 main
scarlettLi 在 feature/scarlettLi-xxx 分支开发
完成后发 Pull Request
wuhaotian0508 审查并合并
```

一句话总结：

> **你负责守住 `main`，对方负责在分支开发，通过 PR 合并。**

这样是最适合两人协作、也最不容易出问题的方式。

---

## 常见问题

### Q1: 推送时提示 `Permission denied (publickey)`

说明 SSH 密钥未正确配置。可以用以下命令测试：

```bash
ssh -T git@github.com
```

成功的话会看到：`Hi wuhaotian0508! You've successfully authenticated...`

### Q2: 想把 `self-learn/` 目录也提交上去

编辑 `.gitignore` 文件，找到 `/self-learn/` 这一行，删除它或在前面加 `#` 注释掉：

```gitignore
# /self-learn/
```

然后重新 `git add .` 并提交推送即可。

### Q3: 提交了不该提交的文件怎么办？

```bash
# 从 Git 追踪中移除（不删除本地文件）
git rm --cached <文件名>
git commit -m "Remove tracked file"
git push
```

### Q4: 想查看提交历史

```bash
git log --oneline
```

---

## 附：项目目录结构说明

```
biojson/
├── .gitignore          # Git 忽略规则
├── configs/            # 配置文件
├── json/               # 输出的 JSON 文件
├── md/                 # 输入的 Markdown 文件
├── reports/            # 验证报告
├── scripts/            # 核心脚本
│   ├── md_to_json.py
│   ├── run.sh
│   ├── token_tracker.py
│   └── verify_response.py
├── self-learn/         # 学习笔记（默认被 .gitignore 忽略）
└── test.ipynb          # 测试 notebook
```
