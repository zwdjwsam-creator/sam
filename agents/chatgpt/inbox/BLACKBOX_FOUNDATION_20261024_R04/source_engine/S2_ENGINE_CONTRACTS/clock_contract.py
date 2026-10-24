# -*- coding: utf-8 -*-
"""Clock contract — logical_time advance policy and lookahead guard."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, TypedDict

CONTRACT_ID = "ClockContract"
CONTRACT_VERSION = "1.0.0"

TimeAdvancePolicy = Literal["bar_close", "tick", "event_driven"]
SessionPhase = Literal[
    "pre_open_call_auction",
    "continuous_auction_am",
    "lunch_break",
    "continuous_auction_pm",
    "close_call_auction",
    "closed",
]


class ContractMeta(TypedDict):
    contract_id: str
    version: str
    released_at: str
    deprecated_at: Optional[str]
    breaking_change: bool
    migration_note: Optional[str]


class ClockContract(TypedDict):
    meta: ContractMeta
    logical_time: str
    wall_clock_time: str
    time_zone: str
    trading_date: str
    session_id: str
    session_phase: SessionPhase
    time_advance_policy: TimeAdvancePolicy
    bar_close_policy: str
    tick_policy: str
    event_driven_policy: str
    lookahead_guard: bool
    deterministic_seed: int
    replay_sequence: int
    replay_hash: str
    calendar_contract_id: str
    session_contract_id: str


@dataclass(frozen=True)
class ClockContractConstants:
    contract_id: str = CONTRACT_ID
    contract_version: str = CONTRACT_VERSION
    lunch_break_handle_bar_forbidden: bool = True
    lookahead_guard: bool = True


__all__ = [
    "CONTRACT_ID",
    "CONTRACT_VERSION",
    "TimeAdvancePolicy",
    "SessionPhase",
    "ContractMeta",
    "ClockContract",
    "ClockContractConstants",
]
