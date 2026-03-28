# 同一服务器用户下的 GitHub 双人协作说明（wuhaotian0508 × scarlettLi）

> 这份说明是针对你们的**真实使用场景**写的：
>
> - 你和 `scarlettLi` 共用**同一台服务器**
> - 你们在服务器上使用的是**同一个 Linux 用户**
> - 服务器默认连接的是 **`wuhaotian0508` 的 GitHub**

这意味着：

- 在服务器上执行 `git push` 时，远程 GitHub 身份通常会显示为 `wuhaotian0508`
- 即使是 `scarlettLi` 在这台服务器上改的代码，只要是通过这台服务器 push，上 GitHub 时本质上也还是走你的认证
- 所以你们协作时，重点不再是“如何区分两个人各自的 GitHub 登录”，而是：
  - **如何区分是谁改的内容**
  - **如何避免互相覆盖**
  - **如何让协作过程可追踪、可回退**

---

## 一、这种场景下最核心的结论

一句话总结：

> **你们可以共用服务器上的 GitHub 认证，但一定要用“分支 + 提交说明 + 操作顺序”来区分协作。**

也就是说：

1. 可以继续让服务器默认连你的 GitHub
2. 但不要两个人都直接在 `main` 上乱改
3. 要用分支名区分任务和操作者
4. 要用 commit message 说明是谁改的、改了什么
5. 合并前先同步，合并后再同步

---

## 二、你们当前环境下，哪些地方和普通多人协作不同

普通情况下：

- `wuhaotian0508` 用自己的电脑和 GitHub 身份提交
- `scarlettLi` 也用自己的电脑和 GitHub 身份提交

而你们现在是：

- 两个人都可能在**同一台服务器**上操作
- 两个人都可能使用**同一个系统用户**
- 远程认证默认连到 **`wuhaotian0508`**

所以会出现下面这些特点：

### 1. GitHub 上的 push 身份不容易区分

从远程认证的角度，很多提交动作都会更像是从你的身份发出去的。

### 2. 本地命令历史和工作目录更容易相互影响

如果两个人在同一个目录、同一个用户下操作：

- 对方可能改了还没提交
- 你可能 pull 了她正在改的目录
- 很容易出现“谁动了这个文件”说不清的情况

### 3. 更需要人为约定协作规范

因为环境本身不能天然区分两个人，所以你们更需要：

- 分支规范
- 提交说明规范
- 开发顺序规范
- 合并规则

---

## 三、最适合你们的协作模式

最推荐你们采用下面的方式：

```text
服务器默认连接 wuhaotian0508 的 GitHub
          │
          ├── main：只放稳定版本
          │
          ├── feature/wuhaotian-xxx：你自己的开发分支
          │
          └── feature/scarlettLi-xxx：scarlettLi 的开发分支
```

也就是说：

- **远程认证可以共用**
- **开发分支必须分开**

这是你们当前场景里最稳妥的做法。

---

## 四、最重要的协作规则

## 规则 1：不要两个人直接共用 `main` 开发

即使服务器默认连的是你的 GitHub，也不要让两个人都直接在 `main` 上改。

原因：

- 容易互相覆盖
- 不容易定位是谁改的
- 出错时难以回退

正确做法：

- `main` 只保留稳定版本
- 新任务一律从 `main` 拉新分支

---

## 规则 2：用分支名标明是谁在做任务

建议直接把名字写进分支名。

例如：

```bash
feature/wuhaotian-update-readme
feature/scarlettLi-add-report-parser
docs/scarlettLi-github-notes
fix/wuhaotian-json-bug
```

这样即使是同一个服务器用户，也能一眼看出来：

- 这个分支是谁开的
- 这个任务是谁在做

---

## 规则 3：commit message 里也写清楚是谁的修改

因为远程身份不一定能准确区分两个人，所以建议在提交信息里也做标记。

例如：

```bash
git commit -m "docs(scarlettLi): add collaboration notes"
git commit -m "feat(scarlettLi): add markdown processing step"
git commit -m "fix(wuhaotian): correct pipeline path"
git commit -m "refactor(wuhaotian): simplify report generation"
```

这样以后看历史时会更清楚。

---

## 规则 4：一个人改代码时，另一个人尽量不要同时在同一个工作目录乱动

因为你们共用同一个服务器用户，如果同时在一个目录里频繁操作，很容易互相影响。

建议：

- 一次只让一个人负责一个分支
- 修改前先说一声“我现在在这个分支上改”
- 如果是重要修改，尽量不要两个人同时在同一个目录下切分支、pull、merge

如果条件允许，更稳妥的方式是：

- 同一仓库保留两个独立目录
- 例如一个给你，一个给 `scarlettLi`

示例：

```bash
/data/haotianwu/biojson-main
/data/haotianwu/biojson-scarlett
```

虽然远程还是同一个 GitHub 认证，但**本地工作目录分开**，冲突会少很多。

---

## 五、推荐的实际操作流程

下面给出最适合你们当前环境的流程。

### 情况 A：scarlettLi 在服务器上开发

先同步主分支：

```bash
cd /data/haotianwu/biojson
git checkout main
git pull origin main
```

新建属于她自己的分支：

```bash
git checkout -b feature/scarlettLi-xxx
```

修改后提交：

```bash
git add .
git commit -m "feat(scarlettLi): describe changes"
```

推送：

```bash
git push -u origin feature/scarlettLi-xxx
```

注意：

- 这里虽然是 `scarlettLi` 在操作
- 但服务器远程认证仍可能用的是 `wuhaotian0508`
- 所以**真正区分她身份的关键是分支名和 commit message**

---

### 情况 B：你自己开发

同样建议不要直接长期在 `main` 上改，而是：

```bash
cd /data/haotianwu/biojson
git checkout main
git pull origin main
git checkout -b feature/wuhaotian-xxx
```

提交时：

```bash
git add .
git commit -m "fix(wuhaotian): describe changes"
git push -u origin feature/wuhaotian-xxx
```

---

## 六、你作为维护者，最该做的事

由于服务器默认连的是你的 GitHub，所以你其实更像是：

- 远程仓库的拥有者
- 主分支的守门人
- 最终合并负责人

所以你最重要的职责是：

### 1. 守住 `main`

不要让 `main` 变成“谁都能直接乱改的开发区”。

### 2. 要求所有重要改动先走分支

哪怕只是两个人协作，也建议：

- 新功能走分支
- 大改动走分支
- 不确定是否稳定的改动走分支

### 3. 合并前先检查

你至少应该看：

- 改了哪些文件
- 有没有误提交缓存、日志、临时文件
- 有没有把不该删的内容删掉
- 改动是否和任务一致

---

## 七、如果不走 PR，也可以用“你审核后再 merge”

因为你们是同一个服务器用户场景，实际协作时不一定非要严格走 GitHub PR 页面。

你们也可以用下面这种更接地气的方式：

1. `scarlettLi` 在 `feature/scarlettLi-xxx` 分支完成修改
2. 她告诉你“我改完了，你来看一下”
3. 你在服务器上检查她的分支
4. 确认没问题后，由你合并到 `main`

示例：

```bash
git checkout main
git pull origin main
git merge feature/scarlettLi-xxx
git push origin main
```

这种方式适合：

- 你们暂时不强调 GitHub 网页上的 PR 流程
- 但仍然想保留“分支隔离 + 你确认后合并”的秩序

---

## 八、如果两个人都要长期在服务器上协作，更推荐这样做

如果后面你们会经常一起在服务器上改代码，我更推荐这两个优化。

### 方案 1：同仓库，不同本地目录

比如：

```bash
/data/haotianwu/biojson_wuhaotian
/data/haotianwu/biojson_scarlett
```

优点：

- 不容易互相覆盖未提交的改动
- 不容易把对方工作区搞乱
- 仍然可以共用同一个 GitHub 认证

这是**最值得你们采用**的现实方案。

---

### 方案 2：同仓库，不同 git config 标识

即使共用同一个系统用户，也可以在不同仓库目录里设置不同的 `git config user.name/user.email`。

例如在 `scarlettLi` 自己的目录里：

```bash
git config user.name "scarlettLi"
git config user.email "scarlett@example.com"
```

这样做的意义是：

- 虽然 push 认证仍可能走你的 GitHub SSH
- 但 commit 作者信息可以更清楚地区分

不过前提是：

- 最好给她单独一个工作目录
- 不然两个人共用一个目录时，这个配置也容易被改乱

---

## 九、最适合你们现在直接执行的简化版规则

如果你想要一个最省事、又不容易出错的版本，就执行下面这套：

### 你们统一遵守

1. `main` 不直接乱改
2. 一人一个功能分支
3. 分支名带名字
4. commit message 带名字
5. 合并前先同步 `main`
6. 合并后双方再同步一次

### 推荐模板

```bash
# 先更新 main
git checkout main
git pull origin main

# 按人名建分支
git checkout -b feature/scarlettLi-xxx

# 提交时注明是谁
git add .
git commit -m "feat(scarlettLi): xxxxx"

# 推送分支
git push -u origin feature/scarlettLi-xxx
```

由你检查后，再决定：

```bash
git checkout main
git pull origin main
git merge feature/scarlettLi-xxx
git push origin main
```

---

## 十、总结

你们现在的关键不是“怎么让服务器分别登录两个 GitHub 账号”，而是：

> **在共用同一个服务器用户、共用同一个远程认证的情况下，仍然把协作流程做规范。**

最重要的做法只有三个：

1. **分支分开**：`feature/wuhaotian-xxx`、`feature/scarlettLi-xxx`
2. **提交写清楚**：`feat(scarlettLi): ...`
3. **合并有顺序**：先同步、再开发、最后由你确认合并

如果你们后面合作会更多，我建议下一步直接把工作目录也分开。这样会比两个人长期共用一个目录稳很多。