package com.oureman.soa.lightesb.example.dts.business;

import java.util.*;

/** Fixed-snapshot order/shipment reconciliation; READY does not imply delivery. */
public final class OrderDeliveryProvider extends BusinessTransform {
    public OrderDeliveryProvider() { super("checkOrderDeliveryV1"); }

    @Override
    protected Map<String, Object> calculate(Map<String, Object> req, Map<String, Object> payload) {
        var orders = rows(payload, "erp", req, "orderId");
        var shipments = rows(payload, "wms", req, "orderId");
        boolean found = orders.size() == 1 && shipments.size() == 1;
        var order = found ? orders.getFirst() : Map.<String, Object>of();
        var shipment = found ? shipments.getFirst() : Map.<String, Object>of();
        boolean valid = found && text(order.get("recordId")) && text(shipment.get("recordId"))
            && Arrays.asList("OPEN", "SHIPPED", "CANCELLED").contains(order.get("status"))
            && integer(order.get("orderedQuantity"), 1_000_000) && integer(shipment.get("shippedQuantity"), 1_000_000)
            && text(order.get("unit")) && text(shipment.get("unit")) && date(order.get("dueDate"))
            && text(order.get("observedAt")) && text(shipment.get("observedAt"));
        String reason = !found ? "MISSING_OR_AMBIGUOUS_RECORD" : !valid ? "INVALID_UPSTREAM_DATA"
            : !Objects.equals(order.get("observedAt"), req.get("asOf")) || !Objects.equals(shipment.get("observedAt"), req.get("asOf"))
                ? "STALE_DATA" : !Objects.equals(order.get("unit"), shipment.get("unit")) ? "UNIT_MISMATCH" : null;
        long ordered = valid ? number(order.get("orderedQuantity")) : 0;
        long shipped = valid ? number(shipment.get("shippedQuantity")) : 0;
        boolean overdue = valid && ((String) order.get("dueDate")).compareTo(req.get("asOf").toString().substring(0, 10)) < 0;
        String status = reason != null ? "UNKNOWN"
            : ("CANCELLED".equals(order.get("status")) && shipped > 0) || shipped > ordered
                || ("SHIPPED".equals(order.get("status")) && shipped != ordered) ? "STATE_CONFLICT"
            : "CANCELLED".equals(order.get("status")) ? "CANCELLED"
            : shipped == ordered ? "READY" : shipped > 0 ? "PARTIAL" : overdue ? "OVERDUE" : "READY";
        List<String> reasons = new ArrayList<>(List.of(reason == null ? status : reason));
        if ("PARTIAL".equals(status) && overdue) reasons.add("OVERDUE");
        var result = base(req, "orderId");
        result.putAll(map("status", status, "reasons", reasons, "orderedQuantity", valid ? ordered : null,
            "shippedQuantity", valid ? shipped : null, "unit", valid ? order.get("unit") : null,
            "evidence", concat(evidence(orders, "ERP", true), evidence(shipments, "WMS", true))));
        return result;
    }

    @Override
    protected Map<String, Object> error(Map<String, Object> req, String reason) {
        var result = base(req, "orderId");
        result.putAll(map("status", "UNKNOWN", "reasons", List.of(reason), "orderedQuantity", null,
            "shippedQuantity", null, "unit", null, "evidence", List.of()));
        return result;
    }
}
