---
name: lightesb-ai-components
description: 配置 AI Agent + Tools、SAP NetWeaver 或其他外部系统扩展样例时使用。
---

# LightESB AI Agent 与外部系统扩展

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
- Agent + Tools POC 推荐使用 `lightesb.ai.agents.route.model-ref` 指向 DashScope `qwen-plus`；不要用旧 `lightesb.ai.logging.model.*` 判断 Agent 模型。
- `openai-responses` / `custom.api-type=responses` 当前不作为 Agent tool-calling 验收模型。
- `memoryId` 可选，缺省可由 route 自动生成；不要把它描述为稳定多轮记忆。
- 高风险工具默认 mock-only；真实外部接口接入前必须补充强确认、权限和审计。
- 响应契约以 `success`、`traceId`、`memoryId`、`responseText`、`timestamp` 为主，不要求额外回传 `toolData`。
- 工具路由调用同服务 HTTP mock 子路由时，避免入口参数 Header 与子路由 path 变量同名造成多值；先存 Exchange Property、移除同名 Header，再用 Property 构造 `toD`。下游响应如为 `byte[]`，继续处理前转为 `java.lang.String`。
- SAP NetWeaver 无现场环境时先生成 HTTP-only mock，请求体只允许业务参数，endpoint、username、password 必须来自配置占位符。
- SAP mock 响应用 `<simple>` 拼 JSON 时避免嵌套对象的连续 `}}`，否则可能与 Camel `{{property}}` 占位符解析冲突；优先扁平 JSON 或转换组件。

验收：

- 演示请求能返回结构化 JSON。
- 外部调用失败时返回可读错误。
- 日志不输出密钥或完整敏感请求。
- `curl /api/ai/agent/chat` 能触发 mock 工具链路或给出可定位错误。
