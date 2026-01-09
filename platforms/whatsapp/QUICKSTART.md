# 💬 WhatsApp Bot 快速上手指南

## 🚀 5分钟快速启动

### 步骤 1: 安装依赖

**Windows:**
```cmd
cd platforms\whatsapp
install.bat
```

**Linux/Mac:**
```bash
cd platforms/whatsapp
chmod +x install.sh
./install.sh
```

### 步骤 2: 配置 AI API

确保项目根目录的 `.env` 文件已配置：

```env
AI_API_KEY=sk-xxxxxxxxxxxx
AI_BASE_URL=https://api.55.ai/v1
AI_MODEL_NAME=deepseek-v3.1
```

### 步骤 3: 启动机器人

**方式一：命令行启动**

```bash
cd platforms/whatsapp
node bot.js
```

**方式二：Web 管理后台**

```bash
# 回到项目根目录
cd ../..

# 启动管理后台（Windows）
.\start_multi_admin.bat

# 或 Linux/Mac
./start_multi_admin.sh
```

然后在浏览器中：
1. 打开 http://localhost:8501
2. 左侧选择 "WhatsApp"
3. 点击 "启动机器人"

### 步骤 4: 扫码登录

1. 终端会显示二维码
2. 打开手机 WhatsApp
3. 前往：**设置 > 已连接的设备 > 连接设备**
4. 扫描终端中的二维码

### 步骤 5: 开始使用

✅ 登录成功后，机器人会自动：
- 回复所有私聊消息
- 回复群聊中的 @ 提及
- 回复包含关键词的群消息

## ⚙️ 配置文件

### prompt.txt - AI 人设
```text
你是一个幽默的个人助理，请用自然、友好的语气回复。
```

### keywords.txt - 群聊关键词
```text
帮我
求助
AI
机器人
```

### config.txt - 功能开关
```ini
PRIVATE_REPLY=on    # 私聊回复
GROUP_REPLY=on      # 群聊回复
```

## 📝 常用命令

```bash
# 启动
node bot.js

# 后台运行（Linux/Mac）
nohup node bot.js > bot.log 2>&1 &

# 查看日志
tail -f bot.log

# 停止（找到 PID 后）
kill <PID>
```

## ❓ 常见问题

**Q: 二维码不显示？**
A: 确保终端支持 Unicode，或使用 Web 管理后台

**Q: 认证失败？**
A: 删除 `.wwebjs_auth` 文件夹重新登录

**Q: AI 不回复？**
A: 检查 `.env` 配置和 API 余额

**Q: 依赖安装失败？**
A: 尝试使用国内镜像：`npm install --registry=https://registry.npmmirror.com`

## 🔗 更多帮助

完整文档：[platforms/whatsapp/README.md](README.md)


