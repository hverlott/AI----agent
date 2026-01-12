# 📦 完整安装指南

本文档提供详细的安装步骤，适用于在全新电脑上从零开始搭建 Telegram AI Bot 系统。

---

## 📋 目录

- [系统要求](#系统要求)
- [快速安装（推荐）](#快速安装推荐)
- [手动安装](#手动安装)
- [配置说明](#配置说明)
- [首次运行](#首次运行)
- [常见问题](#常见问题)

---

## 💻 系统要求

### 硬件要求
- **CPU**: 1核或以上
- **内存**: 最少 512 MB（推荐 1 GB+）
- **硬盘**: 至少 500 MB 可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**:
  - Windows 10/11
  - macOS 10.14+
  - Linux (Ubuntu 18.04+, Debian 10+, CentOS 7+)
- **Python**: 3.8 或更高版本
- **Git** (可选): 用于下载项目

---

## 🚀 快速安装（推荐）

### Windows

```cmd
# 1. 下载项目
git clone https://github.com/hverlott/AI----agent.git
cd AI-Talk

# 2. 运行一键安装脚本
install.bat

# 3. 按照提示完成配置
```

### Linux/Mac

```bash
# 1. 下载项目
git clone <项目地址>
cd AI-Talk

# 2. 添加执行权限并运行安装脚本
chmod +x install.sh
./install.sh

# 3. 按照提示完成配置
```

安装脚本会自动：
- ✅ 检查 Python 版本
- ✅ 升级 pip
- ✅ 安装所有依赖包
- ✅ 创建配置文件模板
- ✅ 运行环境检查

---

## 🔧 手动安装

如果自动安装脚本失败，可以按照以下步骤手动安装。

### 步骤 1：安装 Python

#### Windows

1. 访问 https://www.python.org/downloads/
2. 下载 Python 3.8 或更高版本的安装包
3. 运行安装程序
4. **重要**：勾选 "Add Python to PATH"
5. 完成安装

验证安装：
```cmd
python --version
pip --version
```

#### Linux (Ubuntu/Debian)

```bash
# 更新软件源
sudo apt update

# 安装 Python 和 pip
sudo apt install python3.8 python3-pip

# 验证安装
python3 --version
pip3 --version
```

#### Mac

```bash
# 使用 Homebrew 安装
brew install python@3.8

# 验证安装
python3 --version
pip3 --version
```

### 步骤 2：下载项目

#### 方式 A：使用 Git（推荐）

```bash
git clone https://github.com/hverlott/AI----agent.git
cd AI-Talk
```

## 🔒 安全与隐私

- 本仓库已从历史中移除并忽略本地私密配置、会话文件、日志、数据库与大型压缩/二进制文件（例如 `.env`、`*.session`、`data/tenants/`、`release/`、`*.zip`、`*.exe`）。
- 在发布或共享前，请确保本地的 `.env`、会话文件及租户数据未被加入 Git。当需要共享密钥或敏感信息时，请使用安全渠道或私有仓库/secret 管理。


#### 方式 B：手动下载

1. 访问项目页面
2. 点击 "Code" -> "Download ZIP"
3. 解压到目标目录
4. 打开命令行，进入解压目录

### 步骤 3：安装依赖包

```bash
# Windows
pip install -r requirements.txt

# Linux/Mac
pip3 install -r requirements.txt
```

依赖包列表：
```
telethon==1.34.0        # Telegram 客户端库
openai>=1.30.0          # OpenAI API 客户端
python-dotenv==1.0.0    # 环境变量管理
httpx>=0.27.0           # HTTP 客户端
streamlit>=1.30.0       # Web 框架
psutil>=5.9.0           # 进程管理
```

### 步骤 4：创建配置文件

#### 4.1 创建 .env 文件

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

#### 4.2 编辑 .env 文件

Windows:
```cmd
notepad .env
```

Linux/Mac:
```bash
nano .env
# 或
vim .env
```

填写以下内容：
```env
TELEGRAM_API_ID=你的API_ID
TELEGRAM_API_HASH=你的API_HASH
AI_API_KEY=你的AI密钥
AI_BASE_URL=https://api.open.ai
AI_MODEL_NAME=deepseek-v3.1
```

#### 4.3 创建其他配置文件

**prompt.txt** (AI 人设)：
```
你是一个幽默、专业的个人助理，帮机主回复消息。请用自然、友好的语气回复。
```

**keywords.txt** (触发关键词)：
```
帮我
求助
AI
机器人
```

### 步骤 5：运行环境检查

```bash
# Windows
python check_env.py

# Linux/Mac
python3 check_env.py
```

如果所有检查通过，显示：
```
✅ 所有检查通过！环境配置完成！
```

---

## ⚙️ 配置说明

### 获取 Telegram API 密钥

1. 访问 https://my.telegram.org
2. 使用你的手机号登录
3. 进入 "API development tools"
4. 填写应用信息：
   - App title: 随意（如 "My Bot"）
   - Short name: 随意（如 "mybot"）
   - Platform: 选择 "Desktop"
5. 点击 "Create application"
6. 获取 `api_id` 和 `api_hash`

### 获取 AI API 密钥

#### DeepSeek

1. 访问 https://platform.deepseek.com
2. 注册/登录账号
3. 进入 "API Keys" 页面
4. 创建新的 API Key
5. 复制密钥

配置：
```env
AI_API_KEY=sk-xxx
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL_NAME=deepseek-chat
```

#### OpenAI

1. 访问 https://platform.openai.com
2. 注册/登录账号
3. 进入 "API keys" 页面
4. 创建新的 API Key
5. 复制密钥

配置：
```env
AI_API_KEY=sk-xxx
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL_NAME=gpt-3.5-turbo
```

#### 自定义 API

如果使用第三方 API（如 55.ai）：
```env
AI_API_KEY=sk-xxx
AI_BASE_URL=https://api.open.ai
AI_MODEL_NAME=deepseek-v3.1
```

---

## 🎮 首次运行

### 1. Telegram 登录

```bash
# Windows
python main.py

# Linux/Mac
python3 main.py
```

按提示操作：
```
请输入手机号（国际格式）: +88xxxxxxxxxx
请输入验证码: 12345
(如果启用两步验证) 请输入云密码: ******
```

登录成功后会生成 `userbot_session.session` 文件。

### 2. 启动管理后台

```bash
# Windows
start_admin.bat

# Linux/Mac
chmod +x start_admin.sh
./start_admin.sh
```

浏览器会自动打开 `http://localhost:8501`

### 3. 测试机器人

1. 在管理后台点击 "启动" 按钮
2. 用另一个 Telegram 账号给机器人发送消息
3. 查看 "运行日志" Tab 确认收到消息
4. 应该会收到 AI 的自动回复

---

## 🐛 常见问题

### Q1: Python 未找到或版本过低

**Windows:**
```
'python' 不是内部或外部命令
```

**解决方案：**
1. 确认已安装 Python 3.8+
2. 重新安装并勾选 "Add Python to PATH"
3. 重启命令行窗口

**Linux:**
```bash
# 安装 Python 3.8
sudo apt install python3.8
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
```

### Q2: pip 安装失败

**错误：**
```
Could not find a version that satisfies the requirement
```

**解决方案：**
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q3: SSL 证书错误

**错误：**
```
SSL: CERTIFICATE_VERIFY_FAILED
```

**解决方案：**
```bash
# 临时禁用 SSL 验证（不推荐）
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Q4: 权限不足

**Linux/Mac:**
```
Permission denied
```

**解决方案：**
```bash
# 添加执行权限
chmod +x install.sh start_admin.sh

# 或使用 sudo（不推荐）
sudo pip3 install -r requirements.txt
```

### Q5: Telegram 登录失败

**错误：**
```
PhoneNumberInvalidError
```

**解决方案：**
1. 确保手机号格式正确：`+86xxxxxxxxxx`
2. 确保号码已注册 Telegram
3. 检查网络连接

### Q6: AI API 调用失败

**错误：**
```
❌ AI 调用失败: 401 Unauthorized
```

**解决方案：**
1. 检查 `.env` 文件中的 `AI_API_KEY` 是否正确
2. 确认 `AI_BASE_URL` 是否正确
3. 测试 API 是否可用：
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://api.55.ai/v1/models
   ```

---

## 📝 安装检查清单

在完成安装后，请确认以下事项：

- [ ] Python 3.8+ 已安装
- [ ] pip 可以正常使用
- [ ] 所有依赖包已安装（运行 `pip list`）
- [ ] `.env` 文件已创建并填写
- [ ] `prompt.txt` 和 `keywords.txt` 已创建
- [ ] Telegram 已成功登录（存在 `userbot_session.session`）
- [ ] 环境检查通过（`python check_env.py`）
- [ ] 管理后台可以正常打开
- [ ] 机器人可以正常回复消息

---

## 🎯 下一步

安装完成后，你可以：

1. 📖 阅读 [README.md](README.md) 了解项目功能
2. 🎛️ 查看 [ADMIN_README.md](ADMIN_README.md) 学习管理后台使用
3. 📢 参考 [BROADCAST_README.md](BROADCAST_README.md) 了解群发功能
4. 🔧 根据需要调整配置文件

---

## 💬 获取帮助

如果遇到问题：

1. 查看本文档的 [常见问题](#常见问题) 部分
2. 运行 `python check_env.py` 检查环境
3. 查看项目的其他文档
4. 提交 Issue 到项目仓库

---

**祝你安装顺利！** 🎉


