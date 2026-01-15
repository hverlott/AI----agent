# 关键词配置模块技术文档

## 1. 架构设计
关键词配置模块 (`KeywordManager`) 采用独立的文件存储 (`keywords.json`) 和内存缓存机制，确保高性能和实时性。

### 1.1 核心组件
- **KeywordManager**: 单例/工具类，负责加载、保存和匹配关键词。
- **AuditManager Integration**: 在 LLM 审核前置入关键词检测 (`Pre-Audit Check`)。
- **Admin Panel**: 提供独立的审核员界面，通过 Streamlit 实现。

### 1.2 数据流
1. **配置加载**: `KeywordManager` 每次检测时检查 `keywords.json` 的修改时间 (`mtime`)。如果文件有更新，自动重载。
2. **检测流程**:
   - 用户输入/AI回复 -> `AuditManager.generate_with_audit`
   - -> `KeywordManager.check_text`
   - -> 命中 Block -> 拦截 (Return Fallback)
   - -> 命中 Sensitive -> 记录日志 (Continue/Fail based on policy)
   - -> 未命中 -> 进入 LLM 审核

## 2. 数据结构
`keywords.json` 格式如下：
```json
{
  "block": ["违禁词1", "违禁词2"],
  "sensitive": ["敏感词1", "敏感词2"],
  "allow": ["品牌白名单短语"]
}
```

## 3. 性能
- **检索算法**: 简单的字符串匹配 (O(N*M))。对于目前的关键词规模 (<1000)，性能完全满足要求。
- **基准测试**: 100个关键词，10,000次检测耗时约 0.25秒。

## 4. 安全性
- **权限控制**: 管理后台通过 Session State 的 `user_role` 隔离 Auditor 和 Admin 视图。
- **文件安全**: 关键词文件存储在后端，前端无法直接访问，只能通过 API (UI交互) 修改。

## 5. 策略说明
- allow 优先级：符合 `allow` 的文本直接视为安全并放行，其后再判断 `block` 与 `sensitive`。
- 审核前置：在生成回复前对用户输入与草稿进行关键词检测，命中 `block/sensitive` 时触发兜底并写入审计日志。
