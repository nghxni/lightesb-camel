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

模型提供方和密钥按交付环境配置，不在样例中写真实密钥。

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

- 返回鉴权错误：检查模型配置和 token。
- 响应慢：检查模型服务网络和超时配置。
- 多轮上下文混乱：确认 `memoryId` 是否稳定。
- Agent 不调用工具：检查 `ai.agent.tags` 是否与 `langchain4j-tools:*?tags=...` 一致，工具 description 是否清楚。
