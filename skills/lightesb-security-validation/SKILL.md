---
name: lightesb-security-validation
description: 配置权限校验、Token/IP/CIDR/正则规则、Action 控制面角色与追加式审计、输入/输出/回调 JSON Schema 生成、校验路由和失败分支时使用。
---

# LightESB 权限与校验

先读：

- `docs/components/05-json-schema-validation.md`
- `docs/components/08-permission-validation.md`
- `docs/cli/01-cli-command-reference.md`
- `docs/action-audit-api.md`
- `docs/action-allowlist-api.md`
- `docs/action-token-api.md`
- `docs/action-approval-api.md`
- `docs/action-authorization-api.md`

规则：

- 权限校验使用 `<process ref="permissionCheckProcessor"/>`。
- JSON Schema 校验使用 `<process ref="jsonSchemaValidationProcessor"/>`。
- 已有消息模型且需要 JSON 校验时，先查询服务关系。INPUT 使用当前 `serviceInId` 和 `request-schema.json`，OUTPUT 使用当前 `serviceOutId` 和 `response-schema.json`；CALLBACK 先用 `serviceCallbackId` 查询回调服务，再使用其 `serviceInId` 和 `callback-schema.json`。
- 执行 `lightesb message schema generate --id <messageId>|--file <message.json> --service-name <serviceName> --service-version <vX.Y.Z> --schema-file <fixed-name.json> --yes --output json`。只使用返回的 `schema` 和服务版本目录相对 `jsonSchemaPath`，禁止模型自行生成或修补 Schema。
- `warnings` 非空时停止自动 apply 并展示完整 warnings，只有用户明确确认后继续。
- route XML 是校验和 Action Schema 契约的唯一事实；按方向加入或删除完整校验块或 Action input/output schema route property，不增加配置或数据库开关。普通本地编辑直接完成候选和静态自检；只有用户明确授权远程写入时，才用 `ai route apply --save-remote --yes` 一次提交 route、两个 properties 和 route 实际引用的固定 Schema，会话 allowlist 也必须覆盖这些文件。
- 权限失败建议局部捕获并返回 403。
- 参数校验失败建议返回 400。
- Token 默认按 Exchange 属性 `Token` 处理，不假设会自动读取 `Authorization`。
- Action 控制面 bearer 只保存原 token 的 SHA-256 digest；caller/roles 由服务端映射。审计查询要求 audit+security 双开关和精确 `action-admin`，不能让 `catalog-read` 或 `action-execute` 隐式继承。
- Action 审计只允许固定安全字段和 append/query，不保存 body/header/raw token/details，也不提供公开 cleanup/update/delete。内部 H2 历史清理使用独立边界并要求 audit 与日志自动清理双开关：审计按保留天数，token/approval 还必须已过期，幂等记录按自身到期，有效 allowlist 不清理。目录读取写审计失败保持原查询结果；高风险授权、审批和执行审计失败必须 fail closed。
- Action allowlist 只允许服务端 credential 映射出的精确 caller+actionId+serviceVersion；管理 actor 要 `action-admin`，目标要 `action-execute`。add/enable 重验当前目录，disable 可独立收窄，策略变化与 required audit 同事务；不提供 caller 自报、wildcard/block/delete 或执行能力。
- Action token 与控制面 bearer 隔离；issue 仅允许 execute-self，introspect/revoke 允许 execute-self/admin-any。原 token 只回显一次且服务端只存 SHA-256；每次实际使用仍要重验 allowlist/目录，不能反向获得控制面权限。
- Action 审批会话与 bearer/token 隔离；caller 从 bearer 派生，approver 只来自 allowlist HMAC provider。多 Action 逐项保存 source digest、聚合 scope digest CAS；只有受管 route apply 可延续 lineage，普通/直接变化进入 STALE。会话本身不是 bearer 或执行许可。
- 离线 mock 不预置权限规则时，只能验证 403 失败分支；要验证通过分支，先通过 `/api/lightesb/permission/{applicationCode}` 或现场数据预置规则，并设置 `exchangeProperty.SenderID`。

验收：

- 合法请求通过。
- 无权限返回 403。
- 非法 JSON 或 Schema 不匹配返回 400 或明确错误响应。
- Schema 消息来源、固定文件、warnings 门禁和远程 apply 资源一致。
- Action 审计默认关闭；开启后查询有界、角色精确，响应与存储均无业务报文或原凭据。
- Action allowlist 默认关闭；四开关齐备后仍只收窄目录资格，写失败不得留下无审计策略。
- Action token 默认关闭；五开关齐备后 issue/revoke required audit 失败必须回滚，introspect/revoke 响应不得含原 token/hash/digest。
- Action approval 默认关闭；六开关齐备后状态/transition 与 required audit 同事务。callback 重放、digest 冲突、范围扩大、no-op 和无法证明的恢复必须 fail closed；日志/响应不得含 HMAC secret、raw callback、route/input 正文。
- Action authorization 默认关闭；七开关齐备后 dry-run 只诊断。只旁路精确 POST，严格读取唯一 `lat_` bearer；policy 禁止引用/组合器/条件/正则且必须有界，当前 entry Schema 摘要和 symlink 路径必须重验。
- dry-run 不消费 session/幂等/许可；真实内部 permit 消费时把幂等摘要、executionCount CAS 和 required audit 放在同一事务。raw token、幂等 key、input/policy 正文和 permit 不得外发或持久化。
- Action execution 默认关闭；八开关齐备后只允许声明版本 2 的 `read + requestReply` Action。只接受精确 execute POST 的唯一 `lat_` bearer，不拼接客户端 URI；在服务版本锁内完成最终授权、静态 `direct:` 调用、输出 Schema 校验和 required completed/failed audit。审计不存输入/输出正文、raw token 或内部异常。
