# 实现总结：163 邮箱验证码注册系统

## 已完成的改动

### 1. 配置文件
- **rag/config.py**: 添加了 163 SMTP 配置常量
- **.env**: 添加了 SMTP_USER 和 SMTP_PASSWORD 环境变量

### 2. 后端模块
- **rag/web/email_sender.py** (新建): 邮件发送模块
  - `send_verification_code()`: 使用 163 SMTP 发送 HTML 格式验证码邮件
  - 邮件模板包含 NutriMaster 品牌样式

- **rag/web/auth.py** (FastAPI 版): 添加了三个新函数
  - `generate_verification_code()`: 生成 6 位数字验证码
  - `signup_with_email()`: 注册接口，创建用户并发送验证码
  - `verify_email_code()`: 验证码校验接口
  - `resend_verification_code()`: 重发验证码接口

- **rag/web/auth_flask.py** (Flask 版): 同步添加相同功能
  - `signup_with_email_view()`
  - `verify_email_code_view()`
  - `resend_verification_code_view()`

### 3. 路由配置
- **rag/web/app.py** (FastAPI): 添加了三个新路由
  - `POST /api/auth/signup`: 注册并发送验证码
  - `POST /api/auth/verify`: 验证邮箱验证码
  - `POST /api/auth/resend`: 重新发送验证码

- **rag/web/app_flask.py** (Flask): 同步添加相同路由

### 4. 前端实现
- **rag/web/static/auth.js**: 重构注册流程
  - 修改 `handleSignUp()`: 调用后端 API 而非直接调用 Supabase
  - 新增 `handleVerifyCode()`: 处理验证码提交
  - 新增 `handleResendCode()`: 重新发送验证码
  - 新增 `handleBackToSignup()`: 返回注册表单
  - 更新 `switchAuthForm()`: 支持验证码表单切换
  - 更新 `setupAuthListeners()`: 绑定验证码相关事件

- **rag/web/static/index.html**: 添加验证码输入界面
  - 新增 `#verify-code-form`: 验证码输入表单
  - 包含验证码输入框、验证按钮、重发按钮、返回按钮

- **rag/web/static/style.css**: 添加验证码表单样式
  - `.verify-info`: 提示信息样式
  - `.verify-email`: 邮箱显示样式
  - `#verify-code-input`: 验证码输入框样式（大字号、等宽字体）
  - `.verify-actions`: 按钮组样式
  - `.verify-link-btn`: 链接按钮样式

### 5. 测试工具
- **test_email.py** (新建): 邮件发送测试脚本

## 核心流程

### 注册流程
1. 用户填写邮箱、密码、昵称（可选）、头像（可选）
2. 前端调用 `POST /api/auth/signup`
3. 后端生成 6 位验证码，创建 Supabase 用户（未验证状态）
4. 验证码和过期时间存入 `user_metadata`
5. 通过 163 SMTP 发送验证码邮件
6. 前端显示验证码输入界面

### 验证流程
1. 用户输入 6 位验证码
2. 前端调用 `POST /api/auth/verify`
3. 后端校验验证码和过期时间（10 分钟）
4. 验证成功后标记 `email_confirm = True`，清除验证码
5. 前端自动调用 Supabase 登录接口
6. 登录成功，进入主应用

### 重发流程
1. 用户点击"重新发送"
2. 前端调用 `POST /api/auth/resend`
3. 后端生成新验证码，更新 `user_metadata`
4. 发送新验证码邮件

## 安全特性
- 验证码 10 分钟过期
- 验证成功后立即清除验证码
- 使用 Supabase admin API 管理用户状态
- 支持重复注册检测（已验证用户不能重复注册）
- 未验证用户可重新发送验证码

## 测试方法

### 1. 测试邮件发送
```bash
cd /data/haotianwu/biojson
python test_email.py
```

### 2. 端到端测试
1. 启动服务：
   ```bash
   cd /data/haotianwu/biojson/rag/web
   python app.py  # 或 python app_flask.py
   ```

2. 打开浏览器访问 http://localhost:5000

3. 测试注册流程：
   - 点击"注册"标签
   - 填写邮箱、密码、昵称
   - 点击"注册"
   - 检查邮箱是否收到验证码
   - 输入验证码点击"验证"
   - 验证成功后应自动登录

4. 测试错误场景：
   - 输入错误验证码 → 应显示"验证码错误"
   - 等待 10 分钟后输入验证码 → 应显示"验证码已过期"
   - 点击"重新发送" → 应收到新验证码

## 注意事项

1. **SMTP 密码安全**：
   - `.env` 文件已添加到 `.gitignore`
   - 建议修改文件权限：`chmod 600 .env`

2. **163 邮箱限制**：
   - 每天发送量有限制（通常几百封）
   - 如果用户量大，建议使用专业邮件服务

3. **垃圾邮件风险**：
   - 163 邮箱发送的邮件可能被某些邮箱服务商标记为垃圾邮件
   - 建议用户检查垃圾邮件文件夹

4. **Supabase 配置**：
   - 不需要在 Supabase Dashboard 修改任何设置
   - 使用 admin API 直接控制用户状态

5. **兼容性**：
   - FastAPI 和 Flask 两个版本已同步更新
   - 建议使用 FastAPI 版本（更好的并发性能）

## 文件清单

### 新建文件
- `/data/haotianwu/biojson/rag/web/email_sender.py`
- `/data/haotianwu/biojson/test_email.py`

### 修改文件
- `/data/haotianwu/biojson/rag/config.py`
- `/data/haotianwu/biojson/.env`
- `/data/haotianwu/biojson/rag/web/auth.py`
- `/data/haotianwu/biojson/rag/web/auth_flask.py`
- `/data/haotianwu/biojson/rag/web/app.py`
- `/data/haotianwu/biojson/rag/web/app_flask.py`
- `/data/haotianwu/biojson/rag/web/static/auth.js`
- `/data/haotianwu/biojson/rag/web/static/index.html`
- `/data/haotianwu/biojson/rag/web/static/style.css`
