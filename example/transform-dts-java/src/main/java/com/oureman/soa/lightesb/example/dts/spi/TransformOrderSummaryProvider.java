package com.oureman.soa.lightesb.example.dts.spi;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/**
 * 一个 Provider 支持多个 transformName 的示例。
 */
public class TransformOrderSummaryProvider implements LightesbDtsExtension {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Override
    public String id() {
        return "transformOrderSummaryProvider";
    }

    @Override
    public int priority() {
        return 120;
    }

    @Override
    public String version() {
        return "1.0.0";
    }

    @Override
    public Set<String> supportedTransforms() {
        return Set.of("transformOrderSummary", "transformCustomerSnapshot");
    }

    @Override
    public Map<String, Object> transform(String transformName, String jsonPayload) {
        return transform(transformName, parseJsonToMap(jsonPayload));
    }

    @Override
    public Map<String, Object> transform(String transformName, Map<String, Object> payload) {
        String name = transformName == null ? "" : transformName.trim();
        return switch (name) {
            case "transformOrderSummary" -> transformOrderSummary(payload);
            case "transformCustomerSnapshot" -> transformCustomerSnapshot(payload);
            default -> throw new IllegalArgumentException("Unsupported transformName for provider " + id() + ": " + transformName);
        };
    }

    private Map<String, Object> transformOrderSummary(Map<String, Object> payload) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("transform", "transformOrderSummary");
        result.put("orderId", get(payload, "order", "header", "orderId"));
        result.put("customerId", get(payload, "order", "customer", "personalInfo", "customerId"));
        result.put("itemCount", asListSize(get(payload, "order", "items")));
        result.put("grandTotal", get(payload, "order", "payment", "summary", "total"));
        return result;
    }

    private Map<String, Object> transformCustomerSnapshot(Map<String, Object> payload) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("transform", "transformCustomerSnapshot");
        result.put("customerId", get(payload, "order", "customer", "personalInfo", "customerId"));
        result.put("customerLevel", get(payload, "order", "customer", "membership", "level"));
        result.put("customerEmail", get(payload, "order", "customer", "personalInfo", "contact", "email"));
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

    @SuppressWarnings("unchecked")
    private int asListSize(Object value) {
        if (value instanceof java.util.List<?> list) {
            return list.size();
        }
        return 0;
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
