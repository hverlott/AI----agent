# 📦 部署打包指南

本文档说明如何将项目打包并部署到新电脑。

---

## 🎯 打包项目

### 方式 1：使用 Git（推荐）

```bash
# 1. 初始化 Git 仓库（如果还没有）
git init
git add .
git commit -m "Initial commit"

# 2. 推送到远程仓库（GitHub/GitLab/Gitee）
git remote add origin <你的仓库地址>
git push -u origin main

# 3. 在新电脑上克隆
git clone <你的仓库地址>
cd AI-Talk
```

### 方式 2：直接打包 ZIP

#### 需要包含的文件

**核心程序：**
- `admin_multi.py` (SaaS 管理入口)
- `main.py` (Wrapper)
- `src/` (核心源码目录)

**配置文件：**
- `requirements.txt`
- `.env.example` (不要包含 .env!)
- `config.txt` (默认模板)
- `prompt.txt` (默认模板)

**文档文件：**
- `README.md`
- `ADMIN_README.md`
- `INSTALLATION.md`
- `ADMIN_README.md`
- `BROADCAST_README.md`
- `DATABASE_LOCK_FIX.md`
- `LOG_TROUBLESHOOTING.md`
- `DEPLOYMENT_GUIDE.md`

#### 不要包含的文件

❌ 敏感文件（包含密钥）：
- `.env`
- `*.session`
- `bot.pid`
- `bot.log`

❌ Python 缓存：
- `__pycache__/`
- `*.pyc`
- `*.pyo`

❌ 系统文件：
- `.DS_Store` (Mac)
- `Thumbs.db` (Windows)
- `.git/` (如果使用 Git 可以包含)

#### 创建打包脚本

**Windows (`pack.bat`):**
```cmd
@echo off
echo 正在打包项目...

REM 创建打包目录
mkdir AI-Talk-Package

REM 复制核心文件
copy *.py AI-Talk-Package\
copy *.txt AI-Talk-Package\
copy *.bat AI-Talk-Package\
copy *.sh AI-Talk-Package\
copy *.md AI-Talk-Package\
copy .env.example AI-Talk-Package\

REM 创建 ZIP
powershell Compress-Archive -Path AI-Talk-Package -DestinationPath AI-Talk-Package.zip -Force

REM 清理临时目录
rmdir /s /q AI-Talk-Package

echo 打包完成！文件: AI-Talk-Package.zip
pause
```

**Linux/Mac (`pack.sh`):**
```bash
#!/bin/bash

echo "正在打包项目..."

# 创建打包目录
mkdir -p AI-Talk-Package

# 复制核心文件
cp *.py AI-Talk-Package/
cp *.txt AI-Talk-Package/
cp *.bat AI-Talk-Package/
cp *.sh AI-Talk-Package/
cp *.md AI-Talk-Package/
cp .env.example AI-Talk-Package/

# 创建 tar.gz
tar -czf AI-Talk-Package.tar.gz AI-Talk-Package/

# 清理临时目录
rm -rf AI-Talk-Package

echo "打包完成！文件: AI-Talk-Package.tar.gz"
```

---

## 🚢 在新电脑上部署

### 前置条件

新电脑需要：
- ✅ 互联网连接
- ✅ Python 3.8+ (如果没有，安装脚本会提示)
- ✅ 200 MB 可用空间

### 部署步骤

#### Windows

```cmd
# 1. 解压项目
右键 AI-Talk-Package.zip -> 解压到 AI-Talk\

# 2. 进入目录
cd AI-Talk

# 3. 运行一键安装
install.bat

# 4. 编辑配置
notepad .env

# 5. 首次登录
python main.py

# 6. 启动管理后台
start_admin.bat
```

#### Linux/Mac

```bash
# 1. 解压项目
tar -xzf AI-Talk-Package.tar.gz
cd AI-Talk

# 2. 添加执行权限
chmod +x *.sh

# 3. 运行一键安装
./install.sh

# 4. 编辑配置
nano .env

# 5. 首次登录
python3 main.py

# 6. 启动管理后台
./start_admin.sh
```

---

## 🔄 迁移现有配置

### 如果要保留原电脑的配置

#### 需要迁移的文件

1. **配置文件：**
   - `.env` (包含 API 密钥)
   - `prompt.txt`
   - `keywords.txt`

2. **Session 文件：**
   - `userbot_session.session` (避免重新登录)
   - `admin_session.session`

#### 迁移步骤

**旧电脑：**
```bash
# 创建配置备份
mkdir config-backup
cp .env config-backup/
cp prompt.txt config-backup/
cp keywords.txt config-backup/
cp *.session config-backup/

# 打包备份
tar -czf config-backup.tar.gz config-backup/
# 或 Windows: 右键 -> 压缩
```

**新电脑：**
```bash
# 1. 先按照上述步骤完成基础安装

# 2. 解压配置备份
tar -xzf config-backup.tar.gz

# 3. 复制配置文件
cp config-backup/.env .
cp config-backup/prompt.txt .
cp config-backup/keywords.txt .
cp config-backup/*.session .

# 4. 直接启动（无需重新登录）
streamlit run admin.py
```

---

## 🐳 Docker 部署（进阶）

### 创建 Dockerfile

```dockerfile
FROM python:3.8-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY *.py .
COPY *.txt .
COPY *.md .

# 创建数据目录
RUN mkdir /data

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "admin.py", "--server.address", "0.0.0.0"]
```

### 构建和运行

```bash
# 构建镜像
docker build -t telegram-ai-bot .

# 运行容器
docker run -d \
  --name telegram-bot \
  -p 8501:8501 \
  -v $(pwd)/data:/data \
  -v $(pwd)/.env:/app/.env \
  telegram-ai-bot
```

---

## 🌐 服务器部署

### 云服务器推荐

- **阿里云 ECS**
- **腾讯云 CVM**
- **AWS EC2**
- **Azure VM**
- **Vultr**
- **DigitalOcean**

### 最低配置

- **CPU**: 1核
- **内存**: 512 MB
- **硬盘**: 20 GB
- **带宽**: 1 Mbps

### 部署流程

#### 1. 连接服务器

```bash
ssh root@你的服务器IP
```

#### 2. 安装依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.8 python3-pip git

# CentOS
sudo yum install python3 python3-pip git
```

#### 3. 克隆项目

```bash
git clone <项目地址>
cd AI-Talk
```

#### 4. 安装Python依赖

```bash
pip3 install -r requirements.txt
```

#### 5. 配置环境

```bash
cp .env.example .env
nano .env  # 填写配置
```

#### 6. 首次登录

```bash
python3 main.py
# 输入手机号和验证码
```

#### 7. 使用 Screen 或 tmux 后台运行

**使用 Screen:**
```bash
# 安装 screen
sudo apt install screen  # Ubuntu/Debian
sudo yum install screen  # CentOS

# 创建会话
screen -S telegram-bot

# 启动机器人
python3 main.py

# 断开（保持运行）: Ctrl + A, 然后按 D

# 重新连接
screen -r telegram-bot
```

**使用 tmux:**
```bash
# 安装 tmux
sudo apt install tmux

# 创建会话
tmux new -s telegram-bot

# 启动机器人
python3 main.py

# 断开: Ctrl + B, 然后按 D

# 重新连接
tmux attach -t telegram-bot
```

#### 8. 设置开机自启（Systemd）

创建服务文件：
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

内容：
```ini
[Unit]
Description=Telegram AI Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/AI-Talk
ExecStart=/usr/bin/python3 /root/AI-Talk/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

---

## 📊 监控和维护

### 查看日志

```bash
# 实时查看
tail -f bot.log

# 查看最近 100 行
tail -n 100 bot.log

# 搜索错误
grep "ERROR" bot.log
```

### 定期备份

创建备份脚本 `backup.sh`：
```bash
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"

mkdir -p $BACKUP_DIR

# 备份配置和 session
tar -czf $BACKUP_DIR/config-$DATE.tar.gz \
    .env \
    prompt.txt \
    keywords.txt \
    *.session

echo "备份完成: $BACKUP_DIR/config-$DATE.tar.gz"

# 删除 7 天前的备份
find $BACKUP_DIR -name "config-*.tar.gz" -mtime +7 -delete
```

设置定时任务：
```bash
crontab -e

# 每天凌晨 3 点备份
0 3 * * * /root/AI-Talk/backup.sh
```

---

## ⚠️ 注意事项

### 安全建议

1. **不要泄露敏感文件**
   - `.env`
   - `*.session`
   - `bot.log`（可能包含用户消息）

2. **修改默认端口**
   ```bash
   streamlit run admin.py --server.port 8502
   ```

3. **使用防火墙**
   ```bash
   # Ubuntu
   sudo ufw allow 8501/tcp
   sudo ufw enable
   ```

4. **定期更新**
   ```bash
   git pull
   pip install -r requirements.txt --upgrade
   ```

### 性能优化

1. **限制日志大小**
   ```python
   # 在 main.py 中添加日志轮转
   from logging.handlers import RotatingFileHandler
   ```

2. **定期清理**
   ```bash
   # 每周清理日志
   0 0 * * 0 > /root/AI-Talk/bot.log
   ```

---

## ✅ 部署检查清单

- [ ] Python 3.8+ 已安装
- [ ] 所有依赖已安装
- [ ] .env 文件已配置
- [ ] Telegram 已登录
- [ ] 机器人可以正常运行
- [ ] 管理后台可以访问
- [ ] （服务器）已设置开机自启
- [ ] （服务器）已配置备份任务
- [ ] （服务器）已设置防火墙

---

**部署完成！** 🎉

如有问题，请参考 [INSTALLATION.md](INSTALLATION.md) 或项目文档。


