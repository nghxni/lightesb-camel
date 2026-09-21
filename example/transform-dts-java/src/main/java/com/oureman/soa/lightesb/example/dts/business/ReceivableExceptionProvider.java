package com.oureman.soa.lightesb.example.dts.business;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.*;

/** Synthetic receivable checks using exact integer minor units; never allocates receipts. */
public final class ReceivableExceptionProvider extends BusinessTransform {
    public ReceivableExceptionProvider() { super("checkReceivableExceptionsV1"); }
    private boolean currency(Object value) { return "CNY".equals(value) || "USD".equals(value); }
    private boolean receiptValid(Map<String, Object> row) {
        return fields(row, "recordId", "invoiceId", "amountMinor", "currency", "observedAt")
            && text(row.get("recordId")) && (row.get("invoiceId") == null || text(row.get("invoiceId")))
            && integer(row.get("amountMinor"), 1_000_000_000) && currency(row.get("currency")) && text(row.get("observedAt"));
    }

    @Override
    protected Map<String, Object> calculate(Map<String, Object> req, Map<String, Object> payload) {
        var es = rows(payload, "erp", req, "customerId");
        var bs = rows(payload, "bank", req, "customerId");
        var cs = rows(payload, "contract", req, "customerId");
        boolean bankInvalid = bs.stream().anyMatch(x -> !receiptValid(x));
        boolean keyError = es.stream().anyMatch(x -> !text(x.get("invoiceId")) || !text(x.get("contractId")))
            || cs.stream().anyMatch(x -> !text(x.get("contractId")));
        boolean duplicateReceipt = duplicate(bs), duplicateErp = duplicate(es), duplicateContract = duplicate(cs);
        Set<Object> ids = new HashSet<>();
        es.stream().filter(x -> text(x.get("invoiceId"))).forEach(x -> ids.add(x.get("invoiceId")));
        var unallocated = bs.stream().filter(x -> x.get("invoiceId") == null || !ids.contains(x.get("invoiceId"))).toList();
        boolean staleUnallocated = unallocated.stream().anyMatch(x -> !Objects.equals(x.get("observedAt"), req.get("asOf")));
        List<Map<String, Object>> items = new ArrayList<>();
        Set<String> reasons = new TreeSet<>();
        if (!keyError) for (var e : es) {
            var payments = bs.stream().filter(x -> Objects.equals(x.get("invoiceId"), e.get("invoiceId"))).toList();
            var terms = cs.stream().filter(x -> Objects.equals(x.get("contractId"), e.get("contractId"))).toList();
            boolean unique = es.stream().filter(x -> Objects.equals(x.get("invoiceId"), e.get("invoiceId"))).count() == 1;
            boolean valid = !bankInvalid && text(e.get("recordId")) && text(e.get("observedAt"))
                && integer(e.get("amountMinor"), 1_000_000_000) && currency(e.get("currency"));
            boolean termValid = terms.size() == 1 && text(terms.getFirst().get("recordId"))
                && text(terms.getFirst().get("observedAt")) && date(terms.getFirst().get("dueDate"));
            String missing = !valid || (terms.size() == 1 && !termValid) ? "INVALID_UPSTREAM_DATA"
                : !unique || duplicateReceipt || duplicateErp || duplicateContract || terms.size() > 1 ? "DUPLICATE_RECORD"
                : terms.isEmpty() ? "MISSING_CONTRACT"
                : payments.stream().anyMatch(x -> !Objects.equals(x.get("currency"), e.get("currency"))) ? "CURRENCY_MISMATCH"
                : concat(List.of(e), payments, terms).stream().anyMatch(x -> !Objects.equals(x.get("observedAt"), req.get("asOf"))) ? "STALE_DATA" : null;
            Long received = null, balance = null, excess = null, overdue = null;
            if (missing == null) {
                received = 0L;
                for (var payment : payments) received = Math.addExact(received, number(payment.get("amountMinor")));
                long amount = number(e.get("amountMinor"));
                balance = Math.max(0L, amount - received);
                excess = Math.max(0L, received - amount);
                overdue = balance == 0 ? 0L : Math.max(0L, ChronoUnit.DAYS.between(
                    LocalDate.parse((String) terms.getFirst().get("dueDate")), LocalDate.parse(req.get("asOf").toString().substring(0, 10))));
            }
            String status = missing != null ? "UNKNOWN" : excess > 0 ? "OVERPAID" : balance == 0 ? "SETTLED"
                : received > 0 ? "PARTIAL" : overdue > 0 ? "OVERDUE" : "NOT_DUE";
            List<String> itemReasons = new ArrayList<>(List.of(missing != null ? missing : status));
            if ("PARTIAL".equals(status) && overdue > 0) itemReasons.add("OVERDUE");
            reasons.addAll(itemReasons);
            items.add(map("invoiceId", e.get("invoiceId"), "currency", valid ? e.get("currency") : null,
                "amountMinor", valid ? number(e.get("amountMinor")) : null, "receivedMinor", received,
                "outstandingMinor", balance, "overpaidMinor", excess, "overdueDays", overdue,
                "dueDate", termValid ? terms.getFirst().get("dueDate") : null, "status", status, "reasons", itemReasons,
                "evidence", concat(evidence(List.of(e), "ERP", true), evidence(payments, "TREASURY", true), evidence(terms, "CONTRACT", true))));
        }
        if (!unallocated.isEmpty()) reasons.add("UNALLOCATED_RECEIPT");
        if (keyError) reasons.add("INVALID_ASSOCIATION_KEY"); else if (items.isEmpty()) reasons.add("NO_RECEIVABLES");
        if (staleUnallocated) reasons.add("STALE_DATA");
        if (bankInvalid) reasons.add("INVALID_UPSTREAM_DATA");
        if (duplicateReceipt || duplicateErp || duplicateContract) reasons.add("DUPLICATE_RECORD");
        boolean unknown = keyError || bankInvalid || staleUnallocated || items.isEmpty()
            || items.stream().anyMatch(x -> "UNKNOWN".equals(x.get("status")));
        boolean attention = !unallocated.isEmpty() || items.stream().anyMatch(x -> !Set.of("SETTLED", "NOT_DUE").contains(x.get("status")));
        var result = base(req, "customerId");
        result.putAll(map("moneyUnit", "minor-unit", "status", unknown ? "UNKNOWN" : attention ? "ATTENTION" : "NORMAL",
            "reasons", new ArrayList<>(reasons), "items", items,
            "evidence", concat(evidence(es, "ERP", true), evidence(bs, "TREASURY", true), evidence(cs, "CONTRACT", true)),
            "unallocatedReceipts", unallocated.stream().filter(this::receiptValid)
                .map(x -> map("sourceSystem", "TREASURY", "recordId", x.get("recordId"), "observedAt", x.get("observedAt"),
                    "amountMinor", number(x.get("amountMinor")), "currency", x.get("currency"))).toList()));
        return result;
    }

    @Override
    protected Map<String, Object> error(Map<String, Object> req, String reason) {
        var result = base(req, "customerId");
        result.putAll(map("moneyUnit", "minor-unit", "status", "UNKNOWN", "reasons", List.of(reason),
            "items", List.of(), "evidence", List.of(), "unallocatedReceipts", List.of()));
        return result;
    }
}
