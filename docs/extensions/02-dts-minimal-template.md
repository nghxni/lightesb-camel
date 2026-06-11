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

## 注意

- 模板只放演示数据。
- 打包前确认依赖范围，避免把不需要的运行时依赖塞入扩展包。
- 异常消息要可读，便于路由日志定位。
