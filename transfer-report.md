# 项目迁移报告

## 1. SSH免密登录配置

### 操作步骤
1. 本机已有SSH密钥 `~/.ssh/id_ed25519`，无需重新生成
2. 创建 `~/.ssh/config` 配置文件，添加了 `myserver` 别名：
   ```
   Host myserver
       HostName 39.108.180.113
       User root
       IdentityFile ~/.ssh/id_ed25519
   ```
3. 使用 `expect` 工具自动化 `ssh-copy-id`，将公钥写入远程服务器的 `~/.ssh/authorized_keys`
4. 验证通过：`ssh myserver` 可直接登录，无需密码

### 使用方式
```bash
ssh myserver              # 直接登录
scp file myserver:/path/  # 传文件
```

---

## 2. 依赖库处理

### 依赖扫描
扫描了项目中所有Python文件的 import 语句和已有的 requirements.txt 文件，汇总出完整的第三方依赖列表。

### 生成合并依赖文件
创建了 `requirements-all.txt`，合并了以下来源的依赖：
- `/requirements.txt`（根目录，Vercel部署用）
- `/rag/requirements.txt`（RAG模块）
- `/rag/web/requirements.txt`（Web API）
- 代码中扫描到的额外依赖（openai, biopython, lxml等）

### 依赖清单（共13个包）

| 包名 | 用途 |
|------|------|
| flask | Web框架 |
| flask-cors | 跨域支持 |
| gunicorn | WSGI服务器 |
| numpy | 数值计算 |
| scikit-learn | TF-IDF检索 |
| requests | HTTP请求 |
| openai | AI API调用 |
| supabase | 数据库 |
| PyMuPDF | PDF处理 |
| python-dotenv | 环境变量 |
| biopython | 生物信息学工具 |
| lxml | XML解析 |
| pytest | 测试框架 |

### 安装方式
到远程服务器后执行：
```bash
cd /root/code/biojson
pip3 install -r requirements-all.txt
```

---

## 3. 项目传输

### 体积优化
原始项目 **1.1GB**，排除以下内容后压缩为 **169MB**：

| 排除项 | 大小 | 原因 |
|--------|------|------|
| `.git/` | 137MB | Git历史，可在远程重新 `git init` |
| `old_scripts/` | 414MB | 旧脚本/归档，非运行必需 |
| `.codex/` | 31MB | Codex插件缓存 |
| `clash_*.tar.gz` | 5MB | 代理软件，与项目无关 |
| `output.tar*` | <1MB | 旧输出归档 |
| `rag-nutrimaster-deploy.tar.gz` | 64KB | 旧部署包 |
| `__pycache__/`, `*.pyc` | - | Python缓存 |

### 传输方式
```
tar czf → scp → tar xzf
```
即：本地打包压缩 → SCP传输 → 远程解压。

因远程服务器没有 `rsync`，使用 `scp` 传输。

### 最终结果
- 远程路径：`/root/code/biojson/`
- 远程大小：441MB（解压后）
- 所有核心代码和数据文件完整

---

## 4. 注意事项

### Python版本问题（重要！）
远程服务器 Python 版本为 **3.6.8**，太旧，以下包不兼容：
- `flask==3.0.0` 需要 Python ≥ 3.8
- `numpy>=1.26.4` 需要 Python ≥ 3.9
- `openai>=1.0.0` 需要 Python ≥ 3.7
- `supabase>=2.0.0` 需要 Python ≥ 3.8

**建议**：在远程服务器安装 Python 3.10+（推荐用 miniconda）：
```bash
# 在远程服务器执行
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
conda create -n biojson python=3.11
conda activate biojson
cd /root/code/biojson
pip install -r requirements-all.txt
```

### 如需Git版本控制
```bash
cd /root/code/biojson
git init
git add .
git commit -m "initial transfer"
```

### 如需补充 old_scripts
如果后续需要 old_scripts 目录，可单独传输：
```bash
# 在本机执行
scp -r /data/haotianwu/biojson/old_scripts myserver:/root/code/biojson/
```
