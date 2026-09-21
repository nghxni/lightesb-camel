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


## Java 业务检查示例

同一扩展工程还提供三个业务 Provider，对应 `example/routes/OrderDeliveryCheckJavaSrv`、`InventoryReconcileJavaSrv`、`ReceivableExceptionJavaSrv`；原 DataSonnet 样例保留。

| 服务 | 转换名 | Action ID |
| --- | --- | --- |
| OrderDeliveryCheckJavaSrv | checkOrderDeliveryV1 | check-order-delivery-java |
| InventoryReconcileJavaSrv | reconcileInventoryV1 | reconcile-erp-wms-java |
| ReceivableExceptionJavaSrv | checkReceivableExceptionsV1 | check-receivable-exceptions-java |

正常输入是独立对象：订单/对账包含 request、erp、wms，回款包含 request、erp、bank、contract，各值均为 JSON 对象，上游包含 records 数组。String 入口解析整个对象后调用 Map 入口，不接收嵌套 JSON 字符串或整个 Exchange。XML 中 DataSonnet 仅组装输入；全部业务判断在 Java 内执行。

扩展项目执行 `mvn package`，将生成的 JAR 放入 `services/TransformDS`，显式设置 `lightesb.transformds.enabled=true` 后重启。替换旧工程 JAR，避免同名 Provider 类的多个版本并存；JAR 更新需要重启，version() 不提供服务版本隔离。

各 Provider 的 `<转换名>Error` 仅接受 request 对象和 reasonCode（UPSTREAM_UNAVAILABLE 或 DATA_OR_PROCESSING_ERROR）。上游失败与数据处理失败形成 UNKNOWN 结果；SPI 缺失或加载失败导致执行失败，不能作为正常业务结果。

新服务默认停用，使用相同 Mock 和业务 Schema，须为各自的新 Action ID 准备独立授权。参见 [业务使用说明](../manufacturing-action-demo.md)。
