# SAP NetWeaver 组件

## 用途

SAP NetWeaver 样例用于把 HTTP 请求转换为 SAP NetWeaver 调用参数，并把外部系统响应映射为统一 JSON。

## 使用建议

- 先在 `example/` 中使用演示地址和演示 payload 验证路由结构。
- 需要连接真实 SAP 环境时，在 `service.config.properties` 中配置目标地址、鉴权和超时。
- 不把真实账号、口令或内网地址提交到交付样例。
- 无 SAP 环境时，先做 HTTP-only mock：构造 SAP 请求摘要并返回固定响应，不调用 `sap-netweaver:` endpoint。

当前已验证的范围是：生成候选可在隔离的外部 runnable jar 中启动，HTTP-only mock 请求可返回 `200`。这不证明 `sap-netweaver:` endpoint、真实 SAP Gateway 认证、错误映射或性能目标；这些项目仍需在授权现场验证。

服务配置中的 SAP 地址、用户名和密码应先写为 `PLACEHOLDER_CONFIGURE_IN_SITE`，通过站点安全配置流程替换后再启用服务。服务目录 properties 按字面值读取，不会把 `${SAP_GW_PASSWORD}` 二次解析为环境变量；需要环境变量时，应在路由 URI 中显式使用 `{{env:SAP_GW_PASSWORD}}`。

## 路由编排

典型步骤：

1. HTTP 入站。
2. 编码处理。
3. 操作类型识别。
4. 构造 SAP 请求。
5. 调用外部接口。
6. 错误映射和 JSON 响应。

## 验证

- 演示模式下返回构造后的请求摘要。
- 真实联调时先验证健康检查或只读接口。
- 错误响应应包含可定位的错误码和简短消息。
- 请求体不能覆盖 SAP endpoint、用户名或密码；这些值只能来自服务配置占位符。
- 使用 `<simple>` 拼接 JSON 响应时，避免直接写嵌套对象导致 `}}` 与 Camel `{{property}}` 占位符解析冲突。离线 mock 可先返回扁平 JSON；需要复杂对象时，改用转换组件或专门的 JSON 构造步骤。

离线 mock 请求示例：

```bash
curl -X POST "http://localhost:19188/api/doc-mock/sap/order-summary" \
  -H "Content-Type: application/json" \
  -d '{"orderId":"SAP-1001"}'
```

动态目标拒绝示例：

```bash
curl -X POST "http://localhost:19188/api/doc-mock/sap/order-summary" \
  -H "Content-Type: application/json" \
  -d '{"orderId":"SAP-1001","endpoint":"http://sap.local"}'
```

期望返回 `422` 和 `SAP_DYNAMIC_TARGET_REJECTED`。
