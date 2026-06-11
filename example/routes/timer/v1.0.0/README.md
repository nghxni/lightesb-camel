# Timer 示例服务（v1.0.0）

本目录的 `timer-test-routes.xml` 用于演示**独立 CamelContext** 下的 `timer:` 定时触发路由，并通过日志输出验证路由是否正常运行。

## 路由说明（timer-test-routes.xml）

### 1) independent-timer-test-v1.0.0
- **routeId**：`independent-timer-test-v1.0.0`
- **触发源**：`timer:independentTest?period=10000`
  - **周期**：10000ms（每 10 秒触发一次）
- **处理逻辑**：
  - `setBody` 设置固定文本：`📊 独立CamelContext测试路由运行正常 - timer-test-routes.xml`
  - 输出到 Camel 日志组件：`log:independent-context?level=INFO`
- **预期现象**：日志里周期性出现 INFO 级别的 body 内容（logger 名称为 `independent-context`）。

### 2) independent-status-check-v1.0.0
- **routeId**：`independent-status-check-v1.0.0`
- **触发源**：`timer:statusCheck?period=15000`
  - **周期**：15000ms（每 15 秒触发一次）
- **处理逻辑**：
  - `setBody` 生成一段 JSON 字符串（Simple 表达式）：
    - `file`: `"timer-test-routes.xml"`
    - `status`: `"ACTIVE"`
    - `timestamp`: 当前时间 `${date:now:yyyy-MM-dd HH:mm:ss}`
  - 通过 `<log>` 输出：`📈 独立Context状态检查: ${body}`
- **预期现象**：日志里周期性出现带时间戳的 JSON 内容。

## 常见修改
- **调整周期**：修改 `timer:` URI 的 `period` 参数（单位 ms），例如 `period=5000` 表示每 5 秒触发一次。

