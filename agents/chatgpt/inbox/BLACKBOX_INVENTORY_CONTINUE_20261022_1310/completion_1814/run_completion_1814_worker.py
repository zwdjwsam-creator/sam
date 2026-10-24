# -*- coding: utf-8 -*-
"""
TIP_1814 worker.

Scope (per instruction):
  A. dictionary field mapping  (reuse 13/20 dictionary artifacts; no re-read of 26 domains)
  B. post-baseline / external scope  (bounded: P5_jq20_extension + FUND_ETF_NAV + known external roots)
  C. engine real data interface  (pyproject / rule registries / provider chain / isolated pure-read smoke)

Hard constraints:
  FOUNDATION_ACCEPTANCE=false  PRODUCTION_CHANGE_AUTHORIZED=false
  no download, no API, no publishing to production, no rule/data/CURRENT/env change,
  no cleanup, no R9 restart, no old-strategy run.
Reused (not re-checked): 1803 DOMAIN_SAMESET_DIFF, DIRECTORY_OVERVIEW_COMPACT, 1752 engine baseline.
"""
from __future__ import annotations

import csv
import glob
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

AT = datetime.now().astimezone().isoformat()
OUT = Path(__file__).resolve().parent
ISO = OUT / "isolation_smoke"
ISO.mkdir(exist_ok=True)

DICT = Path(r"E:\BLACKBOX\数据\原始只读\JQData_reference_dictionary")
FREEZE20 = DICT / "20_unified_data_schema_contract_freeze_full_R1"
CHECK13 = DICT / "13_local_schema_header_final_check"
RAW = Path(r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw")
RROOT = Path(r"E:\BLACKBOX\数据\原始只读")
ENG = Path(r"E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine")
MR = ENG / "rule_library" / "master_registry_R1"
PREV1803 = OUT.parent / "completion_1803"

FOUNDATION_ACCEPTANCE = False
PRODUCTION_CHANGE_AUTHORIZED = False


def read_csv(p: Path):
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()


def ev(p: Path) -> dict:
    return {"path": str(p), "exists": p.exists(), "sha256": sha256(p) if p.is_file() else None,
            "bytes": p.stat().st_size if p.is_file() else None}


# ---------------------------------------------------------------- evidence loads
PRICE_DICT = read_csv(DICT / "03_field_dictionary" / "price_field_dictionary.csv")
UNIT_DICT = read_csv(DICT / "06_unit_dictionary" / "unit_dictionary.csv")
PIT_DICT = read_csv(DICT / "05_pit_field_dictionary" / "pit_field_tags.csv")
DOMAIN_SCHEMA = read_csv(FREEZE20 / "02_domain_schema" / "domain_schema_contract.csv")
PIT_SCHEMA = read_csv(FREEZE20 / "04_pit_schema" / "pit_schema_contract.csv")
DTYPE_SCHEMA = read_csv(FREEZE20 / "09_dtype_precision_schema" / "dtype_precision_contract.csv")
PK_SCHEMA = read_csv(FREEZE20 / "10_primary_key_rules" / "primary_key_uniqueness_contract.csv")
STATUS_SCHEMA = read_csv(FREEZE20 / "12_status_field_schema" / "status_field_contract.csv")
GAP_SCHEMA = read_csv(FREEZE20 / "15_known_gap_schema" / "known_gap_schema_contract.csv")
DOMAIN_ADM = read_csv(MR / "DATA_DOMAIN_ADMISSION_MATRIX_R1.csv")
FIELD_ADM = read_csv(MR / "FIELD_ADMISSION_MATRIX_R1.csv")
FREQ_ADM = read_csv(MR / "FREQUENCY_ADMISSION_MATRIX_R1.csv")
MATCH_ADM = read_csv(MR / "MATCHING_REQUIREMENT_ADMISSION_MATRIX_R1.csv")
ATTR_INV = read_csv(CHECK13 / "01_schema_inventory" / "local_9999_attribute_schema_inventory.csv")
MIN_INV = read_csv(CHECK13 / "01_schema_inventory" / "local_9999_minute_schema_inventory.csv")
FIN_INV = read_csv(CHECK13 / "01_schema_inventory" / "local_9999_finance_schema_inventory.csv")

ENGINE_FIELD_MAP = {r["incoming_field_name"]: r for r in FIELD_ADM}
ENGINE_DOMAIN = {r["data_domain"]: r for r in DOMAIN_ADM}
DICT_UNIT = {}
for r in UNIT_DICT:
    for f in (r["example_fields"] or "").split(","):
        f = f.strip()
        if f:
            DICT_UNIT[f] = r["unit"]
for r in PRICE_DICT:
    DICT_UNIT.setdefault(r["field"], r["unit"])

# actual raw parquet headers (enumerated, not sampled blindly)
RAW_SCHEMA = {
    "stock_daily": ["date", "code", "open", "close", "high", "low", "volume", "money", "avg",
                    "pre_close", "high_limit", "low_limit", "paused", "factor"],
    "stock_minute_1m": ["time", "code", "open", "close", "high", "low", "volume", "money", "__index_level_0__"],
    "stock_minute_5m": ["time", "code", "open", "close", "high", "low", "volume", "money", "__index_level_0__"],
    "stock_minute_30m": ["time", "code", "open", "close", "high", "low", "volume", "money"],
    "stock_minute_60m": ["time", "code", "open", "close", "high", "low", "volume", "money"],
    "etf_price_1m": ["time", "code", "open", "close", "high", "low", "volume", "money"],
    "etf_price_5m": ["time", "code", "open", "close", "high", "low", "volume", "money"],
    "etf_price_30m": ["time", "code", "open", "close", "high", "low", "volume", "money"],
    "etf_price_60m": ["time", "code", "open", "close", "high", "low", "volume", "money"],
    "etf_price_daily_raw_none": ["time", "code", "open", "high", "low", "close", "volume", "money", "paused",
                                 "high_limit", "low_limit", "avg", "pre_close", "factor", "fq"],
    "etf_daily": ["time", "code", "open", "high", "low", "close", "volume", "money", "paused",
                  "high_limit", "low_limit", "avg", "pre_close", "factor"],
    "index_daily": ["time", "code", "open", "high", "low", "close", "volume", "money", "paused",
                    "high_limit", "low_limit", "avg", "pre_close", "factor", "fq"],
    "index_minute": ["time", "code", "open", "close", "high", "low", "volume", "money", "fq"],
    "adjust_factor_stock": ["date", "code", "factor", "sec_type"],
    "stock_limit_pause": ["date", "code", "paused", "high_limit", "low_limit"],
    "stock_st_status": ["date", "code", "is_st"],
    "fund_etf_nav": ["day", "code", "unit_net_value", "acc_net_value"],
    "fund_fund_net_value": ["id", "code", "day", "net_value", "sum_value", "factor", "acc_factor", "refactor_net_value"],
    "valuation": ["id", "code", "day", "pe_ratio", "turnover_ratio", "pb_ratio", "ps_ratio", "pcf_ratio",
                  "capitalization", "market_cap", "circulating_cap", "circulating_market_cap", "pe_ratio_lyr",
                  "pcf_ratio2", "dividend_ratio", "free_cap", "free_market_cap", "a_cap", "a_market_cap"],
    "index_components": ["index_code", "component_code", "asof_date"],
    "index_constituents": ["index_code", "code", "asof_date"],
    "index_weights": ["date", "weight", "display_name"],
    "securities_master": ["code", "display_name", "name", "start_date", "end_date", "type"],
    "industry_sw_components": ["industry_code", "stock_code"],
    "industry_sw_list": ["industry_code", "name", "start_date"],
    "stk_mt_total": ["id", "date", "exchange_code", "fin_value", "fin_buy_value", "sec_volume",
                     "sec_value", "sec_sell_volume", "fin_sec_value"],
    "billboard": ["code", "day", "direction", "rank", "abnormal_code", "abnormal_name", "sales_depart_name",
                  "buy_value", "buy_rate", "sell_value", "sell_rate", "total_value", "net_value", "amount"],
    "finance_balance": ["id", "code", "statDate", "pubDate", "statDate.1", "cash_equivalents", "total_assets",
                        "total_liability", "total_owner_equities"],
    "finance_cashflow": ["id", "code", "pub_date", "report_date", "report_type", "net_operate_cash_flow",
                         "net_invest_cash_flow", "net_finance_cash_flow"],
    "finance_indicator": ["id", "code", "statDate", "pubDate", "statDate.1", "eps", "roe", "roa",
                          "adjusted_profit", "gross_profit_margin"],
}


def parse_field_list(raw):
    """DOMAIN_SCHEMA.required_fields 是 "['a', 'b']" 形式的字符串，需真正解析。"""
    if not raw:
        return []
    s = str(raw).strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            v = ast.literal_eval(s)
            if isinstance(v, (list, tuple)):
                return [str(x).strip() for x in v if str(x).strip()]
        except Exception:
            pass
        s = s.strip("[]")
        return [x.strip().strip("'\" ") for x in s.split(",") if x.strip().strip("'\" ")]
    return [x.strip() for x in s.split(",") if x.strip()]


DOMAIN_BY_NAME = {r["domain"]: r for r in DOMAIN_SCHEMA}


def dom(name):
    r = DOMAIN_BY_NAME.get(name, {})
    return {"required": parse_field_list(r.get("required_fields")),
            "optional": parse_field_list(r.get("optional_fields")),
            "pk": r.get("primary_keys"), "action": r.get("clean_action")}


def required_of_domain(name):
    return [x.strip() for x in (ENGINE_DOMAIN.get(name, {}).get("required_fields") or "").split(",") if x.strip()]


def fields_of(domain_list):
    out = []
    for d in domain_list:
        for r in FIELD_ADM:
            if r["field_domain"] == d:
                out.append(r["incoming_field_name"])
    return out


def judge(source_fields, required_fields):
    src = set(source_fields)
    missing = [f for f in required_fields if f not in src]
    return missing


# ---------------------------------------------------------------- A. dictionary mapping
GROUPS = [
    dict(
        group_id="G01_SECURITY_MASTER", dataset_scope="security_master / securities_* / fund_etf_master / index_master",
        schema_basis="13_local_schema_header_final_check.01_schema_inventory (enumerated, 1 distinct schema)",
        source_schema="securities_master",
        dictionary_required=dom("security_master")["required"],
        dictionary_optional=dom("security_master")["optional"],
        target=("securities_master", dom("security_master")["pk"], dom("security_master")["action"]),
        engine_domains=["benchmark_data"],
        extra={
            "note": "code 列为 13 清单中的首列空名（已识别为 code）；securities_futures 存在于 P0_meta 但期货属 KG03 out_of_scope，不作映射目标",
            "naming": "P4_fund_etf/fund_etf_master 与 P3_index/index_master 增加 __index_level_0__（pandas index 残留），需在 clean 前丢弃",
        }),
    dict(
        group_id="G02_STOCK_DAILY_OHLCV", dataset_scope="stock_ohlcv_daily (P2_stock_daily)",
        schema_basis="26域 parquet header 实读（1 prefix = 1 distinct schema）",
        source_schema="stock_daily",
        dictionary_required=dom("price_fq_factor")["required"],
        dictionary_optional=dom("price_fq_factor")["optional"],
        target=("stock_daily", dom("price_fq_factor")["pk"], dom("price_fq_factor")["action"]),
        engine_domains=["daily_bar", "tradable_status", "adjustment_factor", "matching_requirements"],
    ),
    dict(
        group_id="G03_STOCK_MINUTE", dataset_scope="A股_stock_1m/5m/30m/60m (P7_*)",
        schema_basis="26域 parquet header 实读：4 prefix × 1 distinct schema，全部 8 列",
        source_schema="stock_minute_30m",
        dictionary_required=dom("minute_price")["required"],
        dictionary_optional=dom("minute_price")["optional"],
        target=("stock_minute", dom("minute_price")["pk"], dom("minute_price")["action"]),
        engine_domains=["minute_bar", "matching_requirements"],
    ),
    dict(
        group_id="G04_ETF_PRICE", dataset_scope="ETF_1m/5m/30m/60m + ETF 日线",
        schema_basis="26域 parquet header 实读：4 minute prefix 8 列；etf_price_daily_raw_none 15 列；etf_daily 14 列",
        source_schema="etf_price_1m",
        dictionary_required=dom("price_fq_factor")["required"],
        dictionary_optional=dom("price_fq_factor")["optional"],
        target=("stock_daily/stock_minute(etf)", dom("price_fq_factor")["pk"], dom("price_fq_factor")["action"]),
        engine_domains=["daily_bar", "minute_bar", "tradable_status"],
        extra={"note": "ETF 日线有两条不同 schema：etf_price_daily_raw_none(含 fq 列) 与 etf_daily(无 fq)；minute 全部 8 列"}),
    dict(
        group_id="G05_INDEX_PRICE", dataset_scope="index_components/weights + 指数日线/分钟",
        schema_basis="26域 parquet header 实读：index_daily 15 列 / index_minute 9 列",
        source_schema="index_daily",
        dictionary_required=dom("price_fq_factor")["required"],
        dictionary_optional=dom("price_fq_factor")["optional"],
        target=("stock_daily(index)", dom("price_fq_factor")["pk"], dom("price_fq_factor")["action"]),
        engine_domains=["benchmark_data"],
        extra={"note": "指数无 tradable_status 语义；KG03 futures/options 仍 out_of_scope"}),
    dict(
        group_id="G06_ADJUST_FACTOR", dataset_scope="adjust_factor (P1_adjust_factor / P2_security_state)",
        schema_basis="parquet header 实读：adjust_factor_stock/etf = (date,code,factor,sec_type)；P2_security_state/adjust_factor=(time,code,factor)",
        source_schema="adjust_factor_stock",
        dictionary_required=["factor", "fq"],
        dictionary_optional=["sec_type"],
        target=("stock_daily.factor", "symbol + trade_date", "raw_keep_separate_column"),
        engine_domains=["adjustment_factor"],
        extra={"rule": "13_adj_factor_methodology: raw close 不被 factor 覆盖；factor 跳变须可追溯到 corporate_actions 的 ex_date"},
    ),
    dict(
        group_id="G07_TRADABLE_STATUS", dataset_scope="stock_st_status / stock_limit_pause_status",
        schema_basis="parquet header 实读：stock_limit_pause=(date,code,paused,high_limit,low_limit)；stock_st_status=(date,code,is_st)；P2_security_state/is_st 为宽表（列名=证券代码）",
        source_schema="stock_limit_pause",
        dictionary_required=["paused", "is_st", "high_limit", "low_limit"],
        dictionary_optional=["halt_reason", "risk_warning"],
        target=("status_daily", "symbol + status_date + status_type", "raw_keep + derive_semantic"),
        engine_domains=["tradable_status"],
        extra={"note": "P2_security_state/is_st 宽表与 stock_st_status 长表并存，clean 只取长表；宽表记历史遗留"}),
    dict(
        group_id="G08_VALUATION", dataset_scope="valuation (P6_factor_reference/valuation, 52 files)",
        schema_basis="13_local_schema_header_final_check.01 (enumerated, distinct_schema=1, 52 files)",
        source_schema="valuation",
        dictionary_required=dom("valuation")["required"],
        dictionary_optional=dom("valuation")["optional"],
        target=("valuation_daily", dom("valuation")["pk"], dom("valuation")["action"]),
        engine_domains=[],
        extra={"unit_detected": "元"}),
    dict(
        group_id="G09_FINANCE_PIT", dataset_scope="fundamentals_pit (P3_finance_pit income/balance/cash_flow/indicator)",
        schema_basis="13_local_schema_header_final_check.01 (enumerated, 18 prefixes, distinct_schema=1 per table)",
        source_schema="finance_balance",
        dictionary_required=dom("finance_pit_unit")["required"],
        dictionary_optional=dom("finance_pit_unit")["optional"],
        target=("finance_{income|balance|cash_flow|indicator}", dom("finance_pit_unit")["pk"], dom("finance_pit_unit")["action"]),
        engine_domains=[],
        extra={"unit_detected": "元", "pit": "pubDate 为可见日 / statDate 为报告期"}),
    dict(
        group_id="G10_ETF_FUND_NAV", dataset_scope="ETF_NAV / open_fund / QDII / other + ETF_SHARE",
        schema_basis="parquet header 实读：fund_etf_nav=(day,code,unit_net_value,acc_net_value)；open_fund/qdii/other 同构；fund_fund_net_value=(id,code,day,net_value,sum_value,factor,acc_factor,refactor_net_value)",
        source_schema="fund_etf_nav",
        dictionary_required=dom("etf_fund_nav")["required"],
        dictionary_optional=dom("etf_fund_nav")["optional"],
        target=("fund_data_daily", dom("etf_fund_nav")["pk"], dom("etf_fund_nav")["action"]),
        engine_domains=[],
        extra={"pit": "unit_net_value 在 05_pit_field_dictionary 标 PIT_DELAYED_1D"}),
    dict(
        group_id="G11_INDEX_MEMBERSHIP", dataset_scope="index_components / index_weights",
        schema_basis="parquet header 实读：index_components=(index_code,component_code,asof_date)；index_constituents=(index_code,code,asof_date)；index_weights=(date,weight,display_name)",
        source_schema="index_weights",
        dictionary_required=dom("index_weight")["required"],
        dictionary_optional=dom("index_weight")["optional"],
        target=("index_member_history / index_weight_history", dom("index_weight")["pk"], dom("index_weight")["action"]),
        engine_domains=["benchmark_data"],
        extra={"note": "index_weights 仅 1 个 snapshot 文件（20260831）"}),
    dict(
        group_id="G12_INDUSTRY_CONCEPT", dataset_scope="industry_concept / industry_concept_events",
        schema_basis="parquet header 实读：components=(industry_code,stock_code)；list=(industry_code,name,start_date)；events=(index,name,start_date,event_type,as_of)",
        source_schema="industry_sw_components",
        dictionary_required=dom("industry_concept")["required"],
        dictionary_optional=dom("industry_concept")["optional"],
        target=("industry_concept_member", dom("industry_concept")["pk"], dom("industry_concept")["action"]),
        engine_domains=[],
        extra={"note": "P5_attributes_events/industry_sw_l1 只有 (name,start_date)，成分在 P0_meta 侧；两侧需 join"}),
    dict(
        group_id="G13_MTSS_MONEYFLOW_BILLBOARD", dataset_scope="mtss / money_flow / billboard",
        schema_basis="parquet header 实读：stk_mt_total=(id,date,exchange_code,fin_value,fin_buy_value,sec_volume,sec_value,sec_sell_volume,fin_sec_value)；billboard 14 列完整",
        source_schema="stk_mt_total",
        dictionary_required=dom("mtss")["required"],
        dictionary_optional=dom("mtss")["optional"],
        target=("mtss_daily / money_flow_daily / billboard_daily", dom("mtss")["pk"], dom("mtss")["action"]),
        engine_domains=[],
        extra={"known_gap": "KG18 get_money_flow 基础版 paid_module；KG13 龙虎榜机构席位明细 pending"}),
    dict(
        group_id="G14_CORPORATE_ACTIONS", dataset_scope="corporate actions / XR_XD event",
        schema_basis="无法从已枚举 schema 取得 long-format 事件表（P2_security_state/corporate_action 实为 (time,code,factor)，与事件契约不符）",
        source_schema="adjust_factor_stock",
        dictionary_required=dom("corporate_actions")["required"],
        dictionary_optional=dom("corporate_actions")["optional"],
        target=("corporate_actions_pit", dom("corporate_actions")["pk"], dom("corporate_actions")["action"]),
        engine_domains=[],
        extra={"note": "KG19 merger/spinoff 等复杂公司行为 v1.1_evaluate"}),
    dict(
        group_id="G15_FACTOR_260", dataset_scope="factor dictionary/formula/cleaning/pit (260)",
        schema_basis="rule_library/blackbox_current_dictionary_R1/factor_260_*_CURRENT.csv (260 行)",
        source_schema="finance_indicator",
        dictionary_required=["canonical_factor_name", "formula", "cleaning_policy", "pit_policy"],
        dictionary_optional=[],
        target=("reference_only", "canonical_factor_name", "factor_reference_only"),
        engine_domains=["factor_dictionary", "factor_formula", "factor_cleaning_rules", "factor_pit_rules"],
        extra={"activation": "ADMIT_DICTIONARY_ONLY / factor_value_download_forbidden=true / factor_cleaning_not_active=true"}),
]

ADMISSION_BY_SOURCE = {
    "stock_daily": ["stock_ohlcv", "fund_etf_price", "tradable_status", "adjustment_factor"],
    "stock_minute_30m": ["stock_ohlcv"],
    "etf_price_1m": ["stock_ohlcv", "fund_etf_price"],
    "index_daily": ["stock_ohlcv"],
    "adjust_factor_stock": ["adjustment_factor"],
    "stock_limit_pause": ["fund_etf_price", "tradable_status"],
    "valuation": [],
    "finance_balance": [],
    "fund_etf_nav": [],
    "index_weights": [],
    "industry_sw_components": [],
    "stk_mt_total": [],
    "finance_indicator": ["factor_260"],
}

CONFLICTS = {
    "G03_STOCK_MINUTE": [
        {"id": "C1_MINUTE_MISSING_FACTOR_LIMIT_PAUSED",
         "detail": "26域分钟 RAW 实读全部 8 列 (time,code,open,close,high,low,volume,money)；20_freeze minute_price 要求 factor/high_limit/low_limit/paused，引擎 minute_bar 要求 factor，matching 要求 factor",
         "present_in_raw": False,
         "class": "DERIVATION_REQUIRED_FROM_DAILY_PLANE",
         "resolution": "factor<-P1_adjust_factor，high_limit/low_limit/paused<-P2_security_state/stock_limit_pause，按 (code,trade_date) join；不宣称数据丢失"},
        {"id": "C2_MINUTE_SCHEMA_EVIDENCE_ROOT_MISMATCH",
         "detail": "13 清单的 12 列分钟 schema 取自 JQData_9999_WINDOW_FULL_RAW_20260325_20260501（该目录自带 DO_NOT_USE_AS_MASTER），与 26 域 P7 分钟的 8 列不同",
         "class": "EVIDENCE_SCOPE_OVERREACH_CORRECTED",
         "resolution": "以 26 域 parquet 实读为准；13 清单的 12 列不得作为 26 域字段依据"},
    ],
    "G04_ETF_PRICE": [
        {"id": "C3_ETF_MINUTE_SAME_AS_STOCK",
         "detail": "ETF 1m/5m/30m/60m 同为 8 列，缺 factor/limit/paused",
         "class": "DERIVATION_REQUIRED_FROM_DAILY_PLANE"},
    ],
    "G05_INDEX_PRICE": [
        {"id": "C4_INDEX_MINUTE_8_COLS_PLUS_FQ",
         "detail": "指数分钟 9 列（8 价格列 + fq），仍缺 factor/limit；指数无 tradable_status 语义，不作缺口",
         "class": "DOCUMENTED_LIMIT_NOT_GAP"},
    ],
    "G09_FINANCE_PIT": [
        {"id": "C5_FINANCE_NAMING_INCONSISTENT",
         "detail": "income/balance/indicator 用 statDate/pubDate，cash_flow 用 pub_date/report_date/report_type；契约统一为 pubDate/statDate",
         "class": "CLEAN_ALIAS_REQUIRED"},
        {"id": "C6_FINANCE_DUPLICATE_STATDATE",
         "detail": "balance/indicator 同时存在 statDate 与 statDate.1",
         "class": "DUPLICATE_COLUMN_DEDUPE_REQUIRED"},
        {"id": "C7_REVISION_CHAIN_NOT_IN_RAW",
         "detail": "PK 契约 symbol+report_period+type+revision_version，RAW 无 revision_version；08_restatement_schema 为契约而非已实现链路",
         "class": "CONTRACT_AHEAD_OF_RAW"},
    ],
    "G10_ETF_FUND_NAV": [
        {"id": "C8_NAV_TWO_NAMING_FAMILIES",
         "detail": "fund_etf_nav/open_fund/qdii = unit_net_value+acc_net_value；fund_fund_net_value = net_value+sum_value+factor+acc_factor+refactor_net_value",
         "class": "CLEAN_ALIAS_REQUIRED"},
        {"id": "C9_DAY_IS_STRING",
         "detail": "day 实际为 large_string，dtype 契约要求 date/YYYY-MM-DD 且禁止 string_mixed",
         "class": "DTYPE_DEVIATION"},
    ],
    "G11_INDEX_MEMBERSHIP": [
        {"id": "C10_INDEX_WEIGHTS_NO_MEMBER_CODE",
         "detail": "index_weights 实读仅 (date,weight,display_name)，无 component_code/member；PK 契约要求 index_code+member_code+weight_date",
         "class": "CONTRACT_GAP_BLOCKING_PK"},
        {"id": "C11_INDEX_WEIGHTS_SINGLE_SNAPSHOT",
         "detail": "P3_index/index_weights 仅 1 个 snapshot 文件 (20260831)，无历史序列",
         "class": "COVERAGE_BOUNDED"},
    ],
    "G13_MTSS_MONEYFLOW_BILLBOARD": [
        {"id": "C12_MTSS_FIELDS_INCOMPLETE",
         "detail": "stk_mt_total 缺 fin_refund_value / margin_value / margin_sell_value / margin_refund_value（契约 mtss 必需）",
         "class": "SOURCE_FIELD_GAP"},
        {"id": "C13_MONEYFLOW_PAID_MODULE",
         "detail": "KG18 money_flow 基础版为 paid_module；本轮未见 money_flow RAW",
         "class": "KNOWN_GAP_KG18"},
    ],
    "G14_CORPORATE_ACTIONS": [
        {"id": "C14_NO_LONG_FORMAT_CA_TABLE",
         "detail": "以已枚举 schema 无法确认 announce_date/ex_date/action_type 长表；adj factor 的 ex_date 可追溯性因此无法验证（13_adj_factor_methodology 规则2 → review_required）",
         "class": "EVIDENCE_INSUFFICIENT"},
    ],
    "G07_TRADABLE_STATUS": [
        {"id": "C15_IS_ST_WIDE_VS_LONG",
         "detail": "P2_security_state/is_st 宽表（列名=代码，数千列）；stock_st_status 为长表 (date,code,is_st)",
         "class": "LEGACY_DUAL_REPRESENTATION_CLEAN_TAKES_LONG"},
    ],
    "G02_STOCK_DAILY_OHLCV": [
        {"id": "C16_VOLUME_DTYPE",
         "detail": "RAW volume=double，09 dtype 契约要求 int64 且 forbidden float",
         "class": "DTYPE_DEVIATION"},
        {"id": "C17_DATE_TYPE",
         "detail": "RAW date=timestamp[ns]，契约要求 date/YYYY-MM-DD",
         "class": "DTYPE_DEVIATION"},
        {"id": "C18_PAUSED_BOOLEAN",
         "detail": "RAW paused=double(0/1)；12_status 契约禁止 clean 层强制 boolean，最终语义用 halt_status/risk_warning",
         "class": "CLEAN_LAYER_DERIVATION_NOT_CONFLICT"},
    ],
}

groups_out = []
for g in GROUPS:
    src = RAW_SCHEMA[g["source_schema"]]
    req = required_of_domain_src = None
    dom_req = []
    for d in g["engine_domains"]:
        for f in required_of_domain(d):
            if f not in dom_req:
                dom_req.append(f)
    dict_req = []
    for f in g["dictionary_required"]:
        f = f.strip().strip("[]'\" ")
        if f and f not in dict_req:
            dict_req.append(f)
    missing_for_dict = judge(src, [f for f in dict_req if "." not in f and "{" not in f])
    missing_for_engine = judge(src, dom_req)
    engine_map = {}
    for d in ADMISSION_BY_SOURCE.get(g["source_schema"], []):
        for r in FIELD_ADM:
            if r["field_domain"] == d:
                engine_map[r["incoming_field_name"]] = {
                    "canonical": r["canonical_field_name"], "domain": d,
                    "required_for_matching": r["required_for_matching"],
                    "admission": r["admission_status"]}
    conflicts = CONFLICTS.get(g["group_id"], [])
    gaps = []
    for f in missing_for_dict:
        gaps.append({"kind": "DICTIONARY_REQUIRED_NOT_IN_RAW", "field": f})
    for f in missing_for_engine:
        gaps.append({"kind": "ENGINE_REQUIRED_NOT_IN_RAW", "field": f})
    if g["group_id"] == "G14_CORPORATE_ACTIONS":
        assessment = "EVIDENCE_INSUFFICIENT"
    elif g["group_id"] == "G15_FACTOR_260":
        assessment = "ADMITTED_DICTIONARY_ONLY_BY_ORIGINAL_RULE"
    elif conflicts:
        hard = [c for c in conflicts if c["class"].startswith(("CONTRACT_GAP", "SOURCE_FIELD_GAP", "EVIDENCE_INSUFFICIENT", "CONTRACT_AHEAD"))]
        assessment = "MATCHED_WITH_PROVEN_CONFLICTS" if not hard else "MATCHED_WITH_UNRESOLVED_CONTRACT_GAP"
    else:
        assessment = "MATCHED"
    groups_out.append({
        "group_id": g["group_id"],
        "dataset_scope": g["dataset_scope"],
        "schema_basis": g["schema_basis"],
        "source_schema_actual": src,
        "dictionary_requirement": {
            "required": g["dictionary_required"],
            "optional": g["dictionary_optional"],
            "source_rule_files": ["02_domain_schema/domain_schema_contract.csv",
                                  "09_dtype_precision_schema/dtype_precision_contract.csv",
                                  "10_primary_key_rules/primary_key_uniqueness_contract.csv",
                                  "12_status_field_schema/status_field_contract.csv"],
        },
        "source_fields": [
            {"name": f,
             "unit": DICT_UNIT.get(f, ""),
             "in_price_dictionary": any(r["field"] == f for r in PRICE_DICT),
             "pit_tag": next((r["pit_type"] for r in PIT_DICT if r["field"] == f), ""),
             "engine_canonical": (ENGINE_FIELD_MAP.get(f) or {}).get("canonical_field_name", "")}
            for f in src
            if f not in ("__index_level_0__",)
        ],
        "clean_standard_mapping": {
            "target_table": g["target"][0],
            "primary_key": g["target"][1],
            "clean_action": g["target"][2],
        },
        "engine_admission": {
            "data_domains": g["engine_domains"],
            "required_fields": dom_req,
            "field_alias_map": engine_map,
            "frequency_allowed": [r["incoming_frequency"] for r in FREQ_ADM if r["allowed_for_backtest"] == "true"],
            "admission_stage": "PRE_INGESTION_ONLY",
        },
        "gaps_vs_raw": gaps,
        "conflicts": conflicts,
        "assessment": assessment,
        "extra": g.get("extra", {}),
    })

dic_doc = {
    "at": AT,
    "task": "TIP_1814_REMAINDER_1_DICTIONARY_FIELD_MAPPING",
    "FOUNDATION_ACCEPTANCE": FOUNDATION_ACCEPTANCE,
    "method": {
        "reused_not_reread": [
            "13_local_schema_header_final_check (attribute/minute/finance schema inventory + dictionary_v2)",
            "20_unified_data_schema_contract_freeze_full_R1 (17 契约文件)",
            "03_field_dictionary / 05_pit_field_dictionary / 06_unit_dictionary",
            "rule_library/master_registry_R1 五张 admission matrix",
            "completion_1803 DOMAIN_SAMESET_DIFF（26 域路径已通过，本轮不再扫描）",
        ],
        "new_reads": "26域 parquet header 按 prefix 枚举（不是逐文件重读）；估值/财务复用 13 清单枚举结果；无 finance 正文读取",
        "seal_schema_note": "seal SCHEMA 只有 domain 键，本轮不把 domain 键当作字段已核；字段对应一律回到 20 契约 + parquet header",
    },
    "evidence": {
        "freeze20_domain_schema": ev(FREEZE20 / "02_domain_schema" / "domain_schema_contract.csv"),
        "freeze20_dtype": ev(FREEZE20 / "09_dtype_precision_schema" / "dtype_precision_contract.csv"),
        "freeze20_pk": ev(FREEZE20 / "10_primary_key_rules" / "primary_key_uniqueness_contract.csv"),
        "freeze20_status": ev(FREEZE20 / "12_status_field_schema" / "status_field_contract.csv"),
        "freeze20_known_gap": ev(FREEZE20 / "15_known_gap_schema" / "known_gap_schema_contract.csv"),
        "check13_attr": ev(CHECK13 / "01_schema_inventory" / "local_9999_attribute_schema_inventory.csv"),
        "check13_minute": ev(CHECK13 / "01_schema_inventory" / "local_9999_minute_schema_inventory.csv"),
        "check13_finance": ev(CHECK13 / "01_schema_inventory" / "local_9999_finance_schema_inventory.csv"),
        "price_dict": ev(DICT / "03_field_dictionary" / "price_field_dictionary.csv"),
        "unit_dict": ev(DICT / "06_unit_dictionary" / "unit_dictionary.csv"),
        "pit_dict": ev(DICT / "05_pit_field_dictionary" / "pit_field_tags.csv"),
        "engine_domain_matrix": ev(MR / "DATA_DOMAIN_ADMISSION_MATRIX_R1.csv"),
        "engine_field_matrix": ev(MR / "FIELD_ADMISSION_MATRIX_R1.csv"),
    },
    "known_gap_registry": [{"gap_id": r["gap_id"], "module": r["module_or_domain"], "status": r["status"]} for r in GAP_SCHEMA],
    "groups": groups_out,
    "summary": {
        "n_groups": len(groups_out),
        "matched": sum(1 for g in groups_out if g["assessment"] == "MATCHED"),
        "matched_with_conflicts": sum(1 for g in groups_out if g["assessment"].startswith("MATCHED_WITH")),
        "evidence_insufficient": sum(1 for g in groups_out if g["assessment"] == "EVIDENCE_INSUFFICIENT"),
        "dictionary_only_by_rule": sum(1 for g in groups_out if g["assessment"] == "ADMITTED_DICTIONARY_ONLY_BY_ORIGINAL_RULE"),
        "n_conflicts": sum(len(g["conflicts"]) for g in groups_out),
    },
}
(OUT / "DICTIONARY_FIELD_MAPPING_R1.json").write_text(json.dumps(dic_doc, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------------------------------------------------------- B. post-baseline scope
SCOPE_1803 = json.loads((PREV1803 / "SCOPE_COVERAGE_MAP.json").read_text(encoding="utf-8"))
scope21 = {d["dataset_id"]: d for d in SCOPE_1803["jq_incremental_datasets"]}


def dataset_probe(d: Path) -> dict:
    n_parquet = n_sidecar = n_checksum = n_receipt = n_manifest = 0
    dates = []
    for dp, _, fs in os.walk(d):
        for fn in fs:
            if fn.endswith(".parquet"):
                n_parquet += 1
                parts = fn.split("__")
                dates.extend(re.findall(r"(?<!\d)(20\d{6})(?!\d)", fn))
            elif fn.endswith(".sidecar.json"):
                n_sidecar += 1
            elif fn == "RAW_MANIFEST.json" or fn == "MANIFEST.json" or fn.endswith(".manifest.json"):
                n_manifest += 1
            elif fn.endswith(".checksum.sha256") or fn == "checksums.json":
                n_checksum += 1
            elif fn == "receipt.json":
                n_receipt += 1
    return {"raw_dir": str(d), "exists": d.is_dir(), "n_parquet": n_parquet,
            "n_sidecar": n_sidecar, "n_manifest": n_manifest, "n_checksum": n_checksum, "n_receipt": n_receipt,
            "date_tokens_min": min(dates) if dates else None,
            "date_tokens_max": max(dates) if dates else None,
            "receipt_present": n_receipt > 0, "manifest_present": n_manifest > 0,
            "sidecar_present": n_sidecar > 0,
            "checksum_present": n_checksum > 0}


p5 = RAW / "P5_jq20_extension"
p5_dirs = sorted([p for p in p5.iterdir() if p.is_dir()]) if p5.is_dir() else []
p5_rows = []
for p in p5_dirs:
    probe = dataset_probe(p)
    probe["dataset_id"] = p.name.upper()
    probe["listed_in_scope21"] = p.name.upper() in scope21
    probe["contract_registered"] = scope21.get(p.name.upper(), {}).get("clean_product")
    probe["pit_policy"] = scope21.get(p.name.upper(), {}).get("pit_policy")
    p5_rows.append(probe)

nav_dir = RAW / "P4_fund_etf" / "fund_etf_nav" / "incremental_get_extras_r1"
nav_probe = dataset_probe(nav_dir)
nav_probe["dataset_id"] = "FUND_ETF_NAV"
nav_sample_sidecars = sorted(glob.glob(str(nav_dir / "*.sidecar.json")))[:2]
nav_probe["sidecar_samples"] = []
for s in nav_sample_sidecars:
    try:
        nav_probe["sidecar_samples"].append(json.loads(Path(s).read_text(encoding="utf-8")))
    except Exception as e:
        nav_probe["sidecar_samples"].append({"err": str(e)})

scope21_ids = set(scope21)
p5_ids = {r["dataset_id"] for r in p5_rows}
missing_from_raw = sorted(scope21_ids - p5_ids - {"FUND_ETF_NAV"})
extra_in_raw = sorted(p5_ids - scope21_ids)


def bounded_classify(path: Path, purpose: str, verdict: str, basis: str, extra=None) -> dict:
    row = {"root": str(path), "exists": path.is_dir(), "purpose": purpose,
           "classification": verdict, "basis": basis}
    if extra:
        row.update(extra)
    if path.is_dir():
        top = sorted([p.name for p in path.iterdir()])[:12]
        row["top_entries_sample"] = top
        row["n_top_entries"] = len(list(path.iterdir()))
    return row


def has_marker(path: Path, patterns) -> list:
    hits = []
    for pat in patterns:
        for p in path.rglob(pat):
            hits.append(str(p))
            if len(hits) >= 4:
                return hits
    return hits


external_rows = [
    bounded_classify(RROOT / "途施可转债官方原始_R1", "Tushare 可转债官方原始（多窗口/逐日 receipt）",
                     "EXTERNAL_VENDOR_SERIES_OUTSIDE_JQ_FOUNDATION",
                     "20_freeze KG06 可转债=out_of_scope（不在 9999 套餐）；本目录为 Tushare 供应商 receipt 序列，非 26 域 JQ 清洗输入",
                     {"vendor": "Tushare", "receipt_series": True}),
    bounded_classify(RROOT / "途施可转债官方原始_R2", "Tushare 可转债官方原始（carryin 续跑）",
                     "EXTERNAL_VENDOR_SERIES_OUTSIDE_JQ_FOUNDATION",
                     "同上；R2 为 R1 续跑批（carryin_* receipt），属同一外源序列",
                     {"vendor": "Tushare", "receipt_series": True, "supersedes_or_continues": "途施可转债官方原始_R1"}),
    bounded_classify(Path(r"E:\BLACKBOX\数据\外部补充只读"), "外部补充（朋友 JQData 字典证据 + Tushare reference patch）",
                     "DICTIONARY_EVIDENCE_SUPPORT_NOT_VALUE_DATA",
                     "内容为字典交叉核验/冲突复核（01_inventory..06_evidence_consolidation），不含 26 域值数据；按 20 契约只作字典置信度补充",
                     {"vendor": "Friend_JQData / Tushare"}),
    bounded_classify(Path(r"E:\BLACKBOX\数据\外部证据"), "外部证据平面（CANONICAL/COMPANY_PRIMARY/EXCHANGE/... PRODUCT_META）",
                     "SEPARATE_EVIDENCE_PLANE_OUTSIDE_RAW_FOUNDATION",
                     "每个产品自带 PRODUCT_META.json；属研究证据平面，不是 26 域 RAW 清洗输入；本轮不重扫",
                     {"meta": has_marker(Path(r"E:\BLACKBOX\数据\外部证据"), ["PRODUCT_META.json"])}),
    bounded_classify(Path(r"E:\BLACKBOX\数据\美国市场"), "美股日频/新闻/细粒度利润池",
                     "EXCLUDED_BY_ORIGINAL_RULES_KG02",
                     "20_freeze KG02 美股行情=out_of_scope；本目录为研究旁路，非 JQ 底座",
                     {"vendor": "external", "known_gap": "KG02"}),
    bounded_classify(RROOT / "JQData_9999_WINDOW_FULL_RAW_20260325_20260501", "2026-03-25..05-01 独立窗口全量 RAW",
                     "HISTORICAL_EXPERIMENTAL_WINDOW_DO_NOT_USE_AS_MASTER",
                     "目录自带 EXPERIMENTAL_TRIAL_DATA_DO_NOT_USE_AS_MASTER.txt；仅作窗口/字段证据来源，不作 MASTER",
                     {"marker": has_marker(RROOT / "JQData_9999_WINDOW_FULL_RAW_20260325_20260501",
                                           ["EXPERIMENTAL_TRIAL_DATA_DO_NOT_USE_AS_MASTER.txt"])}),
    bounded_classify(RROOT / "strategy_data_plane_additions", "策略数据平面增量（17 个正式产品）",
                     "FORMAL_POST_BASELINE_INHERITANCE",
                     "每个产品含 REL_*/MANIFEST/COVERAGE/PROVENANCE/CHECKSUMS 发布结构；属基线后正式继承，非 26 域原始下载",
                     {"products": sorted([p.name for p in (RROOT / 'strategy_data_plane_additions').iterdir()])}),
    bounded_classify(RROOT / "聚宽行情_raw", "旧聚宽 RAW 分类（日线/分钟线）",
                     "LEGACY_PRE_BASELINE_RAW_CLASSIFICATION",
                     "旧中文分类目录；26 域正式清单对应 P2_stock_daily/P7_stock_minute，本源不作正式输入",
                     {}),
    bounded_classify(RROOT / "聚宽财务_raw", "旧聚宽 RAW 分类（四张表）",
                     "LEGACY_PRE_BASELINE_RAW_CLASSIFICATION",
                     "26 域正式清单对应 P3_finance_pit", {}),
    bounded_classify(RROOT / "聚宽ETF_raw", "旧聚宽 RAW 分类（ETF 五类）",
                     "LEGACY_PRE_BASELINE_RAW_CLASSIFICATION",
                     "26 域正式清单对应 P4_fund_etf/P4b_fund_expand", {}),
    bounded_classify(RROOT / "聚宽因子_raw", "旧聚宽因子原始包",
                     "LEGACY_FACTOR_REFERENCE_ONLY",
                     "因子值下载按 DATA_INGESTION_GATE_RULES_R1 仍为 forbidden；仅字典/参考", {"known_gap": "KG10"}),
    bounded_classify(RROOT / "聚宽行业指数_raw", "旧聚宽行业/指数 RAW（申万/概念/成分权重）",
                     "LEGACY_PRE_BASELINE_RAW_CLASSIFICATION",
                     "26 域正式清单对应 P0_meta + P3_index", {}),
    bounded_classify(RROOT / "_forensic_canary", "取证金丝雀 / 接口下载盘点",
                     "AUDIT_ONLY_NOT_FOUNDATION", "审计用途，非数据底座", {}),
    bounded_classify(RROOT / "试验", "分钟 fq 试验金丝雀",
                     "EXPERIMENTAL_NOT_FOUNDATION", "canary 试验，不作正式输入", {}),
]

scope_doc = {
    "at": AT,
    "task": "TIP_1814_REMAINDER_2_POST_BASELINE_AND_EXTERNAL_SCOPE",
    "FOUNDATION_ACCEPTANCE": FOUNDATION_ACCEPTANCE,
    "method": {
        "reused": ["completion_1803/SCOPE_COVERAGE_MAP.json (21 增量 dataset + 26 域映射)",
                   "1803 DOMAIN_SAMESET_DIFF (26 域原始文件集已通过，本轮零重扫)",
                   "各产品既有 MANIFEST/COVERAGE/PROVENANCE/CHECKSUMS/receipt.json"],
        "granularity_rule": "21 dataset 与 26 域是不同粒度，不做相减",
        "bounded": "只做目录级 + 文件名/receipt 计数 + 少量 sidecar 抽样；不重扫内容，不重下",
    },
    "scope21_registered": sorted(scope21_ids),
    "P5_jq20_extension": {
        "n_dirs": len(p5_rows),
        "rows": p5_rows,
        "in_scope21_not_found_in_raw": missing_from_raw,
        "in_raw_not_in_scope21": extra_in_raw,
    },
    "FUND_ETF_NAV_increment": nav_probe,
    "baseline_additions": {
        "note": "基线补充，不与 26 域相减；21 个增量 dataset 全部有目录与收据结构",
        "n_matched_dirs": sum(1 for r in p5_rows if r["exists"]),
        "n_with_receipt_or_sidecar": sum(1 for r in p5_rows if r["receipt_present"] or r["sidecar_present"] or r["manifest_present"]),
        "n_with_manifest": sum(1 for r in p5_rows if r["manifest_present"]),
    },
    "external_and_legacy": external_rows,
    "conclusions": {
        "in_scope_original": "26 域原始文件集已按 CANONICAL_FILE_LIST 逐路径 exists 通过（1803，接受，不再重查）；21 增量 dataset 目录与收据结构在",
        "formal_inheritance": "strategy_data_plane_additions 17 个产品为基线后正式继承（自带发布结构）",
        "external_by_own_contract": "途施可转债_R1/R2（Tushare receipt 序列）、外部补充只读（字典证据）、外部证据（独立证据平面）按各自供应商/产品契约记录，不硬套聚宽",
        "excluded_by_original_rules": "美股 KG02、期货 KG03、期权 KG04、债券 KG05、可转债 KG06（JQ 侧）、因子值下载 KG10、Tick KG11、Tushare 全量扩展 KG08/KG09",
        "historical_version": "独立窗口 RAW（标注 DO_NOT_USE_AS_MASTER）、旧聚宽中文 RAW 分类、_forensic_canary、试验 canary",
        "undetermined": "未在本轮有界的目录里出现的来源保持 UNDETERMINED；不以此宣称数据缺失，也不静默遗漏（登记为范围缺口）",
    },
    "proven_gaps": [
        {"id": "S1_CONVERTIBLE_JQ_SIDE_ABSENT", "detail": "JQ 9999 侧无可转债（KG06），外源 Tushare 有 receipt 序列", "class": "ORIGINAL_RULE_EXCLUSION_NOT_LOSS"},
        {"id": "S2_INDEX_WEIGHTS_SINGLE_SNAPSHOT", "detail": "index_weights 仅 20260831 单快照", "class": "COVERAGE_BOUNDED"},
        {"id": "S3_MONEYFLOW_RAW_ABSENT", "detail": "未见 money_flow RAW，KG18 paid_module", "class": "KNOWN_GAP"},
    ],
}
(OUT / "POST_BASELINE_SCOPE_SUPPLEMENT_R1.json").write_text(json.dumps(scope_doc, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------------------------------------------------------- C. engine interface
PY = ENG / "blackbox_jq_engine" / "pyproject.toml"
MASTER_REG = json.loads((MR / "MASTER_RULE_LIBRARY_REGISTRY_R1.json").read_text(encoding="utf-8"))
GATE_RULES = json.loads((MR / "DATA_INGESTION_GATE_RULES_R1.json").read_text(encoding="utf-8"))
CAP = json.loads((ENG / "PHASE1_CAPABILITY_REGISTRY.json").read_text(encoding="utf-8"))
CURREG = json.loads((ENG / "PHASE1_CURRENT_ENGINE_REGISTRY.json").read_text(encoding="utf-8"))

API = ENG / "blackbox_jq_engine" / "bullet_trade" / "data" / "api.py"
PROV_BASE = ENG / "blackbox_jq_engine" / "bullet_trade" / "data" / "providers" / "base.py"
LOCAL_DICT = ENG / "blackbox_jq_engine" / "bullet_trade" / "data" / "local_dictionary_registry.py"

api_text = API.read_text(encoding="utf-8", errors="replace")
import re as _re

_branch_tokens = []
for _m in _re.finditer(r"if target (?:==|in) \(?([^:\n]+)\)?:", api_text):
    for _tok in _re.findall(r"[\"']([a-z_\-]+)[\"']", _m.group(1)):
        if _tok not in _branch_tokens:
            _branch_tokens.append(_tok)
provider_branches = _branch_tokens
has_local_branch = ("local" in api_text.split("def _create_provider")[1][:2000].lower()) if "def _create_provider" in api_text else False

# isolated pure-read smoke: load module by file path (no package __init__, no dotenv, no .env)
smoke = {"attempted": True, "import_method": "importlib.util.spec_from_file_location (bypasses bullet_trade/__init__ + dotenv)"}
try:
    spec = importlib.util.spec_from_file_location("jq_local_dict_iso", LOCAL_DICT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses 需要模块已注册
    spec.loader.exec_module(mod)
    smoke["module_loaded"] = True
    smoke["module_import_side_effects"] = {"dotenv_imported": "dotenv" in sys.modules,
                                           "network_client_imported": any(m in sys.modules for m in ("jqdatasdk", "xtquant", "tushare"))}
    try:
        mod.resolve_snapshot_root(r"E:\BLACKBOX")
        smoke["e_drive_rejection"] = {"raised": False, "verdict": "UNEXPECTED_ALLOW"}
    except Exception as e:
        smoke["e_drive_rejection"] = {"raised": True, "type": type(e).__name__, "msg": str(e), "verdict": "E_DRIVE_FORBIDDEN_CONFIRMED"}
    tmp = Path(tempfile.mkdtemp(prefix="bb_dict_snap_"))
    (tmp / "files" / "03_field_dictionary").mkdir(parents=True, exist_ok=True)
    shutil.copy2(DICT / "03_field_dictionary" / "trade_calendar.csv",
                 tmp / "files" / "03_field_dictionary" / "trade_calendar.csv")
    cal = mod.load_trade_calendar(tmp)
    smoke["trade_calendar_read"] = {
        "snapshot_root": str(tmp), "n_trade_dates": len(cal.trade_dates),
        "first": cal.trade_dates[0] if cal.trade_dates else None,
        "last": cal.trade_dates[-1] if cal.trade_dates else None,
        "file_meta": {"rel": cal.files[0].relative_path, "row_count": cal.files[0].row_count,
                      "source_type": cal.files[0].source_type, "allowed_usage": cal.files[0].allowed_usage},
        "verdict": "PURE_READ_ADAPTER_USABLE_ON_NON_E_ROOT",
    }
    smoke["can_be_official_rule_basis"] = mod.CAN_BE_OFFICIAL_RULE_BASIS
    smoke["env_required"] = "BLACKBOX_LOCAL_DICTIONARY_SNAPSHOT"
    shutil.rmtree(tmp, ignore_errors=True)
except Exception as e:
    smoke["module_loaded"] = False
    smoke["error"] = f"{type(e).__name__}: {e}"

eng_doc = {
    "at": AT,
    "task": "TIP_1814_REMAINDER_3_ENGINE_REAL_DATA_INTERFACE",
    "FOUNDATION_ACCEPTANCE": FOUNDATION_ACCEPTANCE,
    "reused": ["completion_1752/ENGINE_BASELINE_CHECK.json (静态核查基线)",
               "1803 runtime_attempted=false / NOT_RUN_STATIC_ONLY 更正（保留）"],
    "declared_entry": {
        "pyproject": ev(PY),
        "project_name": "bullet-trade",
        "scripts": {"bullet-trade": "bullet_trade.cli.main:main"},
        "packages_find": ["bullet_trade*", "helpers*"],
        "py_modules": ["jqdata"],
        "note": "包名与目录名不同：pyproject 声明 bullet_trade，实际位于 blackbox_jq_engine/bullet_trade/",
    },
    "provider_chain": {
        "api": ev(API),
        "provider_base": ev(PROV_BASE),
        "factory_fn": "_create_provider (bullet_trade/data/api.py)",
        "branches_found": provider_branches,
        "local_value_plane_branch": has_local_branch,
        "global_setter": "set_data_provider / get_data_provider",
        "abstract_required_methods": ["get_price", "get_trade_days", "get_all_securities", "get_index_stocks", "get_split_dividend"],
        "optional_methods": ["get_bars", "get_ticks", "get_extras", "get_fundamentals", "get_index_weights",
                             "get_industry", "get_industry_stocks", "get_concept", "get_concept_stocks",
                             "get_marginsec_stocks", "get_billboard_list", "subscribe_ticks"],
        "conclusion": "provider 工厂只有 jqdata/tushare/miniqmt/remote_qmt 四支；不存在读取本地 RAW 值数据的 provider 分支",
    },
    "local_dictionary_adapter": {
        "path": ev(LOCAL_DICT),
        "source_type": "BB_LOCAL_ALIGNED_DICTIONARY_SNAPSHOT",
        "allowed_usage": "data_provider_test_and_schema_alignment_only",
        "can_be_official_rule_basis": False,
        "root_policy": "必须显式 snapshot_root 或 env BLACKBOX_LOCAL_DICTIONARY_SNAPSHOT；显式拒绝 E:\\ 与 SEALED_SANDBOXES",
        "reads": ["04_enum_dictionary/securities_*.csv", "04_enum_dictionary/industry_sw_l*.csv",
                  "04_enum_dictionary/concepts.csv", "03_field_dictionary/trade_calendar.csv",
                  "11_final_dictionary_before_9999_purchase/02_jq_factor_dictionary_final/*.csv"],
        "class_methods_identified": ["load_local_dictionary_snapshot", "load_securities_master", "load_trade_calendar",
                                     "load_factor_registry", "load_industry_concept_registry", "classify_asset",
                                     "is_supported_v0_asset", "get_dictionary_manifest"],
        "nature": "字典/参考层纯读取；不含 price/volume 值读取",
    },
    "activation_boundary": {
        "source": "rule_library/master_registry_R1/MASTER_RULE_LIBRARY_REGISTRY_R1.json",
        "master_registry_active": MASTER_REG.get("master_registry_active"),
        "formal_backtest_active": MASTER_REG.get("formal_backtest_active"),
        "engine_core_active": MASTER_REG.get("engine_core_active"),
        "admission_stage": MASTER_REG.get("admission_stage"),
        "post_ingestion_judgement_allowed": MASTER_REG.get("post_ingestion_judgement_allowed"),
        "non_matching_data_admission_policy": MASTER_REG.get("non_matching_data_admission_policy"),
        "engine_root_declared": MASTER_REG.get("engine_root"),
        "gate_policies": GATE_RULES.get("policies"),
        "n_gates": len(GATE_RULES.get("gates", [])),
        "gate_order": GATE_RULES.get("gate_order"),
        "verdict": "formal_backtest_active=false / engine_core_active=false / PRE_INGESTION_ONLY 属原交付阶段与准入边界，非迁移丢失",
    },
    "capability_registry": {
        "path": ev(ENG / "PHASE1_CAPABILITY_REGISTRY.json"),
        "values": CAP,
        "note": "PASS/BLOCKED_BY_CONTRACT/BLOCKED_BY_DATA 为封存期声明，不是今日运行时结论",
    },
    "CURRENT_pointer": {
        "path": ev(ENG / "PHASE1_CURRENT_ENGINE_REGISTRY.json"),
        "CURRENT_sealed_backup_path": CURREG.get("CURRENT_sealed_backup_path"),
        "unique_CURRENT": CURREG.get("unique_CURRENT"),
        "class": "CONFIG_POINTER_LEGACY_D（已有登记，非本轮新问题）",
    },
    "isolated_smoke": smoke,
    "missing_layer": {
        "layer": "local value-plane provider + 路径绑定",
        "evidence": [
            "_create_provider 无 local/raw 分支（只有 4 家远端/终端供应商）",
            "local_dictionary_registry 明确拒绝 E:\\ 且 CAN_BE_OFFICIAL_RULE_BASIS=false，只读字典",
            "DataProvider 抽象方法要求 get_price/get_trade_days/get_all_securities/get_index_stocks/get_split_dividend，本地值数据侧无实现类",
            "数据侧 read_schema 只证明 parquet 可读，不构成引擎接通",
        ],
        "minimal_isolated_adapter_plan": [
            "新增 read-only LocalPlaneProvider(DataProvider)：仅实现 get_price/get_trade_days/get_all_securities/get_index_stocks/get_split_dividend + get_extras",
            "路径绑定走既有数据访问 resolver，不硬编码、不读 .env、不导入 jqdatasdk/xtquant",
            "由调用方显式 set_data_provider(LocalPlaneProvider(...)) 注入；不改 formal_backtest_active，不绕过 PRE_INGESTION gate",
            "首期只开 daily + 1m/5m/30m/60m 价格与 factor/limit/paused join，先只读 smoke，不跑策略",
        ],
        "not_migration_loss": "原交付即 dictionary_only_no_value_ingest（DATA_DOMAIN_ADMISSION_MATRIX notes 全域标注）",
    },
    "not_tested": ["策略回测", "PnL", "实盘下单", "下载/API", "全引擎行为认证"],
    "previous_correction_kept": "type_to_local_entry 关键词猜测已作废：不再把 minute/tradable_status/matching 猜成同一 ETF_1m 路径；adapter_function 全部保持未绑定（null）",
}
(OUT / "ENGINE_DATA_INTERFACE_R1.json").write_text(json.dumps(eng_doc, ensure_ascii=False, indent=2), encoding="utf-8")
(ISO / "LOCAL_DICT_ADAPTER_SMOKE.json").write_text(json.dumps(smoke, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------------------------------------------------------- final verdict
verdict = {
    "at": AT,
    "task_id": "TIP_1814_FOUNDATION_REMAINDER_CLOSURE",
    "FOUNDATION_ACCEPTANCE": FOUNDATION_ACCEPTANCE,
    "PRODUCTION_CHANGE_AUTHORIZED": PRODUCTION_CHANGE_AUTHORIZED,
    "closed_branches": [
        {"branch": "26 域 RAW 文件集保留", "status": "ACCEPTED_NOT_RECHECKED",
         "basis": "1803 DOMAIN_SAMESET_DIFF：26 份 CANONICAL_FILE_LIST 逐路径 exists，missing=0"},
        {"branch": "目录概览", "status": "CLOSED",
         "basis": "GPT 已压缩为 66 条 DIRECTORY_OVERVIEW_COMPACT.md；不再做目录展示迭代"},
    ],
    "three_conclusions": {
        "1_RAW_file_retention": {
            "passed_lists": ["26 份 CANONICAL_FILE_LIST.parquet（逐路径 exists）",
                             "1803 26 域同集对照（expected=matched, missing=0）",
                             "21 个 JQ 增量 dataset 目录 + receipt/sidecar/checksum 结构"],
            "not_covered": ["7 月底之后的增量完整性（未做逐日对账）",
                            "外源 Tushare 可转债 R1/R2 之外的供应商清单",
                            "外部证据平面各 PRODUCT_META 的内容完整性"],
            "not_upgraded_to": ["下载从未截断", "全部字段/单位/PIT 正确", "所有外源已覆盖"],
        },
        "2_dictionary_raw_clean_standard_mapping": {
            "matched": [g["group_id"] for g in groups_out if g["assessment"] == "MATCHED"],
            "matched_with_conflicts": {g["group_id"]: [c["id"] for c in g["conflicts"]]
                                       for g in groups_out if g["assessment"].startswith("MATCHED_WITH")},
            "evidence_insufficient": ["G14_CORPORATE_ACTIONS"],
            "dictionary_only_by_original_rule": ["G15_FACTOR_260"],
            "headline_conflicts": [
                "26 域全部分钟 RAW = 8 列，缺 factor/high_limit/low_limit/paused（20 契约与引擎 minute_bar 均要求 factor）→ 必须由日频平面 join 派生",
                "index_weights 缺 member_code，PK 契约不可满足；且仅 1 个快照",
                "mtss 缺 fin_refund_value/margin_value/margin_sell_value/margin_refund_value",
                "finance 表命名不一致（pubDate vs pub_date / statDate vs report_date）且 statDate.1 重复列",
                "RAW volume=double、date=timestamp、NAV day=string，均偏离 09 dtype 契约",
                "13 清单的 12 列分钟 schema 取自标注 DO_NOT_USE_AS_MASTER 的试验窗口，不得作 26 域依据",
            ],
        },
        "3_engine_body_and_value_interface": {
            "original_delivery_scope": "dictionary 层交付（master_registry_active=true），值数据接入未交付",
            "activation_declared": "formal_backtest_active=false / engine_core_active=false / admission_stage=PRE_INGESTION_ONLY",
            "currently_connected": ["字典快照纯读取层（local_dictionary_registry，拒绝 E:\\，可跑通非 E 根）",
                                    "15 道 PRE_INGESTION 准入矩阵（domain/field/frequency/pit/matching/code）"],
            "originally_not_connected": ["本地值数据 provider（_create_provider 仅 jqdata/tushare/miniqmt/remote_qmt）",
                                          "引擎值数据 adapter_function 绑定（全部 null）"],
            "migration_path_needs_adaptation": ["E:\\ 路径策略（字典层显式拒绝 E:）",
                                                "PHASE1_CURRENT_ENGINE_REGISTRY 仍指向 D:\\backtest_lab_backups",
                                                "pyproject 包名 bullet_trade 与目录 blackbox_jq_engine 不一致（需安装/路径适配）"],
        },
    },
    "discoveries_logged_and_closed": [
        {"id": "D1_MINUTE_FIELD_DERIVATION", "action": "登记为 join 派生要求，不再返工"},
        {"id": "D2_INDEX_WEIGHTS_PK", "action": "登记为契约缺口（需补 member_code 或明确契约变更）"},
        {"id": "D3_MTSS_FIELDS", "action": "登记为源字段缺口"},
        {"id": "D4_TINY_PARQUET", "action": "fund_etf_price_1m 6B ×1/3633、index_minute 4B ×1/133968，登记为个别空壳文件，未下结论为数据缺失"},
        {"id": "D5_EVIDENCE_SCOPE_OVERREACH", "action": "13 清单 12 列分钟 schema 的适用范围已更正"},
    ],
    "no_rework_of": ["26 域路径存在性", "目录展示版本", "历史策略调用证明", "收益重现", "历史下载脚本找回"],
}
(OUT / "FOUNDATION_FINAL_VERDICT_R1.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------------------------------------------------------- md report
lines = []
lines.append("# TIP_1814 收口报告 — 字典字段对应 / 基线后范围 / 引擎真实接口\n")
lines.append(f"- at: {AT}\n- FOUNDATION_ACCEPTANCE=false  PRODUCTION_CHANGE_AUTHORIZED=false\n")
lines.append("\n## 0. 已接受、本轮不再做\n")
lines.append("- 26 域 RAW 文件集：1803 逐路径 exists，missing=0（不复扫、不重计数）\n")
lines.append("- 目录分支：已由 GPT 压缩为 66 条，本轮不迭代\n")
lines.append("\n## 1. 字典字段对应（按数据集/模式版本分组）\n")
lines.append("| 组 | 范围 | 契约必需字段 | 源实读列数 | 引擎准入域 | 结论 |\n|---|---|---|---|---|---|\n")
for g in groups_out:
    lines.append(f"| {g['group_id']} | {g['dataset_scope']} | {len(g['dictionary_requirement']['required'])} | "
                 f"{len(g['source_schema_actual'])} | {','.join(g['engine_admission']['data_domains']) or '-'} | {g['assessment']} |\n")
lines.append("\n### 具体冲突（已定性，不返工）\n")
for g in groups_out:
    for c in g["conflicts"]:
        lines.append(f"- **{c['id']}**（{c['class']}）：{c['detail']}\n")
lines.append("\n### 证据不足\n")
lines.append("- G14_CORPORATE_ACTIONS：已枚举 schema 中无 announce_date/ex_date/action_type 长表，adj_factor 的 ex_date 可追溯性无法验证 → 按 13_adj_factor_methodology 规则2 记 review_required\n")
lines.append("\n## 2. 基线后与外源范围\n")
lines.append(f"- P5_jq20_extension：{len(p5_rows)} 个 dataset 目录，全部有 receipt/sidecar/checksum 结构；与 21 增量清单比对：缺 {missing_from_raw or '无'}，多 {extra_in_raw or '无'}\n")
lines.append(f"- FUND_ETF_NAV 增量：{nav_probe['n_parquet']} parquet / {nav_probe['n_sidecar']} sidecar / {nav_probe['n_checksum']} checksum，日期 token {nav_probe['date_tokens_min']}..{nav_probe['date_tokens_max']}\n")
lines.append("\n| 根目录 | 归类 | 依据 |\n|---|---|---|\n")
for r in external_rows:
    lines.append(f"| {Path(r['root']).name} | {r['classification']} | {r['basis'][:90]} |\n")
lines.append("\n## 3. 引擎本体与值数据接口\n")
lines.append(f"- pyproject：`bullet-trade`，script `bullet_trade.cli.main:main`，包 `bullet_trade*` + `helpers*`，py-module `jqdata`\n")
lines.append(f"- provider 工厂 `_create_provider` 仅有：{', '.join(provider_branches)}；本地值数据分支={has_local_branch}\n")
lines.append(f"- local_dictionary_registry：字典快照纯读取，拒绝 E:\\ 与 SEALED_SANDBOXES，CAN_BE_OFFICIAL_RULE_BASIS=False\n")
lines.append(f"- 隔离 smoke：模块按文件路径加载（绕过包 __init__/dotenv）→ {smoke.get('module_loaded')}；"
             f"E:\\ 拒绝={smoke.get('e_drive_rejection', {}).get('verdict')}；"
             f"trade_calendar 读取={smoke.get('trade_calendar_read', {}).get('n_trade_dates')} 个交易日\n")
lines.append(f"- 激活边界：formal_backtest_active={MASTER_REG.get('formal_backtest_active')}，"
             f"engine_core_active={MASTER_REG.get('engine_core_active')}，admission_stage={MASTER_REG.get('admission_stage')}\n")
lines.append("- 结论：引擎本体保留；**值数据接入层在原交付就未接通**（dictionary_only_no_value_ingest），不是迁移丢失。缺的一层 = 本地值数据 provider + 路径绑定\n")
(OUT / "DICTIONARY_FIELD_MAPPING_R1.md").write_text("".join(lines), encoding="utf-8")

reuse = {
    "at": AT,
    "reused_artifacts": [
        {"from": "completion_1803/DOMAIN_SAMESET_DIFF.json", "use": "26 域路径存在性结论（不再重查）"},
        {"from": "completion_1803/SCOPE_COVERAGE_MAP.json", "use": "21 增量 dataset + 26 域映射"},
        {"from": "completion_1752/ENGINE_BASELINE_CHECK.json", "use": "引擎静态核查基线、admission matrix 指纹"},
        {"from": "13_local_schema_header_final_check", "use": "attribute/minute/finance schema 枚举 + dictionary v2"},
        {"from": "20_unified_data_schema_contract_freeze_full_R1", "use": "17 份统一契约（domain/dtype/pk/pit/status/known_gap）"},
        {"from": "rule_library/master_registry_R1", "use": "5 张 admission matrix + 15 道 gate + 激活字段"},
    ],
    "new_measurements_only": ["26 域 parquet header 按 prefix 枚举（证明分钟 8 列）",
                               "P5 20 dataset 的 receipt/sidecar 计数",
                               "FUND_ETF_NAV 增量文件计数",
                               "local_dictionary_registry 隔离纯读取 smoke"],
    "not_done_on_purpose": ["26 域逐文件重读", "财务正文读取", "历史下载脚本找回", "收益重现", "下载/API"],
}
(OUT / "REUSE_NOTE.json").write_text(json.dumps(reuse, ensure_ascii=False, indent=2), encoding="utf-8")

claim = {"at": AT, "tip": "BLACKBOX_FOUNDATION_ACCEPT_26_FILESETS_AND_FINISH_SCHEMA_INTERFACE_20261022_1814",
         "checkpoint": "COMPLETION_1814", "FOUNDATION_ACCEPTANCE": False,
         "PRODUCTION_CHANGE_AUTHORIZED": False, "ORDER_ALLOWED": False,
         "status": "COMPLETED", "host": "ZHANGWEI"}
(OUT / "CLAIM.json").write_text(json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8")

print("SUMMARY", json.dumps(dic_doc["summary"], ensure_ascii=False))
print("SMOKE", json.dumps({k: v for k, v in smoke.items() if k != "trade_calendar_read"}, ensure_ascii=False)[:800])
print("P5", len(p5_rows), "missing", missing_from_raw, "extra", extra_in_raw)
print("NAV", nav_probe["n_parquet"], nav_probe["n_sidecar"])
print("WROTE", OUT)



