package com.oureman.soa.lightesb.example.dts.spi;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * 独立 Provider 的示例：与其他 Provider 并存。
 */
public class TransformRiskTagsProvider implements LightesbDtsExtension {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Override
    public String id() {
        return "transformRiskTagsProvider";
    }

    @Override
    public int priority() {
        return 110;
    }

    @Override
    public String version() {
        return "1.0.0";
    }

    @Override
    public Set<String> supportedTransforms() {
        return Set.of("transformRiskTags");
    }

    @Override
    public Map<String, Object> transform(String transformName, String jsonPayload) {
        return transform(transformName, parseJsonToMap(jsonPayload));
    }

    @Override
    public Map<String, Object> transform(String transformName, Map<String, Object> payload) {
        if (!"transformRiskTags".equals(transformName)) {
            throw new IllegalArgumentException("Unsupported transformName for provider " + id() + ": " + transformName);
        }

        List<String> tags = new ArrayList<>();
        Object total = get(payload, "order", "payment", "summary", "total");
        if (toDouble(total) > 5000D) {
            tags.add("HIGH_AMOUNT");
        }

        Object level = get(payload, "order", "customer", "membership", "level");
        if ("gold".equalsIgnoreCase(String.valueOf(level))) {
            tags.add("VIP_CUSTOMER");
        }

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("transform", "transformRiskTags");
        result.put("orderId", get(payload, "order", "header", "orderId"));
        result.put("riskTags", tags);
        result.put("riskLevel", tags.isEmpty() ? "LOW" : "MEDIUM");
        return result;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> parseJsonToMap(String jsonPayload) {
        if (jsonPayload == null || jsonPayload.isEmpty()) {
            return new LinkedHashMap<>();
        }
        try {
            return OBJECT_MAPPER.readValue(jsonPayload, Map.class);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("Invalid JSON payload: " + e.getMessage(), e);
        }
    }

    private double toDouble(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        if (value == null) {
            return 0D;
        }
        try {
            return Double.parseDouble(value.toString());
        } catch (NumberFormatException e) {
            return 0D;
        }
    }

    @SuppressWarnings("unchecked")
    private Object get(Map<String, Object> map, String... path) {
        Object current = map;
        for (String key : path) {
            if (!(current instanceof Map<?, ?> currentMap)) {
                return null;
            }
            current = ((Map<String, Object>) currentMap).get(key);
            if (current == null) {
                return null;
            }
        }
        return current;
    }
}
