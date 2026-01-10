# 系统升级说明文档 (Upgrade Guide)

**适用版本**:
- v1.x -> v2.0
- v2.2.0 -> v2.3.0

**更新日期**: 2026-01-09

---

## 1. 版本更新摘要

本次升级包含以下核心变更：

### v2.3.0（相对 v2.2.0）
- **新增菜单**：🧪 AI学习中心、🧩 技能中心。
- **数据隔离**：学习数据、技能配置支持按平台/租户/业务线隔离，并可绑定到指定 AI 配置。
- **平滑迁移**：新能力默认关闭或不影响默认行为，需显式启用后生效。

### v2.0（相对 v1.x）
- **Supervisor 增强**：会话列表手动刷新、错误处理与加载提示。
- **系统优化**：日志读取缓存减少磁盘 IO。
- **文档更新**：更新架构图与操作指南。

## 2. 升级前准备 (Pre-requisites)

在执行升级前，请确保满足以下条件：

### 2.1 环境检查
- Python 3.8+ 环境正常。
- 依赖包未发生变化 (无需 `pip install`)。

### 2.2 数据备份 (Backup)
建议备份以下关键数据，以防万一：

1. **配置文件**:
   - `platforms/telegram/config.txt`
   - `platforms/telegram/prompt.txt`
   - `platforms/telegram/keywords.txt`
   - `.env` (API 密钥)
2. **数据库**:
   - `data/knowledge_base/db.json` (知识库索引)
   - `data/sessions.db` (如果使用 SQLite)
3. **日志文件**:
   - `platforms/telegram/logs/*.log`
   - `platforms/telegram/logs/*.jsonl`

## 3. 详细升级步骤 (Step-by-Step)

### 步骤 1: 停止服务
请关闭所有正在运行的终端窗口，包括：
- Telegram Bot 主程序 (`python main.py`)
- Web 管理后台 (`start_admin.bat`)

### 步骤 2: 更新代码
将新版代码覆盖到项目根目录：
- `admin_multi.py` (核心后台逻辑)
- `docs/*` (最新文档)

### 步骤 3: 启动服务
1. **启动管理后台**:
   双击运行 `start_admin.bat`。
   > 浏览器自动打开 `http://localhost:8501`。

2. **启动机器人**:
   打开新的终端窗口，运行：
   ```cmd
   python main.py
   ```

## 4. 验证升级 (Verification)

### 4.1 权限验证
- 登录管理后台，检查侧边栏「角色」「租户ID」。
- **预期**:
  - SuperAdmin：可编辑租户ID并访问系统管理/API 网关等模块。
  - BusinessAdmin：租户ID只读且仅显示允许的业务侧模块。

### 4.2 v2.3.0 功能验证（新增模块）
- 进入「🧪 AI学习中心」，筛选并勾选记录，执行一次批量标记（可学习/垃圾/绑定AI/标签）。
- 进入「📦 导出学习集」，导出 JSONL 并确认生成在 `data/tenants/<tenant_id>/learning_exports/`。
- 进入「🧩 技能中心」，创建一条启用技能并选择适用回复路径（kb_only/script_only/both）。

### 4.2 功能验证
- 进入 `Supervisor` 面板。
- **预期**: 顶部出现 `🔄 刷新会话列表` 按钮。
- 点击按钮，**预期**: 按钮变为加载状态，随后列表更新。

### 4.3 性能验证
- 进入 `Telegram` -> `日志` 面板。
- **预期**: 日志加载速度明显快于旧版本。

## 5. 故障排除 (Troubleshooting)

| 问题现象 | 可能原因 | 解决方案 |
| :--- | :--- | :--- |
| **页面显示 "Permission Denied"** | Session 状态未刷新 | 点击页面右上角 `Rerun` 或刷新浏览器 (F5)。 |
| **Supervisor 列表为空** | 数据库连接失败 | 检查控制台报错信息；确认 `data/` 目录权限。 |
| **日志加载旧数据** | 缓存未过期 | 等待 2-5 秒后再次刷新，或重启后台。 |

## 6. 回滚方案 (Rollback Plan)

若升级后发现严重阻断性问题，请执行回滚：

1. 停止所有服务。
2. 使用备份的 `admin_multi.py` 覆盖回当前文件。
3. 重启服务。
4. 联系开发团队反馈问题。

## 修订记录

| 版本号 | 更新日期 | 修改人 | 修改摘要 |
| :--- | :--- | :--- | :--- |
| v2.3.0-docs | 2026-01-09 | Tech Writer | 补充 v2.3.0 新模块与权限验证口径 |
