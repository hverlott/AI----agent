# 系统功能结构（Pro 版）

## 总览
- 多平台社交 AI 机器人与管理后台，覆盖 Telegram、WhatsApp，并预留 Facebook/Messenger/微信扩展
- 统一数据层（SQLite）、多语言（中/英）与多时区显示，租户化配置与审计全链路
- 管理后台提供配置、群发、日志、统计、订阅与品牌定制、API 网关、系统自动化等能力

## 核心模块
- 管理后台：[admin_multi.py](file:///d:/AI%20Talk/admin_multi.py)
- 机器人主链路：[main.py](file:///d:/AI%20Talk/main.py)
- 数据层（SQLite）：[database.py](file:///d:/AI%20Talk/database.py)
- 商业化逻辑：[business_core.py](file:///d:/AI%20Talk/business_core.py)
- 审核系统：[audit_manager.py](file:///d:/AI%20Talk/audit_manager.py)
- 关键词管理：[keyword_manager.py](file:///d:/AI%20Talk/keyword_manager.py)
- Telegram 平台目录：platforms/telegram/*
- WhatsApp 平台目录：platforms/whatsapp/*

## 管理后台面板
- 知识库（KB）：管理/导入/检索测试/设置；SQLite 优先，兼容文本 KB
- 审核配置（Auditor）：关键词管理、审核日志（DB 优先，文件兜底）、远程审核设置
- 商业化运营（Business）：数据看板、订阅管理（Free/Pro/Enterprise）、品牌定制
- Telegram：启停/登录状态/.env 检测；配置/群发/日志/统计/流程图
- WhatsApp：启停/登录二维码与扫码步骤；配置/日志/统计
- 账号管理（Accounts）：平台/账号/分组/标签/刷新间隔，添加更新与列表展示
- AI 配置中心（AGNT）：服务商/模型/Base URL/A-B 权重/超时；API Key 仅运行时使用
- API 网关：路由添加/更新（Path/Method/Auth/Rate Limit），列表展示
- 系统配置自动化：.env 生成与备份、会话文件初始化、二次验证码查看敏感信息（加密/审计）

## 数据层与表结构（SQLite）
- tenants：租户配置（plan、config JSON、timestamps）
- audit_logs：审计日志（tenant_id、user_role、action、details JSON、timestamp）
- message_events：消息流水（平台/群/方向/类型/状态/tokens/timestamp）
- daily_stats：按日聚合（date、tenant、metric_name、metric_value）
- knowledge_base：KB 条目（id/tenant/标题/分类/标签/内容/来源/创建/更新）

## 多语言与多时区
- I18N：集中字典（tg_/wa_/audit_/bus_/api_/sys_/acc_/ai_/kb_/common_）
- tr(key)：按 st.session_state.lang 渲染（默认 zh）
- format_time(dt, tz)：按 st.session_state.timezone 格式化（默认 Asia/Shanghai）

## 角色与权限（RBAC）
- 侧边栏身份切换：Admin / Auditor / Operator / TenantAdmin
- 审核面板仅 Auditor 可访问

## 关键流程
- Telegram 消息处理：关键词/白名单/上下文→QA 命中或 KB 检索→AI 草稿→关键词拦截→审核 AI（本地/远程）→PASS/FAIL→回复与兜底→日志与统计更新  
  参考：[main.py](file:///d:/AI%20Talk/main.py)
- 知识库加载与检索：SQLite 优先、文本兼容；bigram/token/模糊比对综合  
  参考：[main.py:load_kb_entries](file:///d:/AI%20Talk/main.py#L250-L286)
- 审核日志加载：数据库优先，多时区格式化，异常本地化并回退文件  
  参考：[admin_multi.py:render_audit_panel](file:///d:/AI%20Talk/admin_multi.py#L3515-L3554)

## 配置与安全
- .env 自动生成与备份；Secrets 对称加密存储（Fernet 可用时）
- 查看明文需二次验证码并记审计日志；API Key 默认不落盘
  参考：[render_sys_config_panel](file:///d:/AI%20Talk/admin_multi.py#L2685-L2788)

## 日志与统计
- Telegram：system/private/group/audit 四类日志；审核趋势图（近 1000 行）
- Stats：total_messages/total_replies/success_count/error_count/start_time/last_active
- WhatsApp：同构日志与统计，支持刷新与清空

## 运行与预览
- 管理后台：streamlit run admin_multi.py
- 预览地址（本地）：http://localhost:8502/
- Telegram：Telethon 客户端；AI 使用 AsyncOpenAI + httpx（自动修复 Base URL）

## I18N 命名约定
- 模块前缀：tg_ / wa_ / audit_ / bus_ / api_ / sys_ / acc_ / ai_ / kb_ / common_
- 键值覆盖：按钮/标题/提示/错误/成功/标签/统计维度等全面本地化

## 路线图（Pro）
- 已完成：数据层迁移、面板多语言化与多时区、审核拦截与日志、WhatsApp 登录与启停、账号与 AI 配置本地化
- 待完善：Telegram 群发成功/失败提示结构化与 I18N、Business 图表列名与说明统一、API 网关鉴权与限流策略扩展

