# API 文档 / API Reference

本项目使用“兼容 OpenAI 格式”的推理接口，并提供本地脚本与配置文件接口。  
This project uses OpenAI-compatible inference APIs and local script/config interfaces.

## 1. AI 推理接口 / AI Inference API
兼容端点（示例）：`AI_BASE_URL=https://api.55.ai/v1`  
模型（示例）：`AI_MODEL_NAME=deepseek-v3.1`

### 1.1 Chat Completions
POST `{AI_BASE_URL}/chat/completions`

请求 / Request:
```json
{
  "model": "deepseek-v3.1",
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "你好，帮我规划今天的安排。" }
  ],
  "temperature": 0.7,
  "stream": false
}
```

响应 / Response:
```json
{
  "id": "cmpl-123",
  "object": "chat.completion",
  "created": 1712345678,
  "model": "deepseek-v3.1",
  "choices": [
    {
      "index": 0,
      "message": { "role": "assistant", "content": "好的，以下是建议的安排…" },
      "finish_reason": "stop"
    }
  ],
  "usage": { "prompt_tokens": 25, "completion_tokens": 134, "total_tokens": 159 }
}
```

示例调用 / Example:
```bash
curl -X POST "$AI_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

### 1.2 错误结构 / Error Schema
```json
{
  "error": { "message": "Rate limit exceeded", "type": "rate_limit" }
}
```

## 2. 配置与热更新 / Config & Hot Reload
文件接口 / File Interfaces:
- 人设 / Persona: [prompt.txt](file:///d:/AI%20Talk/prompt.txt)
- 关键词 / Keywords: [keywords.txt](file:///d:/AI%20Talk/keywords.txt)
- 平台配置 / Platform Configs: [PLATFORM_CONFIG_GUIDE.md](file:///d:/AI%20Talk/PLATFORM_CONFIG_GUIDE.md)
- 管理后台 / Admin: [admin_multi.py](file:///d:/AI%20Talk/admin_multi.py)

约定 / Conventions:
- 修改文本文件后，管理后台会自动刷新，无需重启
- 对于多租户场景，配置按租户进行隔离与落盘

## 3. Telegram 运行脚本 / Telegram Runtime Scripts
### 3.1 自动回复机器人 / Auto-Responder
```bash
python main.py
```
- 首次运行将进行登录验证（手机号、验证码、云密码）
- 会话文件保存在 `platforms/telegram/` 下（确保 .gitignore 排除）

### 3.2 群发工具 / Broadcast
```bash
python broadcast.py --group "VIP客户" --file msg.txt
```
参数 / Parameters:
- `--group`: 目标分组
- `--file`: 文本文件（群发内容）
- `--dry-run`: 仅预览，不实际发送

异常 / Exceptions:
- `FloodWait`: 按服务端返回秒数进行退避
- `PeerFlood`: 触发风控，需扩大发送间隔与减少发送量

## 4. 管理后台 / Admin Panel
启动 / Launch:
```bash
streamlit run admin_multi.py
```
功能 / Features:
- 平台选择、日志监控、AI配置、群发管理、系统信息
- 配置保存与读取采用文件接口（热更新）

## 5. 安全与限流 / Security & Rate Limiting
- 所有外部调用需 `Authorization: Bearer {AI_API_KEY}`
- 遵循平台限流与政策，避免批量高频触发
- 建议启用代理与最小权限密钥，并隔离运行时会话文件

## 6. 兼容性 / Compatibility
- Python 3.8+
- Telethon 1.34.0+
- Streamlit 1.30.0+
- OpenAI-compatible endpoints (DeepSeek/OpenAI/Azure/LocalAI)

