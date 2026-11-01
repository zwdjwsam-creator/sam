# P4 owner approval and whole-call failure semantics

The owner approved the P4 offline review, while explicitly keeping backtest/research activation, CURRENT/release and orders closed. No native P4 task is issued.

The actual p4_consumer.py implementation validates stock source fields and required state before exposing rows. Null/nonfinite prices or states, missing required fields or invalid statuses raise Rejected and fail the ENTIRE call; there is no bad-row drop-and-continue branch and no returned partial prefix. Even a stock row later excluded by unresolved/time filtering is validated during the source load. Normal availability filtering of a sound but not-yet-visible/UNRESOLVED row is separate from data-quality error handling.

missing_price is currently always false on successful public output because admitted source prices have passed non-null/finite checks. It is not a mechanism to return missing-priced rows. An internal row with missing_price=true is rejected as STATE_TAMPER. Changing this behavior would need an explicit new contract; no behavior/policy/source bytes were changed by this explanation.

The new execution-model draft explicitly includes held-position valuation during suspension, independently of fill eligibility. A paused position is not dropped; proposed stale-mark carry is valuation-only, and a missing previous valid visible mark blocks complete NAV. This is a proposed owner-approval term, not an activated forward-fill or fill policy.
