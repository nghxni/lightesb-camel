# 运行时路由按需加载

本文说明 LightESB-Camel 交付包中的服务路由如何加载、禁用、热更新和验证，适用于交付现场确认启动性能、服务启停和路由变更边界。

## 结论

- LightESB-Camel 不依赖 Spring Boot 启动时自动创建全局 CamelContext 来承载业务路由。
- 业务路由按服务版本目录动态加载；每个 `serviceName + serviceVersion` 目录必须恰好包含一个 XML 路由文件，该文件可以定义多个 `routeId`，运行时只创建一个对应的 Camel 上下文。
- `server.running=false` 的服务包会保留在磁盘上，但不会加载 XML 路由，也不会占用运行态 route、endpoint 或连接资源。
- `server.running` 控制整个服务版本是否加载；XML route 可以使用 Camel 原生 `autoStartup=false` 做单路由启停，服务进入 `RUNNING` 前所有允许自动启动的 route 必须启动成功。
- XML 路由和服务配置文件支持动态热加载；Java 代码、依赖、Spring Bean、启动参数和全局运行参数变化仍需要重新打包或重启。
- 显式启用 `lightesb.action-catalog.enabled=true` 时，Action descriptor 只在对应服务版本进入 `RUNNING` 后发布；被 descriptor 引用或待补回的 schema 变化会强制重载该服务版本。
- Camel component、dataformat、language 的 Spring Boot 自动装配关闭后，只影响启动期自动扫描，不移除交付包内的 Camel 组件能力；XML 路由中引用的 `timer:`、`undertow:`、`http:`、`sql:`、`mqtt:` 等组件会在对应服务加载时按需解析和使用。
- 服务只有在配置、必需组件、异常处理、XML 解析、端口绑定以及全部 route 启动成功后才进入 `RUNNING`；任一必需阶段失败均公开为 `STOPPED`，不影响其他服务和应用整体健康状态。
- 服务启停 API 会等待 Camel 上下文真实启动或卸载；同方向请求共享转换，相反方向请求返回 HTTP `409`，超时不会回滚 `server.running`。

## 路由语法参考

服务路由文件使用 Camel 4.18.x XML DSL。修改 `*-route.xml` 前，建议先用官方文档确认 DSL 元素、EIP、Simple 表达式和 endpoint URI 参数：

- [XML IO DSL](https://camel.apache.org/components/4.18.x/others/java-xml-io-dsl.html)
- [Enterprise Integration Patterns](https://camel.apache.org/components/4.18.x/eips/enterprise-integration-patterns.html)
- [Simple 语言](https://camel.apache.org/components/4.18.x/languages/simple-language.html)
- [Camel 4.18.x 组件总索引](https://camel.apache.org/components/4.18.x/index.html)
- 常用 endpoint：[Undertow](https://camel.apache.org/components/4.18.x/undertow-component.html)、[HTTP](https://camel.apache.org/components/4.18.x/http-component.html)、[SQL](https://camel.apache.org/components/4.18.x/sql-component.html)、[Timer](https://camel.apache.org/components/4.18.x/timer-component.html)、[Direct](https://camel.apache.org/components/4.18.x/direct-component.html)

## 服务包状态

服务包位于：

```text
lightesb-camel-app/{serviceName}/{serviceVersion}
```

每个版本目录只允许一个 `*.xml` 路由文件。部署包缺少 XML 或包含多个 XML 会校验失败；运行中新增第二个 XML 会停止该服务版本原有上下文并将服务公开为 `STOPPED`，不会修改已有部署状态。删除多余 XML 后会自动加载剩余唯一 XML。

路由普通占位符 `{{key}}` 只读取同目录 `common.config.properties` 与 `service.config.properties` 的合并结果，同名键由 service 覆盖 common。普通占位符不会读取平台 Spring 配置、JVM system property 或环境变量；需要环境变量时必须显式使用 `{{env:ENV_NAME}}`。

两个配置文件都可以缺省；文件一旦存在，读取或解析失败会阻断该服务版本加载，不会使用默认配置掩盖错误。`system.components` 使用精确 token，未知 token 或必需组件注册失败同样阻断加载。

共享 HTTP 端口由平台统一维护底层监听器。单个服务卸载只注销自己的 endpoint/handler 和日志资源，不会停止同端口的其他服务；最后一个使用者退出后才关闭监听器。

服务配置通常包含：

```properties
server.running=false
```

常见状态含义：

| 状态 | 运行时行为 |
| --- | --- |
| `server.running=false` | 服务包保留，不加载路由，不占用运行态 Camel 资源 |
| `server.running=true` | 动态加载该服务版本下的 XML 路由和配置 |
| 加载失败 | 公开状态为 `STOPPED`，部署状态保持不变；通过服务日志和运行时诊断查看失败阶段与摘要 |
| 停止服务 | 卸载对应路由和上下文，释放运行态资源 |
| 删除唯一 XML | 卸载服务版本，服务状态进入 `DEFINE`，部署状态进入 `UNDEPLOYED` |
| 删除服务包 | 移除服务资产，需要重新部署才可恢复 |

启停 API 默认等待 30 秒，可通过 `lightesb.route.transition-timeout-seconds` 调整为 1 到 120 秒。停止失败且旧上下文仍在运行时，接口返回真实 `RUNNING` 和失败诊断。完整契约见 [服务启停 API](service-runtime-management-api.md)。

## 变更边界

可优先依赖热加载的变更：

- 修改服务目录内的 Camel XML 路由。
- 修改服务目录内的 `service.config.properties` 或 `common.config.properties`。
- 修改 Action route metadata 明确引用的 schema；启用 Action Catalog 时，缺失 schema 补回也会触发自愈重载。
- 通过 CLI 或管理 API 启停服务、重载服务、重载指定路由文件。
- 将服务配置从 `server.running=false` 改为 `true`，或从 `true` 改回 `false`。

需要重启或重新打包的变更：

- 修改 Java 代码。
- 增减 Maven 依赖或替换运行 jar。
- 修改 Spring Bean、全局配置、启动参数或 JVM 参数。
- 新增需要注册到运行时的全局组件能力。
- 热加载失败后，服务状态、路由状态或端口占用状态不一致。

单个服务版本加载失败不会使 LightESB 应用整体 readiness 失败。修正配置或 XML 后等待文件监听重新加载，再确认服务进入 `RUNNING`；热重载不自动恢复旧实例。

不要在同一服务版本目录中通过新增第二个 XML 拆分路由；需要多个 Camel route 时，应放在该版本唯一 XML 内。

## 验证方式

推荐用 CLI、管理 API 和日志三类证据确认按需加载是否生效：

1. 启动后查询路由状态，确认默认关闭的服务没有被加载。
2. 将目标服务改为启用，或通过 CLI 启动服务。
3. 查询服务和路由状态，确认目标服务的路由出现。
4. 调用样例接口或等待定时任务日志，确认路由实际执行。
5. 停止服务或改回 `server.running=false`。
6. 再次查询路由状态，确认路由已卸载。

可用入口：

- `docs/cli/README.md`
- `docs/cli/01-cli-command-reference.md`
- `docs/runtime-diagnostics-api.md`
- `docs/deployment-management-api.md`

启动性能排查时，也可以开启 Actuator startup 端点作为辅助诊断，用于观察 Spring Boot 启动阶段耗时。业务路由是否加载仍以服务状态、路由状态和运行日志为准。

## 交付建议

- 交付包可以沉淀大量服务包或机器人技能包，默认用 `server.running=false` 保存资产。
- 现场只启用当前需要验证或运行的服务，减少启动期和运行期资源占用。
- 修改 XML 或配置后先等待动态监听完成，再检查状态和日志；不要把所有路由变更都升级为重新打包。
- 自动化脚本如果只是重启现有 jar，可以跳过打包阶段测试；测试应通过前置聚焦测试或后续端到端脚本单独完成。
