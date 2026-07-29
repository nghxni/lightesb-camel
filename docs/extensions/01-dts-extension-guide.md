# DTS 扩展开发指南

## 用途

DTS 扩展用于把自定义转换逻辑打包成可交付组件，供 LightESB 路由调用。

## 开发目录

参考：

- `example/transform-dts-java/`：独立 Maven/SPI 扩展示例。
- `example/routes/PlatformHttp/v1.0.0/`：DataSonnet import 与 `commonFunctions` 组合演示。
- `example/routes/PlatformHttp/v2.0.0/`：DTS 通用入口串联演示。

## 基本步骤

1. 创建 Java Maven 项目。
2. 实现正式 SPI `LightesbDtsExtension`。
3. 在 `META-INF/services/com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension` 中登记 Provider。
4. 编写示例输入输出。
5. 打包 jar。
6. 放入交付包约定目录。
7. 显式启用 DTS 扩展并在路由或转换配置中引用。

平台运行配置：

```properties
lightesb.transformds.enabled=true
lightesb.transformds.directory=services/TransformDS
```

DTS 默认关闭；不配置 `enabled=true` 时不会扫描或装载扩展 jar。运行时在扩展
重载和关闭时释放扩展类加载器。旧 `TransformDtsExtension` 已废弃，只保留一个
版本作为迁移过渡，新扩展不要再实现旧接口。

## 示例工程

`example/transform-dts-java/` 包含：

```text
pom.xml
src/main/java/com/oureman/soa/lightesb/core/dts/spi/LightesbDtsExtension.java
src/main/java/com/oureman/soa/lightesb/example/dts/core/TransformCommonFunctions.java
src/main/java/com/oureman/soa/lightesb/example/dts/core/transformComplexOrder.java
src/main/java/com/oureman/soa/lightesb/example/dts/spi/TransformComplexOrderProvider.java
src/main/java/com/oureman/soa/lightesb/example/dts/spi/TransformOrderSummaryProvider.java
src/main/java/com/oureman/soa/lightesb/example/dts/spi/TransformRiskTagsProvider.java
src/main/resources/META-INF/services/com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension
```

构建：

```bash
cd example/transform-dts-java
mvn package
```

Provider 暴露的转换名：

- `transformComplexOrder`
- `transformOrderSummary`
- `transformCustomerSnapshot`
- `transformRiskTags`

路由侧可参考 `example/routes/PlatformHttp/v1.0.0/complex-json-transform-route.xml` 和 `example/routes/PlatformHttp/v2.0.0/complex-json-transform-route.xml` 中的 `commonFunctions.invokeDtsTransform(...)`。

## 转换方法建议

- 输入使用 `String` 或 `Map<String, Object>`。
- 输出使用 `Map<String, Object>` 或 JSON 字符串。
- 对缺失字段返回明确默认值或抛出可解释异常。
- 输入字符串按调用方提供的内容处理，不要按乱码特征隐式重编码；历史兼容应由服务路由或扩展自己的显式开关完成。
- 不在转换类中写死客户环境地址、凭据或不可外发数据。

## 验证

- 使用 demo JSON 执行单元测试或 `mvn package`。
- 确认平台显式配置 `lightesb.transformds.enabled=true`。
- 在 `example/routes/PlatformHttp/` 中接入后调用 HTTP 样例。
- 故意传入非法 JSON，确认错误信息可读。
