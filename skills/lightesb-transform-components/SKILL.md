---
name: lightesb-transform-components
description: 配置 conditionaltransform、jsontransform、JSON 映射和 DTS 转换样例时使用。
---

# LightESB 转换组件

先读：

- `docs/components/04-transform-components.md`
- `example/routes/PlatformHttp/v1.0.0/`
- `example/routes/PlatformHttp/v2.0.0/`
- `example/routes/PlatformHttp/v3.0.0/`
- `docs/extensions/01-dts-extension-guide.md`
- `docs/extensions/02-dts-minimal-template.md`

规则：

- `conditionaltransform` 和 `jsontransform` 放在 `<to>`，不要放在 `<from>`。
- 动态 `jsontransform:dynamic` 必须提供 `transformConfigId`。
- 可选转换用 `skipOnError=true`，强规则转换用 `failOnError=true`。
- DataSonnet import 参考 `PlatformHttp/v1.0.0/input-transform-with-import.ds`，相关文件要和路由一起放在同一服务版本目录。
- JSONPath 提取和 `commonFunctions` 方法调用参考 `PlatformHttp`，正式接口要补异常分支。
- `PlatformHttp/v1.0.0` 默认端口 `18081`，入口包括 `/api/transform/complex-order` 和 `/api/demo`。
- `PlatformHttp/v2.0.0` 默认端口 `18081`，入口为 `/2.0.0/api/demo`，用于 DTS 通用入口串联演示。
- `PlatformHttp/v3.0.0` 默认端口 `18080`，入口包括 `/api/transform/order` 和 `/api/transform/order1`。
- DTS 扩展示例只使用演示数据。
- `example/routes/**/log4j2.properties` 不需要随样例提供，运行时会自动生成。

验收：

- 合法输入能输出目标 JSON。
- 缺失配置或非法 JSON 有明确错误。
- 样例可从 `example/` 复制到 `lightesb-camel-app/` 临时运行。
- `PlatformHttp` 样例复制后，v1/v3 的端口配置不要与现有正式服务冲突。
