package com.oureman.soa.lightesb.core.dts.spi;

import java.util.Collections;
import java.util.Map;
import java.util.Set;

/**
 * 示例工程使用的 DTS SPI 接口（与运行时契约保持一致）。
 */
public interface LightesbDtsExtension {

    String id();

    default int priority() {
        return 0;
    }

    default String version() {
        return "0.0.0";
    }

    default Set<String> supportedTransforms() {
        return Collections.singleton("transformComplexOrder");
    }

    Map<String, Object> transform(String transformName, String jsonPayload);

    Map<String, Object> transform(String transformName, Map<String, Object> payload);
}
