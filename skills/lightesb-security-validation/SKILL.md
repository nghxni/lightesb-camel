---
name: lightesb-security-validation
description: 配置权限校验、Token/IP/CIDR/正则规则、输入/输出/回调 JSON Schema 生成、校验路由和失败分支时使用。
---

# LightESB 权限与校验

先读：

- `docs/components/05-json-schema-validation.md`
- `docs/components/08-permission-validation.md`
- `docs/cli/01-cli-command-reference.md`

规则：

- 权限校验使用 `<process ref="permissionCheckProcessor"/>`。
- JSON Schema 校验使用 `<process ref="jsonSchemaValidationProcessor"/>`。
- 已有消息模型且需要 JSON 校验时，先查询服务关系。INPUT 使用当前 `serviceInId` 和 `request-schema.json`，OUTPUT 使用当前 `serviceOutId` 和 `response-schema.json`；CALLBACK 先用 `serviceCallbackId` 查询回调服务，再使用其 `serviceInId` 和 `callback-schema.json`。
- 执行 `lightesb message schema generate --id <messageId>|--file <message.json> --service-name <serviceName> --service-version <vX.Y.Z> --schema-file <fixed-name.json> --yes --output json`。只使用返回的 `schema` 和 `jsonSchemaPath`，禁止模型自行生成或修补 Schema。
- `warnings` 非空时停止自动 apply 并展示完整 warnings，只有用户明确确认后继续。
- route XML 是校验唯一开关；按方向加入或删除完整校验块，不增加配置或数据库开关。用户审核候选后，用 `ai route apply --save-remote --yes` 一次提交 route、两个 properties 和 route 实际引用的固定 Schema。
- 权限失败建议局部捕获并返回 403。
- 参数校验失败建议返回 400。
- Token 默认按 Exchange 属性 `Token` 处理，不假设会自动读取 `Authorization`。
- 离线 mock 不预置权限规则时，只能验证 403 失败分支；要验证通过分支，先通过 `/api/lightesb/permission/{applicationCode}` 或现场数据预置规则，并设置 `exchangeProperty.SenderID`。

验收：

- 合法请求通过。
- 无权限返回 403。
- 非法 JSON 或 Schema 不匹配返回 400 或明确错误响应。
- Schema 消息来源、固定文件、warnings 门禁和远程 apply 资源一致。
