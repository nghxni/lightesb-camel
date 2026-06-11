---
name: lightesb-dts-extension
description: 开发、打包和接入第三方 DTS 转换扩展时使用。
---

# LightESB DTS 扩展

先读：

- `docs/extensions/01-dts-extension-guide.md`
- `docs/extensions/02-dts-minimal-template.md`
- `example/transform-dts-java/`
- `example/routes/PlatformHttp/v1.0.0/`
- `example/routes/PlatformHttp/v2.0.0/`

规则：

- 扩展项目使用演示输入输出，不写真实环境信息。
- 转换方法要处理缺失字段和非法 JSON。
- Provider 需要在 `META-INF/services/com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension` 中登记。
- 打包后先在 `example/routes/PlatformHttp/` 路由中验证。

验收：

- Maven 构建通过。
- demo JSON 可转换。
- 路由接入后错误可在服务日志中定位。
