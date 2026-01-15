# WhatsApp 模块租户隔离升级指南 (v2.5.1)

## 1. 概述

本版本对 WhatsApp 模块进行了重大的租户数据隔离优化，确保多租户环境下的数据安全和独立运行。升级后，WhatsApp 机器人将支持：
- 租户独立的会话存储 (Sessions)
- 租户独立的配置文件 (config.txt, keywords.txt, prompt.txt)
- 租户独立的日志和统计数据
- 支持多租户同时运行各自的 WhatsApp 机器人

## 2. 变更内容

### 2.1 bot.js (Node.js 核心)
- 引入 `TENANT_ID` 环境变量支持。
- 动态计算 `BASE_DIR`：
  - 如果存在 `TENANT_ID`，工作目录指向 `data/tenants/{TENANT_ID}/platforms/whatsapp`。
  - 否则，保持原有的共享目录模式（兼容旧版）。
- 更新 `LocalAuth` 存储路径为 `{BASE_DIR}/sessions`。
- 更新所有文件读写路径（stats.json, config.txt 等）为 `{BASE_DIR}/...`。

### 2.2 admin_multi.py (Python 管理端)
- 修正 `render_whatsapp_stats` 中的重置统计逻辑，使其写入租户特定的 `stats.json`。
- 确认 `start_whatsapp_bot` 已正确传递 `TENANT_ID` 环境变量。

## 3. 升级步骤

1.  **备份数据**：
    - 备份 `platforms/whatsapp` 目录下的 `bot.js` 和 `stats.json`。
    - 备份 `admin_multi.py`。

2.  **应用代码更新**：
    - 替换 `platforms/whatsapp/bot.js` 为新版代码。
    - 更新 `admin_multi.py`。

3.  **数据迁移 (如果需要保留旧租户数据)**：
    - 如果之前是单租户运行，数据位于 `platforms/whatsapp`。
    - 升级后，建议将旧数据迁移到默认租户目录 `data/tenants/default/platforms/whatsapp`。
    - 迁移命令示例 (Linux/Mac):
      ```bash
      mkdir -p data/tenants/default/platforms/whatsapp
      cp platforms/whatsapp/*.txt data/tenants/default/platforms/whatsapp/
      cp platforms/whatsapp/stats.json data/tenants/default/platforms/whatsapp/
      # Session 数据迁移 (注意 .wwebjs_auth 结构变化)
      # 旧: .wwebjs_auth/session-whatsapp-ai-bot
      # 新: data/tenants/default/platforms/whatsapp/sessions/session-whatsapp-ai-bot
      ```

4.  **重启服务**：
    - 在管理后台停止当前的 WhatsApp 机器人。
    - 重新点击 "启动机器人"。

## 4. 验证方法

1.  **启动测试**：
    - 使用租户 A 登录后台，配置 WhatsApp 并启动。
    - 检查目录 `data/tenants/{TENANT_ID_A}/platforms/whatsapp` 是否生成了 `bot.pid` 和 `bot.log`。
    - 扫描二维码登录。

2.  **隔离测试**：
    - 使用租户 B 登录后台。
    - 确认无法看到租户 A 的日志和统计数据。
    - 尝试启动租户 B 的机器人，确认生成了独立的 `data/tenants/{TENANT_ID_B}/platforms/whatsapp` 目录。

3.  **功能测试**：
    - 发送消息给租户 A 的机器人，确认能正常自动回复。
    - 检查租户 A 的统计数据是否增加。
    - 确认租户 B 的统计数据不受影响。

## 5. 回滚方案

如果升级后出现严重问题，请执行以下回滚步骤：
1. 停止所有 WhatsApp 进程。
2. 恢复备份的 `bot.js` 和 `admin_multi.py`。
3. 删除 `data/tenants/{TENANT_ID}/platforms/whatsapp` 下的新生成文件（可选）。
4. 重启服务。
