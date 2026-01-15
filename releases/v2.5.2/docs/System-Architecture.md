# 系统业务流程与架构图

## 总览架构

```mermaid
graph TD
    Admin[管理后台 Streamlit<br/>admin_multi.py/admin.py] -->|配置/操作| TG[Telegram Bot<br/>main.py/Telethon]
    Admin -->|配置/操作| WA[WhatsApp Bot<br/>platforms/whatsapp/bot.js]
    TG -->|读取/写入| CFG[(配置与话术<br/>data/tenants/{tenant}/platforms/telegram/*)]
    TG --> LOGS[(日志<br/>data/tenants/{tenant}/platforms/telegram/logs/*)]
    TG --> STATS[(统计<br/>data/tenants/{tenant}/platforms/telegram/stats.json)]
    TG --> KB[(知识库<br/>data/knowledge_base/db.json + files/)]
    TG -->|AI请求| API[(OpenAI兼容 API)]
    WA -->|AI请求| API
    Admin --> KB
    Admin --> LOGS
    Admin --> STATS
```

## Telegram 消息处理流程（时序）

```mermaid
sequenceDiagram
    participant U as 用户 (User)
    participant TG as Telegram Platform
    participant H as handlers.py (Listener)
    participant Filter as ContentFilter
    participant QA as QA Engine
    participant KB as KBEngine (RAG)
    participant Sup as Supervisor (Orchestrator)
    participant Worker as StageAgent
    participant AI as LLM Service
    participant Aud as AuditManager
    participant DB as Database (MessageEvents)

    U->>TG: 发送消息
    TG->>H: NewMessage 事件
    H->>H: 加载配置/白名单检查
    
    # 1. 前置过滤
    H->>Filter: 关键词密度检测
    alt 触发过滤
        Filter-->>H: Blocked
        H-->>DB: 记录 Filtered 事件
        H-->>TG: (可选) 忽略或回复拦截提示
    else 通过过滤
        
        # 2. QA 优先匹配
        H->>QA: 精确匹配
        alt QA 命中
            QA-->>H: 固定回复
            H->>TG: 发送回复
            H-->>DB: 记录 QA 回复
        else QA 未命中
            
            # 3. 业务分支决策
            alt KB_ONLY 模式 (纯知识库)
                H->>KB: 向量检索 Top-K
                KB-->>H: 参考上下文
                H->>AI: 生成回复 (仅基于上下文)
                AI-->>H: 回复内容
            else Orchestration 模式 (剧本编排)
                H->>Sup: 获取当前状态 (State)
                Sup->>Sup: 路由决策 (Router)
                Sup-->>Worker: 分发任务 (Persona/Stage)
                Worker->>KB: 检索业务知识
                Worker->>AI: 执行 Agent 任务
                AI-->>Worker: 生成草稿
                Worker-->>H: 候选回复
            else Default 模式 (通用 RAG)
                H->>KB: 向量检索
                H->>AI: 通用生成
                AI-->>H: 草稿
            end

            # 4. 后置审核
            H->>Aud: 内容合规审核 (Audit)
            alt 审核通过
                Aud-->>H: Pass
                H->>TG: 发送最终回复
                H-->>DB: 记录 Success
            else 审核拒绝
                Aud-->>H: Reject (触发兜底)
                H->>TG: 发送兜底话术 (Fallback)
                H-->>DB: 记录 Fallback
            end
        end
    end
```

## Telegram 触发与回复（流程图）

```mermaid
flowchart LR
    A[NewMessage] --> B[触发检查]
    B --> C[QA匹配]
    C --> D[回复]
```

## 知识库生命周期（导入/管理/检索）

```mermaid
graph TD
    Upload[导入文件] --> Parse[解析器: PyPDF2/python-docx/openpyxl/TXT]
    Parse --> Item[保存为条目<br/>db.json]
    NewText[新建文本条目] --> Item
    Item --> Manage[管理: 列表/编辑/删除]
    Item --> Search[检索测试 Top-N]
    Search --> Inject[主流程注入上下文]
```

## 管理后台（多平台面板）

```mermaid
graph TD
    Sidebar[左侧导航] --> Platform[平台]
    Sidebar --> DataMgmt[数据管理]
    Platform --> Panels[Telegram/WhatsApp]
    Panels --> StartStop[启动/停止/重启]
    Panels --> Config[Prompt/Keywords/QA/开关]
    Panels --> Broadcast[群发工具]
    Panels --> Logs[日志查看/清空]
    Panels --> Stats[统计与重置]
    DataMgmt --> KBPanel[知识库管理/导入/检索/设置]
```

## WhatsApp 消息处理（时序）

```mermaid
sequenceDiagram
    participant WU as 用户
    participant WA as WhatsApp 客户端
    participant WB as bot.js
    participant AI as AI API
    WU->>WA: 发送消息
    WA->>WB: message 事件
    WB->>WB: 触发检查（被@或关键词）
    alt 触发满足
        WB->>AI: 调用 AI
        AI-->>WB: 回复
        WB->>WA: 发送消息
    else 未触发
        WB-->>WA: 忽略
    end
```

## 关键代码参考
- 事件处理与触发逻辑：[main.py:386-457](file:///d:/AI%20Talk/main.py#L386-L457)
- QA 解析与匹配：[main.py:158-241](file:///d:/AI%20Talk/main.py#L158-L241)
- 知识库读取与检索注入：[main.py:241-305](file:///d:/AI%20Talk/main.py#L241-L305)、[main.py:466-481](file:///d:/AI%20Talk/main.py#L466-L481)
- 管理后台平台与面板：[admin_multi.py:409-545](file:///d:/AI%20Talk/admin_multi.py#L409-L545)
- 知识库管理/导入/检索/设置：[admin_multi.py:446-750](file:///d:/AI%20Talk/admin_multi.py#L446-L750)
- WhatsApp 机器人主逻辑：[platforms/whatsapp/bot.js](file:///d:/AI%20Talk/platforms/whatsapp/bot.js)

---

## 群白名单与群发流程

```mermaid
flowchart TD
    Cache[群缓存<br/>group_cache.json] --> WL[白名单<br/>selected_groups.json]
    WL --> Filter[面板筛选加载群组]
    Filter --> Select[选择/全选/反选]
    Select --> Interval[设置间隔]
    Interval --> Send[开始群发（异步）]
    Send --> Progress[进度/成功失败记录]
    Progress --> Logs[bot.log/群聊日志]
```

## 后台登录与会话复用

```mermaid
sequenceDiagram
    participant Admin as 管理后台
    participant Sess as admin_session.session
    participant UserSess as userbot_session.session
    Admin->>Admin: 点击“登录”
    alt admin_session 不存在
        Admin->>Admin: 从 userbot_session 复制生成 admin_session
    end
    Admin->>Sess: 连接并校验授权
    Sess-->>Admin: 登录成功/需要二次密码
```

## 错误处理与日志归档

```mermaid
graph TD
    Bot[main.py 运行] --> Write[写入 system/private/group 日志]
    Admin[管理后台] --> View[查看与刷新日志]
    Admin --> Clear[清空当前日志]
    Admin --> Archive[归档日志到 archive/ 目录]
    Archive --> History[历史日志列表]
```
