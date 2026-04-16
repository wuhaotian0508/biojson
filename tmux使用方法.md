# tmux 使用方法

`tmux` 是一个终端复用工具，可以让你在一个终端里管理多个会话、窗口和窗格，并且在断开 SSH 后继续保留运行状态。


## 2. 基本概念

- `session`：一个 tmux 会话
- `window`：会话中的一个窗口，类似标签页
- `pane`：窗口中的一个分屏区域

默认前缀键是 `Ctrl+b`，后续很多命令都需要先按这个前缀键。

例如：

- `Ctrl+b d`：先按住 `Ctrl` 再按 `b`，松开后再按 `d`

## 3. 最常用的操作

### 创建新会话

```bash
tmux
```

或者指定会话名：

```bash
tmux new -s mysession
```

### 查看会话列表

```bash
tmux ls
```

### 进入指定会话

```bash
tmux attach -t mysession
```

### 退出但不关闭会话

按：

```text
Ctrl+b d
```

这叫做 `detach`，会话会继续在后台运行。

### 关闭会话

在 tmux 中直接输入：

```bash
exit
```

如果该窗口和会话里没有其他进程，会话会被关闭。

也可以直接在外部执行：

```bash
tmux kill-session -t mysession
```

## 4. 窗口操作

### 新建窗口

```text
Ctrl+b c
```

### 切换窗口

```text
Ctrl+b n   # 下一个窗口
Ctrl+b p   # 上一个窗口
Ctrl+b 0   # 切到编号 0 的窗口
Ctrl+b 1   # 切到编号 1 的窗口
```

### 重命名窗口

```text
Ctrl+b ,
```

### 关闭当前窗口

在当前窗口执行：

```bash
exit
```

## 5. 窗格分屏操作

### 垂直分屏

```text
Ctrl+b %
```

### 水平分屏

```text
Ctrl+b "
```

### 在窗格之间切换

```text
Ctrl+b 方向键
```

### 关闭当前窗格

在当前窗格执行：

```bash
exit
```

### 调整窗格大小

先按前缀键，再按：

```text
Ctrl+b :resize-pane -L 10
Ctrl+b :resize-pane -R 10
Ctrl+b :resize-pane -U 5
Ctrl+b :resize-pane -D 5
```

也可以进入命令模式后执行：

```text
Ctrl+b :
```

然后输入：

```text
resize-pane -R 10
```

## 6. 复制模式

当终端输出很多内容时，可以进入复制模式查看历史。

### 进入复制模式

```text
Ctrl+b [
```

进入后可以使用：

- 方向键移动
- `PageUp` / `PageDown` 翻页
- `q` 退出复制模式

## 7. 常用命令速查

| 功能 | 命令 |
|---|---|
| 新建会话 | `tmux new -s 名称` |
| 查看会话 | `tmux ls` |
| 进入会话 | `tmux attach -t 名称` |
| 后台挂起会话 | `Ctrl+b d` |
| 新建窗口 | `Ctrl+b c` |
| 切换下一个窗口 | `Ctrl+b n` |
| 切换上一个窗口 | `Ctrl+b p` |
| 垂直分屏 | `Ctrl+b %` |
| 水平分屏 | `Ctrl+b "` |
| 切换窗格 | `Ctrl+b 方向键` |
| 进入复制模式 | `Ctrl+b [` |
| 关闭会话 | `tmux kill-session -t 名称` |

## 8. 一个常见使用场景

比如你通过 SSH 登录服务器跑训练或脚本：

1. 先创建会话：

```bash
tmux new -s work
```

2. 在里面运行程序：

```bash
python main.py
```

3. 临时离开时按：

```text
Ctrl+b d
```

4. 下次重新登录服务器后恢复：

```bash
tmux attach -t work
```

这样即使 SSH 断开，程序通常也会继续运行。

## 9. 建议记住的最小命令集

如果你刚开始用，只需要先记住这几个：

- `tmux new -s 名称`
- `tmux ls`
- `tmux attach -t 名称`
- `Ctrl+b d`
- `Ctrl+b c`
- `Ctrl+b %`
- `Ctrl+b "`
- `Ctrl+b 方向键`

掌握这些后，已经足够覆盖大部分日常使用场景。

## 10. 注意事项

### 嵌套 tmux 问题

如果你已经在一个 tmux session 里，再用 `tmux new-session -d` 创建的 session 是独立的，无法用 `tmux attach` 直接找到（因为属于不同层）。

解决方法：在已有 tmux 里用 `new-window` 代替 `new-session`：

```bash
tmux new-window -n biojson 'ssh ali "cd ~/code/biojson/rag/web && bash run.sh"'
```

### 在 ali 服务器上跑 biojson 服务的标准流程

```bash
# 1. 登录 ali
ssh ali

# 2. 新建 session
tmux new -s biojson

# 3. 启动服务（带日志）
cd ~/code/biojson/rag/web
bash run.sh 2>&1 | tee ~/biojson.log

# 4. 离开但保持运行
Ctrl+b d

# 5. 查看日志
tail -f ~/biojson.log

# 6. 下次回来
ssh ali
tmux attach -t biojson
```

### 开启鼠标支持

在 `~/.tmux.conf` 中加入：

```
set -g mouse on
```

然后执行：

```bash
tmux source ~/.tmux.conf
```

之后可以用鼠标滚轮查看历史输出，点击切换窗格。
