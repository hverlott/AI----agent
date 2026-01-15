-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Tenants (租户表)
CREATE TABLE tenants (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    config JSONB DEFAULT '{}', -- 存储原 config_json
    status VARCHAR(20) DEFAULT 'active'
);

-- Users (管理后台用户)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(20) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, username)
);

-- Knowledge Base (知识库元数据)
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(200),
    content TEXT,
    category VARCHAR(50),
    tags JSONB DEFAULT '[]', -- 存储标签数组
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- KB Embeddings (向量数据 - 核心优化)
CREATE TABLE kb_embeddings (
    id SERIAL PRIMARY KEY,
    kb_id INTEGER REFERENCES knowledge_base(id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    embedding vector(1536), -- 假设使用 OpenAI text-embedding-3-small
    created_at TIMESTAMP DEFAULT NOW()
);
-- 创建向量索引 (IVFFlat 或 HNSW)
CREATE INDEX ON kb_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Conversation States (会话状态)
CREATE TABLE conversation_states (
    user_id VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    current_stage VARCHAR(50) DEFAULT 'S0',
    persona_id VARCHAR(50) DEFAULT 'default',
    memory JSONB DEFAULT '{}', -- 存储上下文记忆
    slots JSONB DEFAULT '{}',  -- 存储槽位信息
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (tenant_id, platform, user_id)
);

-- Message Events (消息流水 - 分区表建议按月分区)
CREATE TABLE message_events (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    platform VARCHAR(20),
    chat_id VARCHAR(100),
    direction VARCHAR(10) CHECK (direction IN ('inbound', 'outbound')),
    event_type VARCHAR(50), -- sent, received, error
    content TEXT,
    model VARCHAR(50),
    stage VARCHAR(50),
    metadata JSONB DEFAULT '{}', -- 存储 usage, cost 等额外信息
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_msg_tenant_time ON message_events(tenant_id, created_at DESC);

-- Audit Logs (审计日志)
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    module VARCHAR(50),
    action VARCHAR(50),
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Script Profiles (剧本/人设配置)
CREATE TABLE script_profiles (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    profile_type VARCHAR(20), -- stage, persona, binding
    name VARCHAR(100),
    version VARCHAR(20),
    content JSONB NOT NULL, -- 直接存储配置 JSON
    is_active BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, profile_type, name, version)
);

-- Skills (技能配置)
CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100),
    description TEXT,
    config JSONB DEFAULT '{}', -- 包含 prompt_template, tool_definition
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
