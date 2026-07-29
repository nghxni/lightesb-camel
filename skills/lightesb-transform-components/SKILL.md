---
name: lightesb-transform-components
description: 配置 conditionaltransform、jsontransform、JSON 映射和 DTS 转换样例时使用。
---

# LightESB 转换组件

先读：

- `docs/components/16-route-static-preflight.md`
- `docs/components/04-transform-components.md`
- 基础转换读 `example/routes/transform-json/`；DataSonnet import 再读 `example/routes/PlatformHttp/v1.0.0/`；DTS Java 扩展才读 `docs/extensions/01-dts-extension-guide.md` 和 `docs/extensions/02-dts-minimal-template.md`。

规则：

- `conditionaltransform` 和 `jsontransform` 放在 `<to>`，不要放在 `<from>`。
- 动态 `jsontransform:dynamic` 必须提供 `transformConfigId`。
- JSON Transform 规则只放在所属服务版本目录，文件名包含 `transform`，后缀为 `.yml`、`.yaml` 或 `.json`；不要使用全局 `config/transforms` 目录。
- 规则配置 ID 在运行时全局唯一；热更新无效时继续使用最后一次有效配置。
- 可选转换用 `skipOnError=true`，强规则转换用 `failOnError=true`。
- DataSonnet import 参考 `PlatformHttp/v1.0.0/input-transform-with-import.ds`，相关文件要和路由一起放在同一服务版本目录。
- JSONPath 提取和 `commonFunctions` 方法调用参考 `PlatformHttp`，正式接口要补异常分支。
- `PlatformHttp/v1.0.0` 默认端口 `18081`，入口包括 `/api/transform/complex-order` 和 `/api/demo`。
- `PlatformHttp/v2.0.0` 默认端口 `18081`，入口为 `/2.0.0/api/demo`，用于 DTS 通用入口串联演示。
- `PlatformHttp/v3.0.0` 默认端口 `18080`，入口包括 `/api/transform/order` 和 `/api/transform/order1`。
- DTS 扩展示例只使用演示数据。
- 字符串默认不按乱码特征重编码；仅在确认历史链路需要时设置服务配置 `charset.legacy-mojibake-repair.enabled=true`。
- `example/routes/**/log4j2.properties` 不需要随样例提供，运行时会自动生成。
- 交付前确认 `system.components` 同时包含所用的 `jsontransform` / `conditionaltransform`，`input-transform.file` 与同目录 `.ds` 文件一致；默认只做该静态检查，不运行样例。

验收：

- 静态检查确认转换组件、配置键、`.ds` 资源和 XML 引用一致。
- 用户明确授权运行态验证时，才验证合法/非法输入与端口冲突。
