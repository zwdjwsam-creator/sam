# -*- coding: utf-8 -*-
"""Data visibility contract — STRUCTURE_ONLY with lookahead guard."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional, TypedDict

CONTRACT_ID = "DataVisibilityContract"
CONTRACT_VERSION = "1.0.0"

ContractStatus = Literal["STRUCTURE_ONLY"]
AccessMode = Literal["read_snapshot", "read_registry", "query_index"]


class ContractMeta(TypedDict):
    contract_id: str
    version: str
    released_at: str
    deprecated_at: Optional[str]
    breaking_change: bool
    migration_note: Optional[str]


class DataVisibilityContract(TypedDict):
    meta: ContractMeta
    status: ContractStatus
    data_snapshot_id: str
    data_domain: str
    logical_time: str
    visible_until: str
    lookahead_forbidden: bool
    lookahead_guard: bool
    allowed_access_modes: List[AccessMode]
    forbidden_access_modes: List[str]
    source_manifest_path: str
    source_registry_path: str
    parquet_only_after_cleaning: bool
    csv_pass_artifact_forbidden: bool
    e_drive_scatter_scan_forbidden: bool
    blackbox_code_format_required: bool


@dataclass(frozen=True)
class DataVisibilityContractConstants:
    contract_id: str = CONTRACT_ID
    contract_version: str = CONTRACT_VERSION
    status: ContractStatus = "STRUCTURE_ONLY"
    lookahead_guard: bool = True


__all__ = [
    "CONTRACT_ID",
    "CONTRACT_VERSION",
    "ContractStatus",
    "AccessMode",
    "ContractMeta",
    "DataVisibilityContract",
    "DataVisibilityContractConstants",
]
