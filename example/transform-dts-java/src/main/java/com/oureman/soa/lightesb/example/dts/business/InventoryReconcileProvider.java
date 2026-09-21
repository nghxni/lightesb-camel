package com.oureman.soa.lightesb.example.dts.business;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.*;

/** Reconciles outbound rows, never inventory balances or merged duplicate records. */
public final class InventoryReconcileProvider extends BusinessTransform {
    private static final ObjectMapper JSON = new ObjectMapper();
    private record Key(String lineId, String sku) {
        String sortKey() {
            try { return JSON.writeValueAsString(List.of(lineId, sku)); }
            catch (com.fasterxml.jackson.core.JsonProcessingException e) { throw new IllegalArgumentException(e); }
        }
    }
    public InventoryReconcileProvider() { super("reconcileInventoryV1"); }

    private boolean valid(Map<String, Object> row) {
        return nonempty(row.get("recordId")) && nonempty(row.get("unit")) && nonempty(row.get("observedAt"))
            && integer(row.get("quantity"), 1_000_000);
    }
    private Map<Key, List<Map<String, Object>>> index(List<Map<String, Object>> rows) {
        Map<Key, List<Map<String, Object>>> result = new HashMap<>();
        for (var row : rows) result.computeIfAbsent(new Key((String) row.get("lineId"), (String) row.get("sku")),
            k -> new ArrayList<>()).add(row);
        return result;
    }

    @Override
    protected Map<String, Object> calculate(Map<String, Object> req, Map<String, Object> payload) {
        var es = rows(payload, "erp", req, "documentId", "warehouseId");
        var ws = rows(payload, "wms", req, "documentId", "warehouseId");
        boolean keyError = concat(es, ws).stream().anyMatch(x -> !nonempty(x.get("lineId")) || !nonempty(x.get("sku")));
        List<Map<String, Object>> items = new ArrayList<>();
        if (!keyError) {
            var ei = index(es); var wi = index(ws);
            Set<Key> keys = new TreeSet<>(Comparator.comparing(Key::sortKey));
            keys.addAll(ei.keySet()); keys.addAll(wi.keySet());
            for (Key key : keys) {
                var e = ei.getOrDefault(key, List.of()); var w = wi.getOrDefault(key, List.of());
                boolean invalid = concat(e, w).stream().anyMatch(x -> !valid(x));
                boolean ambiguous = e.size() > 1 || w.size() > 1;
                boolean stale = concat(e, w).stream().anyMatch(x -> !Objects.equals(x.get("observedAt"), req.get("asOf")));
                boolean both = e.size() == 1 && w.size() == 1;
                boolean mismatch = both && !Objects.equals(e.getFirst().get("unit"), w.getFirst().get("unit"));
                String reason = invalid ? "INVALID_UPSTREAM_DATA" : ambiguous ? "DUPLICATE_RECORD"
                    : stale ? "STALE_DATA" : mismatch ? "UNIT_MISMATCH" : e.isEmpty() ? "MISSING_ERP"
                    : w.isEmpty() ? "MISSING_WMS" : number(e.getFirst().get("quantity")) != number(w.getFirst().get("quantity"))
                        ? "QUANTITY_DIFFERENCE" : "MATCHED";
                items.add(map("lineId", key.lineId(), "sku", key.sku(), "status",
                    invalid || ambiguous || stale || mismatch ? "UNKNOWN" : reason, "reason", reason,
                    "erpQuantity", !invalid && e.size() == 1 ? number(e.getFirst().get("quantity")) : null,
                    "wmsQuantity", !invalid && w.size() == 1 ? number(w.getFirst().get("quantity")) : null,
                    "difference", both && !invalid && !ambiguous && !stale && !mismatch
                        ? number(e.getFirst().get("quantity")) - number(w.getFirst().get("quantity")) : null,
                    "unit", both && !invalid && !mismatch ? e.getFirst().get("unit") : null,
                    "evidence", concat(evidence(e, "ERP", false), evidence(w, "WMS", false))));
            }
        }
        boolean unknown = items.isEmpty() || items.stream().anyMatch(x -> "UNKNOWN".equals(x.get("status")));
        var reasons = new TreeSet<String>();
        items.forEach(x -> reasons.add((String) x.get("reason")));
        var result = base(req, "documentId", "warehouseId");
        result.putAll(map("status", unknown ? "UNKNOWN" : items.stream().anyMatch(x -> !"MATCHED".equals(x.get("status")))
            ? "DIFFERENCES" : "MATCHED", "reasons", keyError ? List.of("INVALID_UPSTREAM_DATA")
            : items.isEmpty() ? List.of("NO_RECORDS") : new ArrayList<>(reasons), "items", items));
        return result;
    }

    @Override
    protected Map<String, Object> error(Map<String, Object> req, String reason) {
        var result = base(req, "documentId", "warehouseId");
        result.putAll(map("status", "UNKNOWN", "reasons", List.of(reason), "items", List.of()));
        return result;
    }
}
