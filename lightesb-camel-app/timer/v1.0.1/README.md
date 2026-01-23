# Timer 示例服务（v1.0.1）

本目录通过 `timer-test-routes.xml` 演示两件事：

- 使用 `timer:` 触发定时路由（状态检查 / 数据处理）
- 使用 `servicelog:` 进行**服务级别日志**输出，并在路由中引入 `jsonResponseProcessor` 进行响应编码/Content-Type 处理

## 路由说明（timer-test-routes.xml）

### 1) independent-status-check
- **routeId**：`independent-status-check`
- **触发源**：`timer:statusCheck?period=1500000`
  - **周期**：1500000ms（约 25 分钟触发一次）
- **处理逻辑**：
  - 通过 `servicelog:info?message=Timer v1.0.1 状态检查开始` 记录路由开始
  - `setBody` 生成 JSON 字符串（Simple 表达式）：
    - `file`: `"timer-test-routes.xml"`
    - `status`: `"ACTIVE"`
    - `timestamp`: 当前时间 `${date:now:yyyy-MM-dd HH:mm:ss}`
    - `version`: `"v1.0.1"`
  - 通过 `servicelog:info?message=独立Context状态检查&showBody=true` 输出服务级日志（并展示 body）
  - `process ref="jsonResponseProcessor"`：处理 UTF-8 编码与 Content-Type（需在上下文中已注册该 Processor Bean）
  - 同时保留 `<log message="📈 独立Context状态检查: ${body}"/>` 作为标准日志对比
- **预期现象**：
  - 服务日志中可看到“状态检查开始”和“独立Context状态检查”两条 INFO 日志（第二条可展示 body）
  - 标准 Camel 日志也会输出带时间戳的 JSON 内容

### 2) timer-data-processing
- **routeId**：`timer-data-processing`
- **触发源**：`timer:dataProcessing?period=30000`
  - **周期**：30000ms（每 30 秒触发一次）
- **处理逻辑**：
  - `setBody` 模拟生成处理数据：
    - `processId`: `${random(1000,9999)}`
    - `timestamp`: `${date:now:yyyy-MM-dd'T'HH:mm:ss}`
    - `service`: `"timer-v1.0.1"`
  - 该路由中的 `servicelog` 调试/信息输出目前以注释形式保留（需要可自行打开）

## 配置文件说明

### service.config.properties（服务特定配置）
- **service.name**：`TimerSrv`
- **service.version**：`1.0.1`
- **service.instance.id**：`timer-srv-001`
- **service.environment**：`development`

### common.config.properties（通用配置摘录）
- **system.version**：`1.0.1`
- **server.port**：`8081`
- **HTTP.Listener**：`false`

## 常见修改
- **调整触发周期**：修改 `timer:` URI 的 `period`（单位 ms）
  - 例：`period=60000` 表示每 60 秒触发一次
- **开启服务级日志**：将 `timer-data-processing` 路由中注释掉的 `servicelog:` 行取消注释即可

