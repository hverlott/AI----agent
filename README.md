# AI Customer Service System (SaaS Edition)

> **Latest Version**: v2.5.1 (Cloud-Native Multi-Tenant)

SaaS-AIs is an enterprise-grade AI customer service management system supporting multi-tenancy and multi-platform integration (Telegram, WhatsApp, etc.). It leverages LLM technology to provide automatic replies, knowledge base Q&A, intent recognition, and multi-turn conversation management.

## 🚀 Key Features (v2.5.1)

- **Multi-Tenant Architecture**: Complete data and configuration isolation for infinite tenants.
- **Platform Isolation**: Dedicated environments for Telegram and WhatsApp with independent data paths.
- **Visual Orchestration**: Built-in flow orchestrator for drag-and-drop conversation logic.
- **RBAC & Audit**: Role-based access control with strict tenant-level audit logging.
- **One-Click Deployment**: Simplified startup scripts for Windows and Linux.

## 📂 Repository Structure

The project follows a release-based structure. The latest stable version is located in `releases/v2.5.1`.

```
/
├── releases/
│   └── v2.5.1/           <-- 🌟 MAIN PROJECT ROOT
│       ├── admin_multi.py
│       ├── platforms/
│       ├── src/
│       └── ...
└── ...
```

## 🛠️ Quick Start

### 1. Clone & Navigate
```bash
git clone https://github.com/hverlott/AI----agent.git
cd AI----agent/releases/v2.5.1
```

### 2. Install Dependencies
```bash
# Python
pip install -r requirements.txt

# Node.js (for WhatsApp)
cd platforms/whatsapp
npm install
cd ../..
```

### 3. Configure Environment
Copy the example environment file and configure your API keys:
```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run the System
**Admin Panel**:
```bash
# Linux/Mac
./start_admin.sh

# Windows
start_admin.bat
```
Or directly via Python:
```bash
streamlit run admin_multi.py
```

## 📚 Documentation

Detailed documentation can be found in the [docs](releases/v2.5.1/docs) directory of the release.

- [User Guide](releases/v2.5.1/docs/help_center/v1.0/zh_CN/1索引.md)
- [Deployment Guide](releases/v2.5.1/DEPLOYMENT_GUIDE.md)
- [WhatsApp Guide](releases/v2.5.1/WHATSAPP_GUIDE.md)

## 📄 License
MIT License
