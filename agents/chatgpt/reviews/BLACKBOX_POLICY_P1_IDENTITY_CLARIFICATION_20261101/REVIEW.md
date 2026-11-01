# P1 policy identity, fixture task and real-data activation are separate

Execution host for any later authorized native work: ZHANGWEI.
This is a desk review and ledger clarification. No native task, supplier call, Cleaning run, backtest, CURRENT/release change or order is authorized or issued.

## Verified policy approval

The owner already stated P1签字 and subsequently requested HUB publication. APPROVAL.json binds policy BLACKBOX_DAILY_AVAILABILITY_PRESUMPTION_P1, revision R2_STOCK_ONLY_20261101, status OWNER_APPROVED_POLICY_ONLY. GPT independently recomputed POLICY_BODY.txt's exact UTF-8 SHA256:
31dee3a67f7674db25b0ba4d56c169c941e28f857b8656454b6006401938f884
This matches both approval and p1_layer.py's pin. No new signature or policy change is requested.

The actual signed revision explicitly contains: stock/JQ/RAW_NONE-only scope; ETF/index excluded; factor not exposed; next strictly frozen-calendar session09:00+08:00 as a modeling presumption;2026-10-27 UNRESOLVED; no pre-09-24 calendar extrapolation; no reliance on lookahead_risk=false; and no claim of actual historical availability. Its corrected examples include10-26 to10-27 and10-27 toUNRESOLVED. The erroneous old example10-27 to10-28 is not in this approved body.

POLICY_P1 and TASK_P1 are ledger/display labels only, not replacement policy IDs, source aliases or newly authorized task classes:
- POLICY_P1: the above approved modeling policy, not real historical PIT evidence.
- TASK_P1: BLACKBOX_P1_NATIVE_TEST_20261101, accepted/closed for20 native fixtures and a date-only plan. No replay.
- REAL_DATA_P1_CONSUMER: not implemented/accepted/activated. P3 candidate acceptance did not activate it.

## Exact field binding

Fourteen source fields: time,code,open,high,low,close,volume,money,paused,high_limit,low_limit,avg,pre_close,factor.
The dictionary has twelve required names: symbol,trade_date,open,high,low,close,volume,money,factor,high_limit,low_limit,paused.
time/code map explicitly to trade_date/symbol. The two supplemental fields are avg and pre_close, already explicitly listed by the signed policy and SEMANTIC_BINDINGS. They are not guessed. Numeric units/formal target types remain unbound; source retention does not grant all fields consumer eligibility. Excluding factor from P1 never deletes it from native RAW_NONE evidence or rewrites dictionary required_fields.

## Actual code gap and next implementation requirements

p1_layer.py is the previously tested fixture implementation. Its FIELDS currently includes avg/pre_close, and select() filters presumed availability and requested fields but is not a trade-execution guard. Fixture acceptance does not certify supplemental-field unit/null bindings, paused=1 rejection at execution, tradability or real-candidate integrity. Do not activate this code unchanged against real backtests. Correct these gaps in the separately reviewed consumer; do not reinterpret the existing20 tests as covering them.

The next GPT-owned offline implementation must bind the accepted P3 candidate generation/manifest/row provenance and the exact policy/calendar digests; admit only the approved stock universe; deny factor; keep avg/pre_close closed until their independent semantic/null/unit binding is supplied; reject unresolved date exposure; enforce timezone and decision-time filtering; preserve observation state and ensure paused rows cannot execute. Known status fields, volume, money, applicable limits and missing-price states must be mandatory integrity inputs, not optional fields a caller can omit to bypass execution restrictions. paused=0 alone never proves a tradable quote.

Daily availability, valuation and fills are separate contracts. No default valuation/fill policy is invented here. Execution-day price/limit/liquidity rules require a reviewed execution model: a prior data day's limits cannot silently substitute for execution-day limits, and a limit-price field alone does not prove whether an order could fill.

Meaningful later offline controls must use pandas3.0.3/pyarrow24.0.0/numpy2.5.4, the actual P3 stock values and row lineage, the192 paused observations, factor/product/unresolved-date denial and the exact600621 quarantine. Other products remain retained in the candidate but denied by the stock-only P1 interface. The192 count across all products must not be assumed to mean192 stock rows; measure the actual product split before constructing stock tests. No local fixture/candidate rerun is needed to make this ledger clarification.

## Arithmetic correction in the owner's supplied review

Admitted stock rows are88811, not88812. The latter is the physical stock input before its one quarantine:88812=88811+1. ETF28530 and index119 complete the117460 admitted total. Daily listing/delisting causes must not be inferred merely from non-divisibility by17; existing exact per-date/key measurements control. P3 remains closed. No original receipt or prior policy was rewritten by this clarification.

Reviewed source blobs are recorded in the accompanying state update. No executable command is issued.
