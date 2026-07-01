# 交付文档来源映射

| 交付包文档 | 来源 |
| --- | --- |
| `../README.md` | GitHub 公开技术入口，基于交付包内容、组件文档、样例索引和支持边界整理 |
| `components/01-http-route-basics.md` | `docs/07-undertow-component-usage.md`，按交付场景重写 |
| `components/02-service-log.md` | `docs/12-camel-servicelog-component-usage.md`，按交付场景重写 |
| `components/03-charset-processing.md` | `docs/13-charset-processor-usage.md`，按交付场景重写 |
| `components/04-transform-components.md` | `docs/09-conditional-jsontransform-component-usage.md`、`docs/10-conditionaltransform-dts-sample.md` |
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
| `experience/01-robotics-protocol-precheck.md` | `docs/experience/01-robotics-protocol-precheck.md`，按机器人协议接入交付场景重写 |
| `experience/02-robotics-protocol-correct-practices.md` | `docs/experience/02-robotics-protocol-correct-practices.md`，按机器人协议接入交付场景重写 |
| `../proto/robot/robot_command.proto` | `proto/robot/robot_command.proto`，机器人 gRPC IDL 契约草案 |
| `extensions/01-dts-extension-guide.md` | `docs/23-third-party-dts-extension-guide.md` |
| `extensions/02-dts-minimal-template.md` | `docs/24-third-party-dts-extension-minimal-template.md` |
| `api-response-contract.md` | 管理 API 响应契约，外发整理版 |
| `deployment-management-api.md` | 部署管理 API 说明，外发整理版 |
| `ai-route-cache-api.md` | `docs/ai-route-cache-api.md`，按交付场景压缩整理 |
| `runtime-diagnostics-api.md` | 运行时诊断 API 与 H2 fallback POC 设计结论，按交付场景压缩整理 |
| `robot-command-dispatcher-api.md` | 机器人 dispatcher API 与 H2 fallback POC 设计结论，按交付场景压缩整理 |
| `../skills/lightesb-robot-integration/SKILL.md` | 机器人协议接入经验、机器人 dispatcher API、交付样例和 gRPC IDL 契约，按交付任务路由整理 |
| `cli/README.md` | `docs/cli/README.md`，外发压缩版 |
| `cli/01-cli-command-reference.md` | `docs/cli/*` 与 `lightesb-cli/src/main/java/.../cli/command/*`，按命令域压缩整理 |

源码仓库组件文档保持原编号，经验复盘类文档放入 `docs/experience/`。本交付包文档为外发整理版，不直接复制内部实现路径或内部流程说明。
