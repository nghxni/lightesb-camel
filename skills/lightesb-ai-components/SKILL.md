---
name: lightesb-ai-components
description: 配置 AI Chat、SAP NetWeaver 或其他外部系统扩展样例时使用。
---

# LightESB AI 与外部系统扩展

先读：

- `docs/components/12-ai-chat.md`
- `docs/components/13-sap-netweaver.md`
- `example/routes/AiAgentDemoSrv/v1.0.0/`

规则：

- 样例不写真实模型密钥、账号、口令或内网地址。
- 先在 `example/` 中验证演示 payload。
- 外部调用必须有异常分支和日志。
- Agent + Tools 演示需保持 `service.ai.type`、`ai.agent.tags` 与 `langchain4j-agent` / `langchain4j-tools` 路由一致。
- 工具路由 description 用清晰英文描述，便于模型选择工具。

验收：

- 演示请求能返回结构化 JSON。
- 外部调用失败时返回可读错误。
- 日志不输出密钥或完整敏感请求。
- `curl /api/ai/agent/chat` 能触发 mock 工具链路或给出可定位错误。
