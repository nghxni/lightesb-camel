---
name: lightesb-ai-components
description: 迁移旧内置 Agent、通过普通 HTTP 接入外部 AI，或使用 SAP 外部系统扩展样例时使用。
---

# 外部 Agent 与系统集成

先读 `docs/components/12-ai-chat.md`、`docs/components/13-sap-netweaver.md` 和 `docs/components/16-route-static-preflight.md`。

- 模型、上下文、工具选择由外部 Agent 负责。LightESB 只执行确定性业务路由和已授权的 CLI/控制面动作。
- 不生成 LangChain4j 组件、内置 Agent Bean、`service.ai.*`、`ai.agent.*` 或服务端模型注册表配置；旧 Agent 服务先迁移再校验与应用。
- 普通 HTTP 调用外部 AI 服务按 HTTP 组件契约处理，保持超时、鉴权、错误分支和日志；不记录凭据或完整敏感请求。
- 用户要求实际服务时修改目标服务目录；演示或 POC 才使用 `example/`。默认不连接模型或外部系统验证 payload。
- Action 和机器人外部决策仍受既有身份、权限、审批、审计和显式启用开关约束。
- SAP 无现场环境时先生成 HTTP mock，请求体只允许业务参数；endpoint、username、password 来自配置占位符。
- SAP mock 响应用 `<simple>` 拼 JSON 时避免连续 `}}` 与 Camel 属性语法冲突；优先转换组件或扁平 JSON。

交付前运行适用的静态预检，说明尚未完成的加载和业务验证。静态检查不等于已运行；仅在明确授权范围内执行 runtime、远程 apply、curl 或外部连接。
