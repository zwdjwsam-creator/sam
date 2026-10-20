# -*- coding: utf-8 -*-
"""
BLACKBOX Deterministic Data Access Resolver R1.

rule_id: BLACKBOX_DETERMINISTIC_DATA_ACCESS_RESOLVER_GATE_R1
status: ACTIVE

Purpose: 任何 Agent/模型只需执行此脚本即可得到当前正式 Cache 的产品位置/Reader/PIT 合约。
模型不得自行猜路径、模糊搜索、或使用聊天记忆中的旧 release。

Usage:
  python blackbox_data_access_resolver_r1.py --dataset "SW_L2" --asof "2026-08-11"
  python blackbox_data_access_resolver_r1.py --dataset "FUND_MF_DAILY_PROFIT"
  python blackbox_data_access_resolver_r1.py --dataset "FINANCE_BALANCE_SHEET" --scope "PARENT"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── mandatory pointers (read from disk, never hardcoded) ──
HAND_PATH = ROOT / "HAND.txt"
CACHE_CURRENT_PTR = ROOT / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
CLEANING_CURRENT_PTR = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
CATALOG_CSV = ROOT / "数据" / "回测缓存" / "registry" / "CACHE_PRODUCT_CATALOG.csv"
MANIFEST_JSON = ROOT / "数据" / "回测缓存" / "registry" / "CACHE_MANIFEST_REGISTRY.json"
LEDGER_JSON = ROOT / "运行" / "BLACKBOX_JQ_ACCESSIBLE_DATASET_LEDGER_CURRENT.json"
R19_PROVENANCE = ROOT / "运行" / "BLACKBOX_CLEANING_RELEASE_PROVENANCE_R19_POST_SEAL_MUTATION.json"
INDEX_PATH = ROOT / "运行" / "BLACKBOX_DATA_ACCESS_INDEX_CURRENT.json"
SIDECAR_PRODUCTS = ROOT / "运行" / "BLACKBOX_SIDECAR_CACHE_PRODUCTS_CURRENT.json"
CBOND_CACHE_CURRENT_PTR = ROOT / "数据" / "回测缓存" / "可转债指针" / "CURRENT_CBOND_CACHE_RELEASE.json"
CBOND_PRODUCT_PREFIX = "TUSHARE_CBOND_"
EXTERNAL_EVIDENCE_RESOLVER_PTR = ROOT / "运行" / "BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json"

# ── known ambiguous scopes ──
AMBIGUOUS_DATASETS = {
    "FINANCE_BALANCE_SHEET": {
        "scope_required": True,
        "options": {"CONSOLIDATED": "JQ20_FINANCE_BALANCE_SHEET_PIT_R1",
                    "PARENT": "JQ20_FINANCE_BALANCE_SHEET_PARENT_PIT_R1"},
    },
    "FINANCE_CASHFLOW_STATEMENT": {
        "scope_required": True,
        "options": {"CONSOLIDATED": "JQ20_FINANCE_CASHFLOW_STATEMENT_PIT_R1",
                    "PARENT": "JQ20_FINANCE_CASHFLOW_STATEMENT_PARENT_PIT_R1"},
    },
    "FINANCE_INCOME_STATEMENT": {
        "scope_required": True,
        "options": {"CONSOLIDATED": "JQ20_FINANCE_INCOME_STATEMENT_PIT_R1",
                    "PARENT": "JQ20_FINANCE_INCOME_STATEMENT_PARENT_PIT_R1"},
    },
}

# ── explicit aliases (no fuzzy matching) ──
ALIASES = {
    "sw_l1": "SW_L1_MEMBERSHIP_PIT_R1",
    "SW_L1": "SW_L1_MEMBERSHIP_PIT_R1",
    "申万一级行业": "SW_L1_MEMBERSHIP_PIT_R1",
    "sw_l2": "SW_L2_MEMBERSHIP_PIT_R1",
    "SW_L2": "SW_L2_MEMBERSHIP_PIT_R1",
    "申万二级行业": "SW_L2_MEMBERSHIP_PIT_R1",
    "sw_l3": "SW_L3_MEMBERSHIP_PIT_R1",
    "SW_L3": "SW_L3_MEMBERSHIP_PIT_R1",
    "申万三级行业": "SW_L3_MEMBERSHIP_PIT_R1",
    "fi": "FINANCIAL_INDICATOR_PIT_R1",
    "FI": "FINANCIAL_INDICATOR_PIT_R1",
    "financial_indicator": "FINANCIAL_INDICATOR_PIT_R1",
    "财务指标": "FINANCIAL_INDICATOR_PIT_R1",
    "valuation": "VALUATION_PIT_R1",
    "VALUATION": "VALUATION_PIT_R1",
    "估值": "VALUATION_PIT_R1",
    "stock_daily": "STOCK_DAILY_PIT_R1",
    "STOCK_DAILY": "STOCK_DAILY_PIT_R1",
    "股票日线": "STOCK_DAILY_PIT_R1",
    "stock_daily_raw": "STOCK_DAILY_RAW_PIT_R1",
    "STOCK_DAILY_RAW": "STOCK_DAILY_RAW_PIT_R1",
    "STOCK_DAILY_RAW_PIT_R1": "STOCK_DAILY_RAW_PIT_R1",
    "股票日线RAW": "STOCK_DAILY_RAW_PIT_R1",
    "stock_factor": "STOCK_FACTOR_DAILY_R1",
    "stock_price": "STOCK_DAILY_PIT_R1",
    "price": "STOCK_DAILY_PIT_R1",
    "csi2000": "INDEX_DAILY_R1",
    "CSI2000": "INDEX_DAILY_R1",
    "中证2000": "INDEX_DAILY_R1",
    "399303": "INDEX_DAILY_R1",
    "etf_daily": "ETF_DAILY_PIT_R1",
    "ETF_DAILY": "ETF_DAILY_PIT_R1",
    "ETF_DAILY_PIT_R1": "ETF_DAILY_PIT_R1",
    "etf_1m": "ETF_MINUTE_1M_R1",
    "ETF_1M": "ETF_MINUTE_1M_R1",
    "ETF_MINUTE_1M": "ETF_MINUTE_1M_R1",
    "ETF_MINUTE_1M_R1": "ETF_MINUTE_1M_R1",
    "etf_minute": "ETF_MINUTE_1M_R1",
    # A-share stock 1m — Cleaning CURRENT plane (unified_market_data_plane product_id)
    "stock_1m": "STOCK_MINUTE_1M_R1",
    "STOCK_1M": "STOCK_MINUTE_1M_R1",
    "STOCK_MINUTE_1M": "STOCK_MINUTE_1M_R1",
    "STOCK_MINUTE_1M_R1": "STOCK_MINUTE_1M_R1",
    "A股_1m": "STOCK_MINUTE_1M_R1",
    "A股_stock_1m": "STOCK_MINUTE_1M_R1",
    "分钟1m": "STOCK_MINUTE_1M_R1",
    "1m": "STOCK_MINUTE_1M_R1",
    "etf_factor": "ETF_FACTOR_DAILY_R1",
    "index_daily": "INDEX_DAILY_R1",
    "index_factor": "INDEX_FACTOR_DAILY_R1",
    "index_constituent": "INDEX_CONSTITUENT_PIT_R1",
    "index_weight": "INDEX_WEIGHT_PIT_R1",
    "INDEX_WEIGHT": "INDEX_WEIGHT_PIT_R1",
    "INDEX_WEIGHT_PIT_R1": "INDEX_WEIGHT_PIT_R1",
    "get_index_weights": "INDEX_WEIGHT_PIT_R1",
    "etf_tracking_index": "ETF_TRACKING_INDEX_MAP_R1",
    "tracking_index": "ETF_TRACKING_INDEX_MAP_R1",
    "ETF_TRACKING_INDEX_MAP_R1": "ETF_TRACKING_INDEX_MAP_R1",
    "fund_portfolio_stock": "FUND_PORTFOLIO_STOCK_PIT_R1",
    "FUND_PORTFOLIO_STOCK": "FUND_PORTFOLIO_STOCK_PIT_R1",
    "FUND_PORTFOLIO_STOCK_PIT_R1": "FUND_PORTFOLIO_STOCK_PIT_R1",
    "market_structure": "MARKET_STRUCTURE_DAILY_R1",
    "market_universe": "MARKET_UNIVERSE_PIT_R1",
    "tradeability": "STOCK_TRADEABILITY_PIT_R1",
    "可交易状态": "STOCK_TRADEABILITY_PIT_R1",
    "billboard": "BILLBOARD_DAILY_PIT_R1",
    "BILLBOARD": "BILLBOARD_DAILY_PIT_R1",
    "龙虎榜": "BILLBOARD_DAILY_PIT_R1",
    "get_billboard_list": "BILLBOARD_DAILY_PIT_R1",
    "fund_mf_daily_profit": "JQ20_FUND_MF_DAILY_PROFIT_PIT_R1",
    "FUND_MF_DAILY_PROFIT": "JQ20_FUND_MF_DAILY_PROFIT_PIT_R1",
    "基金货币收益": "JQ20_FUND_MF_DAILY_PROFIT_PIT_R1",
    "fund_dividend": "JQ20_FUND_DIVIDEND_EVENT_PIT_R1",
    "top10": "CORP_SHAREHOLDER_TOP10_PIT_R1",
    "十大股东": "CORP_SHAREHOLDER_TOP10_PIT_R1",
    "floating_top10": "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1",
    "十大流通股东": "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1",
    "xr_xd": "CORP_XR_XD_EVENT_PIT_R1",
    "除权除息": "CORP_XR_XD_EVENT_PIT_R1",
    "corp_xr_xd": "CORP_XR_XD_EVENT_PIT_R1",
    "adjust_factor": "ADJUST_FACTOR_PIT_R1",
    "ADJUST_FACTOR": "ADJUST_FACTOR_PIT_R1",
    "复权因子": "ADJUST_FACTOR_PIT_R1",
    "pre_pit_factor": "ADJUST_FACTOR_PIT_R1",
    "stk_performance_letters": "JQ20_STK_PERFORMANCE_LETTERS_PIT_R1",
    "业绩快报": "JQ20_STK_PERFORMANCE_LETTERS_PIT_R1",
    "stk_report_disclosure": "JQ20_STK_REPORT_DISCLOSURE_PIT_R1",
    "财报披露": "JQ20_STK_REPORT_DISCLOSURE_PIT_R1",
    "ah_price": "JQ20_STK_AH_PRICE_COMP_PIT_R1",
    "employee_info": "JQ20_STK_EMPLOYEE_INFO_PIT_R1",
    "stk_list": "JQ20_STK_LIST_REFERENCE_PIT_R1",
    "股票列表": "JQ20_STK_LIST_REFERENCE_PIT_R1",
    "name_history": "JQ20_STK_NAME_HISTORY_PIT_R1",
    "exchange_trade_info": "JQ20_STK_EXCHANGE_TRADE_INFO_PIT_R1",
    "el_const_change": "JQ20_STK_EL_CONST_CHANGE_EVENT_PIT_R1",
    "el_top_activate": "JQ20_STK_EL_TOP_ACTIVATE_PIT_R1",
    "exchange_calendar": "JQ20_STK_EXCHANGE_LINK_CALENDAR_R1",
    "shareholders_change": "JQ20_STK_SHAREHOLDERS_SHARE_CHANGE_EVENT_PIT_R1",
    "fund_fin_indicator": "JQ20_FUND_FIN_INDICATOR_PIT_R1",
    "finance_balance_sheet": "FINANCE_BALANCE_SHEET",
    "资产负债表": "FINANCE_BALANCE_SHEET",
    "finance_cashflow": "FINANCE_CASHFLOW_STATEMENT",
    "现金流量表": "FINANCE_CASHFLOW_STATEMENT",
    "finance_income": "FINANCE_INCOME_STATEMENT",
    "利润表": "FINANCE_INCOME_STATEMENT",
    "CBOND": "TUSHARE_CBOND_DAILY_MARKET_R1",
    "可转债": "TUSHARE_CBOND_DAILY_MARKET_R1",
    "TUSHARE_CBOND": "TUSHARE_CBOND_DAILY_MARKET_R1",
    "CONVERTIBLE_BOND": "TUSHARE_CBOND_DAILY_MARKET_R1",
    "CONBOND": "TUSHARE_CBOND_DAILY_MARKET_R1",
    "TUSHARE_CBOND_BASIC_R1": "TUSHARE_CBOND_BASIC_R1",
    "TUSHARE_CBOND_DAILY_MARKET_R1": "TUSHARE_CBOND_DAILY_MARKET_R1",
    "TUSHARE_CBOND_STOCK_BRIDGE_R1": "TUSHARE_CBOND_STOCK_BRIDGE_R1",
    "TUSHARE_CBOND_RATING_PIT_R1": "TUSHARE_CBOND_RATING_PIT_R1",
    "TUSHARE_CBOND_CALL_PIT_R1": "TUSHARE_CBOND_CALL_PIT_R1",
    "TUSHARE_CBOND_REMAIN_SIZE_PIT_R1": "TUSHARE_CBOND_REMAIN_SIZE_PIT_R1",
    "TUSHARE_CBOND_TOP10_HOLDERS_R1": "TUSHARE_CBOND_TOP10_HOLDERS_R1",
    "TUSHARE_CBOND_RATING_R1": "TUSHARE_CBOND_RATING_R1",
    "COMPANY_EVIDENCE_INDEX": "COMPANY_EVIDENCE_INDEX_R1",
    "COMPANY_EVIDENCE_INDEX_R1": "COMPANY_EVIDENCE_INDEX_R1",
    "公司证据索引": "COMPANY_EVIDENCE_INDEX_R1",
    "EXTERNAL_EVIDENCE": "COMPANY_EVIDENCE_INDEX_R1",
    "JQ_FINANCIAL_INDICATOR_PIT_R1": "FINANCIAL_INDICATOR_PIT_R1",
    "JQ_FUND_NAV_PIT_R1": "FUND_NAV_PIT_R1",
}

# ── PIT policies (from HAND R2/CACHE product definitions) ──
PIT_POLICIES = {
    "SW_L1_MEMBERSHIP_PIT_R1": {"pit_policy": "ASOF_SNAPSHOT", "asof_behavior": "PIT_AT_DATE"},
    "SW_L2_MEMBERSHIP_PIT_R1": {"pit_policy": "ASOF_SNAPSHOT", "asof_behavior": "PIT_AT_DATE"},
    "SW_L3_MEMBERSHIP_PIT_R1": {"pit_policy": "ASOF_SNAPSHOT", "asof_behavior": "PIT_AT_DATE"},
    "FINANCIAL_INDICATOR_PIT_R1": {"pit_policy": "PUBDATE_AVAILABLE_FROM", "asof_behavior": "KNOWN_AT_PUBDATE"},
    "CORP_XR_XD_EVENT_PIT_R1": {"pit_policy": "JQ_FINANCE_DAILY_24H_NEXT_TRADE_DAY_R1", "asof_behavior": "PIT_VALID_FROM"},
    "ADJUST_FACTOR_PIT_R1": {"pit_policy": "ASOF_EFFECTIVE_AT_T", "asof_behavior": "PIT_AT_SIGNAL_DATE_NO_FUTURE_REWRITE"},
    "CORP_SHAREHOLDER_TOP10_PIT_R1": {"pit_policy": "JQ_FINANCE_DAILY_24H_NEXT_TRADE_DAY_R1", "asof_behavior": "PIT_VALID_FROM"},
    "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1": {"pit_policy": "JQ_FINANCE_DAILY_24H_NEXT_TRADE_DAY_R1", "asof_behavior": "PIT_VALID_FROM"},
    "BILLBOARD_DAILY_PIT_R1": {"pit_policy": "BILLBOARD_DAY_EOD_R1", "asof_behavior": "KNOWN_AT_DAY_EOD"},
    "STOCK_DAILY_PIT_R1": {"pit_policy": "EOD_SAME_DAY", "asof_behavior": "PIT_AT_SIGNAL_DATE"},
    "STOCK_DAILY_RAW_PIT_R1": {"pit_policy": "EOD_SAME_DAY", "asof_behavior": "PIT_AT_SIGNAL_DATE"},
    "STOCK_FACTOR_DAILY_R1": {"pit_policy": "EOD_SAME_DAY", "asof_behavior": "PIT_AT_SIGNAL_DATE"},
    "ETF_DAILY_PIT_R1": {"pit_policy": "EOD_SAME_DAY", "asof_behavior": "PIT_AT_SIGNAL_DATE"},
    "ETF_MINUTE_1M_R1": {"pit_policy": "BAR_END_ASOF", "asof_behavior": "BAR_AVAILABLE_AT_LE_REQUEST_TIME"},
    "STOCK_MINUTE_1M_R1": {"pit_policy": "BAR_END_ASOF", "asof_behavior": "BAR_AVAILABLE_AT_LE_REQUEST_TIME"},
    "INDEX_DAILY_R1": {"pit_policy": "EOD_SAME_DAY", "asof_behavior": "PIT_AT_SIGNAL_DATE"},
    "INDEX_WEIGHT_PIT_R1": {"pit_policy": "LAST_KNOWN_OFFICIAL_SNAPSHOT_PLUS_1D", "asof_behavior": "PIT_VALID_FROM_LE_SIGNAL_TIME"},
    "ETF_TRACKING_INDEX_MAP_R1": {"pit_policy": "MAP_ASOF", "asof_behavior": "JOIN_ON_ETF_CODE"},
    "INDEX_CONSTITUENT_PIT_R1": {"pit_policy": "ASOF_MEMBERSHIP_NO_WEIGHT", "asof_behavior": "PIT_AT_DATE_WEIGHT_FORBIDDEN"},
    "STOCK_TRADEABILITY_PIT_R1": {"pit_policy": "EOD_SAME_DAY", "asof_behavior": "PIT_AT_SIGNAL_DATE"},
    "MARKET_UNIVERSE_PIT_R1": {"pit_policy": "EOD_SAME_DAY", "asof_behavior": "PIT_AT_SIGNAL_DATE"},
    "JQ20_FUND_MF_DAILY_PROFIT_PIT_R1": {"pit_policy": "DISCLOSURE_UPSERT", "asof_behavior": "KNOWN_AT_NEXT_TRADE_DAY"},
    "TUSHARE_CBOND_DAILY_MARKET_R1": {"pit_policy": "EOD_SAME_DAY", "asof_behavior": "PIT_AT_SIGNAL_DATE"},
    "TUSHARE_CBOND_DAILY_MARKET_JQCOMPAT_R1": {"pit_policy": "EOD_SAME_DAY", "asof_behavior": "PIT_AT_SIGNAL_DATE"},
    "TUSHARE_CBOND_BASIC_R1": {"pit_policy": "SNAPSHOT_DICTIONARY", "asof_behavior": "NOT_CONVERT_PRICE_PIT"},
    "TUSHARE_CBOND_BASIC_JQCOMPAT_R1": {"pit_policy": "SNAPSHOT_DICTIONARY", "asof_behavior": "NOT_CONVERT_PRICE_PIT"},
    "TUSHARE_CBOND_STOCK_BRIDGE_R1": {"pit_policy": "DICTIONARY_MAP", "asof_behavior": "JOIN_ON_STOCK_CODE_JQ"},
    "TUSHARE_CBOND_RATING_PIT_R1": {"pit_policy": "NEXT_TRADE_DAY_AFTER_ANN_DATE", "asof_behavior": "PIT_VALID_FROM"},
    "TUSHARE_CBOND_CALL_PIT_R1": {"pit_policy": "NEXT_TRADE_DAY_AFTER_ANN_DATE", "asof_behavior": "PIT_VALID_FROM"},
    "TUSHARE_CBOND_REMAIN_SIZE_PIT_R1": {"pit_policy": "NEXT_TRADE_DAY_AFTER_PUBLISH_DATE", "asof_behavior": "PIT_VALID_FROM"},
    "TUSHARE_CBOND_TOP10_HOLDERS_R1": {"pit_policy": "REPORT_PERIOD_ONLY_NOT_PIT", "asof_behavior": "BACKTEST_DEFAULT_FORBIDDEN"},
    "TUSHARE_CBOND_RATING_R1": {"pit_policy": "EVENT_TABLE", "asof_behavior": "USE_RATING_PIT_PRODUCT"},
}
DEFAULT_PIT = {"pit_policy": "DISCLOSURE_UPSERT", "asof_behavior": "KNOWN_AT_NEXT_TRADE_DAY"}

# Finance statement products — scope is part of product identity (R22 paired Cache)
FINANCE_PRODUCT_CONTRACTS = {
    "JQ20_FINANCE_INCOME_STATEMENT_PIT_R1": {
        "statement_family": "INCOME",
        "statement_scope": "CONSOLIDATED",
        "cleaning_rel": "finance/income_statement/CONSOLIDATED",
        "primary_key": ["code", "end_date", "statement_scope"],
        "year_slice_key": "end_date.year",
        "pit_fields": {
            "known_at": "publication_date",
            "report_period": "end_date|report_period_end",
            "pit_valid_from": "pit_valid_from",
            "local_only_not_known_at": "BACKFILL_ACQUIRED_AT",
        },
        "forbidden": [
            "PARENT_AS_CONSOLIDATED",
            "RAW_FALLBACK",
            "price/fundamentals_pit",
            "USE_BACKFILL_ACQUIRED_AT_AS_KNOWN_AT",
        ],
    },
    "JQ20_FINANCE_INCOME_STATEMENT_PARENT_PIT_R1": {
        "statement_family": "INCOME",
        "statement_scope": "PARENT",
        "cleaning_rel": "finance/income_statement/PARENT",
        "primary_key": ["code", "end_date", "statement_scope"],
        "year_slice_key": "end_date.year",
        "pit_fields": {
            "known_at": "publication_date",
            "report_period": "end_date|report_period_end",
            "pit_valid_from": "pit_valid_from",
            "local_only_not_known_at": "BACKFILL_ACQUIRED_AT",
        },
        "forbidden": [
            "CONSOLIDATED_AS_PARENT",
            "RAW_FALLBACK",
            "price/fundamentals_pit",
            "USE_BACKFILL_ACQUIRED_AT_AS_KNOWN_AT",
        ],
    },
    "JQ20_FINANCE_CASHFLOW_STATEMENT_PIT_R1": {
        "statement_family": "CASHFLOW",
        "statement_scope": "CONSOLIDATED",
        "cleaning_rel": "finance/cash_flow/CONSOLIDATED",
        "primary_key": ["code", "end_date", "statement_scope"],
        "year_slice_key": "end_date.year",
        "pit_fields": {
            "known_at": "publication_date",
            "report_period": "end_date|report_period_end",
            "pit_valid_from": "pit_valid_from",
            "local_only_not_known_at": "BACKFILL_ACQUIRED_AT",
        },
        "forbidden": [
            "PARENT_AS_CONSOLIDATED",
            "RAW_FALLBACK",
            "price/fundamentals_pit",
            "USE_BACKFILL_ACQUIRED_AT_AS_KNOWN_AT",
        ],
    },
    "JQ20_FINANCE_CASHFLOW_STATEMENT_PARENT_PIT_R1": {
        "statement_family": "CASHFLOW",
        "statement_scope": "PARENT",
        "cleaning_rel": "finance/cash_flow/PARENT",
        "primary_key": ["code", "end_date", "statement_scope"],
        "year_slice_key": "end_date.year",
        "pit_fields": {
            "known_at": "publication_date",
            "report_period": "end_date|report_period_end",
            "pit_valid_from": "pit_valid_from",
            "local_only_not_known_at": "BACKFILL_ACQUIRED_AT",
        },
        "forbidden": [
            "CONSOLIDATED_AS_PARENT",
            "RAW_FALLBACK",
            "price/fundamentals_pit",
            "USE_BACKFILL_ACQUIRED_AT_AS_KNOWN_AT",
        ],
    },
    "JQ20_FINANCE_BALANCE_SHEET_PIT_R1": {
        "statement_family": "BALANCE",
        "statement_scope": "CONSOLIDATED",
        "cleaning_rel": "finance/balance_sheet/CONSOLIDATED",
        "primary_key": ["code", "end_date", "statement_scope"],
        "year_slice_key": "end_date.year",
        "pit_fields": {
            "known_at": "publication_date",
            "report_period": "end_date|report_period_end",
            "pit_valid_from": "pit_valid_from",
            "local_only_not_known_at": "BACKFILL_ACQUIRED_AT",
        },
        "forbidden": [
            "PARENT_AS_CONSOLIDATED",
            "RAW_FALLBACK",
            "price/fundamentals_pit",
            "USE_BACKFILL_ACQUIRED_AT_AS_KNOWN_AT",
        ],
    },
    "JQ20_FINANCE_BALANCE_SHEET_PARENT_PIT_R1": {
        "statement_family": "BALANCE",
        "statement_scope": "PARENT",
        "cleaning_rel": "finance/balance_sheet/PARENT",
        "primary_key": ["code", "end_date", "statement_scope"],
        "year_slice_key": "end_date.year",
        "pit_fields": {
            "known_at": "publication_date",
            "report_period": "end_date|report_period_end",
            "pit_valid_from": "pit_valid_from",
            "local_only_not_known_at": "BACKFILL_ACQUIRED_AT",
        },
        "forbidden": [
            "CONSOLIDATED_AS_PARENT",
            "RAW_FALLBACK",
            "price/fundamentals_pit",
            "USE_BACKFILL_ACQUIRED_AT_AS_KNOWN_AT",
        ],
    },
}
for _fid in FINANCE_PRODUCT_CONTRACTS:
    PIT_POLICIES[_fid] = {
        "pit_policy": "BLACKBOX_HAND_FINANCE_PIT_KNOWN_AT_ANTILEAK_R1",
        "asof_behavior": "KNOWN_AT_NEXT_TRADE_DAY",
    }

# ── security cross-section contracts ──
SEC_NAMESPACES = {
    "STOCK": {"canonical_key": "code", "namespace": "A_SHARE", "join_rule": "INNER_ON_STOCK_CODE"},
    "ETF": {"canonical_key": "code", "namespace": "A_SHARE", "join_rule": "INNER_ON_ETF_CODE"},
    "FUND": {"canonical_key": "code", "namespace": "FUND", "join_rule": "INNER_ON_FUND_CODE"},
    "INDEX": {"canonical_key": "code", "namespace": "INDEX", "join_rule": "INNER_ON_INDEX_CODE"},
    "MIXED": {"canonical_key": "code", "namespace": "A_SHARE_OR_FUND", "join_rule": "LEFT_ON_CODE"},
    "MARKET": {"canonical_key": "date", "namespace": "MARKET_LEVEL", "join_rule": "ON_DATE"},
    "INDUSTRY": {"canonical_key": "date", "namespace": "INDUSTRY_LEVEL", "join_rule": "ON_DATE"},
    "CBOND": {"canonical_key": "bond_code_jq", "namespace": "CBOND", "join_rule": "INNER_ON_BOND_CODE"},
}


def sha256_short(path: Path) -> str:
    if not path.is_file():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def read_currents():
    """Read all CURRENT pointers from disk. Fail if missing."""
    errors = []
    result = {}

    # HAND
    if HAND_PATH.is_file():
        result["hand_read"] = True
        result["hand_path"] = str(HAND_PATH)
        result["hand_hash"] = sha256_short(HAND_PATH)
    else:
        errors.append("HAND.txt MISSING")
        result["hand_read"] = False

    # CACHE CURRENT
    if CACHE_CURRENT_PTR.is_file():
        cache = json.loads(CACHE_CURRENT_PTR.read_text(encoding="utf-8"))
        result["cache_current"] = cache
        result["cache_release_id"] = cache.get("cache_release_id", "")
        # CURRENT_CACHE_RELEASE.json uses release_root; some older pointers used standard_root
        result["cache_release_root"] = (
            cache.get("release_root")
            or cache.get("standard_root")
            or cache.get("cache_root")
            or ""
        )
        result["cache_asof"] = cache.get("asof", "")
    else:
        errors.append("CACHE_CURRENT_POINTER MISSING")
        result["cache_current"] = None

    if CBOND_CACHE_CURRENT_PTR.is_file():
        cbond = json.loads(CBOND_CACHE_CURRENT_PTR.read_text(encoding="utf-8"))
        result["cbond_cache_current"] = cbond
        result["cbond_cache_release_id"] = cbond.get("cache_release_id", "")
        result["cbond_cache_release_root"] = cbond.get("release_root", "")
        result["cbond_source_vendor"] = cbond.get("source_vendor", "TUSHARE_PRO")
        result["cbond_product_path_map"] = cbond.get("product_path_map") or {}
        result["cbond_parent_release_root"] = cbond.get("parent_release_root") or ""
    else:
        result["cbond_cache_current"] = None
        result["cbond_cache_release_root"] = ""

    result["sidecar_product_path_map"] = {}
    if SIDECAR_PRODUCTS.is_file():
        side = json.loads(SIDECAR_PRODUCTS.read_text(encoding="utf-8"))
        result["sidecar_products"] = side
        pmap = {}
        for pid, meta in (side.get("products") or {}).items():
            if isinstance(meta, dict) and meta.get("cache_product_path"):
                pmap[pid] = meta["cache_product_path"]
        result["sidecar_product_path_map"] = pmap
    else:
        result["sidecar_products"] = None

    # EXTERNAL EVIDENCE resolver (source-isolated; never mixes into JQ products)
    if EXTERNAL_EVIDENCE_RESOLVER_PTR.is_file():
        ext = json.loads(EXTERNAL_EVIDENCE_RESOLVER_PTR.read_text(encoding="utf-8"))
        result["external_evidence_resolver"] = ext
        emap = {}
        for row in ext.get("products") or []:
            if not isinstance(row, dict):
                continue
            pid = row.get("product_id")
            if pid and row.get("resolver_ready") and row.get("path"):
                emap[pid] = row
        result["external_evidence_product_map"] = emap
    else:
        result["external_evidence_resolver"] = None
        result["external_evidence_product_map"] = {}

    # CLEANING CURRENT
    if CLEANING_CURRENT_PTR.is_file():
        clean = json.loads(CLEANING_CURRENT_PTR.read_text(encoding="utf-8"))
        result["cleaning_current"] = clean
        result["cleaning_release_id"] = clean.get("release_id", "")
    else:
        errors.append("CLEANING_CURRENT_POINTER MISSING")
        result["cleaning_current"] = None

    # CATALOG
    if CATALOG_CSV.is_file():
        import pandas as pd
        catalog = pd.read_csv(CATALOG_CSV)
        result["catalog"] = catalog
        result["catalog_read"] = True
    else:
        errors.append("CATALOG CSV MISSING")
        result["catalog"] = None
        result["catalog_read"] = False

    # MANIFEST
    if MANIFEST_JSON.is_file():
        manifest = json.loads(MANIFEST_JSON.read_text(encoding="utf-8"))
        result["manifest"] = manifest
        result["manifest_read"] = True
    else:
        result["manifest"] = None
        result["manifest_read"] = False

    # R19 provenance
    if R19_PROVENANCE.is_file():
        r19 = json.loads(R19_PROVENANCE.read_text(encoding="utf-8"))
        result["r19_authoritative"] = r19.get("authoritative_for_future_use", True)
    else:
        result["r19_authoritative"] = True  # if missing, assume caution

    # LEDGER
    if LEDGER_JSON.is_file():
        result["ledger"] = json.loads(LEDGER_JSON.read_text(encoding="utf-8"))
    else:
        result["ledger"] = None

    result["authority_ready"] = len(errors) == 0
    result["errors"] = errors
    return result


def resolve_product(dataset_raw: str, asof: str | None, scope: str | None, currents: dict) -> dict:
    """Deterministic resolution of a dataset to a formal cache product."""

    # 1. Normalize via aliases
    normalized = ALIASES.get(dataset_raw, dataset_raw)

    # 1b. External evidence products (source-isolated index)
    ext_map = currents.get("external_evidence_product_map") or {}
    if normalized in ext_map:
        meta = ext_map[normalized]
        path = meta.get("path")
        ready = bool(path) and Path(str(path)).exists()
        return {
            "resolved": bool(ready),
            "result_status": "READY" if ready else "EXTERNAL_EVIDENCE_PATH_MISSING",
            "product_id": normalized,
            "source_namespace": meta.get("source_namespace"),
            "source_vendor": meta.get("source_vendor"),
            "cache_product_path": path,
            "meta_path": meta.get("meta_path"),
            "rights_status": meta.get("rights_status"),
            "EXTERNAL_EVIDENCE": True,
            "forbid_write_into_jq_products": True,
            "note": meta.get("note") or "Resolved via BLACKBOX_EXTERNAL_EVIDENCE_RESOLVER_CURRENT.json",
        }

    # 1c. A-share stock 1m — authority is Cleaning CURRENT (not cache shard root, not Entry fixture)
    if normalized in {
        "STOCK_MINUTE_1M_R1",
        "STOCK_MINUTE_1M",
        "STOCK_1M",
        "A股_stock_1m",
        "A股_1m",
        "stock_1m",
        "分钟1m",
        "1m",
    }:
        try:
            from blackbox_stock_minute_1m_reader_r1 import PRODUCT_ID as _SM_PID
            from blackbox_stock_minute_1m_reader_r1 import resolve_cleaning_stock_1m_source
        except Exception as e:
            return {
                "resolved": False,
                "result_status": "STOCK_MINUTE_READER_UNAVAILABLE",
                "product_id": "STOCK_MINUTE_1M_R1",
                "error": str(e),
                "download_required": False,
            }
        src = resolve_cleaning_stock_1m_source()
        ready = src.get("status") == "READY"
        pit = PIT_POLICIES.get("STOCK_MINUTE_1M_R1", {})
        return {
            "resolved": bool(ready),
            "result_status": "READY" if ready else (src.get("status") or "MISSING"),
            "product_id": _SM_PID,
            "logical_dataset_id": dataset_raw,
            "product_path": src.get("source_dir"),
            "authority_status": "FORMAL_CLEANING_CURRENT",
            "CAN_SERVE_PLANE": "CLEANING_CURRENT",
            "source_cleaning_release": src.get("cleaning_release_id"),
            "cleaning_as_of": src.get("cleaning_as_of"),
            "source_paths": src.get("source_paths") or [],
            "source_sha256": src.get("source_sha256") or {},
            "evidence_gaps": src.get("evidence_gaps") or [],
            "pit_policy": pit.get("pit_policy"),
            "asof_behavior": pit.get("asof_behavior"),
            "timezone": "Asia/Shanghai",
            "raw_fallback_allowed": False,
            "download_required": False,
            "authoritative": True,
            "reader": {
                "module": "blackbox_stock_minute_1m_reader_r1",
                "function": "fetch_stock_minute_1m",
            },
            "note": "STOCK_MINUTE_1M_R1 resolves via Cleaning CURRENT A股_stock_1m; Entry/refining paths forbidden",
        }

    # 2. Check for ambiguous scope
    if normalized in AMBIGUOUS_DATASETS:
        amb = AMBIGUOUS_DATASETS[normalized]
        if amb["scope_required"] and not scope:
            return {
                "resolved": False,
                "result_status": "AMBIGUOUS_SCOPE",
                "error": f"Dataset '{dataset_raw}' requires --scope (CONSOLIDATED or PARENT)",
                "options": amb["options"],
            }
        if scope:
            target = amb["options"].get(scope.upper())
            if not target:
                return {
                    "resolved": False,
                    "result_status": "INVALID_SCOPE",
                    "error": f"Scope '{scope}' not valid for '{dataset_raw}'. Options: {list(amb['options'].keys())}",
                }
            normalized = target

    # 3. Look up in catalog
    catalog = currents.get("catalog")
    if catalog is None:
        return {"resolved": False, "result_status": "CATALOG_MISSING"}

    if normalized in ("FUND_PORTFOLIO_STOCK_PIT_R1", "FUND_PORTFOLIO_STOCK", "fund_portfolio_stock"):
        return {
            "resolved": False,
            "result_status": "SOURCE_PRESENT_AUTHORITY_NOT_PRODUCTIZED",
            "product_id": "FUND_PORTFOLIO_STOCK_PIT_R1",
            "SOURCE_API_AVAILABLE": True,
            "LOCAL_RAW_PRESENT": False,
            "FORMAL_PRODUCT_AVAILABLE": False,
            "CACHE_PRODUCT_AVAILABLE": False,
            "OLD_LEDGER_POINTER_STATUS": "MISCLASSIFIED_NAV_SOURCE",
            "must_not_return": "NAV",
            "WEIGHT_PROXY_FORBIDDEN": True,
            "download_required": False,
            "error": "finance.FUND_PORTFOLIO_STOCK API exists; local holdings RAW/formal product absent. P4b_fund_expand is NAV, not holdings.",
        }

    product_rows = catalog[catalog["product_id"] == normalized]
    if len(product_rows) == 0:
        # Formal coverage classification — do not say "maybe missing download"
        related = None
        if normalized == "VALUATION_PIT_R1":
            related = "STOCK_FACTOR_DAILY_R1"
        return {
            "resolved": False,
            "result_status": "CACHE_PRODUCT_UNAVAILABLE",
            "root_cause": "CACHE_PRODUCT_UNAVAILABLE",
            "download_required": False,
            "error": f"Product '{normalized}' not in CACHE catalog. Requested as '{dataset_raw}'.",
            "related_product_hint": related,
            "note": (
                "Do not claim BLACKBOX has no valuation source; RAW may exist. "
                "Dedicated VALUATION_PIT cache product is unavailable — use formal diagnosis."
            ),
        }
    product_info = product_rows.iloc[0].to_dict()

    # 4. Check R19 superseded guard for FUND_MF
    if "FUND_MF" in normalized and "R19" in str(currents.get("cache_release_id", "")):
        return {
            "resolved": False,
            "result_status": "SUPERSEDED_RELEASE",
            "error": f"FUND_MF must use R20 CURRENT, not R19. Current: {currents.get('cache_release_id')}",
        }
    if normalized == "JQ20_FUND_MF_DAILY_PROFIT_PIT_R1" and currents.get("r19_authoritative"):
        return {
            "resolved": False,
            "result_status": "SUPERSEDED_RELEASE",
            "error": "FUND_MF_DAILY_PROFIT: R19 is NOT authoritative. Use R20 CURRENT.",
        }

    # 5. Build physical path
    cache_root = currents.get("cache_release_root", "")
    is_cbond = str(normalized).startswith("TUSHARE_CBOND_") or str(product_info.get("asset_type", "")).upper() == "CBOND"
    sidecar_map = currents.get("sidecar_product_path_map") or {}
    used_sidecar = False
    if normalized in sidecar_map:
        product_path = sidecar_map[normalized]
        cache_root = str(Path(product_path).parent)
        used_sidecar = True
    elif is_cbond:
        cache_root = currents.get("cbond_cache_release_root") or cache_root
        _pmap = currents.get("cbond_product_path_map") or {}
        if normalized in _pmap:
            product_path = _pmap[normalized]
            cache_root = str(Path(product_path).parent)
    if not cache_root:
        return {"resolved": False, "result_status": "CACHE_ROOT_MISSING"}

    if not used_sidecar and not (is_cbond and (currents.get("cbond_product_path_map") or {}).get(normalized)):
        product_path = os.path.join(cache_root, normalized)

    # 6. Check product path exists
    if not os.path.isdir(product_path):
        # Some products may use alternate layouts - try common patterns
        alt = os.path.join(cache_root, normalized, "data")
        if os.path.isdir(alt):
            product_path = alt
        else:
            return {
                "resolved": False,
                "result_status": "PRODUCT_PATH_MISSING",
                "error": f"Product path not found: {product_path}",
            }

    # 7. Security namespace
    asset_type = product_info.get("asset_type", "MIXED")
    sec = SEC_NAMESPACES.get(asset_type, SEC_NAMESPACES["MIXED"])

    # 8. PIT policy
    pit = PIT_POLICIES.get(normalized, DEFAULT_PIT)

    # 9. Manifest (best effort)
    manifest_path = os.path.join(cache_root, normalized, "PROVENANCE.json")
    if not os.path.isfile(manifest_path):
        manifest_path = os.path.join(cache_root, normalized, "GATE_DECISION.md")

    # 10. Reader (best effort - common patterns)
    reader_module = f"cache_{normalized.lower()}_reader_r1"
    reader_function = "read"

    # 11. Coverage contract (control-plane; optional date range)
    coverage_mode = None
    coverage_min = None
    coverage_max = None
    coverage_distinct = None
    historical_ready = None
    coverage_ready = None
    missing_trade_days = []
    expected_trade_days = None
    available_trade_days = None
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from blackbox_data_coverage_common_r1 import (  # local import
            infer_mode_for_product,
            load_trade_calendar,
            product_date_coverage,
        )
        cov = product_date_coverage(Path(product_path))
        coverage_mode = infer_mode_for_product(normalized, cov)
        coverage_min = cov.get("min_date")
        coverage_max = cov.get("max_date")
        coverage_distinct = cov.get("distinct_dates")
        historical_ready = coverage_mode in ("FULL_HISTORY", "DAILY_HISTORY", "ASOF_SNAPSHOT_HISTORY") and (
            (coverage_distinct or 0) > 1
        )
        # start/end injected via currents optional keys
        start_date = currents.get("_request_start_date")
        end_date = currents.get("_request_end_date")
        if start_date and end_date and normalized in ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1"):
            expected = [str(d) for d in load_trade_calendar(start_date, end_date)]
            have = set(cov.get("dates") or [])
            missing_trade_days = [d for d in expected if d not in have]
            expected_trade_days = len(expected)
            available_trade_days = len(expected) - len(missing_trade_days)
            coverage_ready = len(missing_trade_days) == 0 and coverage_mode != "INCREMENTAL_PATCH"
        elif start_date and end_date:
            # generic: min/max containment
            coverage_ready = (
                coverage_min is not None
                and coverage_max is not None
                and coverage_min <= start_date
                and coverage_max >= end_date
                and coverage_mode != "INCREMENTAL_PATCH"
            )
        else:
            coverage_ready = historical_ready if normalized in (
                "STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "INDEX_DAILY_R1", "STOCK_FACTOR_DAILY_R1"
            ) else True
    except Exception as e:
        coverage_mode = "UNKNOWN_STOP"
        coverage_ready = False
        currents["_coverage_error"] = str(e)

    # 12. Build result
    result = {
        "resolved": True,
        "result_status": "READY",
        "logical_dataset_id": dataset_raw,
        "product_id": normalized,
        "cache_release_id": currents.get("cache_release_id", ""),
        "cache_asof": currents.get("cache_asof", ""),
        "product_path": product_path,
        "coverage_mode": coverage_mode,
        "coverage_min_date": coverage_min,
        "coverage_max_date": coverage_max,
        "coverage_distinct_dates": coverage_distinct,
        "historical_ready": historical_ready,
        "coverage_ready": coverage_ready,
        "requested_start": currents.get("_request_start_date"),
        "requested_end": currents.get("_request_end_date"),
        "expected_trade_days": expected_trade_days,
        "available_trade_days": available_trade_days,
        "missing_trade_days": missing_trade_days,
        "download_required": False if coverage_ready else None,
        "manifest_path": manifest_path if os.path.isfile(manifest_path) else None,
        "schema_path": None,
        "qa_path": os.path.join(cache_root, normalized, "_qa") if os.path.isdir(os.path.join(cache_root, normalized, "_qa")) else None,
        "reader": {
            "module": reader_module,
            "function": reader_function,
            "arguments": {"product_path": product_path, "asof": asof or currents.get("cache_asof")},
        },
        "pit_policy": pit["pit_policy"],
        "asof_behavior": pit["asof_behavior"],
        "authority_status": "FORMAL_CURRENT",
        "asset_type": asset_type,
        "security_namespace": sec["namespace"],
        "canonical_key": sec["canonical_key"],
        "cross_section_contract": sec["join_rule"],
        "source_cleaning_product": product_info.get("description", ""),
        "source_cleaning_release": currents.get("cleaning_release_id", ""),
        "r19_superseded_guard": "PASS" if not currents.get("r19_authoritative", True) else "NOT_APPLICABLE",
        "raw_fallback_allowed": False,
        "authoritative": True,
        "source_vendor": ("TUSHARE_PRO" if str(normalized).startswith("TUSHARE_CBOND_") else None),
        "jq_native_data": False if str(normalized).startswith("TUSHARE_CBOND_") else None,
        "schema_compat_target": ("JOINQUANT_CONBOND" if str(normalized).startswith("TUSHARE_CBOND_") else None),
        "COMPATIBILITY_ALIAS_ONLY": True if dataset_raw in ("CONBOND",) else False,
        "NATIVE_JQ_DATA": False,
        "CBOND_CONVERT_PRICE_PIT": "NOT_READY" if str(normalized).startswith("TUSHARE_CBOND_") else None,
    }
    if used_sidecar:
        result["authority_status"] = "SIDECAR_SUCCESSOR_NOT_LIVE_CURRENT"
        result["authoritative"] = False
        result["LIVE_CAN_SERVE"] = "NO"
        result["CAN_SERVE_PLANE"] = "SIDECAR"
        result["result_status"] = "READY_SIDECAR_NOT_CURRENT"
        if normalized in ("INDEX_WEIGHT_PIT_R1", "ETF_TRACKING_INDEX_MAP_R1"):
            result["INDEX_WEIGHT_LIVE_CAN_SERVE"] = "NO"
            result["INDEX_WEIGHT_HISTORICAL_BACKTEST_ELIGIBLE"] = False
            result["LAST_KNOWN_SNAPSHOT_FORWARD_SUPPORTED"] = normalized == "INDEX_WEIGHT_PIT_R1"
            result["PIT_VISIBILITY_CONTRACT"] = "UNRESOLVED"
    fin = FINANCE_PRODUCT_CONTRACTS.get(normalized)
    if fin:
        result["statement_family"] = fin["statement_family"]
        result["statement_scope"] = fin["statement_scope"]
        result["scope_required"] = True
        result["cleaning_rel"] = fin["cleaning_rel"]
        result["primary_key"] = fin["primary_key"]
        result["year_slice_key"] = fin["year_slice_key"]
        result["pit_fields"] = fin["pit_fields"]
        result["forbidden"] = fin["forbidden"]
        result["reader_contract"] = {
            "filter_scope": fin["statement_scope"],
            "visible_iff": "pit_valid_from <= SIGNAL_TIME",
            "known_at_field": fin["pit_fields"]["known_at"],
            "never_use_as_known_at": fin["pit_fields"]["local_only_not_known_at"],
        }
    return result


def build_index(currents: dict) -> dict:
    """Generate DATA_ACCESS_INDEX from authoritative sources only."""
    import pandas as pd

    catalog = currents.get("catalog")
    if catalog is None:
        return {"error": "CATALOG_MISSING"}

    products = []
    for _, row in catalog.iterrows():
        pid = row["product_id"]
        if pid == "CACHE_MANIFEST_REGISTRY_R1" or pid == "CACHE_DEPENDENCY_REGISTRY_R1":
            continue
        is_cbond = str(pid).startswith("TUSHARE_CBOND_") or str(row.get("asset_type", "")).upper() == "CBOND"
        root = currents.get("cbond_cache_release_root") if is_cbond else currents.get("cache_release_root", "")
        _pmap = currents.get("cbond_product_path_map") or {}
        _smap = currents.get("sidecar_product_path_map") or {}
        product_path = _smap.get(pid) or _pmap.get(pid) or os.path.join(root or "", pid)
        exists = os.path.isdir(product_path) or os.path.isfile(product_path.replace("_R1", "_R1") + ".parquet")
        asset_type = row.get("asset_type", "MIXED")
        sec = SEC_NAMESPACES.get(asset_type, SEC_NAMESPACES["MIXED"])
        pit = PIT_POLICIES.get(pid, DEFAULT_PIT)
        products.append({
            "product_id": pid,
            "layer": row.get("layer", ""),
            "asset_type": asset_type,
            "status": "READY" if exists else "PATH_NOT_FOUND",
            "grain": row.get("partition_key", ""),
            "description": row.get("description", ""),
            "cache_release_id": currents.get("cache_release_id", ""),
            "cache_product_path": product_path,
            "security_namespace": sec["namespace"],
            "cross_section_contract": sec["join_rule"],
            "pit_policy": pit["pit_policy"],
            "asof_behavior": pit["asof_behavior"],
            "aliases": [a for a, p in ALIASES.items() if p == pid],
            **(
                {
                    "statement_family": FINANCE_PRODUCT_CONTRACTS[pid]["statement_family"],
                    "statement_scope": FINANCE_PRODUCT_CONTRACTS[pid]["statement_scope"],
                    "cleaning_rel": FINANCE_PRODUCT_CONTRACTS[pid]["cleaning_rel"],
                    "forbidden": FINANCE_PRODUCT_CONTRACTS[pid]["forbidden"],
                    "pit_fields": FINANCE_PRODUCT_CONTRACTS[pid]["pit_fields"],
                }
                if pid in FINANCE_PRODUCT_CONTRACTS
                else {}
            ),
        })

    index = {
        "index_id": "BLACKBOX_DATA_ACCESS_INDEX_R1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_from_cache_release": currents.get("cache_release_id", ""),
        "generated_from_catalog_hash": sha256_short(CATALOG_CSV),
        "generated_from_hand_hash": sha256_short(HAND_PATH),
        "cleaning_current_id": currents.get("cleaning_release_id", ""),
        "cache_current_id": currents.get("cache_release_id", ""),
        "cache_current_asof": currents.get("cache_asof", ""),
        "cache_current_root": currents.get("cache_release_root", ""),
        "product_count": len(products),
        "products": products,
    }
    return index


def main():
    parser = argparse.ArgumentParser(description="BLACKBOX Deterministic Data Access Resolver R1")
    parser.add_argument("--dataset", default=None, help="Dataset/product to resolve (e.g. SW_L2, FUND_MF_DAILY_PROFIT)")
    parser.add_argument("--asof", default=None, help="Optional as-of date")
    parser.add_argument("--scope", default=None, help="CONSOLIDATED or PARENT (required for finance statements)")
    parser.add_argument("--start-date", default=None, help="Optional coverage request start (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=None, help="Optional coverage request end (YYYY-MM-DD)")
    parser.add_argument("--build-index", action="store_true", help="Build DATA_ACCESS_INDEX_CURRENT.json")
    parser.add_argument("--dump-current", action="store_true", help="Dump CURRENT state")
    args = parser.parse_args()

    if not args.dataset and not args.build_index and not args.dump_current:
        parser.error("--dataset is required unless --build-index or --dump-current is set")

    currents = read_currents()

    if not currents["authority_ready"]:
        print(json.dumps({
            "authority_ready": False,
            "resolved": False,
            "result_status": "STOP",
            "errors": currents["errors"],
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    if args.dump_current:
        print(json.dumps({
            "authority_ready": True,
            "cleaning_current": currents.get("cleaning_release_id"),
            "cache_current": currents.get("cache_release_id"),
            "cache_asof": currents.get("cache_asof"),
            "cache_root": currents.get("cache_release_root"),
            "catalog_read": currents.get("catalog_read"),
            "manifest_read": currents.get("manifest_read"),
            "r19_authoritative": currents.get("r19_authoritative"),
        }, ensure_ascii=False, indent=2))
        return

    if args.build_index:
        index = build_index(currents)
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"index_built": True, "path": str(INDEX_PATH), "product_count": index.get("product_count", 0)}, ensure_ascii=False))
        return

    if args.start_date:
        currents["_request_start_date"] = args.start_date
    if args.end_date:
        currents["_request_end_date"] = args.end_date
    result = resolve_product(args.dataset, args.asof, args.scope, currents)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
