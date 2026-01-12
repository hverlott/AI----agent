# 贡献指南

欢迎贡献！为保证项目质量与隐私安全，请遵循以下流程：

1. Fork 仓库并在你的 fork 上创建 feature 分支：

```bash
git clone https://github.com/hverlott/AI----agent.git
git checkout -b feature/your-change
```

2. 提交前请检查：
- 是否包含敏感信息（API Key、会话文件、租户数据等）？若有，请移除并将敏感信息放入 `.env`（不要提交）。
- 是否包含大型二进制或压缩文件？请改用外部存储或 Git LFS，并先与维护者沟通。

3. 提交并发起 Pull Request（PR）：

```bash
git add .
git commit -m "feat: 描述你的修改"
git push origin feature/your-change
# 在 GitHub 上创建 PR
```

4. PR 规范：
- 清晰描述变更目的与影响范围
- 如涉及外部依赖或数据库变更，请在 PR 中说明
- 所有单元测试通过或附上手动验证步骤

感谢你的贡献！
