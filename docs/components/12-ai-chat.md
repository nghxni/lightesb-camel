# AI Agent + Tools 组件

## 用途

AI Agent + Tools 用于把自然语言请求映射到服务目录内可见的工具路由，适合“自然语言调用已发布接口”的 POC 和交付演示。

旧 HTTP Chat 代理 `AiChatHttpSrv` 已删除。交付包不再推荐 `/api/ai/chat`、`ai.api.*`、`aiChatMemoryProcessor` 或 H2 聊天记忆表。现场如果安装 Codex，应由 Codex 直接读取本交付包的 `AGENTS.md`、`docs/`、`skills/` 和 `example/` 理解项目静态知识。

运行时状态排查使用已实现的 CLI/API：

```bash
lightesb diagnostics snapshot --server http://localhost:8080
lightesb diagnostics warnings --server http://localhost:8080
```

对应 API 为 `GET /api/diagnostics/runtime-snapshot`。

## 服务配置

Agent + Tools 示例：

```properties
service.ai.route=true
service.ai.type=orderdemo
service.ai.mode=agent
ai.agent.tags=order-demo
ai.system.prompt=你是一个订单管理助手。你可以帮助用户查询订单状态和列出客户最近订单。取消订单工具仅用于 mock 演示，必须在用户明确确认后才可调用，并传入 confirmed=true。请用中文回答。
```

配置规则：

- `service.ai.route=true` 只用于实际包含 `langchain4j-agent`、`langchain4j-chat` 或 `langchain4j-tools` 的服务。
- `ai.agent.tags` 必须与工具路由中的 `tags` 一致。
- Agent 服务配置不写真实模型密钥、provider、base URL 或模型名；模型由服务端统一模型注册表管理。
- `genericAiAgent` 按 `lightesb.ai.agents.route.model-ref` 创建模型，不复用日志助手模型。
- 当前 `AiAgentDemoSrv` 会传入 `CamelLangChain4jAgentMemoryId`，但默认 `genericAiAgent` 不承诺稳定多轮记忆。
- `memoryId` 可选；为空时样例 route 使用 `exchangeId` 自动生成。当前它只作为 trace/session 标识，不代表模型上下文记忆。

普通 HTTP、DB、MQTT、SAP、Timer 或转换路由不要生成 `service.ai.*`、`ai.agent.*` 或 `ai.system.prompt`。

## 路由样例

入口路由：

```xml
<route id="ai-agent-demo-entry">
    <from uri="undertow:http://0.0.0.0:{{server.port}}/api/ai/agent/chat?httpMethodRestrict=POST"/>
    <process ref="requestCharsetProcessor"/>
    <setProperty name="agentTraceId">
        <simple>${exchangeId}</simple>
    </setProperty>
    <setProperty name="agentMemoryId">
        <jsonpath suppressExceptions="true">$.memoryId</jsonpath>
    </setProperty>
    <setProperty name="agentUserMessage">
        <jsonpath resultType="java.lang.String" suppressExceptions="true">$.message</jsonpath>
    </setProperty>
    <setHeader name="CamelLangChain4jAgentSystemMessage">
        <constant>{{ai.system.prompt}}</constant>
    </setHeader>
    <setHeader name="CamelLangChain4jAgentMemoryId">
        <simple>${exchangeProperty.agentMemoryId}</simple>
    </setHeader>
    <setBody>
        <simple>${exchangeProperty.agentUserMessage}</simple>
    </setBody>
    <to uri="langchain4j-agent:{{service.ai.type}}Assistant?agent=#genericAiAgent&amp;tags={{ai.agent.tags}}"/>
    <process ref="jsonResponseProcessor"/>
</route>
```

工具路由：

```xml
<route id="tool-demo-query-order">
    <from uri="langchain4j-tools:queryOrderDetail?tags=order-demo&amp;description=Query order details by order ID. Returns order status, items, and total amount.&amp;parameter.orderId=string"/>
    <toD uri="http://127.0.0.1:{{server.port}}/api/ai/agent/mock/order/${header.orderId}?bridgeEndpoint=true&amp;throwExceptionOnFailure=false"/>
</route>
```

## 请求样例

```bash
curl -X POST "http://localhost:19095/api/ai/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"memoryId":"demo-order-session","message":"查询订单 MOCK-1001 的状态"}'
```

## 后端工具编排入口状态

`/api/ai/chat/tools`、`/api/ai/chat/tools/plan` 和 `/api/ai/chat/tools/execute` 已删除。服务管理不再通过隐藏工具表保存可调用工具；AI 路由生成统一走自然语言入口，最终以路由 XML、properties、`.ds` 和资源文件体现。

运行时 Agent + Tools 仍通过服务 XML 暴露：入口路由调用 `langchain4j-agent:*`，每个工具能力写成可见 `langchain4j-tools:*` 路由，并由 `tags` 与 Agent 关联。

## 样例目录

```text
example/routes/AiAgentDemoSrv/v1.0.0/
```

该样例包含：

- `langchain4j-agent:{{service.ai.type}}Assistant` Agent 入口。
- `langchain4j-tools:*` 工具路由。
- 同端口 mock HTTP 子路由，用于演示订单查询、取消和列表查询。
- `CamelLangChain4jAgentSystemMessage` 和 `CamelLangChain4jAgentMemoryId` 头设置。
- 稳定响应字段为 `success`、`traceId`、`memoryId`、`responseText`、`timestamp`；不承诺额外回传 `toolData`。
- `cancelOrder` 只作为 mock-only 高风险工具演示，真实外部接口接入前必须补充强确认、权限和审计。

推荐使用 DashScope `qwen-plus` 验证 Agent + Tools POC：

```properties
lightesb.ai.models.default.provider=dashscope
lightesb.ai.models.default.dashscope.api-key=${DASHSCOPE_API_KEY:}
lightesb.ai.models.default.dashscope.model-name=qwen-plus
lightesb.ai.agents.route.model-ref=default
```

`openai-responses` 和 `custom.api-type=responses` 当前用于 AI 路由生成/微调和普通文本调用，不作为 Agent tool-calling 验收模型。

## 常见问题

- 返回鉴权错误：检查服务端模型注册表和服务入口鉴权配置。
- Agent 不调用工具：检查 `ai.agent.tags` 是否与 `langchain4j-tools:*?tags=...` 一致，工具 description 是否清楚。
- 模型切换未生效：确认 `lightesb.ai.agents.route.model-ref` 指向目标模型；日志助手使用 `lightesb.ai.agents.logging.model-ref`，不要用旧 `lightesb.ai.logging.model.*` 判断 Agent 模型。
- 缺少 `message`：样例返回 `AI_AGENT_MESSAGE_REQUIRED`，请在请求 JSON 中传入 `message`。
- 多轮上下文不稳定：当前样例不承诺稳定多轮记忆；如需多轮，需要二阶段接入 LangChain4j Memory 或统一模型 session。
- 需要排查运行时状态：使用 `diagnostics snapshot/warnings`，不要恢复旧 `/api/ai/chat`。
- 本轮不新增专用 CLI 命令；交付验证使用 `curl` 调用 Agent 入口，并用现有服务、日志和 diagnostics CLI 排查。
