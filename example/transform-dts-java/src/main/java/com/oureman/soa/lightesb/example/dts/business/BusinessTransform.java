package com.oureman.soa.lightesb.example.dts.business;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.oureman.soa.lightesb.core.dts.spi.LightesbDtsExtension;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.*;

/** Shared JSON boundary for the three stateless, synthetic business transforms. */
public abstract class BusinessTransform implements LightesbDtsExtension {
    private static final ObjectMapper JSON = new ObjectMapper();
    private final String name;

    protected BusinessTransform(String name) { this.name = name; }
    @Override public String id() { return name + "Provider"; }
    @Override public String version() { return "1.0.0"; }
    @Override public Set<String> supportedTransforms() { return Set.of(name, name + "Error"); }

    @Override
    public Map<String, Object> transform(String transformName, String jsonPayload) {
        try {
            return transform(transformName, JSON.readValue(jsonPayload, new TypeReference<Map<String, Object>>() {}));
        } catch (com.fasterxml.jackson.core.JsonProcessingException e) {
            throw new IllegalArgumentException("Invalid business input JSON", e);
        }
    }

    @Override
    public Map<String, Object> transform(String transformName, Map<String, Object> payload) {
        if (!supportedTransforms().contains(transformName)) {
            throw new IllegalArgumentException("Unsupported business transform: " + transformName);
        }
        Map<String, Object> request = object(payload.get("request"));
        if (transformName.equals(name + "Error")) {
            Object reason = payload.get("reasonCode");
            if (!Set.of("UPSTREAM_UNAVAILABLE", "DATA_OR_PROCESSING_ERROR").contains(reason)) {
                throw new IllegalArgumentException("Unsupported business error reason");
            }
            return error(request, (String) reason);
        }
        try {
            return calculate(request, payload);
        } catch (RuntimeException e) {
            // The SPI lookup occurs outside this provider. Only data/computation errors reach here.
            return error(request, "DATA_OR_PROCESSING_ERROR");
        }
    }

    protected abstract Map<String, Object> calculate(Map<String, Object> request, Map<String, Object> payload);
    protected abstract Map<String, Object> error(Map<String, Object> request, String reason);

    @SuppressWarnings("unchecked")
    static Map<String, Object> object(Object value) {
        if (!(value instanceof Map<?, ?>)) throw new IllegalArgumentException("Expected JSON object");
        return (Map<String, Object>) value;
    }

    static List<Map<String, Object>> rows(Map<String, Object> payload, String source,
                                          Map<String, Object> request, String... keys) {
        Object records = object(payload.get(source)).get("records");
        if (!(records instanceof List<?> list)) throw new IllegalArgumentException("Expected records array");
        List<Map<String, Object>> selected = new ArrayList<>();
        for (Object item : list) {
            Map<String, Object> row = object(item);
            boolean match = true;
            for (String key : keys) {
                if (!row.containsKey(key)) throw new IllegalArgumentException("Missing association field: " + key);
                match &= Objects.equals(row.get(key), request.get(key));
            }
            if (match) selected.add(row);
        }
        return selected;
    }

    static boolean text(Object value) { return value instanceof String s && !s.isEmpty() && s.length() <= 64; }
    static boolean nonempty(Object value) { return value instanceof String s && !s.isEmpty(); }
    static boolean integer(Object value, long max) {
        if (!(value instanceof Number number)) return false;
        try {
            BigDecimal decimal = new BigDecimal(number.toString());
            return decimal.signum() >= 0 && decimal.compareTo(BigDecimal.valueOf(max)) <= 0
                && decimal.stripTrailingZeros().scale() <= 0;
        } catch (NumberFormatException e) { return false; }
    }
    static long number(Object value) { return new BigDecimal(value.toString()).longValueExact(); }
    static boolean date(Object value) {
        if (!(value instanceof String s) || !s.matches("[0-9]{4}-[0-9]{2}-[0-9]{2}")) return false;
        try { return LocalDate.parse(s).getYear() >= 1; }
        catch (DateTimeParseException e) { return false; }
    }
    static boolean fields(Map<String, Object> row, String... names) {
        return Arrays.stream(names).allMatch(row::containsKey);
    }
    static boolean duplicate(List<Map<String, Object>> rows) {
        Set<Object> ids = new HashSet<>();
        return rows.stream().anyMatch(x -> text(x.get("recordId")) && !ids.add(x.get("recordId")));
    }
    static List<Map<String, Object>> evidence(List<Map<String, Object>> rows, String source, boolean bounded) {
        return rows.stream().filter(x -> bounded
            ? text(x.get("recordId")) && text(x.get("observedAt"))
            : nonempty(x.get("recordId")) && nonempty(x.get("observedAt")))
            .map(x -> map("sourceSystem", source, "recordId", x.get("recordId"), "observedAt", x.get("observedAt")))
            .toList();
    }
    @SafeVarargs
    static <T> List<T> concat(List<T>... lists) {
        List<T> result = new ArrayList<>();
        for (List<T> list : lists) result.addAll(list);
        return result;
    }
    static Map<String, Object> map(Object... pairs) {
        Map<String, Object> result = new LinkedHashMap<>();
        for (int i = 0; i < pairs.length; i += 2) result.put((String) pairs[i], pairs[i + 1]);
        return result;
    }
    static Map<String, Object> base(Map<String, Object> request, String... ids) {
        Map<String, Object> result = map("mock", true, "asOf", request.get("asOf"));
        for (String id : ids) result.put(id, request.get(id));
        return result;
    }
}
