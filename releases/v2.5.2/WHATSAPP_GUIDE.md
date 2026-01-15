# 💬 WhatsApp AI Bot 完整指南

## 📋 目录

1. [功能特性](#功能特性)
2. [安装步骤](#安装步骤)
3. [快速启动](#快速启动)
4. [Web 管理后台](#web-管理后台)
5. [配置说明](#配置说明)
6. [常见问题](#常见问题)
7. [注意事项](#注意事项)

---

## ✨ 功能特性

### 核心功能
- ✅ **私聊自动回复**：自动回复所有私人消息
- ✅ **群聊智能回复**：@ 提及或关键词触发自动回复
- ✅ **上下文记忆**：记住最近 5 条对话，提供连贯回复
- ✅ **热更新配置**：无需重启即可更新人设、关键词、开关
- ✅ **打字状态**：显示"正在输入"，模拟真人
- ✅ **AI 驱动**：使用 DeepSeek 强大的 AI 模型

### 管理功能
- 🎛️ **Web 管理界面**：可视化控制所有功能
- 📊 **实时状态监控**：查看运行状态、登录状态
- 📜 **日志查看**：实时查看机器人运行日志
- ⚙️ **在线配置**：Web 界面修改配置

---

## 🚀 安装步骤

### 前置要求

1. **Node.js** (v16 或更高)
   - 下载：https://nodejs.org/
   - 验证：`node --version`

2. **Python 3.8+** (管理后台需要)
   - 已安装 Streamlit
   - 已安装 psutil

3. **WhatsApp 账号**
   - 需要手机扫码登录

### 安装依赖

#### Windows

```cmd
cd D:\AI Talk\platforms\whatsapp
install.bat
```

#### Linux/Mac

```bash
cd platforms/whatsapp
chmod +x install.sh install.sh start.sh
./install.sh
```

#### 手动安装

```bash
cd platforms/whatsapp
npm install
```

---

## 🎯 快速启动

### 方法一：命令行启动（推荐用于首次登录）

1. 打开终端，进入 WhatsApp 目录：
   ```bash
   cd platforms/whatsapp
   ```

2. 启动机器人：
   ```bash
   node bot.js
   ```

3. 扫描二维码登录：
   - 手机打开 WhatsApp
   - 前往：**设置 > 已连接的设备 > 连接设备**
   - 扫描终端显示的二维码

4. 等待登录成功提示：
   ```
   ✅ WhatsApp 已连接！
   🤖 AI 机器人已启动，开始监听消息...
   ```

### 方法二：Web 管理后台启动

1. 启动多平台管理后台：

   **Windows:**
   ```cmd
   D:\AI Talk> .\start_multi_admin.bat
   ```

   **Linux/Mac:**
   ```bash
   ./start_multi_admin.sh
   ```

2. 浏览器打开 http://localhost:8501

3. 左侧栏选择 "💬 WhatsApp"

4. 点击 "🚀 启动机器人" 按钮

5. 首次登录需要在终端查看二维码：
   - 打开项目目录下的日志文件
   - 或者直接使用命令行启动（推荐）

---

## 🎛️ Web 管理后台

### 访问地址

```
http://localhost:8501
```

### 功能面板

#### 1. 状态监控

- **运行状态**：显示机器人是否运行中（PID）
- **登录状态**：显示是否已登录 WhatsApp
- **配置状态**：显示 .env 是否已配置

#### 2. 控制按钮

- **🚀 启动机器人**：启动 WhatsApp 自动回复
- **⛔ 停止机器人**：停止运行
- **🔄 重启机器人**：重新启动（更新配置后）

#### 3. 配置管理

- **AI 人设**：编辑机器人的回复风格
- **触发关键词**：设置群聊触发词（每行一个）
- **功能开关**：
  - 私聊回复开关
  - 群聊回复开关

#### 4. 日志查看

- 实时查看机器人运行日志
- 刷新日志按钮
- 清空日志按钮

#### 5. 统计数据（开发中）

- 今日消息数
- 今日回复数
- 成功率

---

## ⚙️ 配置说明

所有配置文件位于项目根目录：

### 1. `.env` - API 配置

```env
# AI API 配置
AI_API_KEY=sk-xxxxxxxxxxxx
AI_BASE_URL=https://api.55.ai/v1
AI_MODEL_NAME=deepseek-v3.1
```

### 2. `prompt.txt` - AI 人设

```text
你是一个由AI托管的自动回复助手。请用简短、礼貌、幽默的语气回复消息。
绝不要透露你是AI。如果遇到处理不了的问题，回复"稍等，本人稍后回复"。
```

**修改提示：**
- 可以在 Web 管理后台修改
- 也可以直接编辑文件
- 修改后立即生效，无需重启

### 3. `keywords.txt` - 群聊关键词

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

**触发逻辑：**
- 群聊中包含任意关键词 → 自动回复
- 被 @ 提及 → 自动回复

### 4. `config.txt` - 功能开关

```ini
# 私聊回复开关（on/off）
PRIVATE_REPLY=on

# 群聊回复开关（on/off）
GROUP_REPLY=on
```

**修改方式：**
- Web 管理后台：使用开关按钮
- 手动编辑：将 `on` 改为 `off` 关闭功能

---

## ❓ 常见问题

### 1. 二维码无法显示

**问题**：终端不显示二维码或显示乱码

**解决方法：**
- Windows：使用 PowerShell 或 Windows Terminal
- 安装 Unicode 字体（如 Cascadia Code）
- 或者使用其他方式显示二维码（修改代码）

### 2. 认证失败

**错误信息**：`auth_failure` 或 `Authentication failed`

**解决方法：**
1. 停止机器人
2. 删除 `platforms/whatsapp/.wwebjs_auth` 文件夹
3. 重新启动并扫码登录
4. 确保 WhatsApp 版本为最新

### 3. AI 回复失败

**错误信息**：`AI API 调用失败`

**解决方法：**
1. 检查 `.env` 文件配置是否正确
2. 确认 API Key 有效且有余额
3. 测试 API 连接：
   ```bash
   curl -X POST https://api.55.ai/v1/chat/completions \
     -H "Authorization: Bearer sk-xxxxx" \
     -H "Content-Type: application/json" \
     -d '{"model":"deepseek-v3.1","messages":[{"role":"user","content":"hi"}]}'
   ```

### 4. 依赖安装失败

**错误信息**：`npm install` 失败

**解决方法：**
```bash
# 清理缓存
npm cache clean --force

# 使用国内镜像
npm install --registry=https://registry.npmmirror.com

# 或使用 cnpm
npm install -g cnpm --registry=https://registry.npmmirror.com
cnpm install

# 或使用 yarn
npm install -g yarn
yarn install
```

### 5. 会话频繁断开

**问题**：WhatsApp 连接不稳定，频繁掉线

**解决方法：**
- 确保网络稳定
- 避免在手机上同时登录相同会话
- 更新 `whatsapp-web.js` 到最新版本：
  ```bash
  cd platforms/whatsapp
  npm update whatsapp-web.js
  ```
- 检查是否被 WhatsApp 限制（频繁自动回复可能导致）

### 6. 机器人无法启动

**错误信息**：各种启动失败

**排查步骤：**
1. 检查 Node.js 是否安装：`node --version`
2. 检查依赖是否安装：`ls node_modules`（查看是否有 node_modules 文件夹）
3. 检查端口占用：确保没有其他 WhatsApp Web 实例运行
4. 查看详细错误：`node bot.js` 直接运行查看错误信息

### 7. Web 管理后台无法启动机器人

**问题**：点击启动按钮没反应或报错

**解决方法：**
1. 确保 Node.js 在 PATH 中：`node --version`
2. 确保 `psutil` 已安装：`pip install psutil`
3. 首次使用建议用命令行启动（需要扫码）
4. 查看日志文件：`platforms/whatsapp/bot.log`

---

## ⚠️ 注意事项

### 安全提示

1. **保护登录凭证**
   - 不要分享二维码
   - 扫码登录后，任何人都可以完全控制你的 WhatsApp

2. **保护 API Key**
   - 不要将 `.env` 文件提交到 Git
   - 不要在公开场合泄露 API Key

3. **遵守规则**
   - 不要用于垃圾信息、诈骗等违法用途
   - WhatsApp 可能会封禁违规账号

### 使用建议

1. **避免被封号**
   - 不要 24 小时不间断运行
   - 添加适当的回复延迟
   - 不要在短时间内回复大量消息
   - 不要频繁群发消息

2. **稳定运行**
   - 定期检查日志
   - 监控 API 余额
   - 保持网络稳定
   - 定期更新依赖

3. **隐私保护**
   - 不要在不信任的设备上登录
   - 定期检查已连接的设备
   - 谨慎处理用户隐私数据

### 资源消耗

- **内存**：约 200-500 MB
- **CPU**：低（空闲时 < 5%）
- **网络**：根据消息量而定
- **存储**：会话数据约 50-100 MB

---

## 📚 相关文档

- **详细文档**：[platforms/whatsapp/README.md](platforms/whatsapp/README.md)
- **快速上手**：[platforms/whatsapp/QUICKSTART.md](platforms/whatsapp/QUICKSTART.md)
- **主项目文档**：[README.md](README.md)

---

## 🆘 获取帮助

如遇到其他问题：

1. 查看日志文件：`platforms/whatsapp/bot.log`
2. 查看控制台输出
3. 检查 Node.js 和依赖版本
4. 尝试删除 `.wwebjs_auth` 重新登录
5. 查阅 `whatsapp-web.js` 官方文档

---

## 📄 许可证

MIT License

---

**最后提醒**：WhatsApp 可能会限制频繁自动回复的账号，请：
- 合理设置回复频率
- 避免长时间不间断运行
- 不要发送垃圾信息
- 仅在信任的设备上登录
- 定期检查账号状态

祝使用愉快！ 💬✨


