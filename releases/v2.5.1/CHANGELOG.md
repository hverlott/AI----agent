# 更新日志 (Changelog)

## [2.5.1] - 2026-01-09

### ✨ 新增功能 (Features)
- **多API凭证管理 (Multi-API Management)**:
  - 支持在【账号管理】中添加多个 Telegram Bot API 配置 (API ID/Hash/AI Key)。
  - Telegram 面板新增 **API 配置选择器**，可灵活切换并应用不同的 API 凭证启动机器人。
- **租户隔离增强**:
  - API 配置现存储于 `data/tenants/{tenant_id}/api_configs.json`，确保租户间数据完全隔离。
  - 移除了环境变量对 API 密钥的强制依赖，支持纯 SaaS 模式配置。

### 🏗️ 架构重构 (Refactoring)
- **模块化架构 (Modular Architecture)**:
  - 将庞大的 `main.py` 拆分为清晰的模块结构，位于 `src/` 目录下。
  - **Core**: 核心组件（数据库、日志、AI客户端）。
  - **Config**: 统一的配置加载与管理。
  - **Modules**: 业务模块（Telegram, Knowledge Base, Audit, Orchestrator）。
  
- **低耦合设计 (Decoupling)**:
  - 实现了 `ConfigManager` 和 `TenantLogger`，不再依赖全局变量。
  - Telegram 机器人逻辑封装为 `TelegramBotApp` 类。
  - 知识库逻辑独立为 `KBEngine` 和 `KBLoader`。

- **代码质量**:
  - 移除了冗余的全局状态。
  - 统一了 AI 客户端的 SSL 验证和 Base URL 修复逻辑。
  - 优化了导入路径，减少了循环依赖风险。

### ⚡ 优化 (Improvements)
- **启动速度**: 模块按需加载，提升了系统初始化效率。
- **可维护性**: 业务逻辑分散在独立文件中，便于后续功能扩展和 Bug 修复。

---

## [2.4.0] - 2026-01-09

### ✨ 新增功能 (Features)
- **多租户架构升级 (Multi-Tenancy)**:
  - 实现了完全的数据隔离：每个租户拥有独立的配置、日志、知识库和账号数据。
  - 新增 `data/tenants/{tenant_id}/` 目录结构，支持无限扩展租户。
  - 系统管理员可管理所有租户，业务管理员仅可见自己租户的数据。

- **多账号管理 (Multi-Account Support)**:
  - **账号选择器**: Telegram 控制面板顶部新增账号切换功能，支持单租户管理多个 Telegram 账号。
  - **批量导入**: 支持批量上传 Session 文件，自动识别账号。
  - **账号列表优化**: 全新的账号管理界面，支持查看 Session 状态、批量勾选删除账号及关联文件。

- **审计与安全 (Audit & Security)**:
  - **操作审计**: 关键操作（配置修改、账号增删）全量记录审计日志。
  - **审计面板**: 租户后台新增 "Audit Logs" 面板，方便追踪变更记录。

### ⚡ 优化 (Improvements)
- **Telegram 面板**:
  - 登录状态检测现在基于选中的账号，而非全局 Session。
  - 启动/停止/重启机器人时，会自动加载当前选中账号的 Session。
- **UI 交互**:
  - 账号列表升级为交互式表格，操作更便捷。
  - 优化了错误提示和引导流程。

### 🐛 修复 (Bug Fixes)
- 修复了多账号环境下，机器人启动时 Session 混淆的问题。
- 修复了 Streamlit 数据编辑器列名冲突 (`_index` 保留字段) 导致的崩溃问题。
- 修复了删除账号时未能彻底清理磁盘 Session 文件的问题。

---

## [2.3.0] - 2026-01-08
...
