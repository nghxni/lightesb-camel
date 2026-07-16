---
name: lightesb-security-validation
description: 配置权限校验、Token/IP/CIDR/正则规则、JSON Schema 校验和失败分支时使用。
---

# LightESB 权限与校验

先读：

- `docs/components/05-json-schema-validation.md`
- `docs/components/08-permission-validation.md`

规则：

- 权限校验使用 `<process ref="permissionCheckProcessor"/>`。
- JSON Schema 校验使用 `<process ref="jsonSchemaValidationProcessor"/>`。
- 已有消息模型且需要 JSON 校验时，先执行 `lightesb message schema generate --id <messageId>|--file <message.json> --service-name <serviceName> --service-version <vX.Y.Z> --schema-file <name.json> --yes --output json`。Schema 必须写入对应服务版本目录，检查 warnings，并把返回的 `jsonSchemaPath` 用作路由 `JsonSchemaPath`；不要手写重复 Schema。
- 权限失败建议局部捕获并返回 403。
- 参数校验失败建议返回 400。
- Token 默认按 Exchange 属性 `Token` 处理，不假设会自动读取 `Authorization`。
- 离线 mock 不预置权限规则时，只能验证 403 失败分支；要验证通过分支，先通过 `/api/lightesb/permission/{applicationCode}` 或现场数据预置规则，并设置 `exchangeProperty.SenderID`。

验收：

- 合法请求通过。
- 无权限返回 403。
- 非法 JSON 或 Schema 不匹配返回 400 或明确错误响应。
