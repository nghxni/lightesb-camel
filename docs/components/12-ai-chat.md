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

## 后端受控工具编排入口

当消息入口需要让模型选择业务工具，但不希望模型直接决定任意 URL 调用时，可使用管理端工具编排接口：

```text
POST /api/ai/chat/tools
POST /api/ai/chat/tools/plan
POST /api/ai/chat/tools/execute
```

`/api/ai/chat/tools` 是 one-shot 入口，会读取已登记服务和工具定义，向模型提供可用工具清单，并在后端校验后执行 HTTP 工具。

`/api/ai/chat/tools/plan` 只返回候选 `toolCall`，不执行工具；`/api/ai/chat/tools/execute` 执行已规划 `toolCall`，执行前会重新校验当前工具定义和服务状态。CLI、CI 或其他自动化场景需要先确认工具再执行时，优先使用 `plan -> execute` 两阶段。

基础配置：

```properties
lightesb.ai.tools.enabled=true
lightesb.ai.tools.auth-token=
lightesb.ai.tools.allowed-hosts=127.0.0.1,localhost
lightesb.ai.tools.max-tools=20
lightesb.ai.tools.http-timeout-seconds=10
lightesb.ai.tools.model-timeout-seconds=30
lightesb.ai.tools.json-repair-retry=1
```

工具执行约束：

- 只执行已登记工具。
- 只允许 `GET`、`POST`。
- 工具 URL 只允许 `http`、`https`。
- 不允许 URL 携带用户名或密码。
- 目标 host 必须在 `lightesb.ai.tools.allowed-hosts` 白名单内。
- `GET` 参数可替换路径模板，未使用参数追加为 query；`POST` 参数作为 JSON body。

请求示例：

```bash
curl -X POST "http://localhost:8080/api/ai/chat/tools" \
  -H "Content-Type: application/json" \
  -d '{"memoryId":"demo-order-session","message":"查询订单 MOCK-1001 的详情"}'
```

规划示例：

```bash
curl -X POST "http://localhost:8080/api/ai/chat/tools/plan" \
  -H "Content-Type: application/json" \
  -d '{"memoryId":"cli-session-001","message":"查询订单 MOCK-1001 的详情"}'
```

执行示例：

```bash
curl -X POST "http://localhost:8080/api/ai/chat/tools/execute" \
  -H "Content-Type: application/json" \
  -d '{"memoryId":"cli-session-001","message":"查询订单 MOCK-1001 的详情","toolCall":{"serviceId":"AIAGENTDEMO001","actionName":"queryOrderDetail","method":"GET","path":"http://127.0.0.1:19095/api/ai/agent/mock/order/{orderId}","params":{"orderId":"MOCK-1001"}}}'
```

成功响应会包含：

- `response`：模型基于工具结果生成的中文回复。
- `toolCall`：后端校验后的工具调用计划。
- `toolResult`：本地 HTTP 工具响应。

`plan` 响应会包含 `matched`、`userMessage`、`toolCall`、`availableToolCount`。`matched=false` 表示没有匹配工具，不会执行服务调用。

常见错误码包括 `NO_TOOL_MATCH`、`TOOL_PLAN_PARSE_ERROR`、`TOOL_PARAM_MISSING`、`TOOL_NOT_ALLOWED`、`TOOL_HTTP_ERROR`、`AI_UPSTREAM_ERROR`。

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
