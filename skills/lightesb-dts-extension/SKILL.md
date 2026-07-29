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
- 平台默认关闭 DTS；装载扩展 jar 前必须显式设置 `lightesb.transformds.enabled=true`。
- 新扩展只实现正式 SPI `LightesbDtsExtension`，不再使用已废弃的 `TransformDtsExtension`。
- 转换代码不按乱码特征隐式重编码输入；历史兼容必须使用明确配置。
- 打包后先在 `example/routes/PlatformHttp/` 路由中验证。

验收：

- Maven 构建通过。
- 平台显式启用 DTS 后可发现 Provider，关闭时不装载扩展。
- demo JSON 可转换。
- 路由接入后错误可在服务日志中定位。
