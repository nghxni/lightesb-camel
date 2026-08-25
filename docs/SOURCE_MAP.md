# 交付文档来源映射

| 交付包文档 | 来源 |
| --- | --- |
| `../README.md` | GitHub 公开技术入口，基于交付包内容、组件文档、样例索引和支持边界整理 |
| `README.md` | `docs/README.md`，按交付包组件索引、样例入口和 Camel 官方参考链接整理 |
| `product-overview.md` | `README.md`、内部产品能力边界、英文站实施方案、系统架构和机器人集成架构结论，按外发英文站和公开交付包口径重写 |
| `components/01-http-route-basics.md` | `docs/07-undertow-component-usage.md`，按交付场景重写 |
| `runtime-route-loading.md` | 运行时生命周期设计结论、路由热加载经验和 jar 快速重启经验，按交付场景重写 |
| `runtime-configuration-reference.md` | 服务端运行配置参数参考与日志脱敏/访问控制经验，按交付配置、安全占位和脱敏边界压缩整理 |
| `components/02-service-log.md` | `docs/12-camel-servicelog-component-usage.md` 与日志脱敏/访问控制经验，按交付场景重写 |
| `components/03-charset-processing.md` | `docs/13-charset-processor-usage.md`，按交付场景重写 |
| `components/04-transform-components.md` | `docs/09-conditional-jsontransform-component-usage.md`、`docs/10-conditionaltransform-dts-sample.md` |
| `transform-logging-operations-api.md` | `docs/api/06-transform-and-logging-operations.md`，按交付调用、响应和错误处理场景重写 |
| `components/05-json-schema-validation.md` | `docs/14-jsonschema-validation-processor-usage.md` |
| `components/06-json-keyword.md` | `docs/01-json-keyword.md`，重新编写外发版 |
| `components/07-stream-cache.md` | `docs/11-streamcache-component-usage.md` |
| `components/08-permission-validation.md` | `docs/15-permission-check-processor-usage.md` |
| `components/09-exception-handling.md` | 异常处理组件说明与管理 API 异常边界，外发整理版 |
| `components/10-h2-jsonkeyword-chain.md` | `docs/16-h2-jsonkeyword-processor-chain-usage.md` 与 H2 fallback POC 设计结论，按交付场景重写 |
| `components/11-externaldb.md` | `docs/18-externaldb-component-usage.md` |
| `components/12-ai-chat.md` | `docs/22-ai-chat-framework-usage.md`、`docs/experience/09-ai-agent-memory-practices.md`，结合 AI 配置可见 runtime 自洽边界、旧 Chat/工具接口删除说明和 CLI 自动化说明，按交付场景重写 |
| `components/13-sap-netweaver.md` | `docs/26-sap-netweaver-component-usage.md` |
| `components/14-timer-routes.md` | 交付样例 `example/routes/timer/` 与 `example/routes/MysqlRouteSrv/` 整理 |
| `components/15-aveva-plant-scada-opcua-mqtt.md` | `docs/27-aveva-plant-scada-opcua-mqtt-usage.md`，按交付场景重写 |
| `components/16-route-static-preflight.md` | 交付包路由文件闭包、组件配置、占位符和资源自检要求，结合现有组件文档和样例整理 |
| `components/17-action-catalog.md` | 服务 Action 目录架构、只读查询 API 与 CLI 契约，按交付配置、离线/在线命令、样例和验证步骤重写 |
| `action-manual-testing.md` | 用户手工验收记录整理为交付包 Action 全链路手动测试指南；保留可复现步骤，收紧授权和恢复边界 |
| `action-allowlist-api.md` | `docs/api/09-action-allowlist.md`、Action 目录架构和精确 allowlist 经验，按交付配置、权限、CLI、事务审计和安全边界重写 |
| `action-token-api.md` | `docs/api/10-action-token.md`、Action 目录架构和不透明 token 经验，按交付启用、权限、API/CLI、一次回显、事务审计和非执行边界重写 |
| `action-approval-api.md` | `docs/api/11-action-approval-session.md`、Action 目录架构和有界审批 lineage 经验，按交付启用、CLI、HMAC callback、受管 apply 和失败处理重写 |
| `action-authorization-api.md` | `docs/api/12-action-authorization-dry-run.md`、Action 目录架构和精确授权经验，按交付启用、运行 token、受限输入策略、闭合诊断和非执行边界重写 |
| `action-execution-api.md` | `docs/api/13-action-execution.md`、Action 目录架构和精确授权经验，按交付启用、运行 token、静态 direct invocation、输出校验、CLI 和审计边界重写 |
| `action-audit-api.md` | `docs/api/08-action-audit.md`、Action 目录架构和追加式审计经验，按交付配置、权限、查询与安全字段边界重写 |
| `experience/01-robotics-protocol-precheck.md` | `docs/experience/01-robotics-protocol-precheck.md`，按机器人协议接入交付场景重写 |
| `experience/02-robotics-protocol-correct-practices.md` | `docs/experience/02-robotics-protocol-correct-practices.md`，按机器人协议接入交付场景重写 |
| `../proto/robot/robot_command.proto` | `proto/robot/robot_command.proto`，机器人 gRPC IDL 契约草案 |
| `extensions/01-dts-extension-guide.md` | `docs/23-third-party-dts-extension-guide.md` |
| `extensions/02-dts-minimal-template.md` | `docs/24-third-party-dts-extension-minimal-template.md` |
| `api-response-contract.md` | 管理 API 响应契约，外发整理版 |
| `service-runtime-management-api.md` | `docs/api/03-service-runtime-management.md` 与运行时生命周期结论，按交付启停场景重写 |
| `deployment-management-api.md` | 管理 API 契约、部署服务安全边界与回退行为，按外发调用场景整理 |
| `ai-route-cache-api.md` | `docs/api/01-ai-route-cache.md`，按交付场景压缩整理 |
| `runtime-diagnostics-api.md` | 运行时诊断 API、H2 fallback POC 设计结论与控制面始终安全摘要边界，按交付场景压缩整理 |
| `robot-command-dispatcher-api.md` | 机器人 dispatcher API、MQTT 回执接入基线与 H2 fallback POC 设计结论，按交付场景压缩整理 |
| `robot-edge-inference-mock.md` | 机器人边缘 AI 推理设计与 Build B mock baseline，按可交付配置、输入输出、验收和限制重写 |
| `robot-ai-approval-api.md` | `docs/api/04-robot-ai-approval-callback.md`、`docs/api/05-robot-ai-decision-submit.md` 和机器人 AI 可信审批架构结论，按交付配置、HMAC 回调、查询、提交与 MySQL 部署场景重写 |
| `../skills/lightesb-robot-integration/SKILL.md` | 机器人协议接入经验、边缘 AI 推理 mock/可信审批门禁、dispatcher API、交付样例和 gRPC IDL 契约，按交付任务路由整理 |
| `../skills/lightesb-security-validation/SKILL.md` | 权限校验、消息 Schema 与 Action 控制面角色/审计/allowlist/token/有界审批安全边界，按交付任务路由整理 |
| `../skills/lightesb-temp-form/SKILL.md` | `skills/lightesb-temp-form/SKILL.md` 与 `skills/lightesb-route-development/SKILL.md` 最小创建集及 simple 常见坑，按交付场景重写 |
| `../skills/lightesb-project-troubleshooting/SKILL.md` | 源码仓库项目问题处理规则的通用排障流程，去除个人画像和内部经验后按本机开发/业务现场场景重写；发布基线可升级，根目录项目经验独立维护 |
| `cli/README.md` | `docs/cli/README.md`，外发压缩版 |
| `cli/01-cli-command-reference.md` | `docs/cli/*` 与 `lightesb-cli/src/main/java/.../cli/command/*`，按命令域压缩整理 |
| `cli/support-diagnostics.md` | `docs/cli/12-support-diagnostics-runbook.md`，按外发支持诊断场景重写，不包含内部演示样例命令 |

源码仓库组件文档保持原编号，经验复盘类文档放入 `docs/experience/`。本交付包文档为外发整理版，不直接复制内部实现路径或内部流程说明。
