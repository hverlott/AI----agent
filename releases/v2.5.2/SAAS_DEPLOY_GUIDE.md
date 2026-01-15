# 🚀 SaaS AI 系统 v2.5.1 运维部署指南 (Ops Guide)

本文档适用于运维人员搭建 SaaS-AI-System v2.5.1 版本的生产或测试环境。

---

## 1. 环境准备 (Prerequisites)

请确保服务器满足以下基础要求：

### 操作系统
- **推荐**: Linux (Ubuntu 20.04 LTS+ / CentOS 7+)
- **支持**: Windows Server 2019+, macOS

### 运行环境
- **Python**: 版本必须为 **3.10** 或更高。
- **虚拟环境**: 强烈建议使用 `venv` 或 `conda` 进行环境隔离，避免依赖冲突。

### 网络配置
- **外网访问**: 服务器必须能访问 Telegram API (`api.telegram.org`)。
- **端口开放**: 需开放 TCP 端口 **8501**（默认管理后台端口）。
- **代理设置**: 若服务器位于国内，请配置系统级代理或在 `.env` 中指定 `HTTPS_PROXY`。

---

## 2. 安装部署 (Installation)

假设发布包 `SaaS-AI-System-v2.5.1-Release-xxxx.zip` 已上传至服务器。

### 步骤 A: 解压文件
将发布包解压到目标应用目录，例如 `/opt/saas-ai/` (Linux) 或 `D:\SaaS-AI\` (Windows)。

**Linux 示例:**
```bash
mkdir -p /opt/saas-ai
unzip SaaS-AI-System-v2.5.1-Release-xxxx.zip -d /opt/saas-ai/
cd /opt/saas-ai
```

### 步骤 B: 创建虚拟环境
**Linux / macOS:**
```bash
# 创建名为 venv 的虚拟环境
python3 -m venv venv

# 激活环境
source venv/bin/activate
```

**Windows:**
```cmd
:: 创建名为 venv 的虚拟环境
python -m venv venv

:: 激活环境
venv\Scripts\activate
```

### 步骤 C: 安装依赖
在激活的虚拟环境中，执行以下命令安装依赖库：
```bash
# 升级 pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

> **⚠️ 常见问题**: 
> 如果遇到 `protobuf` 相关报错，请设置环境变量 `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` 后重试。

---

## 3. 启动服务 (Startup)

本系统采用 SaaS 多租户架构，统一通过 **管理后台 (Admin Panel)** 进行租户和机器人的管理。

### 方式 1: Windows 脚本启动
直接双击运行根目录下的批处理脚本：
- **`start_multi_admin.bat`**

### 方式 2: Linux/macOS 脚本启动
```bash
# 赋予脚本执行权限
chmod +x start_multi_admin.sh

# 启动服务
./start_multi_admin.sh
```

### 方式 3: 手动命令启动 (通用)
如果脚本无法运行，可直接使用 streamlit 命令启动：
```bash
# 确保已激活虚拟环境
streamlit run admin_multi.py --server.port 8501 --server.address 0.0.0.0
```

### 方式 4: Systemd 守护进程 (生产环境推荐)
在 Linux 生产环境中，建议配置为系统服务以实现开机自启和崩溃重启。

创建文件 `/etc/systemd/system/saas-ai.service`:
```ini
[Unit]
Description=SaaS AI Admin Panel Service
After=network.target

[Service]
# 修改为实际的运行用户
User=root
# 修改为实际的项目路径
WorkingDirectory=/opt/saas-ai
# 修改为实际的 venv 路径
ExecStart=/opt/saas-ai/venv/bin/streamlit run admin_multi.py --server.port 8501 --server.address 0.0.0.0
# 失败自动重启
Restart=always
RestartSec=5
# 环境变量 (如需代理)
# Environment="HTTPS_PROXY=http://127.0.0.1:7890"

[Install]
WantedBy=multi-user.target
```

**启用并启动服务:**
```bash
systemctl daemon-reload
systemctl enable saas-ai
systemctl start saas-ai
systemctl status saas-ai
```

---

## 4. 验证与交付 (Verification)

服务启动后，请执行以下验证步骤：

1.  **访问管理后台**: 
    在浏览器中输入 `http://<服务器IP>:8501`。
2.  **创建租户**:
    首次进入无需密码，在左侧菜单栏选择 "Tenant Management"（或系统管理），创建一个测试租户（如 `tenant_demo`）。
3.  **功能自检**:
    - **Telegram 面板**: 切换到新租户，确认能看到 Telegram 配置界面。
    - **知识库测试**: 在 "Knowledge Base" 页面上传一个小的 PDF 文件，确认状态能变为 "Indexed"（已索引）。

---

## 5. 运维与维护 (Operations)

### 📂 数据目录结构
所有业务数据均存储在 `data/` 目录下，**请务必定期备份**：
- `data/tenants/`: **[核心]** 租户数据（配置文件、知识库索引、会话日志）。
- `data/backups/`: 系统自动备份目录。

### 📝 日志监控
- **控制台日志**: `systemctl status saas-ai` 或直接查看前台输出。
- **业务日志**: 
  - 路径: `data/tenants/<tenant_id>/platforms/telegram/logs/`
  - 文件: `bot.log` (机器人运行日志), `audit.log` (操作审计日志)。

### 🔄 版本升级
1. 备份 `data/` 目录。
2. 覆盖代码文件（保留 `data/` 不被覆盖）。
3. 重新运行 `pip install -r requirements.txt` 更新依赖。
4. 重启服务。
