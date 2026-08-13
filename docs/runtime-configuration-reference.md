# 服务端运行配置参考

本文说明交付包中 LightESB 服务端常用运行配置。运行配置用于启动 LightESB、加载服务包、连接数据库和启用 AI 能力；不要把这些配置写入单个服务的 `common.config.properties` 或 `service.config.properties`，服务包配置只描述该服务自己的路由、端口、组件和业务参数。

## 配置文件入口

默认配置文件：

```text
lightesb-camel-app/lightesb-config.properties
```

启动时可覆盖：

```bash
java -Dlightesb.config.file=/opt/lightesb/lightesb-config.properties -jar lightesb-camel.jar
```

所有密钥、token、密码、证书路径和真实内网地址必须通过环境变量或现场安全配置注入，不要写入交付包仓库。服务 XML 需要读取环境变量时使用显式 `{{env:ENV_NAME}}`；普通 `{{key}}` 只读取同服务版本的 common/service 配置，不会隐式读取平台配置或环境变量。

## 基础服务配置

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `server.port` | `8080` | HTTP 服务端口。 |
| `spring.application.name` | `lightesb` | Spring 应用名。 |
| `lightesb.config.file` | `lightesb-camel-app/lightesb-config.properties` | 外部运行配置文件路径，通常通过 JVM 参数覆盖。 |
| `logging.level.com.oureman.soa.lightesb` | `INFO` | LightESB 应用日志级别。 |
| `logging.level.org.apache.camel` | `INFO` | Camel 框架日志级别。 |
| `logging.level.org.springframework` | `WARN` | Spring 日志级别。 |
| `logging.file.name` | `logs/lightesb.log` | 应用主日志文件。 |
| `logging.charset.console` | `UTF-8` | 控制台日志编码。 |
| `logging.charset.file` | `UTF-8` | 文件日志编码。 |

## 路由加载

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `lightesb.route.enabled` | `true` | 是否启用动态路由加载器和路由管理 API。 |
| `lightesb.route.directory` | `lightesb-camel-app` | 服务包根目录。 |
| `lightesb.app.directory` | `lightesb.route.directory` | 调试文件流和服务日志定位目录，通常省略并跟随路由目录。 |
| `lightesb.route.temp-only-service` | 空 | 只加载指定服务目录，多个服务用英文逗号分隔；用于本地验收或排障。 |
| `lightesb.route.encoding` | `UTF-8` | XML 路由文件编码。 |
| `lightesb.route.recursive-monitoring` | `true` | 是否递归监听服务目录。 |
| `lightesb.route.file-stable-wait-ms` | `100` | 热加载前文件稳定性检查间隔。 |
| `lightesb.route.file-stable-max-attempts` | `10` | 文件稳定性检查最大尝试次数。 |
| `lightesb.route.shutdown-timeout-seconds` | `10` | 关闭时等待路由加载任务结束的时间。 |
| `lightesb.route.force-shutdown-timeout-seconds` | `5` | 正常关闭超时后的强制终止等待时间。 |
| `lightesb.route.debounce-cleanup-threshold` | `100` | 防抖事件缓存清理阈值。 |
| `lightesb.route.debounce-retention-multiplier` | `5` | 防抖事件保留窗口倍数。 |
| `lightesb.route.startup.virtual-thread.enabled` | `true` | 启动初始加载路由时使用 JDK21 虚拟线程并发加载；设为 `false` 可回退串行加载。 |
| `lightesb.route.startup.max-concurrency` | `16` | 虚拟线程模式下最大同时加载路由数。 |
| `lightesb.route.transition-timeout-seconds` | `30` | 服务启停 API 等待真实 Camel 上下文状态的超时，允许 1 到 120 秒；超时不回滚 `server.running`。 |
| `lightesb.action-catalog.enabled` | `false` | 显式开启后，从已运行服务版本构建只读 Action Catalog 内存快照；XML/properties 重载成功后与 route generation 成对刷新，明确引用或待补回的 schema 变化会触发强制重载。与 Action security 同时开启时提供只读查询；真实执行还要求全部安全开关。 |
| `lightesb.action-security.enabled` | `false` | 显式开启后注册 `/api/actions/**` 专用 bearer 身份边界；与 Action Catalog 同时开启时注册要求 `catalog-read` 的 status/list/search/get，任一开关关闭均不注册查询端点。 |
| `lightesb.action-security.credentials[n].name/caller/roles/token-sha256` | 空 | 命名控制面 credential；role 仅允许 `catalog-read`、`action-admin`、`action-execute`。只注入原 token 的 SHA-256 digest，不在仓库保存原 token 或 digest 实值。 |
| `lightesb.action-audit.enabled` | `false` | 显式开启后注册追加式 Action 审计存储；与 Action security 同时开启时提供仅 `action-admin` 可用的只读查询。固定事件不保存业务报文、header、原 token 或任意 details。 |
| `lightesb.action-allowlist.enabled` | `false` | 显式开启精确 Action allowlist；还要求 catalog、security、audit 三个开关同时开启。只提供 list/add/enable/disable，目标 caller 由服务端 credential name 映射，策略变化与 required audit 同事务；执行层只读取精确资格。 |
| `lightesb.action-token.enabled` | `false` | 显式开启短期不透明 Action token；还要求 catalog、security、audit、allowlist 同时开启。运行 token 不进入控制面身份；只有 execution 八开关齐备时才可调用执行入口。 |
| `lightesb.action-token.default-ttl-seconds` | `300` | 未指定 TTL 时的默认秒数，必须在 30 到配置最大值之间。 |
| `lightesb.action-token.max-ttl-seconds` | `3600` | 最大 TTL，范围 30–3600 秒；只能收窄。 |
| `lightesb.action-approval.enabled` | `false` | 显式开启有界任务会话、HMAC callback 和会话受管 route apply；还要求 token、allowlist、audit、security、catalog 同时开启。会话不提供 Action 执行入口。 |
| `lightesb.action-approval.default-ttl-seconds` / `max-ttl-seconds` | `900` / `3600` | 默认/最大会话 TTL；允许范围 60–3600 秒，只能收窄上限。 |
| `lightesb.action-approval.default-max-transitions` / `max-transitions` | `5` / `20` | 默认/最大受管 Action digest 迁移次数。 |
| `lightesb.action-approval.default-max-executions` / `max-executions` | `10` / `100` | 默认/最大成功 dispatch 预算；当前会话层不执行 Action。 |
| `lightesb.action-approval.hmac.provider-name/key-id/secret` | 空 | callback provider、key ID 与至少 32 字符的 HMAC secret；secret 只从安全配置注入。 |
| `lightesb.action-approval.hmac.allowed-approver-ids[n]` | 空 | provider approver allowlist，至少一项、最多 50 项。 |
| `lightesb.action-approval.hmac.max-clock-skew-seconds` | `300` | callback 最大时钟偏差，范围 1–900 秒。 |
| `lightesb.action-approval.hmac.max-body-bytes` | `16384` | callback raw JSON 最大字节数，范围 256–65536。 |
| `lightesb.action-authorization.enabled` | `false` | 显式开启统一授权和精确 dry-run；还要求 approval、token、allowlist、audit、security、catalog 同时开启。dry-run 不执行 Action。 |
| `lightesb.action-authorization.max-input-bytes` | `1048576` | canonical input 最大 UTF-8 字节数，范围 1024–2097152。 |
| `lightesb.action-authorization.permit-ttl-seconds` | `5` | 服务端内部 one-shot permit 有效秒数，范围 1–30；不提供给客户端。 |
| `lightesb.action-authorization.max-idempotency-key-bytes` | `256` | 幂等 key 最大 UTF-8 字节数，范围 16–512；只保存 SHA-256。 |
| `lightesb.action-authorization.idempotency-retention-seconds` | `86400` | 授权幂等摘要保留秒数，范围 60–604800。 |
| `lightesb.action-execution.enabled` | `false` | 显式开启 transport-neutral 执行服务和 `POST /api/actions/execute`；还要求 authorization、approval、token、allowlist、audit、security、catalog 全部开启。当前只支持声明版本 2 的 read/requestReply HTTP Action。 |
| `lightesb.action-execution.timeout-ms` | `5000` | Camel request/reply 等待时间，范围 100–30000 毫秒；超时结果不确定。 |
| `lightesb.action-execution.max-output-bytes` | `1048576` | canonical JSON 输出最大字节数，范围 1024–2097152。 |
| `lightesb.action-execution.max-output-depth` | `64` | JSON 输出最大深度，范围 1–128。 |
| `lightesb.action-execution.max-output-nodes` | `10000` | JSON 输出最大节点数，范围 1–100000。 |

常用排障配置：

```properties
lightesb.route.temp-only-service=PlatformHttp,RobotMqttCommandSrv
```

该配置只影响启动扫描范围，不改变服务目录结构。任一指定服务目录不存在时，启动会失败，避免误回退到全量加载。

不要写入交付仓库的旧键：

| 配置键 | 原因 |
| --- | --- |
| `lightesb.route.file-extensions` | 当前路由文件后缀固定为 `.xml`。 |
| `lightesb.route.debounce-delay-ms` | 当前防抖窗口使用内置默认值。 |

## 数据源与 H2 POC

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `spring.datasource.url` | H2 文件库 | 平台主数据源。POC 可使用 H2，正式环境按现场策略配置。 |
| `spring.datasource.driver-class-name` | `org.h2.Driver` | 主数据源 JDBC Driver。 |
| `spring.datasource.username` | `sa` | 主数据源用户名。 |
| `spring.datasource.password` | 空 | 主数据源密码。 |
| `spring.h2.console.enabled` | `true` | H2 Console 开关；生产建议关闭。 |
| `spring.h2.console.path` | `/h2-console` | H2 Console 路径。 |
| `spring.h2.console.settings.web-allow-others` | `true` | 是否允许远程访问 H2 Console；生产建议关闭。 |
| `lightesb.poc.h2-fallback.enabled` | `false` | 无 MySQL 小数据量 POC 模式；实例日志、JsonKeyword 查询和机器人命令账本等使用 H2 fallback。 |
| `lightesb.mysql.url` | 空 | MySQL JDBC URL；生产或正式联调应配置。 |
| `lightesb.mysql.driver` | 空 | JDBC Driver，例如 `com.mysql.cj.jdbc.Driver`。 |
| `lightesb.mysql.username` | 空 | MySQL 用户名。 |
| `lightesb.mysql.password` | 空 | MySQL 密码。 |

示例：

```properties
spring.datasource.url=${LIGHTESB_DATASOURCE_URL:jdbc:h2:file:./H2Database/data/tempdb;DB_CLOSE_DELAY=-1;MODE=MySQL;AUTO_SERVER=TRUE;AUTO_SERVER_PORT=9092;MV_STORE=TRUE;CACHE_SIZE=65536;}
spring.datasource.driver-class-name=${LIGHTESB_DATASOURCE_DRIVER:org.h2.Driver}
spring.datasource.username=${LIGHTESB_DATASOURCE_USERNAME:sa}
spring.datasource.password=${LIGHTESB_DATASOURCE_PASSWORD:}

lightesb.poc.h2-fallback.enabled=false
lightesb.mysql.url=${LIGHTESB_MYSQL_URL:}
lightesb.mysql.driver=com.mysql.cj.jdbc.Driver
lightesb.mysql.username=${LIGHTESB_MYSQL_USERNAME:}
lightesb.mysql.password=${LIGHTESB_MYSQL_PASSWORD:}
```

`lightesb.poc.h2-fallback.enabled=true` 只适合小数据量演示，不承诺生产级归档、迁移或备份恢复。

## 部署上传

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `lightesb.deployment.temp-dir` | `${user.dir}/temp` | 服务包上传、解压和校验的临时目录。 |
| `lightesb.deployment.backup-dir` | `${user.dir}/backups` | 服务部署备份目录，也用于部分归档备份。 |
| `lightesb.deployment.allowed-extensions` | `zip,tar.gz,tgz` | 允许上传的服务包扩展名。 |
| `lightesb.deployment.max-archive-entries` | `2000` | 单个服务包最大归档条目数。 |
| `lightesb.deployment.max-entry-size` | `50MB` | 单个归档文件最大解压后大小。 |
| `lightesb.deployment.max-extracted-size` | `200MB` | 单个服务包最大解压总量。 |
| `lightesb.deployment.max-entry-depth` | `16` | 归档条目的最大相对目录深度。 |
| `spring.servlet.multipart.max-file-size` | `100MB` | 单个上传文件大小限制。 |

服务端使用受控临时文件名，拒绝路径穿越、重复条目、TAR 链接/特殊条目和超过
上述配额的归档。部署目录由 `lightesb.route.directory` 统一决定。

## 服务日志

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `lightesb.logging.default-level` | `INFO` | 服务级日志默认级别。 |
| `lightesb.logging.console-enabled` | `true` | 服务日志是否同时输出控制台。 |
| `lightesb.logging.file-max-size` | `10MB` | 单个服务日志文件滚动大小。 |
| `lightesb.logging.file-max-backup` | `10` | 滚动备份数量。 |
| `lightesb.logging.log-retention-days` | `30` | 服务日志保留天数。 |
| `lightesb.logging.auto-cleanup-enabled` | `true` | 是否自动清理过期服务日志。 |
| `lightesb.logging.cleanup-schedule-hours` | `24` | 自动清理间隔。 |
| `lightesb.logging.debug-file-ttl-minutes` | `30` | 动态 DEBUG 文件保留时间。 |
| `lightesb.logging.health-check-enabled` | `true` | 服务日志健康检查开关。 |
| `lightesb.logging.max-log-file-size-mb` | `100` | 健康检查中单文件大小阈值。 |

完整模型 prompt、响应正文、业务 payload 和配置正文不应进入默认日志。排障时可以临时提高局部包日志级别，完成后恢复 `INFO`。

以下键写入目标服务版本的 `common.config.properties` 或 `service.config.properties`，不是平台全局配置：

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `log.redaction.enabled` | `false` | 服务日志和 H2/MySQL 实例日志写入前脱敏总开关。关闭保留原文；开启后 DEBUG 也脱敏。 |
| `log.redaction.additional-fields` | 空 | 最多 64 个逗号分隔的额外敏感字段精确名称，不接受正则。 |
| `log.redaction.max-input-chars` | `1048576` | 单次输入字符上限，允许 1–1048576；超限或结构解析失败时整段安全替换。 |

生产服务应显式开启脱敏并配合日志读取权限。该开关控制持久化内容，不按读取者角色返回不同版本；开启不会清理历史原文，也不覆盖任意普通 Camel `log:` 或第三方日志。

## StreamCache

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `lightesb.cache.base-directory` | `lightesb-camel-app/lightesb-StreamCache` | StreamCache 文件缓存根目录。 |
| `lightesb.cache.directory-pattern` | `#camelId#/#operateName#/#exchangeId#` | 缓存目录模式。 |
| `lightesb.cache.file-name-pattern` | `#systemId#_#operateName#` | 缓存文件名模式。 |
| `lightesb.cache.max-files-per-directory` | `1000` | 单目录最大缓存文件数。 |
| `lightesb.cache.directory-cleanup-enabled` | `true` | 是否清理缓存目录。 |
| `lightesb.cache.cleanup-retention-hours` | `24` | 缓存保留小时数。 |
| `lightesb.cache.compression-enabled` | `false` | 是否压缩缓存。 |
| `lightesb.cache.encryption-enabled` | `false` | 是否加密缓存。 |
| `lightesb.cache.buffer-size` | `8192` | 缓冲区大小。 |

缓存目录应放在可写数据盘，并排除在服务路由文件监听之外。

## Transform 与 DTS 扩展

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `lightesb.transform.cache-enabled` | `true` | 转换配置管理器缓存开关。 |
| `lightesb.transform.validation-enabled` | `true` | 加载转换规则时是否校验。 |
| `lightesb.transform.cache.enabled` | `true` | Transform 缓存总开关。 |
| `lightesb.transform.cache.result-cache-size` | `1000` | 转换结果缓存容量。 |
| `lightesb.transform.cache.result-ttl-minutes` | `30` | 转换结果缓存 TTL。 |
| `lightesb.transform.cache.config-cache-size` | `100` | 转换配置缓存容量。 |
| `lightesb.transform.cache.config-ttl-minutes` | `60` | 转换配置缓存 TTL。 |
| `lightesb.transform.cache.expression-cache-size` | `500` | 表达式缓存容量。 |
| `lightesb.transform.cache.expression-ttl-minutes` | `120` | 表达式缓存 TTL。 |
| `lightesb.transform.cache.stats-enabled` | `true` | 是否记录 Transform 缓存统计。 |
| `lightesb.transform.cache.warmup-enabled` | `true` | 是否启用 Transform 缓存预热。 |
| `lightesb.transformds.enabled` | `false` | 是否加载 TransformDS 外部扩展 jar；必须显式启用。 |
| `lightesb.transformds.directory` | `services/TransformDS` | TransformDS 扩展目录。 |
| `lightesb.transformds.scan-pattern` | `*.jar` | TransformDS 扩展 jar 匹配模式。 |

Transform 规则没有全局扫描目录。规则文件必须与所属路由一起放在
`lightesb-camel-app/{serviceName}/{serviceVersion}`，文件名包含
`transform`，后缀为 `.yml`、`.yaml` 或 `.json`。运行时通过服务目录监听完成
热更新；解析或校验失败时保留最后一次有效配置。

启用第三方 DTS：

```properties
lightesb.transformds.enabled=true
```

正式 SPI 是
`com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension`。旧
`TransformDtsExtension` 仅用于一个版本的迁移兼容。

## 服务版本内的兼容与临时状态配置

以下键写入目标服务版本的 `service.config.properties`，不是平台全局配置：

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `charset.legacy-mojibake-repair.enabled` | `false` | 显式兼容已确认的 ISO-8859-1 误解码历史数据；常规 UTF-8 链路保持关闭。 |
| `robot.command.state.max-entries` | `10000` | 单个 CamelContext 路由内临时命令状态容量。 |
| `robot.command.state.ttl-seconds` | `86400` | 路由内临时命令状态 TTL。 |
| `robot.audit.max-events` | `10000` | 单个 CamelContext 路由内临时审计事件容量。 |
| `robot.audit.ttl-seconds` | `86400` | 路由内临时审计事件 TTL。 |

机器人这四个键只保护路由内存 Bean，不替代管理面数据库中的生产命令账本、
状态快照和审计。

## AI 模型注册表

AI 能力统一通过模型注册表配置：

```properties
lightesb.ai.default-model=default
lightesb.ai.models.default.provider=dashscope
lightesb.ai.models.default.dashscope.api-key=${DASHSCOPE_API_KEY:}
lightesb.ai.models.default.dashscope.model-name=qwen-plus
lightesb.ai.agents.route.model-ref=default
lightesb.ai.agents.chat.model-ref=default
```

常用键：

| 配置键 | 用法 |
| --- | --- |
| `lightesb.ai.default-model` | 默认模型引用。 |
| `lightesb.ai.models.<ref>.provider` | 模型提供方：`dashscope`、`gemini`、`openai-responses`、`custom`。 |
| `lightesb.ai.models.<ref>.name` | 通用模型名。 |
| `lightesb.ai.models.<ref>.temperature` | 温度。结构化生成建议低温。 |
| `lightesb.ai.models.<ref>.max-tokens` | 单次响应 token 上限。 |
| `lightesb.ai.models.<ref>.timeout-seconds` | 模型调用超时。 |
| `lightesb.ai.models.<ref>.<provider>.api-key` | 模型密钥，只能使用环境变量占位。 |
| `lightesb.ai.models.<ref>.<provider>.base-url` | 模型服务 base URL。真实私有网关地址不要写入仓库。 |
| `lightesb.ai.models.<ref>.<provider>.model-name` | provider 专属模型名。 |
| `lightesb.ai.models.<ref>.dashscope.top-p` | DashScope top-p。 |
| `lightesb.ai.models.<ref>.custom.api-type` | 自定义网关类型：`chat-completions` 或 `responses`。 |
| `lightesb.ai.models.<ref>.custom.top-p` | OpenAI-compatible top-p。 |
| `lightesb.ai.agents.<agent>.model-ref` | 指定 Agent 使用的模型引用。常用 `route`、`chat`。 |
| `lightesb.ai.agents.<agent>.temperature` | Agent 温度覆盖。 |
| `lightesb.ai.agents.<agent>.max-tokens` | Agent token 上限覆盖。 |
| `lightesb.ai.agents.<agent>.timeout-seconds` | Agent 调用超时覆盖。 |
| `lightesb.ai.agents.<agent>.json-repair-retry` | JSON 外层修复重试次数；AI 路由常用。 |

`provider=openai-responses` 用于 OpenAI 原生 Responses API；自定义网关使用 `provider=custom`，再通过 `custom.api-type=chat-completions|responses` 区分接口形态。

## Agent 记忆

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `lightesb.ai.agents.chat.memory.enabled` | `false` | 是否启用 JVM 内存态窗口记忆。 |
| `lightesb.ai.agents.chat.memory.max-messages` | `20` | 每个会话保留消息数。 |
| `lightesb.ai.agents.chat.memory.max-sessions` | `1000` | 最大会话数。 |
| `lightesb.ai.agents.chat.memory.ttl-seconds` | `1800` | 会话 TTL。 |

该记忆不跨 JVM 实例，不持久化，服务重启后丢失。

## AI 路由

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `lightesb.ai.route.provider-label` | `route-agent` | AI 路由结果缺少模型响应对象时的展示标签，通常省略。 |
| `lightesb.ai.route.model.log-payload` | `false` | 是否打印完整 prompt 和模型响应，只用于临时排障。 |
| `lightesb.ai.route.context.allowed-prefixes` | `docs/,skills/,example/` | AI 路由可读取的外部上下文前缀。 |
| `lightesb.ai.route.context.candidate-excluded-prefixes` | 内置排除内部经验、商业、待办和研究类目录 | AI 路由候选上下文扫描排除前缀。 |
| `lightesb.ai.route.context.max-files` | `12` | 单次外部上下文最大文件数。 |
| `lightesb.ai.route.context.max-file-chars` | `20000` | 单个上下文文件最大字符数。 |
| `lightesb.ai.route.context.max-total-chars` | `200000` | 单次上下文总字符数上限。 |
| `lightesb.ai.route.context.selection-cache-ttl-seconds` | `1800` | 上下文选择缓存 TTL。 |
| `lightesb.ai.route.context.selection-cache-max-size` | `100` | 上下文选择缓存容量。 |
| `lightesb.ai.route.cache-cleanup.fixed-delay-seconds` | `300` | AI 路由缓存清理调度间隔。 |
| `lightesb.ai.route.baseline-cache.ttl-seconds` | `900` | baseline 缓存 TTL。 |
| `lightesb.ai.route.baseline-cache.max-size` | `100` | baseline 缓存容量。 |

`lightesb.ai.route.model.log-payload=true` 会输出完整提示词和模型响应，可能包含业务内容，只能临时启用。

## AI 日志助手

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `lightesb.ai.logging.enabled` | `false` | 是否启用 AI 日志聊天接口。 |
| `lightesb.ai.logging.read-only` | `true` | 只读模式；为 `true` 时不会实际改日志级别。 |
| `lightesb.ai.logging.auth-token` | 空 | 可选 `X-AI-Token` 鉴权。 |
| `lightesb.ai.logging.base-url` | `http://localhost:8080` | 管理 API 和 Actuator 根地址。 |
| `lightesb.ai.logging.agent-gateway-url` | `http://localhost:19093/api/ai/logging/agent` | AI 日志 Agent 路由入口。 |
| `lightesb.ai.logging.allowed-levels` | 空 | 允许设置的日志级别。 |
| `lightesb.ai.logging.allowed-logger-prefixes` | 空 | 允许操作的 logger 前缀。 |
| `lightesb.ai.logging.system-message` | 默认提示词 | 透传给 AI 日志 Agent 的能力约束提示词。 |
| `lightesb.ai.logging.clarification-fallback-enabled` | `true` | 澄清续答兜底处理开关。 |
| `lightesb.ai.logging.clarification.max-turns` | `5` | 同一会话澄清最大轮次。 |
| `lightesb.ai.logging.retry.enabled` | `true` | 限流重试开关。 |
| `lightesb.ai.logging.retry.max-attempts` | `4` | 最大请求次数，包含首次请求。 |
| `lightesb.ai.logging.retry.initial-delay-ms` | `1000` | 重试初始等待毫秒数。 |
| `lightesb.ai.logging.retry.max-delay-ms` | `30000` | 重试最大等待毫秒数。 |
| `lightesb.ai.logging.retry.multiplier` | `2.0` | 指数退避倍率。 |
| `lightesb.ai.logging.retry.jitter-ms` | `250` | 重试抖动毫秒数。 |

建议先以只读模式验收：

```properties
lightesb.ai.logging.enabled=true
lightesb.ai.logging.read-only=true
lightesb.ai.logging.auth-token=${AI_LOGGING_AUTH_TOKEN:}
lightesb.ai.logging.allowed-levels=TRACE,DEBUG,INFO,WARN,ERROR
lightesb.ai.logging.allowed-logger-prefixes=com.oureman.soa.lightesb,org.apache.camel
```

## 机器人控制面配置

`lightesb.robot.dispatcher.*` 是控制面命令派发配置，不是服务路由 XML 的 MQTT endpoint 配置。具体服务路由连接哪个 MQTT broker，应在服务包自己的业务配置中维护。

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `lightesb.robot.audit.archive.enabled` | `true` | 是否启用机器人审计归档任务。 |
| `lightesb.robot.audit.archive.retention-months` | `1` | 在线审计记录保留月数。 |
| `lightesb.robot.audit.archive.backup-retention-months` | `24` | 归档备份保留月数。 |
| `lightesb.robot.audit.archive.max-field-chars` | `65536` | 单字段归档最大字符数。 |
| `lightesb.robot.audit.archive.initial-delay-seconds` | `0` | 归档任务启动延迟。 |
| `lightesb.robot.audit.archive.interval-seconds` | `86400` | 归档任务执行间隔。 |
| `lightesb.robot.dispatcher.enabled` | `false` | 是否启用控制面 MQTT 命令派发器。 |
| `lightesb.robot.dispatcher.broker-uri` | 空 | 控制面派发 MQTT broker URI。 |
| `lightesb.robot.dispatcher.client-id` | `lightesb-robot-dispatcher` | MQTT clientId。 |
| `lightesb.robot.dispatcher.qos` | `1` | 命令派发 QoS。 |
| `lightesb.robot.dispatcher.retained` | `false` | 是否发送 retained 消息。 |
| `lightesb.robot.dispatcher.clean-start` | `true` | MQTT clean start。 |
| `lightesb.robot.dispatcher.session-expiry-interval` | `0` | MQTT session expiry interval。 |
| `lightesb.robot.dispatcher.username` | 空 | MQTT 用户名。 |
| `lightesb.robot.dispatcher.password` | 空 | MQTT 密码。 |
| `lightesb.robot.dispatcher.command-topic-pattern` | `robot/{siteId}/{robotId}/command/{commandId}` | 命令 topic 模板。 |
| `lightesb.robot.dispatcher.max-retries` | `3` | 派发最大重试次数。 |
| `lightesb.robot.dispatcher.retry-delay-seconds` | `30` | 派发重试间隔。 |

机器人 AI 审批默认关闭；只有显式开启时才注册回调、decision 查询和一次性 AI submit 能力。以下字段在开启时全部必填，完整签名和 API 契约见 [机器人 AI 可信审批与一次性提交](robot-ai-approval-api.md)。

| 配置键 | 默认值 | 用法 |
| --- | --- | --- |
| `lightesb.robot.ai.approval.enabled` | `false` | 机器人 AI 审批总开关。 |
| `lightesb.robot.ai.approval.provider` | 空 | 当前必须设置为 `hmac-webhook`。 |
| `lightesb.robot.ai.approval.decision-max-age-ms` | 空 | decision 最大存活时间；最终有效期还受推理时效和候选 TTL 限制。 |
| `lightesb.robot.ai.approval.hmac.provider-name` | 空 | 审批 provider 稳定名称。 |
| `lightesb.robot.ai.approval.hmac.key-id` | 空 | 当前激活 HMAC key 标识。 |
| `lightesb.robot.ai.approval.hmac.secret` | 空 | HMAC secret，只能使用受控配置或环境变量占位。 |
| `lightesb.robot.ai.approval.hmac.allowed-approver-ids` | 空列表 | 允许审批的 approver allowlist。 |
| `lightesb.robot.ai.approval.hmac.max-clock-skew-seconds` | 空 | 回调时间戳允许的最大时钟偏差，必须为正数。 |
| `lightesb.robot.ai.approval.hmac.max-body-bytes` | 空 | 回调 raw body 最大字节数，必须为正数。 |

## 推荐模板

```properties
server.port=8080
logging.level.com.oureman.soa.lightesb=INFO
logging.level.org.apache.camel=INFO

spring.h2.console.enabled=false
spring.h2.console.settings.web-allow-others=false

lightesb.route.directory=lightesb-camel-app
lightesb.route.temp-only-service=
lightesb.route.startup.virtual-thread.enabled=true
lightesb.route.startup.max-concurrency=16

lightesb.deployment.temp-dir=${LIGHTESB_DEPLOYMENT_TEMP_DIR:temp}
lightesb.deployment.backup-dir=${LIGHTESB_DEPLOYMENT_BACKUP_DIR:backups}

lightesb.poc.h2-fallback.enabled=false
lightesb.mysql.url=${LIGHTESB_MYSQL_URL:}
lightesb.mysql.driver=com.mysql.cj.jdbc.Driver
lightesb.mysql.username=${LIGHTESB_MYSQL_USERNAME:}
lightesb.mysql.password=${LIGHTESB_MYSQL_PASSWORD:}

lightesb.cache.base-directory=${LIGHTESB_CACHE_DIR:lightesb-camel-app/lightesb-StreamCache}

lightesb.ai.default-model=default
lightesb.ai.models.default.provider=dashscope
lightesb.ai.models.default.dashscope.api-key=${DASHSCOPE_API_KEY:}
lightesb.ai.models.default.dashscope.model-name=qwen-plus
lightesb.ai.agents.route.model-ref=default
lightesb.ai.agents.chat.model-ref=default
lightesb.ai.agents.chat.memory.enabled=false

lightesb.robot.dispatcher.enabled=false
lightesb.robot.dispatcher.broker-uri=${ROBOT_MQTT_BROKER_URI:}
lightesb.robot.dispatcher.username=${ROBOT_MQTT_USERNAME:}
lightesb.robot.dispatcher.password=${ROBOT_MQTT_PASSWORD:}
```

## 不要写入交付仓库

- 真实 API key、token、密码、证书路径。
- 真实内网数据库地址、模型代理地址、MQTT broker 地址。
- 本地调试用 `DEBUG` 日志级别作为默认值。
- 已下线或代码不读取的配置键，例如旧的 `lightesb.ai.logging.model.*`、`lightesb.ai.route.agent-gateway-url`、`lightesb.ai.route.system-message`。
- 单个服务包 `common.config.properties` 或 `service.config.properties` 中不要写平台运行配置，例如 `lightesb.ai.models.*`、`lightesb.ai.agents.*`、`spring.*`、`logging.*`、`management.*`。
