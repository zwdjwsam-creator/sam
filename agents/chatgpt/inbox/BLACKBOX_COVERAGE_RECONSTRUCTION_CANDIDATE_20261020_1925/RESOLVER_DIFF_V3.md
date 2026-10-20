# Resolver candidate diff (V3) — minimal

Base: V2 candidate copy of `blackbox_data_access_resolver_r1.py` (ROOT pinned to `E:\BLACKBOX`).

Only section **#11 Coverage contract** changed:

1. Import `SUPPORTED_DATE_PRODUCTS`
2. `product_date_coverage(Path(product_path), normalized)`
3. License gate before any window/min-max logic:
   - unsupported / extract!=OK / errors / UNKNOWN_STOP / EMPTY / INCREMENTAL_PATCH → `coverage_ready=False`
4. No-window unsupported default `True` **removed** → `historical_ready` only for supported+extract_ok
5. Generic window: day-set vs calendar when dates present; else false (no min/max license for unsupported)
6. Record `_coverage_extract_status` / `_coverage_supported` on currents
7. except path also forces `historical_ready=False`

No other resolver behavior paths modified.
