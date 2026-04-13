# 23 第三方 DTS 扩展接入指南（SPI）

## 1. 适用场景

本文用于指导第三方业务团队在**不修改 LightESB 核心源码**的前提下，通过 Java SPI 方式扩展 DTS 转换能力。

适用对象：

- 需要新增自定义转换（如 `transformRiskTags`）
- 需要覆盖已有转换（如 `transformComplexOrder`）
- 需要一个 Provider 支持多个 `transformName`

---

## 2. 运行机制概览

LightESB 启动后会按以下链路加载第三方扩展：

1. 扫描目录：`services/TransformDS`
2. 匹配 Jar：`lightesb.transformds.scan-pattern`（当前实现按 `*.jar` 处理）
3. SPI 加载：通过 `ServiceLoader<LightesbDtsExtension>` 发现扩展类
4. 注册选择：按 `supportedTransforms()` 建立映射，冲突时按 `priority()` 选择高优先级
5. 路由调用：通过 `commonFunctions` Bean 统一调用扩展实现

关键默认配置（`application.yaml`）：

```yaml
lightesb:
  transformds:
    enabled: true
    directory: services/TransformDS
    scan-pattern: "*.jar"
```

---

## 3. 开发规范

### 3.1 实现 SPI 接口

第三方扩展必须实现接口：

- `com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension`

最小实现要求：

- `id()`：扩展唯一标识（建议与业务语义相关）
- `priority()`：冲突时选择依据，值越大优先级越高
- `version()`：扩展版本（建议语义化版本）
- `supportedTransforms()`：声明当前 Provider 支持的转换名集合
- `transform(String, String)` 与 `transform(String, Map<String,Object>)`：字符串与对象两种入参形态都要支持

建议：

- 当 `supportedTransforms()` 返回多个 transformName 时，在 `transform(...)` 内使用 `switch` 分发
- 对非法 JSON、字段缺失、类型不匹配抛出可解释异常，便于路由侧排障

### 3.2 SPI 声明文件

在扩展 Jar 中创建文件：

- `META-INF/services/com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension`

文件内容为扩展实现类全限定名（每行一个），例如：

```text
com.oureman.soa.lightesb.example.dts.spi.TransformComplexOrderProvider
com.oureman.soa.lightesb.example.dts.spi.TransformOrderSummaryProvider
com.oureman.soa.lightesb.example.dts.spi.TransformRiskTagsProvider
```

### 3.3 工程示例参考

可直接参考示例工程：

- `example/transform-dts-java`

示例覆盖了三种常见模式：

- 单 Provider 单 transform：`TransformComplexOrderProvider`
- 单 Provider 多 transform：`TransformOrderSummaryProvider`
- 多 Provider 并存：`TransformRiskTagsProvider`

---

## 4. 打包与投放

### 4.1 构建扩展 Jar

在示例工程目录执行（或在你自己的扩展工程执行同等命令）：

```bash
mvn clean package
```

构建产物通常位于：

- `target/*.jar`

### 4.2 投放目录

将扩展 Jar 复制到：

- `services/TransformDS`

目录建议遵循：

- 命名：`<biz>-dts-impl-<semver>.jar`
- 多版本并存时保留版本号，不覆盖不同版本文件

---

## 5. 路由调用方式

第三方扩展接入后，路由层仍通过 `commonFunctions` 调用，无需改造整体调用风格。

### 5.1 调用默认 transform（兼容老路由）

```xml
<setProperty name="complexOrderResult">
    <method ref="commonFunctions" method="transformComplexOrder(${body})" />
</setProperty>
```

### 5.2 调用通用入口（推荐）

```xml
<setProperty name="orderSummaryResult">
    <method ref="commonFunctions" method="invokeDtsTransform('transformOrderSummary', ${body})" />
</setProperty>
```

说明：

- `transformName` 必须在某个扩展的 `supportedTransforms()` 中声明
- 入参可为原始 JSON 字符串或 `Map`

---

## 6. 冲突与回退策略

### 6.1 扩展冲突

当多个扩展声明同一 `transformName` 时：

- 系统按 `priority()` 选择高优先级实现
- 低优先级实现会被丢弃并记录告警日志

### 6.2 默认回退（仅 `transformComplexOrder`）

`CommonFunctionsFacade` 中对 `transformComplexOrder` 提供了默认实现回退：

- 未找到扩展：回退到内置 `super.transformComplexOrder(...)`
- 扩展执行异常：记录告警后回退内置实现

### 6.3 非默认 transform 的行为

对于非默认转换（如 `transformRiskTags`）：

- 未找到扩展：抛出 `IllegalArgumentException`
- 扩展执行失败：抛出 `IllegalStateException`

建议业务路由在调用新 transform 时增加异常分支或全局异常映射。

---

## 7. 验收清单

投放后建议按以下清单验收：

1. 启动日志出现 `TransformDS 扩展 Jar 扫描结束`
2. 启动日志出现 `ServiceLoader 命中扩展`
3. 启动日志出现 `TransformDS 扫描完成，当前生效扩展`
4. 路由调用 `invokeDtsTransform('<yourTransform>', ...)` 返回预期结果
5. 移除扩展 Jar 后，`transformComplexOrder` 可回退默认实现

---

## 8. 常见问题排查

### 8.1 扫描不到扩展 Jar

- 检查 `lightesb.transformds.enabled` 是否为 `true`
- 检查目录是否为 `services/TransformDS`
- 检查 Jar 文件后缀是否为 `.jar`

### 8.2 SPI 未命中

- 检查 `META-INF/services/...LightesbDtsExtension` 文件路径是否正确
- 检查文件内容是否是**实现类全限定名**，并且类可被 Jar 正常加载

### 8.3 路由调用报 “No DTS extension found”

- 检查 `invokeDtsTransform` 的 `transformName` 拼写是否与 `supportedTransforms()` 完全一致
- 确认当前 transform 是否属于默认回退范围（仅 `transformComplexOrder`）

### 8.4 XML 路由命名空间错误

如果在 XML 路由中写了前缀标签（如 `<servicelog:info .../>`），需先声明对应 namespace；
更稳妥的写法是使用 URI 形式：

```xml
<to uri="servicelog:info?message=..."/>
```

---

## 9. 推荐实践

- 新增 transform 时优先使用 `invokeDtsTransform`，避免将路由绑定到单一方法名
- 一个 Provider 可以承载一组相关 transform，但建议控制边界，避免“巨型 Provider”
- `priority()` 只用于冲突仲裁，不建议滥用超大数值
- 发布时保留版本号并可快速回滚（移除 Jar 即回退）

---

## 10. 最小可复制模板（第三方项目）

### 10.1 目录结构

```text
acme-dts-extension/
  pom.xml
  src/main/java/com/acme/lightesb/dts/spi/AcmeOrderProvider.java
  src/main/resources/META-INF/services/com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension
```

### 10.2 `pom.xml` 模板（最小依赖）

说明：以下模板假设你已将 LightESB DTS SPI 接口以依赖方式提供（例如 sdk-api）。

```xml
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.acme.lightesb</groupId>
    <artifactId>acme-dts-extension</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.release>21</maven.compiler.release>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>

    <dependencies>
        <!-- 按你们发布的 DTS SPI 坐标替换 -->
        <dependency>
            <groupId>com.oureman.soa.lightesb</groupId>
            <artifactId>lightesb-dts-sdk-api</artifactId>
            <version>${lightesb.sdk.version}</version>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.13.0</version>
                <configuration>
                    <release>${maven.compiler.release}</release>
                    <encoding>${project.build.sourceEncoding}</encoding>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

### 10.3 Provider 骨架代码

```java
package com.acme.lightesb.dts.spi;

import com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

public class AcmeOrderProvider implements LightesbDtsExtension {

    @Override
    public String id() {
        return "acmeOrderProvider";
    }

    @Override
    public int priority() {
        return 100;
    }

    @Override
    public String version() {
        return "1.0.0";
    }

    @Override
    public Set<String> supportedTransforms() {
        return Set.of("transformAcmeOrder");
    }

    @Override
    public Map<String, Object> transform(String transformName, String jsonPayload) {
        // 生产环境建议把 jsonPayload 反序列化后复用 Map 入口
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("transform", "transformAcmeOrder");
        result.put("raw", jsonPayload);
        return result;
    }

    @Override
    public Map<String, Object> transform(String transformName, Map<String, Object> payload) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("transform", "transformAcmeOrder");
        result.put("orderId", payload.get("orderId"));
        result.put("source", "acme");
        return result;
    }
}
```

### 10.4 SPI 文件内容模板

文件：`src/main/resources/META-INF/services/com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension`

```text
com.acme.lightesb.dts.spi.AcmeOrderProvider
```

### 10.5 投放与调用示例

1. 构建 Jar：`mvn clean package`
2. 复制到：`services/TransformDS`
3. 路由调用：

```xml
<setProperty name="acmeResult">
    <method ref="commonFunctions" method="invokeDtsTransform('transformAcmeOrder', ${body})" />
</setProperty>
```

4. 验证启动日志中存在：
   - `ServiceLoader 命中扩展`
   - `TransformDS 扫描完成，当前生效扩展`

