package com.oureman.soa.lightesb.example.dts.core;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 从 lightesb-camel-core 迁移的复杂订单转换实现。
 */
public class transformComplexOrder {

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private transformComplexOrder() {
    }

    public static Map<String, Object> execute(String jsonPayload, TransformCommonFunctions commonFunctions) {
        return execute(parseJsonToMap(jsonPayload), commonFunctions);
    }

    public static Map<String, Object> execute(Map<String, Object> payload, TransformCommonFunctions commonFunctions) {
        Map<String, Object> result = new LinkedHashMap<>();

        result.put("orderId", get(payload, "order", "header", "orderId"));
        result.put("orderDate", get(payload, "order", "header", "orderDate"));
        result.put("customerId", get(payload, "order", "customer", "personalInfo", "customerId"));

        Map<String, Object> customerName = asMap(get(payload, "order", "customer", "personalInfo", "name"));
        result.put("customerName", commonFunctions.formatFullName(customerName));

        result.put("customerEmail", get(payload, "order", "customer", "personalInfo", "contact", "email"));
        result.put("customerPhone", get(payload, "order", "customer", "personalInfo", "contact", "phone", "primary"));
        result.put("customerLevel", get(payload, "order", "customer", "membership", "level"));
        result.put("customerPoints", get(payload, "order", "customer", "membership", "points"));
        result.put("channel", get(payload, "order", "header", "metadata", "channel"));
        result.put("source", get(payload, "order", "header", "source"));

        Map<String, Object> shippingAddress = asMap(get(payload, "order", "customer", "personalInfo", "contact", "address", "shipping"));
        result.put("shippingAddress", commonFunctions.formatAddress(shippingAddress));

        List<Object> inputItems = asList(get(payload, "order", "items"));
        List<Map<String, Object>> transformedItems = new ArrayList<>();
        for (Object obj : inputItems) {
            Map<String, Object> item = asMap(obj);
            Map<String, Object> transformedItem = new LinkedHashMap<>();

            transformedItem.put("productId", get(item, "product", "productId"));
            transformedItem.put("productName", get(item, "product", "details", "name"));
            transformedItem.put("sku", get(item, "product", "inventory", "sku"));

            Map<String, Object> category = asMap(get(item, "product", "details", "category"));
            transformedItem.put("category", commonFunctions.formatCategory(category));

            transformedItem.put("quantity", get(item, "orderDetails", "quantity"));
            transformedItem.put("unitPrice", get(item, "product", "details", "pricing", "unitPrice"));
            transformedItem.put("discountPrice", get(item, "product", "details", "pricing", "discountPrice"));
            transformedItem.put("lineTotal", commonFunctions.calculateLineTotal(
                    get(item, "product", "details", "pricing", "discountPrice"),
                    get(item, "orderDetails", "quantity")
            ));

            Map<String, Object> specs = asMap(get(item, "product", "details", "specifications"));
            transformedItem.put("specifications", commonFunctions.formatSpecifications(specs));

            Map<String, Object> warranty = asMap(get(item, "orderDetails", "customizations", "warranty"));
            transformedItem.put("warranty", commonFunctions.formatWarranty(warranty));

            transformedItem.put("expedited", get(item, "orderDetails", "fulfillment", "options", "expedited"));
            transformedItems.add(transformedItem);
        }
        result.put("items", transformedItems);

        Map<String, Object> financial = new LinkedHashMap<>();
        financial.put("subtotal", commonFunctions.formatAmount(get(payload, "order", "payment", "summary", "subtotal")));
        financial.put("discountTotal", commonFunctions.formatAmount(get(payload, "order", "payment", "summary", "discounts", "total")));
        financial.put("tax", commonFunctions.formatAmount(get(payload, "order", "payment", "summary", "tax")));
        financial.put("shipping", commonFunctions.formatAmount(get(payload, "order", "payment", "summary", "shipping")));
        financial.put("grandTotal", commonFunctions.formatAmount(get(payload, "order", "payment", "summary", "total")));
        financial.put("currency", "CNY");
        financial.put("paymentMethod", get(payload, "order", "payment", "method", "type"));
        financial.put("cardLast4", get(payload, "order", "payment", "method", "details", "last4Digits"));
        result.put("financial", financial);

        Map<String, Object> shipping = new LinkedHashMap<>();
        shipping.put("carrier", get(payload, "order", "shipping", "method", "carrier"));
        shipping.put("service", get(payload, "order", "shipping", "method", "service"));
        shipping.put("trackingNumber", get(payload, "order", "shipping", "method", "trackingNumber"));
        shipping.put("estimatedDelivery", commonFunctions.formatDate(str(get(payload, "order", "shipping", "timeline", "estimated", "delivery"))));
        result.put("shipping", shipping);

        return result;
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> parseJsonToMap(String jsonPayload) {
        if (jsonPayload == null || jsonPayload.isEmpty()) {
            return new LinkedHashMap<>();
        }
        try {
            String normalizedJson = normalizePotentiallyGarbled(jsonPayload);
            return OBJECT_MAPPER.readValue(normalizedJson, Map.class);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("Invalid JSON payload: " + e.getMessage(), e);
        }
    }

    private static String normalizePotentiallyGarbled(String value) {
        if (value == null || value.isEmpty()) {
            return value;
        }
        if (!containsGarbledChinese(value)) {
            return value;
        }
        try {
            return new String(value.getBytes(StandardCharsets.ISO_8859_1), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return value;
        }
    }

    private static boolean containsGarbledChinese(String str) {
        return str.contains("å") || str.contains("æ") || str.contains("ç")
                || str.contains("é") || str.contains("è") || str.contains("ä")
                || str.contains("ï") || str.contains("±") || str.contains("¼");
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> asMap(Object obj) {
        if (obj instanceof Map) {
            return (Map<String, Object>) obj;
        }
        return new LinkedHashMap<>();
    }

    @SuppressWarnings("unchecked")
    private static List<Object> asList(Object obj) {
        if (obj instanceof List) {
            return (List<Object>) obj;
        }
        return new ArrayList<>();
    }

    private static Object get(Map<String, Object> map, String... path) {
        Object current = map;
        for (String key : path) {
            if (!(current instanceof Map)) {
                return null;
            }
            current = ((Map<?, ?>) current).get(key);
            if (current == null) {
                return null;
            }
        }
        if (current instanceof String) {
            return normalizePotentiallyGarbled((String) current);
        }
        return current;
    }

    private static String str(Object o) {
        if (o == null) {
            return "";
        }
        if (o instanceof String) {
            return normalizePotentiallyGarbled((String) o);
        }
        return o.toString();
    }
}
