package com.oureman.soa.lightesb.example.dts.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 与 common-functions.ds 对齐的最小函数集。
 */
public class TransformCommonFunctions {

    public String formatAddress(Map<String, Object> address) {
        if (address == null) {
            return "";
        }
        return safeStr(str(address.get("province")))
                + safeStr(str(address.get("city")))
                + safeStr(str(address.get("street")))
                + " "
                + safeStr(str(address.get("zipCode")));
    }

    public String formatFullName(Map<String, Object> name) {
        if (name == null) {
            return "";
        }
        return safeStr(str(name.get("firstName"))) + safeStr(str(name.get("lastName")));
    }

    public String formatCategory(Map<String, Object> category) {
        if (category == null) {
            return "";
        }
        return safeStr(str(category.get("primary")))
                + " > "
                + safeStr(str(category.get("secondary")))
                + " > "
                + safeStr(str(category.get("tertiary")));
    }

    public String formatSpecifications(Map<String, Object> specs) {
        if (specs == null) {
            return "";
        }
        List<String> parts = new ArrayList<>();
        addIfPresent(parts, specs, "color");
        addIfPresent(parts, specs, "storage");
        addIfPresent(parts, specs, "connectivity");
        return String.join(", ", parts);
    }

    public String formatWarranty(Map<String, Object> warranty) {
        if (warranty == null) {
            return "";
        }
        return safeStr(str(warranty.get("type"))) + "-" + safeStr(str(warranty.get("duration"))) + "months";
    }

    public double calculateLineTotal(Object price, Object quantity) {
        return toDouble(price) * toInt(quantity);
    }

    public double formatAmount(Object amount) {
        double value = toDouble(amount);
        return Math.floor(value * 100) / 100.0;
    }

    public String formatDate(String dateStr) {
        return dateStr;
    }

    private void addIfPresent(List<String> parts, Map<String, Object> data, String key) {
        String value = str(data.get(key));
        if (!value.isEmpty()) {
            parts.add(value);
        }
    }

    private int toInt(Object value) {
        if (value == null) {
            return 0;
        }
        if (value instanceof Number) {
            return ((Number) value).intValue();
        }
        try {
            return Integer.parseInt(value.toString().trim());
        } catch (Exception e) {
            return 0;
        }
    }

    private double toDouble(Object value) {
        if (value == null) {
            return 0D;
        }
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        }
        try {
            return Double.parseDouble(value.toString().trim());
        } catch (Exception e) {
            return 0D;
        }
    }

    private String safeStr(String value) {
        return value == null ? "" : value;
    }

    private String str(Object value) {
        return value == null ? "" : value.toString();
    }
}
