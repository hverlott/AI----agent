# AI Customer Service System (SaaS Edition)

## 📖 简介 (Introduction)
SaaS-AIs 是一个企业级 AI 客服管理系统，支持多租户、多平台（Telegram, WhatsApp, WeChat 等）接入。它基于 LLM 大模型技术，提供自动回复、知识库问答、意图识别和多轮对话管理功能。

## � 最新版本 v2.4.0 特性
- **多租户支持**: 完善的数据隔离，支持无限开通租户。
- **多账号矩阵**: 单租户可管理多个社交媒体账号，一键切换。
- **可视化编排**: 内置对话流程编排器 (Orchestrator)，支持拖拽式配置。
- **审计日志**: 全操作留痕，安全合规。

## �️ 快速开始 (Quick Start)

### 1. 环境准备
- Windows / Linux / macOS
- Python 3.10+
- 推荐使用虚拟环境

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 启动系统
**单机开发/测试模式**:
```bash
python admin_multi.py
```
*默认访问地址: http://localhost:8501*

**生产环境启动**:
请参考 `DEPLOYMENT_GUIDE.md`

## 📂 目录结构
```
d:\SaaS-AIs/
├── admin_multi.py      # 主管理后台入口 (SaaS版)
├── main.py             # 机器人启动入口 (Wrapper)
├── src/                # 核心源码 (v2.5.0+)
│   ├── config/         # 配置管理
│   ├── core/           # 核心组件 (DB, Logger, AI)
│   ├── modules/        # 业务模块 (Telegram, KB, Audit)
│   └── utils/          # 通用工具
├── data/
│   └── tenants/        # 租户数据隔离目录
├── platforms/          # 旧版适配器 (Legacy)
└── docs/               # 开发与使用文档
```

## 🔐 账号管理
1. 登录后台 -> **业务管理** -> **账号管理**。
2. 支持 **批量导入** `.session` 文件或手动添加账号。
3. 在 **Telegram 控制面板** 中选择要操作的账号进行启动/停止。

## 📚 文档资源
- [用户手册 (User Guide)](docs/USER_GUIDE.txt)
- [更新日志 (Changelog)](CHANGELOG.md)
- [部署指南 (Deployment)](DEPLOYMENT_GUIDE.md)

## 📄 License
MIT License
