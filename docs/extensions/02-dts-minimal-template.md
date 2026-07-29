# DTS 最小模板

## Maven 项目

```text
transform-dts-java/
  pom.xml
  src/main/java/demo/OrderTransform.java
  src/test/resources/order-input.json
```

## Java 模板

```java
package demo;

import java.util.LinkedHashMap;
import java.util.Map;

public class OrderTransform {
    public Map<String, Object> execute(Map<String, Object> input) {
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("status", "OK");
        out.put("source", input);
        return out;
    }
}
```

## 路由接入思路

```xml
<to uri="conditionaltransform:custom?file=order-transform&amp;required=true"/>
```

平台默认不装载第三方 DTS。把 jar 放入约定目录后，还需在运行配置中显式启用：

```properties
lightesb.transformds.enabled=true
lightesb.transformds.directory=services/TransformDS
```

Provider 使用正式 SPI
`com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension`，并在同名
`META-INF/services` 文件中登记。

## 注意

- 模板只放演示数据。
- 打包前确认依赖范围，避免把不需要的运行时依赖塞入扩展包。
- 异常消息要可读，便于路由日志定位。
- 不按字符特征隐式修复输入编码；需要历史兼容时使用明确配置。
