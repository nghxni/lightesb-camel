# LightESB CLI 使用参考

LightESB CLI 是面向接入建模、交付运维、路由治理、日志检索和 AI 辅助编排的命令行工具。

大模型需要生成或修改 CLI 命令时，先读：

- [CLI 命令压缩参考](01-cli-command-reference.md)

核心命令域：

```text
profile -> doctor -> app -> message -> service -> deploy -> route -> log -> ai
```

基本调用：

```bash
lightesb --server http://localhost:8080 <command>
lightesb --profile dev <command>
lightesb --output json <command>
lightesb --yes <write-command>
lightesb --file payload.json <command>
```

安全边界：

- CLI 是控制面客户端，不直接修改 `lightesb-camel-app/`。
- 写操作默认传 `--yes`。
- CI 中优先用 `--output json`。
- `--ai-token` 只用于服务端 AI 日志问答和 AI 工具接口的 `X-AI-Token`，不是模型 API key。
- `ai tool plan/run` 只调用服务端接口，不在 CLI 本地查库或调用工具 URL；执行命令使用 `--yes`，自动化场景优先加 `--output json`。
