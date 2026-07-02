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
- 权限失败建议局部捕获并返回 403。
- 参数校验失败建议返回 400。
- Token 默认按 Exchange 属性 `Token` 处理，不假设会自动读取 `Authorization`。
- 离线 mock 不预置权限规则时，只能验证 403 失败分支；要验证通过分支，先通过 `/api/lightesb/permission/{applicationCode}` 或现场数据预置规则，并设置 `exchangeProperty.SenderID`。

验收：

- 合法请求通过。
- 无权限返回 403。
- 非法 JSON 或 Schema 不匹配返回 400 或明确错误响应。
