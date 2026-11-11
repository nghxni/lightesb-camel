# 外部 Agent 接入与旧内置 Agent 迁移

当前包不提供 LangChain4j Agent、模型工厂或 JVM 会话记忆。由外部 Codex 或其他 Agent 管理模型、凭据、上下文和工具选择，通过 LightESB CLI 操作可见服务文件与控制面。

## 升级前迁移

1. 用 `ai route read/prepare` 读取旧服务。将 `langchain4j-agent/chat/tools`、`genericAiAgent`、`logAgent`、`aiLogToolService` 引用迁为普通业务路由和外部 Agent 调用。
2. 删除候选中的 `service.ai.route/type/mode`、`ai.agent.*`、内置 prompt/memory 配置。旧模型注册表 `lightesb.ai.models.*`、`lightesb.ai.agents.*` 和 `lightesb.ai.default-model` 已退出，不再设置模型密钥。
3. 按 [CLI 参考](../cli/01-cli-command-reference.md) 完成候选校验、授权 apply、运行态与业务验证。Schema 仍由消息管理能力生成。
4. 检查需回退的服务备份：新运行时拒绝恢复已识别的内置 Agent 服务，`autoStart=false` 也不能绕过。需要旧能力时使用已批准的完整版本回滚方案。

旧 `AiAgentDemoSrv` 演示已退出，不再复制到运行目录。仅删除配置开关不能修复仍含旧组件的 XML。停止态旧目录可以读取和迁移；激活前必须完成改造。普通 HTTP 外部 AI 调用继续按 [HTTP 组件](01-http-route-basics.md) 配置，不增加内置 Agent 声明。

## 校验边界

管理面保存、部署、配置更新、启动与用户请求的回退会在写入或激活前检查已识别的退役引用。目录加载跳过 `server.running=false`；启用后发现旧能力会给出迁移错误。普通注释、日志文字和消息正文不会因为包含旧名称而被拒绝。

静态检查不执行动态表达式或环境函数，不代表全部运行验证。加载时会检查解析后的属性；包中已不包含 LangChain4j 组件和 SDK。故障补偿保留原始文件恢复能力，不代表恢复的旧 Agent 能运行。

## 保留的使用方式

- 路由文件、两个 properties 和实际引用资源保持服务版本目录契约；每文件独立生命周期、热加载和 Schema 规则继续生效。
- 用 `log snapshot`、`log instance`、`diagnostics snapshot/warnings`、`ai diagnose` 收集证据，由外部 Agent 分析。
- Action 的身份、token、审批、授权、审计与执行开关继续生效；机器人外部决策接口保留。
- CLI profile 管理控制面地址与认证。模型凭据保存在外部 Agent 环境，不写入交付仓库或 CLI profile。
