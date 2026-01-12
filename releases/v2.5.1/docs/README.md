# AI 剧本系统文档总览 / AI Script System Documentation Overview

本目录汇总系统说明文档、架构与流程图、API与操作指南，帮助开发者与运营人员快速理解与使用系统。  
This directory consolidates documentation, architecture and flow diagrams, APIs and user guides for quick onboarding.

## 文档结构 / Documentation Structure
- 系统架构图 / System Architecture:
  - 图片：`docs/images/01-总览架构.png`（≥1280×720）
  - 说明：整体技术架构、平台组件与数据流
- 核心功能流程图 / Core Feature Flow:
  - 图片：`docs/images/03-telegram-触发与回复流程图.png`（≥1280×720）
  - 说明：消息接收、上下文记忆、AI调用与发送的主要流程
- 使用教程 / User Guide:
  - 文档：`docs/使用教程.md`
  - 内容：图文并茂的操作指南、关键功能截图与标注
- API 文档 / API Reference:
  - 文档：`docs/API文档.md`
  - 内容：接口参数、返回体与调用示例（兼容 OpenAI 格式）
- 版本与更新 / Versioning & Changelog:
  - 文档：`CHANGELOG.md`（仓库根目录）
  - 内容：版本号、兼容性、变更项、已知问题与未来规划

## 快速入口 / Quick Links
- 项目根 README / Root README: [README.md](file:///d:/AI%20Talk/README.md)
- 管理后台说明 / Admin Panel Guide: [ADMIN_README.md](file:///d:/AI%20Talk/ADMIN_README.md)
- 知识库接口 / Knowledge Base API: [KB-API.md](file:///d:/AI%20Talk/docs/KB-API.md)
- 系统架构说明 / System Architecture: [System-Architecture.md](file:///d:/AI%20Talk/docs/System-Architecture.md)

## 伪代码示例 / Pseudocode Example
消息处理核心算法（简化）  
Core message handling (simplified):

```text
on_message(event):
  user_id = event.sender
  text = event.content

  ctx = load_recent_context(user_id, limit=8)
  prompt = build_prompt(system_role, ctx, text)

  ai_resp = call_model(
    base_url=AI_BASE_URL,
    api_key=AI_API_KEY,
    model=AI_MODEL_NAME,
    messages=prompt
  )

  delay = random_between(50ms, 1200ms)  # typing simulation
  sleep(delay)
  send_reply(event.chat, ai_resp.text)

  persist_context(user_id, text, ai_resp.text)
```

## 关键截图 / Key Screenshots
- 管理后台总览（多平台面板） / Admin overview (multi-platform): `docs/images/05-管理后台多平台面板.png`
- 错误处理与日志归档 / Error handling & log archive: `docs/images/09-错误处理与日志归档.png`
- 客户到 AI 完整时序 / Full customer-to-AI sequence: `docs/images/10-客户到AI完整时序.png`

以上图片分辨率均不低于 1280×720。  
All images have resolution ≥1280×720.

