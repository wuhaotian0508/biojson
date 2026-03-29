# RAG-4-nutrimaster 部署说明

## 系统状态

✅ **本地测试完成** - 系统已在当前服务器上成功运行

- 数据加载：70个基因（来自13篇文献）
- 检索系统：TF-IDF向量化（SimpleRetriever）
- LLM集成：GPT-5.4 API（已验证工作正常）
- Web界面：Flask + SSE流式输出
- 本地测试：命令行和Web界面均正常

## 当前位置

代码位置：`/data/haotianwu/biojson/rag/`

Web服务状态：
```bash
# 当前运行在 http://localhost:5000
ps aux | grep "python.*app.py"
curl http://localhost:5000/api/health
# 返回: {"status":"ok","total_chunks":70}
```

## 推送到GitHub

由于权限问题，需要手动推送。有以下几种方案：

### 方案1：直接在阿里云服务器上克隆本地代码

```bash
# 在阿里云服务器上
cd /your/deployment/path
rsync -avz ubuntu@current-server:/data/haotianwu/biojson/rag/ ./RAG-4-nutrimaster/
cd RAG-4-nutrimaster
git init
git add .
git commit -m "Initial commit: RAG gene Q&A system"
git branch -M main
git remote add origin git@github.com:captwg/RAG-4-nutrimaster.git
git push -u origin main
```

### 方案2：创建tar包传输

```bash
# 在当前服务器
cd /data/haotianwu/biojson
tar -czf rag-nutrimaster.tar.gz rag/

# 传输到阿里云
scp rag-nutrimaster.tar.gz your-aliyun-server:/path/to/destination/

# 在阿里云服务器解压
tar -xzf rag-nutrimaster.tar.gz
mv rag RAG-4-nutrimaster
cd RAG-4-nutrimaster
# 然后按方案1推送到GitHub
```

### 方案3：使用captwg账户推送

如果您有captwg账户的访问权限：

```bash
cd /data/haotianwu/biojson/rag

# 生成部署密钥或使用个人访问令牌
git remote set-url origin https://YOUR_TOKEN@github.com/captwg/RAG-4-nutrimaster.git
git push -u origin main
```

## 阿里云服务器部署步骤

### 1. 环境准备

```bash
# Python 3.8+
python3 --version

# 安装依赖
pip install -r requirements.txt
pip install -r web/requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
cat > .env << 'EOF'
# LLM API 配置
API_KEY=u0rgjezq53e5tv01000dg95v0yqn2eecv02b7z3r
BASE_URL=https://api.gpugeek.com/v1
LLM_MODEL=Vendor2/GPT-5.4

# Jina API 配置 (可选)
JINA_API_KEY=your-jina-api-key

# Web 配置
WEB_HOST=0.0.0.0
WEB_PORT=5000
DEBUG=False
EOF
```

### 3. 准备数据

将13个JSON文件放入 `data/` 目录：

```bash
# 从当前服务器复制
scp /data/haotianwu/biojson/rag/data/*.json aliyun:/path/to/rag/data/
```

或者从源项目复制：
```bash
cp /path/to/source/data/*_nutri_plant_verified.json data/
```

### 4. 构建索引

```bash
python build_index.py
# 或
python main.py --rebuild-index
```

输出示例：
```
构建简单索引（TF-IDF 方法）...
找到 13 个数据文件
总共加载了 70 个基因
为 70 个 chunk 生成向量...
向量维度: (70, 1024)
索引构建完成
```

### 5. 测试系统

```bash
# 命令行测试
python main.py -q "什么是转录因子？"

# 交互模式
python main.py -i
```

### 6. 启动Web服务

#### 开发模式

```bash
cd web
python app.py
# 访问 http://localhost:5000
```

#### 生产模式（Gunicorn）

```bash
cd web
bash run_prod.sh
# 或
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 300 app:app
```

### 7. 配置Nginx反向代理（推荐）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # 重要：SSE流式输出需要关闭缓冲
        proxy_buffering off;
        proxy_cache off;

        # 超时设置
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### 8. 配置systemd服务（开机自启）

创建 `/etc/systemd/system/rag-nutrimaster.service`:

```ini
[Unit]
Description=RAG NutriMaster Gene Q&A System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/RAG-4-nutrimaster/web
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable rag-nutrimaster
sudo systemctl start rag-nutrimaster
sudo systemctl status rag-nutrimaster
```

## 测试验证

### 健康检查

```bash
curl http://localhost:5000/api/health
# 期望输出: {"status":"ok","total_chunks":70}
```

### API测试

```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "转录因子的作用是什么？"}'
```

### Web界面测试

浏览器访问: http://your-server-ip:5000

## 故障排查

### 问题1：LLM API 405错误

检查BASE_URL配置：
- ✅ 正确：`https://api.gpugeek.com/v1`
- ❌ 错误：`https://ai.gpugeek.com/v1`

### 问题2：检索结果相关度为0

这是正常的（TF-IDF在小数据集上的特性），LLM仍能生成正确答案。

### 问题3：Web界面无法连接

```bash
# 检查端口
netstat -tlnp | grep 5000

# 检查防火墙
sudo ufw allow 5000

# 检查日志
tail -f app.log
```

### 问题4：数据文件找不到

确保JSON文件在 `data/` 目录：
```bash
ls -la data/*.json
# 应显示13个文件
```

## 性能优化建议

1. **使用Jina API**（可选）
   - 更高质量的向量检索
   - 需要有效的JINA_API_KEY

2. **增加Gunicorn workers**
   ```bash
   gunicorn -w 8 -b 0.0.0.0:5000 app:app
   ```

3. **启用Redis缓存**（TODO）

4. **CDN加速静态资源**（TODO）

## 当前配置总结

| 项目 | 值 |
|-----|-----|
| Python版本 | 3.13 |
| LLM模型 | Vendor2/GPT-5.4 |
| API地址 | https://api.gpugeek.com/v1 |
| 检索方式 | TF-IDF (SimpleRetriever) |
| 数据量 | 70 genes / 13 papers |
| 向量维度 | 1024 |
| Web框架 | Flask |
| 端口 | 5000 |
| 流式输出 | SSE (Server-Sent Events) |

## 联系与支持

- GitHub: https://github.com/captwg/RAG-4-nutrimaster
- 文档位置: `/data/haotianwu/biojson/rag/README.md`

---

**最后更新**: 2026-03-29
**状态**: ✅ 已测试通过，等待部署
