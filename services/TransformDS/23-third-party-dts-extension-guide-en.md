# 23 Third-Party DTS Extension Integration Guide (SPI)

## 1. Applicable Scenarios

This guide helps third-party business teams extend DTS transformation capabilities through Java SPI **without modifying LightESB core source code**.

Target use cases:

- Add new custom transforms (for example, `transformRiskTags`)
- Override existing transforms (for example, `transformComplexOrder`)
- Let one Provider support multiple `transformName` values

---

## 2. Runtime Loading Overview

After LightESB starts, third-party extensions are loaded in this chain:

1. Scan directory: `services/TransformDS`
2. Match jars: `lightesb.transformds.scan-pattern` (current implementation uses `*.jar`)
3. SPI loading: discover extension classes via `ServiceLoader<LightesbDtsExtension>`
4. Registration and selection: build mapping by `supportedTransforms()`, resolve conflicts by higher `priority()`
5. Route invocation: call extension implementations through the `commonFunctions` bean

Key default configuration (`application.yaml`):

```yaml
lightesb:
  transformds:
    enabled: true
    directory: services/TransformDS
    scan-pattern: "*.jar"
```

---

## 3. Development Specification

### 3.1 Implement the SPI Interface

Third-party extensions must implement:

- `com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension`

Minimum implementation requirements:

- `id()`: unique extension identifier (recommended to reflect business semantics)
- `priority()`: conflict resolution priority; larger value wins
- `version()`: extension version (semantic versioning is recommended)
- `supportedTransforms()`: declared transform names supported by this Provider
- `transform(String, String)` and `transform(String, Map<String,Object>)`: both string and object payload forms must be supported

Recommendations:

- If `supportedTransforms()` returns multiple transform names, dispatch with `switch` inside `transform(...)`
- Throw explainable exceptions for invalid JSON, missing fields, or type mismatch to simplify route troubleshooting

### 3.2 SPI Descriptor File

Create this file inside the extension jar:

- `META-INF/services/com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension`

The file content must be fully qualified implementation class names (one per line), for example:

```text
com.oureman.soa.lightesb.example.dts.spi.TransformComplexOrderProvider
com.oureman.soa.lightesb.example.dts.spi.TransformOrderSummaryProvider
com.oureman.soa.lightesb.example.dts.spi.TransformRiskTagsProvider
```

### 3.3 Reference Example Project

You can directly reference:

- `example/transform-dts-java`

The sample covers three common patterns:

- One Provider, one transform: `TransformComplexOrderProvider`
- One Provider, multiple transforms: `TransformOrderSummaryProvider`
- Multiple Providers together: `TransformRiskTagsProvider`

---

## 4. Packaging and Deployment

### 4.1 Build Extension Jar

Run this in the sample project directory (or an equivalent command in your own extension project):

```bash
mvn clean package
```

Build artifacts are usually in:

- `target/*.jar`

### 4.2 Deployment Directory

Copy extension jars to:

- `services/TransformDS`

Directory conventions:

- Naming: `<biz>-dts-impl-<semver>.jar`
- Keep version numbers when multiple versions coexist; do not overwrite different versions

---

## 5. Route Invocation Patterns

After integrating third-party extensions, routes still call through `commonFunctions`, so no major route style refactor is required.

### 5.1 Call default transform (legacy route compatible)

```xml
<setProperty name="complexOrderResult">
    <method ref="commonFunctions" method="transformComplexOrder(${body})" />
</setProperty>
```

### 5.2 Call unified entry (recommended)

```xml
<setProperty name="orderSummaryResult">
    <method ref="commonFunctions" method="invokeDtsTransform('transformOrderSummary', ${body})" />
</setProperty>
```

Notes:

- `transformName` must be declared in some extension's `supportedTransforms()`
- Input can be raw JSON string or `Map`

---

## 6. Conflict and Fallback Strategy

### 6.1 Extension Conflict

When multiple extensions declare the same `transformName`:

- The system selects the implementation with higher `priority()`
- Lower-priority implementations are discarded with warning logs

### 6.2 Default Fallback (only `transformComplexOrder`)

`CommonFunctionsFacade` provides default fallback for `transformComplexOrder`:

- Extension not found: fallback to built-in `super.transformComplexOrder(...)`
- Extension execution exception: log warning then fallback to built-in implementation

### 6.3 Behavior for non-default transforms

For non-default transforms (for example, `transformRiskTags`):

- Extension not found: throw `IllegalArgumentException`
- Extension execution failure: throw `IllegalStateException`

It is recommended to add exception branches or global exception mapping when calling new transforms in business routes.

---

## 7. Acceptance Checklist

After deployment, verify with this checklist:

1. Startup log contains `TransformDS 扩展 Jar 扫描结束`
2. Startup log contains `ServiceLoader 命中扩展`
3. Startup log contains `TransformDS 扫描完成，当前生效扩展`
4. Route call `invokeDtsTransform('<yourTransform>', ...)` returns expected result
5. After removing extension jar, `transformComplexOrder` falls back to default implementation

---

## 8. Common Troubleshooting

### 8.1 Extension jar is not scanned

- Check whether `lightesb.transformds.enabled` is `true`
- Check whether the directory is `services/TransformDS`
- Check whether jar file suffix is `.jar`

### 8.2 SPI is not discovered

- Check whether `META-INF/services/...LightesbDtsExtension` path is correct
- Check whether file content is the **fully qualified implementation class name**, and class is loadable from the jar

### 8.3 Route error: "No DTS extension found"

- Check whether `transformName` in `invokeDtsTransform` exactly matches `supportedTransforms()`
- Confirm whether current transform is covered by default fallback scope (only `transformComplexOrder`)

### 8.4 XML route namespace error

If you use prefixed XML tags (for example, `<servicelog:info .../>`), you must declare the namespace first.
The safer style is URI form:

```xml
<to uri="servicelog:info?message=..."/>
```

---

## 9. Recommended Practices

- Prefer `invokeDtsTransform` for new transforms to avoid binding routes to a single method name
- One Provider can host related transforms, but keep boundaries controlled to avoid "giant Provider" design
- Use `priority()` only for conflict arbitration; avoid abusing very large values
- Keep versioned jars for release and rollback (remove jar to rollback quickly)

---

## 10. Minimal Copyable Template (Third-Party Project)

### 10.1 Directory Structure

```text
acme-dts-extension/
  pom.xml
  src/main/java/com/acme/lightesb/dts/spi/AcmeOrderProvider.java
  src/main/resources/META-INF/services/com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension
```

### 10.2 `pom.xml` Template (minimal dependency)

Note: this template assumes your LightESB DTS SPI interface is provided via dependency coordinates (for example, sdk-api).

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
        <!-- Replace with your published DTS SPI coordinates -->
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

### 10.3 Provider skeleton code

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
        // In production, consider deserializing jsonPayload and reuse the Map-based path
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

### 10.4 SPI file content template

File: `src/main/resources/META-INF/services/com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension`

```text
com.acme.lightesb.dts.spi.AcmeOrderProvider
```

### 10.5 Deployment and invocation example

1. Build jar: `mvn clean package`
2. Copy to: `services/TransformDS`
3. Route invocation:

```xml
<setProperty name="acmeResult">
    <method ref="commonFunctions" method="invokeDtsTransform('transformAcmeOrder', ${body})" />
</setProperty>
```

4. Verify startup logs contain:
   - `ServiceLoader 命中扩展`
   - `TransformDS 扫描完成，当前生效扩展`
