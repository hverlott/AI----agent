# 系统升级说明文档 (Upgrade Guide)

**适用版本**: v1.x -> v2.0 (SuperAdmin & Supervisor Enhanced)  
**更新日期**: 2026-01-07

---

## 1. 版本更新摘要

本次升级包含以下核心变更：
- **权限管控**: 强制启用 SuperAdmin 单一角色，移除普通 User/Admin 角色切换，增强系统安全性。
- **Supervisor 增强**: 增加会话列表手动刷新功能，优化数据库连接错误处理，增加加载状态提示。
- **系统优化**: 优化日志读取性能 (Cache)，减少磁盘 IO。
- **文档更新**: 全面更新架构图与操作指南。

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
- 登录管理后台，检查侧边栏。
- **预期**: 不再显示 "当前角色" 切换下拉框，默认拥有所有模块的编辑权限 (SuperAdmin)。

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
