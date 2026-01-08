# Changelog

All notable changes to this project are documented here.  
此文件记录本项目的所有重要更新。

## [2.2.0] - 2026-01-08
### Added
- 新增文档总览：`docs/README.md`（中英文）
- 新增使用教程：`docs/使用教程.md`，包含截图标注与伪代码
- 新增 API 文档：`docs/API文档.md`（兼容 OpenAI 格式调用示例）
- 引用了高分辨率图片（≥1280×720）：
  - 架构总览：`docs/images/01-总览架构.png`
  - 核心流程：`docs/images/03-telegram-触发与回复流程图.png`
- 在文档中补充安全与合规、限流与异常处理建议

### Changed
- README 结构保持不变，新增文档入口在 `docs/README.md`

### Compatibility
- Python 3.8+
- Telethon 1.34.0+
- Streamlit 1.30.0+
- 兼容 OpenAI 格式的推理端点（DeepSeek/OpenAI/Azure/LocalAI）

### Known Issues
- 架构与流程 PNG 由现有图生成；若需定制导出，请使用 `docs/System-Architecture.md` 与 `docs/render_diagrams.py` 生成。
- 未引入自动化测试与CI流程，建议后续添加（pytest/ruff/mypy/GitHub Actions）。

### Roadmap
- 引入最小单元与集成测试覆盖消息触发、记忆窗口与群发节流
- 增加 CI：lint、typecheck、tests 与链接有效性检查
- 扩充 API 文档，覆盖更详细的错误码与重试策略
- 增强多租户配置与权限隔离，完善安全披露流程

---
格式遵循 Keep a Changelog 与 Semantic Versioning。  
Following Keep a Changelog and Semantic Versioning.

