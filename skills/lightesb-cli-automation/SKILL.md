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
- `ai tool plan/run` 只调用服务端 AI 工具接口，不在本地查库或调用工具 URL。
- `robot doctor --offline` 只做本地静态检查，不连接真实 endpoint，不下发机器人命令。
- `robot list/get/capabilities/state/audit` 只做机器人管理 API 只读查询，不证明真实资产库、真实在线状态、真实审计源或真实能力发现。
- `robot command validate --file` 只调用 `POST /service-management/v1/robots/{robotId}/commands:validate`，不调用 `/commands`，不创建命令或执行审计。
- `robot command status --robot-id --command-id` 只调用 `GET /service-management/v1/robots/{robotId}/commands/{commandId}`，不提交新命令或连接真实协议 endpoint。
- `robot command submit --file --yes` 只调用 `POST /service-management/v1/robots/{robotId}/commands` 本地持久化入口；`protocolReceipt.dispatched=false` 时不能当作真实协议执行成功。
- 机器人 CLI 后续真实执行能力必须另开协议闭环切片；不要生成协议写控命令。
- 机器人 CLI 默认只要求本机 WSL 可运行 Maven；用 mock HTTP 和本地测试验证，不要求真实地址或真实机器人环境。
- 自动化执行自然语言工具调用时，先用 `ai tool plan --output json` 保存计划，再用 `ai tool run --plan-file plan-result.json --yes` 执行。
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
