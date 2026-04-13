package com.oureman.soa.lightesb.example.dts.spi;

import com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension;
import com.oureman.soa.lightesb.example.dts.core.TransformCommonFunctions;
import com.oureman.soa.lightesb.example.dts.core.transformComplexOrder;

import java.util.Map;
import java.util.Set;

/**
 * transformComplexOrder 的 SPI Provider。
 */
public class TransformComplexOrderProvider implements LightesbDtsExtension {

    private final TransformCommonFunctions commonFunctions = new TransformCommonFunctions();

    @Override
    public String id() {
        return "transformComplexOrder";
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
        return Set.of("transformComplexOrder");
    }

    @Override
    public Map<String, Object> transform(String transformName, String jsonPayload) {
        return transformComplexOrder.execute(jsonPayload, commonFunctions);
    }

    @Override
    public Map<String, Object> transform(String transformName, Map<String, Object> payload) {
        return transformComplexOrder.execute(payload, commonFunctions);
    }
}
