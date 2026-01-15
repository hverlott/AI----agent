-- PostgreSQL Schema for SaaS-AIs v2.5.2+
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Tenants (租户表)
CREATE TABLE IF NOT EXISTS tenants (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users (后台用户表)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'operator',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, username)
);

-- Knowledge Base (知识库元数据)
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(255),
    content TEXT,
    category VARCHAR(50),
    tags JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- KB Embeddings (向量存储 - 核心 RAG 表)
CREATE TABLE IF NOT EXISTS kb_embeddings (
    id SERIAL PRIMARY KEY,
    kb_id INTEGER REFERENCES knowledge_base(id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    embedding vector(1536), -- 假设使用 OpenAI text-embedding-3-small
    created_at TIMESTAMP DEFAULT NOW()
);
-- 创建向量索引 (IVFFlat 或 HNSW)
CREATE INDEX ON kb_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Conversation States (会话状态)
CREATE TABLE IF NOT EXISTS conversation_states (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    platform VARCHAR(20),
    user_id VARCHAR(100),
    current_stage VARCHAR(50),
    persona_id VARCHAR(50),
    memory JSONB DEFAULT '{}'::jsonb,
    slots JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, platform, user_id)
);

-- Message Events (消息流水 - 分区表准备)
CREATE TABLE IF NOT EXISTS message_events (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    platform VARCHAR(20),
    chat_id VARCHAR(100),
    direction VARCHAR(10) CHECK (direction IN ('inbound', 'outbound')),
    status VARCHAR(20),
    model VARCHAR(50),
    stage VARCHAR(50),
    user_content TEXT,
    bot_response TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);
-- 建议按月分区 (Partitioning) - 此处仅展示主表

-- Audit Logs (审计日志)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    platform VARCHAR(20),
    user_input TEXT,
    draft_reply TEXT,
    reason TEXT,
    suggestion TEXT,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Script Profiles (剧本配置)
CREATE TABLE IF NOT EXISTS script_profiles (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    profile_type VARCHAR(20), -- stage, persona, binding
    name VARCHAR(100),
    version VARCHAR(20),
    content JSONB,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, profile_type, name, version)
);

-- Skills (技能配置)
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(100),
    description TEXT,
    config_json JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
