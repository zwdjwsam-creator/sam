# BLACKBOX Backtest-Only Scope (D Drive Lab Fork)

## Scope

- **Fork location**: `D:\backtest_lab\02_blackbox_jq_compat_engine\blackbox_jq_engine`
- **Scope name**: `BLACKBOX_JQ_COMPAT_ENGINE_V0`
- **Engine mode**: `backtest_only`
- **Purpose**: D drive backtest lab only — not connected to E:\BLACKBOX

## Allowed (V0 active planning)

- A-share, ETF, money market fund
- HK Connect / HK Connect ETF (reserved asset types)
- Day and minute backtest only
- JoinQuant-style API: `run_daily` / `run_weekly` / `run_monthly`
- Orders: `order` / `order_value` / `order_target` / `order_target_value`
- Models: `context` / `portfolio` / `position` / `order` / `trade`
- Bar matching, T+1 `closeable_amount`, fees / tax / slippage
- Ledger outputs: orders / trades / positions / portfolio / diff report

## Inactive (retained, not active in V0)

- QMT data interfaces (`miniqmt`, `remote_qmt`) — **inactive only**
- External DataProvider abstraction (JQData, Tushare, etc.)
- Report / visualization CLI
- CLI backtest entry (kept, not run in guard-patch phase)

## Disabled (must not run)

- Tick backtest / five-level book matching
- Live trading, broker, QMT order placement
- QMT server / remote server
- Futures, options, margin trading
- Auto-trading / real account operations
- Live examples and runtime probes

## Guard module

Configuration and guards live in:

`bullet_trade/blackbox_scope.py`

Blocked CLI commands: `live`, `server`

## Hard boundaries

- Do **not** write to E:\BLACKBOX
- Do **not** connect real brokerage accounts
- Do **not** run live / QMT / broker / tick examples in this fork without removing guards
