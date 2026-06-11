---
name: lightesb-cli-automation
description: 生成、审查或排查 LightESB CLI 命令、profile、doctor、app/message/service/deploy/route/log/ai 自动化流程时使用。
---

# LightESB CLI 自动化

先读：

- `docs/cli/README.md`
- `docs/cli/01-cli-command-reference.md`

规则：

- CLI 是控制面客户端，不直接修改 `lightesb-camel-app/`。
- 写操作加 `--yes`，CI 中优先加 `--output json`。
- 需要服务端地址时优先使用 `--server` 或 profile，不在命令中写真实密钥。
- `--ai-token` 只用于 `X-AI-Token`，不是模型 API key。
- AI 路由生成和优化只返回候选内容，不自动保存、打包或部署。
- 排查部署问题时先查 `deploy status/history`、`route status/mapping`、`log instance`。

常用链路：

```bash
lightesb profile add --name dev --server http://localhost:8080
lightesb profile use dev
lightesb doctor
lightesb app create --file app.json --yes
lightesb message create --file request-message.json --yes
lightesb message create --file response-message.json --yes
lightesb service create --file service.json --yes
lightesb service config save --file service.json --yes
lightesb service package deploy --file package.json --yes
lightesb route status
lightesb log instance list --service-name DemoSrv --service-version 1.0.0
```

验收：

- 命令能说明输入文件、服务端地址和是否写操作。
- 写操作有 `--yes` 或明确说明需要人工确认。
- 输出给 CI 的命令使用 `--output json`。
- AI 相关说明不要求本地保存模型 provider 密钥。
