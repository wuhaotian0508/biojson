# GitHub 多人协作入门指南（wuhaotian0508 × scarlettLi）

> 本文档适合你和 `scarlettLi` 一起协作维护 GitHub 项目时使用。
> 这里默认主仓库为：`wuhaotian0508/biojson`
> 你是仓库维护者：`wuhaotian0508`，协作者是：`scarlettLi`。

---

## 一、什么是多人协作 GitHub

GitHub 多人协作，简单来说就是：

- 大家把代码放在同一个远程仓库里
- 每个人先在自己本地修改
- 修改完成后提交到各自分支
- 再通过 Pull Request（PR）合并到主分支

这样做的好处是：

1. **不会互相覆盖代码**
2. **每次修改都有记录**
3. **可以先 review 再合并**
4. **出了问题可以回退**

对于你们两个人来说，最推荐的方式是：

- `wuhaotian0508` 维护主仓库和 `main` 分支
- `scarlettLi` 负责在自己的功能分支上开发
- 开发完成后发起 PR，再合并进 `main`

---

## 二、你们两个人的推荐协作关系

建议按下面的角色分工：

### 1. `wuhaotian0508`

- 创建并维护 GitHub 仓库
- 管理主分支 `main`
- 审查并合并 `scarlettLi` 的代码
- 处理最终发布版本

### 2. `scarlettLi`

- Clone 仓库到本地
- 新建自己的开发分支
- 在分支上完成修改
- Push 到 GitHub 后发起 Pull Request

---

## 三、协作开始前的准备

### 3.1 仓库所有者先添加协作者

如果 `wuhaotian0508` 是仓库拥有者，需要先在 GitHub 上把 `scarlettLi` 加为协作者。

操作方法：

1. 打开仓库主页：`https://github.com/wuhaotian0508/biojson`
2. 点击 **Settings**
3. 点击左侧 **Collaborators** 或 **Manage access**
4. 点击 **Add people**
5. 输入 `scarlettLi`
6. 发送邀请
7. `scarlettLi` 接受邀请

这样对方就有权限直接推送到仓库中的分支了。

---

### 3.2 双方配置 Git 身份

在各自电脑上配置自己的 Git 用户名和邮箱。

#### `wuhaotian0508` 配置

```bash
git config --global user.name "wuhaotian0508"
git config --global user.email "wuhaotian0508@sjtu.edu.cn"
```

#### `scarlettLi` 配置

```bash
git config --global user.name "scarlettLi"
git config --global user.email "你的邮箱@example.com"
```

查看是否配置成功：

```bash
git config --global --list
```

---

### 3.3 配置 SSH（推荐）

如果你们使用 SSH 连接 GitHub，推送时会更方便。

测试命令：

```bash
ssh -T git@github.com
```

如果成功，会看到类似：

```bash
Hi wuhaotian0508! You've successfully authenticated...
```

或者：

```bash
Hi scarlettLi! You've successfully authenticated...
```

---

## 四、推荐的多人协作流程

最推荐的流程是：

```text
main 主分支
  ↑
PR 合并
  ↑
feature/scarlettLi-xxx   feature/wuhaotian-xxx
```

也就是说：

- 不要直接在 `main` 上写功能
- 每次任务都新建一个分支
- 做完后提交 PR
- 确认没问题再合并

---

## 五、标准协作操作示例

下面以 `scarlettLi` 修改项目内容为例。

### 5.1 第一次获取仓库

```bash
git clone git@github.com:wuhaotian0508/biojson.git
cd biojson
```

查看远程仓库：

```bash
git remote -v
```

你应该能看到：

```bash
origin  git@github.com:wuhaotian0508/biojson.git (fetch)
origin  git@github.com:wuhaotian0508/biojson.git (push)
```

---

### 5.2 开始新任务前，先同步最新主分支

无论是 `wuhaotian0508` 还是 `scarlettLi`，开始写代码前都建议先执行：

```bash
git checkout main
git pull origin main
```

这样可以确保你本地的 `main` 是最新的。

---

### 5.3 新建自己的功能分支

例如 `scarlettLi` 要新增一个说明文档：

```bash
git checkout -b feature/scarlettLi-add-doc
```

如果是 `wuhaotian0508` 自己开发，也建议：

```bash
git checkout -b feature/wuhaotian-update-readme
```

分支命名建议：

- `feature/名字-功能`
- `fix/名字-问题`
- `docs/名字-文档`

例如：

```bash
feature/scarlettLi-login
fix/scarlettLi-import-bug
docs/wuhaotian-github-guide
```

---

### 5.4 编写代码后查看状态

```bash
git status
```

这个命令能看到：

- 哪些文件被修改了
- 哪些文件还没加入暂存区
- 当前所在分支

---

### 5.5 添加并提交修改

```bash
git add .
git commit -m "docs: add github collaboration guide"
```

也可以只添加指定文件：

```bash
git add self-learn/git+bash/github_collaboration_guide.md
git commit -m "docs: add collaboration notes"
```

---

### 5.6 推送自己的分支到 GitHub

```bash
git push -u origin feature/scarlettLi-add-doc
```

第一次推送建议带 `-u`，后面再次推送就可以直接：

```bash
git push
```

---

### 5.7 发起 Pull Request

推送成功后，GitHub 页面通常会提示你创建 Pull Request。

PR 的基本流程：

1. 进入 GitHub 仓库页面
2. 点击 **Compare & pull request**
3. 选择：
   - base: `main`
   - compare: `feature/scarlettLi-add-doc`
4. 填写标题和说明
5. 提交 PR

建议 PR 标题写清楚，比如：

- `docs: add GitHub collaboration guide`
- `fix: correct import path in pipeline`
- `feat: add new markdown processing step`

---

### 5.8 合并 Pull Request

一般由 `wuhaotian0508` 负责检查并合并：

1. 查看改动内容
2. 确认没有冲突
3. 点击 **Merge pull request**
4. 删除已合并分支（可选但推荐）

合并完成后，`scarlettLi` 本地也要同步最新代码。

```bash
git checkout main
git pull origin main
```

如果原来的功能分支已经合并，可以删除本地分支：

```bash
git branch -d feature/scarlettLi-add-doc
```

---

## 六、适合你们两个人的最简协作模板

### 情况 A：`scarlettLi` 提交修改

```bash
cd /你的项目目录/biojson

# 先同步主分支
git checkout main
git pull origin main

# 新建分支
git checkout -b feature/scarlettLi-xxx

# 修改文件后提交
git add .
git commit -m "feat: xxxxx"

# 推送分支
git push -u origin feature/scarlettLi-xxx
```

然后去 GitHub 发 PR，等待 `wuhaotian0508` 合并。

### 情况 B：`wuhaotian0508` 合并后同步

```bash
git checkout main
git pull origin main
```

---

## 七、两人协作时的建议约定

为了减少混乱，建议你们提前约定下面这些规则。

### 1. 不直接在 `main` 上开发

即使只有两个人，也尽量不要直接改 `main`。

原因：

- 容易互相覆盖
- 出问题不好排查
- 不方便 review

---

### 2. 一个任务一个分支

不要把多个不相关的修改混在一个分支里。

例如：

- 改 README 用一个分支
- 修复脚本 bug 用一个分支
- 新增文档再用一个分支

这样 PR 会更清楚。

---

### 3. 提交信息尽量规范

推荐格式：

```bash
feat: 新功能
fix: 修复问题
docs: 文档修改
refactor: 重构
test: 测试相关
chore: 杂项维护
```

例如：

```bash
git commit -m "docs: add git collaboration tutorial"
git commit -m "fix: correct report output path"
git commit -m "feat: support new json schema"
```

---

### 4. 开发前先 pull

每次开始工作前都执行：

```bash
git checkout main
git pull origin main
```

否则容易基于旧代码开发，最后产生冲突。

---

### 5. 合并前先看改动

合并 PR 前建议检查：

- 改了哪些文件
- 是否误提交无关内容
- 是否包含临时文件
- 是否影响主流程

---

## 八、如果两个人改到了同一个文件怎么办

这就是常见的 **冲突（conflict）**。

例如：

- `wuhaotian0508` 改了 `README.md`
- `scarlettLi` 也改了 `README.md`
- 两人都改了同一段内容

这时 Git 无法自动判断保留谁的版本，就需要手动解决。

### 解决步骤

先拉取最新主分支：

```bash
git checkout main
git pull origin main
git checkout feature/scarlettLi-add-doc
git merge main
```

如果有冲突，Git 会在文件里标记：

```text
这是你当前分支的内容
```

你需要手动编辑成最终想保留的内容，然后再执行：

```bash
git add .
git commit -m "fix: resolve merge conflict"
git push
```

---

## 九、常见问题

### Q1：为什么 push 失败，提示被拒绝？

常见原因：

1. 远程分支有新的提交，你本地没同步
2. 你没有权限
3. SSH 没配置好

可以先尝试：

```bash
git pull origin main
```

如果你正在自己的功能分支上，也可以先：

```bash
git pull origin main
```

或者先切回 `main` 同步后再处理。

---

### Q2：我不小心直接在 main 上提交了怎么办？

如果还没 push，可以考虑把提交转移到新分支。

简单做法：

```bash
git branch feature/save-my-work
git checkout feature/save-my-work
```

然后再把 `main` 回到远程状态。

如果已经 push 了，最好先和对方确认，再决定是否回退。

---

### Q3：PR 合并后，本地为什么还是旧的？

因为你本地不会自动更新，需要手动拉取：

```bash
git checkout main
git pull origin main
```

---

### Q4：功能做完后旧分支要不要删？

建议删掉，保持分支清爽。

删除本地分支：

```bash
git branch -d feature/scarlettLi-add-doc
```

删除远程分支：

```bash
git push origin --delete feature/scarlettLi-add-doc
```

---

## 十、你们这次协作可以直接照抄的流程

### `wuhaotian0508` 负责

```bash
# 保持主分支最新
git checkout main
git pull origin main
```

- 维护主仓库
- 审核 PR
- 合并到 `main`

### `scarlettLi` 负责

```bash
# 1. 拉最新代码
git checkout main
git pull origin main

# 2. 新建分支
git checkout -b feature/scarlettLi-task-name

# 3. 修改并提交
git add .
git commit -m "feat: describe your changes"

# 4. 推送到远程
git push -u origin feature/scarlettLi-task-name
```

然后：

1. 去 GitHub 发 PR
2. 由 `wuhaotian0508` 审查并合并
3. 合并后双方都执行：

```bash
git checkout main
git pull origin main
```

---

## 十一、总结

对于 `wuhaotian0508` 和 `scarlettLi` 这种两人协作场景，最稳妥的方式就是：

1. **主分支只放稳定内容**
2. **每次开发都新建分支**
3. **通过 PR 合并**
4. **开始前先 pull，结束后再 push**

如果你们后面协作变多，还可以继续增加：

- 分支保护规则
- PR review 要求
- commit message 规范
- issue 分工流程

但对现在来说，先把“**分支开发 + PR 合并**”这个基本流程养成习惯，就已经非常够用了。