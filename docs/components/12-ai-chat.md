# AI Chat 组件

## 用途

AI Chat 能力用于在路由中调用模型服务，适合日志问答、辅助诊断和轻量编排类演示。

## 服务配置

HTTP Chat 模式：

```properties
service.ai.route=true
service.ai.type=chat
```

`service.ai.type=chat` 对应 HTTP Chat 演示模式，可参考 `AiChatHttpSrv`。如使用 Agent + Tools 编排模式，可参考 `AiAgentDemoSrv`，通常会设置自己的 `service.ai.type` 和 `ai.agent.tags`。

模型提供方和密钥按交付环境配置，不在样例中写真实密钥。服务端统一使用 `lightesb.ai.models.*` 模型注册表和 `lightesb.ai.agents.*.model-ref` 引用模型，CLI profile 中的 `aiToken` 只用于 `X-AI-Token`，不是模型 API key。

`ai.api.*`、`ai.model.name`、`ai.temperature`、`ai.max.tokens` 只属于 HTTP Chat 代理示例的路由本地配置。Agent + Tools 服务配置只保留 `service.ai.*`、`ai.agent.tags`、`ai.system.prompt` 等运行时服务键；AI 路由生成/微调的模型选择统一走服务端模型注册表。

示例：

```properties
lightesb.ai.default-model=default
lightesb.ai.models.default.provider=dashscope
lightesb.ai.models.default.dashscope.api-key=${DASHSCOPE_API_KEY:}
lightesb.ai.models.default.dashscope.model-name=qwen-plus
lightesb.ai.agents.logging.model-ref=default
```

AI 路由生成/微调如需接入 OpenAI 原生 Responses API，可新增 `provider=openai-responses` 模型并让 `lightesb.ai.agents.route.model-ref` 指向该模型。自定义网关使用 `provider=custom` 和 `custom.api-type=chat-completions|responses`。

Agent + Tools 演示：

```properties
service.ai.route=true
service.ai.type=orderdemo
service.ai.mode=agent
ai.agent.tags=order-demo
```

样例目录：`example/routes/AiAgentDemoSrv/v1.0.0/`

该样例包含：

- `langchain4j-agent:{{service.ai.type}}Assistant` Agent 入口。
- `langchain4j-tools:*` 工具路由。
- 同端口 mock HTTP 子路由，用于演示订单查询、取消和列表查询。
- `CamelLangChain4jAgentSystemMessage` 和 `CamelLangChain4jAgentMemoryId` 头设置。

## 后端工具编排入口状态

`/api/ai/chat/tools`、`/api/ai/chat/tools/plan` 和 `/api/ai/chat/tools/execute` 已删除。服务管理不再通过隐藏工具表保存可调用工具；AI 路由生成统一走自然语言入口，最终以路由 XML、properties、`.ds` 和资源文件体现。

运行时 Agent + Tools 仍通过服务 XML 暴露：入口路由调用 `langchain4j-agent:*`，每个工具能力写成可见 `langchain4j-tools:*` 路由，并由 `tags` 与 Agent 关联。交付时不要再配置或调用旧的 plan/execute 接口。

## 路由建议

- HTTP 入站后先做编码处理和基本参数校验。
- 对模型调用增加超时和异常分支。
- AI 响应前调用 `jsonResponseProcessor`。
- 日志中不要输出完整密钥、token 或敏感提示词。

## 请求样例

HTTP Chat：

```bash
curl -X POST "http://localhost:18090/api/ai/chat" \
  -H "Content-Type: application/json" \
  -d '{"memoryId":"demo-session","message":"总结最近一次错误"}'
```

Agent + Tools：

```bash
curl -X POST "http://localhost:19095/api/ai/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"memoryId":"demo-order-session","message":"查询订单 MOCK-1001 的状态"}'
```

## 常见问题

- 返回鉴权错误：检查 `lightesb.ai.models.<model-ref>.*` 模型配置和 `X-AI-Token`。
- 响应慢：检查模型服务网络和超时配置。
- 多轮上下文混乱：确认 `memoryId` 是否稳定。
- Agent 不调用工具：检查 `ai.agent.tags` 是否与 `langchain4j-tools:*?tags=...` 一致，工具 description 是否清楚。
