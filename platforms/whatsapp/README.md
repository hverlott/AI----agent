# 💬 WhatsApp AI 自动回复机器人

基于 `whatsapp-web.js` 的智能回复系统，支持私聊和群聊自动回复。

## ✨ 功能特性

- ✅ **私聊自动回复**：自动回复所有私聊消息（可配置开关）
- ✅ **群聊智能回复**：支持 @ 提及和关键词触发
- ✅ **上下文记忆**：记忆最近 5 条对话，提供连贯回复
- ✅ **热更新配置**：无需重启即可更新提示词、关键词、开关
- ✅ **模拟打字延迟**：显示"正在输入"状态，更像真人
- ✅ **DeepSeek AI**：接入强大的 AI 模型生成回复

## 📋 安装要求

### 系统要求
- **Node.js** 16.0 或更高版本
- **npm** 包管理器
- **WhatsApp** 账号（需要手机扫码登录）

### 依赖项
```json
{
  "whatsapp-web.js": "^1.23.0",  // WhatsApp Web 客户端
  "qrcode-terminal": "^0.12.0",   // 终端显示二维码
  "axios": "^1.6.0",              // HTTP 请求
  "dotenv": "^16.3.1"             // 环境变量
}
```

## 🚀 快速开始

### 1️⃣ 安装依赖

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

或手动安装：
```bash
cd platforms/whatsapp
npm install
```

### 2️⃣ 配置 .env（项目根目录）

确保根目录的 `.env` 文件包含：

```env
# AI API 配置
AI_API_KEY=sk-xxxxxxxxxxxx
AI_BASE_URL=https://api.55.ai/v1
AI_MODEL_NAME=deepseek-v3.1
```

### 3️⃣ 启动机器人

**方法一：使用启动脚本**

Windows:
```cmd
start.bat
```

Linux/Mac:
```bash
chmod +x start.sh
./start.sh
```

**方法二：直接运行**

```bash
node bot.js
```

### 4️⃣ 扫码登录

1. 启动后会显示二维码
2. 打开手机 WhatsApp
3. 前往：**设置 > 已连接的设备 > 连接设备**
4. 扫描终端显示的二维码

## 📖 配置说明

### 功能开关（config.txt）

位置：`项目根目录/config.txt`

```ini
# 私聊回复开关（on/off）
PRIVATE_REPLY=on

# 群聊回复开关（on/off）
GROUP_REPLY=on
```

### 关键词配置（keywords.txt）

位置：`项目根目录/keywords.txt`

```text
帮我
求助
AI
机器人
问一下
咨询

# 使用说明：
# - 每行一个关键词
# - 支持中英文
# - 不区分大小写
# - 以 # 开头的行会被忽略
```

### AI 人设配置（prompt.txt）

位置：`项目根目录/prompt.txt`

```text
你是一个由AI托管的自动回复助手。请用简短、礼貌、幽默的语气回复消息。
绝不要透露你是AI。如果遇到处理不了的问题，回复"稍等，本人稍后回复"。
```

## 🔧 高级配置

### 修改历史消息数量

编辑 `bot.js` 第 82 行：

```javascript
// 获取聊天历史（简化版）
async function getChatHistory(chat, limit = 5) {  // 修改这里的数字
    // ...
}
```

### 修改打字延迟

编辑 `bot.js` 第 238 行：

```javascript
// 模拟打字延迟
const typingDelay = Math.min(reply.length * 50, 3000);  // 50ms/字符，最多3秒
```

### 自定义回复逻辑

编辑 `bot.js` 第 180-230 行的消息处理逻辑：

```javascript
// 判断是否应该回复
let shouldReply = false;

if (!chat.isGroup) {
    // 私聊逻辑
    shouldReply = true;
} else {
    // 群聊逻辑：@ 提及或关键词匹配
    // 在这里添加自定义条件
}
```

## 📊 运行状态

### 正常运行

```
✅ WhatsApp 已连接！
🤖 AI 机器人已启动，开始监听消息...

提示：按 Ctrl+C 停止运行

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📩 收到私聊 [张三]: 你好
🤖 AI 正在思考...
📤 已回复: 你好！有什么可以帮助你的吗？
```

### 停止运行

按 `Ctrl+C` 优雅退出：

```
⚠️ 正在停止机器人...
✅ 机器人已停止
```

## ❓ 常见问题

### 1. 二维码无法显示

**问题**：终端不支持 Unicode 字符

**解决**：
- Windows：确保使用 PowerShell 或 Windows Terminal
- 手动登录：访问 `http://localhost:PORT` 查看二维码（需修改代码）

### 2. 认证失败

**问题**：`auth_failure` 错误

**解决**：
1. 删除 `.wwebjs_auth` 文件夹
2. 重新运行机器人扫码登录
3. 确保 WhatsApp 版本为最新

### 3. AI 回复失败

**问题**：`AI API 调用失败`

**解决**：
1. 检查 `.env` 文件配置
2. 确认 API Key 有效
3. 测试 API 连接：
   ```bash
   curl -X POST https://api.55.ai/v1/chat/completions \
     -H "Authorization: Bearer sk-xxxxx" \
     -H "Content-Type: application/json" \
     -d '{"model":"deepseek-v3.1","messages":[{"role":"user","content":"hi"}]}'
   ```

### 4. 依赖安装失败

**问题**：`npm install` 报错

**解决**：
```bash
# 清理缓存
npm cache clean --force

# 使用国内镜像
npm install --registry=https://registry.npmmirror.com

# 或使用 yarn
yarn install
```

### 5. 会话频繁断开

**问题**：WhatsApp 连接不稳定

**解决**：
- 确保网络稳定
- 避免在手机上同时登录相同会话
- 更新 `whatsapp-web.js` 到最新版本：
  ```bash
  npm update whatsapp-web.js
  ```

## 🔐 安全提示

1. **不要分享二维码**：扫码登录的二维码可以完全控制你的 WhatsApp 账号
2. **保护 .env 文件**：不要将 API Key 泄露给他人
3. **谨慎使用群发**：频繁群发可能导致账号被封
4. **遵守规则**：不要用于垃圾信息、诈骗等违法用途

## 📝 日志查看

日志输出到终端，包含：

- `📩` 收到的消息
- `🤖` AI 处理状态
- `📤` 发送的回复
- `❌` 错误信息

### 保存日志到文件

```bash
node bot.js 2>&1 | tee whatsapp_bot.log
```

## 🔄 集成 Web 管理后台

WhatsApp 已集成到多平台管理后台 (`admin_multi.py`)：

1. 启动管理后台：
   ```bash
   streamlit run admin_multi.py
   ```

2. 在侧边栏选择 "WhatsApp"

3. 功能：
   - 启动/停止机器人
   - 查看运行状态
   - 配置提示词和关键词
   - 查看运行日志

## 🆘 技术支持

如遇问题，请：

1. 查看控制台输出的错误信息
2. 检查 `.env` 配置是否正确
3. 确保 Node.js 版本 >= 16
4. 尝试删除 `.wwebjs_auth` 重新登录
5. 更新依赖：`npm update`

## 📄 许可证

MIT License

---

**提示**：WhatsApp 可能会限制频繁自动回复的账号，建议：
- 添加回复延迟
- 避免 24 小时不间断运行
- 不要在短时间内回复大量消息
- 仅在信任的设备上登录
