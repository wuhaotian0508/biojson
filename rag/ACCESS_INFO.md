# RAG Web UI 访问指南

## 🌐 访问地址

### 服务器内部访问
```
http://localhost:5000
http://127.0.0.1:5000
```

### 外部访问（推荐使用）
```
http://115.190.3.161:5000
```

## 📋 系统状态

✅ Web 服务器运行中
- 进程 ID: 3507758
- 监听地址: 0.0.0.0:5000
- 运行时间: 自 10:30 开始

## 🔧 快速测试命令

### 1. 健康检查 API
```bash
# 本地测试
curl http://localhost:5000/api/health

# 外部测试（从你的本地机器运行）
curl http://115.190.3.161:5000/api/health
```

预期返回：
```json
{
  "status": "ok",
  "total_chunks": 70
}
```

### 2. 测试问答 API
```bash
curl -X POST http://115.190.3.161:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "NAC37基因的功能是什么？"}'
```

### 3. 浏览器直接访问
打开浏览器，输入：
```
http://115.190.3.161:5000
```

## 🚨 如果无法访问

### 问题 1: 防火墙限制
需要以 root 权限开放端口 5000：

```bash
# 如果使用 ufw
sudo ufw allow 5000/tcp
sudo ufw status

# 如果使用 iptables
sudo iptables -I INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables-save
```

### 问题 2: 云服务器安全组
如果是云服务器（阿里云、腾讯云等），需要在控制台配置安全组：
- 协议: TCP
- 端口: 5000
- 来源: 0.0.0.0/0（或你的 IP 地址）

### 问题 3: SSH 端口转发（临时方案）
如果防火墙无法配置，可以使用 SSH 隧道：

在你的本地机器运行：
```bash
ssh -L 5000:localhost:5000 ubuntu@115.190.3.161
```

然后在本地浏览器访问：
```
http://localhost:5000
```

## 🔄 重启服务

如果需要重启 Web 服务：

```bash
# 停止当前服务
pkill -f "python app.py"

# 启动服务
cd /data/haotianwu/biojson/rag/web
bash run.sh
```

或使用生产模式：
```bash
bash run_prod.sh
```

## 📊 服务监控

查看服务状态：
```bash
ps aux | grep "python app.py" | grep -v grep
```

查看端口监听：
```bash
netstat -tuln | grep 5000
# 或
ss -tuln | grep 5000
```

查看服务日志（如果使用后台运行）：
```bash
tail -f /data/haotianwu/biojson/rag/web/app.log
```

## 📝 配置信息

配置文件: [config.py](/data/haotianwu/biojson/rag/config.py)

当前配置：
- `WEB_HOST`: 0.0.0.0（允许外部访问）
- `WEB_PORT`: 5000
- `DEBUG`: False

---

**更新时间**: 2026-03-29
**服务器 IP**: 115.190.3.161
**用户**: ubuntu
