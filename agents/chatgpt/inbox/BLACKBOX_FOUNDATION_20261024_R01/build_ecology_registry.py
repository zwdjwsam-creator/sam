# -*- coding: utf-8 -*-
"""
ROUND 1 — build the executable BLACKBOX ecology registry.

Design rules
------------
* dynamic: every CURRENT pointer / release / manifest is READ at build time (no hard-coded
  audit-era drive letters standing in for the authority)
* layered: RAW / CLEAN / CACHE / FACTOR_DICTIONARY / FACTOR_VALUE / STRATEGY_OUTPUT / EVIDENCE
  are separate layer records; a dataset may exist in several layers
* honest: accepted / observed / unknown / conflict are recorded per dataset with the source
* no blood mixing: supplier is kept (JQData / Tushare / external); no JQ naming imposed on
  non-JQ sources; unknown/ungrouped branches are preserved explicitly
* read-only: nothing under E:\\BLACKBOX production trees is written
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

CN = datetime.now().astimezone()
OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

BB = Path(r"E:\BLACKBOX")
RROOT = BB / "数据" / "原始只读"
RAW = RROOT / "JQData_9999_official_raw"
CLEAN_CUR = BB / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
CACHE_CUR = BB / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
DAILY_MANIFEST = BB / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"
RULELIB = Path(r"E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine\rule_library")
MASTER_REG = RULELIB / "master_registry_R1" / "MASTER_RULE_LIBRARY_REGISTRY_R1.json"
GATE_RULES = RULELIB / "master_registry_R1" / "DATA_INGESTION_GATE_RULES_R1.json"
FIELD_ADM = RULELIB / "master_registry_R1" / "FIELD_ADMISSION_MATRIX_R1.csv"
DOMAIN_ADM = RULELIB / "master_registry_R1" / "DATA_DOMAIN_ADMISSION_MATRIX_R1.csv"
DICT_ROOT = RROOT / "JQData_reference_dictionary"
FREEZE20 = DICT_ROOT / "20_unified_data_schema_contract_freeze_full_R1"
PREV = BB / "_OPS" / "SYSTEM_INVENTORY_20261020_2150" / "v2" / "continue_0010" / "correction_0650" / "continue_1310" / "completion_1814"


def jload(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def csv_rows(p: Path):
    import csv
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def n_parquet(root: Path) -> int:
    if not root.is_dir():
        return 0
    c = 0
    for _, _, fs in os.walk(root):
        c += sum(1 for f in fs if f.endswith(".parquet"))
    return c


def sha_short(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 16), b""):
            h.update(c)
    return h.hexdigest()[:16]


CLEAN = jload(CLEAN_CUR, {}) or {}
CLEAN_ASOF = CLEAN.get("cleaning_as_of") or CLEAN.get("cleaning_asof")
CACHE = jload(CACHE_CUR, {}) or {}
DAILY = jload(DAILY_MANIFEST, {}) or {}
MASTER = jload(MASTER_REG, {}) or {}
GATE = jload(GATE_RULES, {}) or {}
PREV1803 = jload(PREV / "SCOPE_COVERAGE_MAP.json", {}) or {}
PREV1814 = jload(PREV / "DICTIONARY_FIELD_MAPPING_R1.json", {}) or {}
PREV_ENG = jload(PREV / "ENGINE_DATA_INTERFACE_R1.json", {}) or {}

STD = Path(CLEAN.get("standard_root") or "")
CACHE_ROOT = Path(CACHE.get("release_root") or "")

DOMAIN_MATRIX = {r["data_domain"]: r for r in csv_rows(DOMAIN_ADM)}
FIELD_MATRIX = csv_rows(FIELD_ADM)
SCOPE21 = {d["dataset_id"]: d for d in (PREV1803.get("jq_incremental_datasets") or [])}
GROUPS1814 = {g["group_id"]: g for g in (PREV1814.get("groups") or [])}

SUPPLIER_JQ = "JQData"
DATASETS = []


def add(rec: dict) -> None:
    rec.setdefault("layers", {})
    rec.setdefault("status", {})
    DATASETS.append(rec)


def layer(root: Path | str | None, *, release=None, asof=None, pit_rule=None,
          adjust_note=None, kind=None, extra=None) -> dict:
    d: dict = {}
    if root:
        p = Path(root)
        d["root"] = str(p)
        d["exists"] = p.is_dir() if not str(root).endswith(".parquet") else p.is_file()
        d["n_parquet"] = n_parquet(p) if p.is_dir() else (1 if p.name.endswith(".parquet") and p.is_file() else 0)
    if kind:
        d["kind"] = kind
    if release:
        d["release_id"] = release
    if asof:
        d["asof"] = asof
    if pit_rule:
        d["pit_rule"] = pit_rule
    if adjust_note:
        d["adjust_note"] = adjust_note
    if extra:
        d.update(extra)
    return d


def dict_ref(name: str, path: Path) -> dict:
    return {"id": name, "path": str(path), "exists": path.exists(), "sha256_16": sha_short(path)}


# ---------------------------------------------------------------- 1. JQ price domains (26-domain family)
PRICE_DOMAINS = [
    ("PRICE_STOCK_DAILY", "A股日线 OHLCV（原始/清洗）", [RAW / "P2_stock_daily"],
     STD / "price" / "stock_ohlcv_daily", "daily_bar", "price_fq_factor",
     "trade_date 收盘后可见（bar_date_close_visible_same_day）",
     "RAW_NONE 未复权；factor 为独立列，不并入 close，不得默认 factor=1"),
    ("PRICE_STOCK_1M", "A股 1 分钟线", [RAW / "P7_stock_raw_none_replacement_1m", RAW / "P7_stock_minute"],
     STD / "price" / "A股_stock_1m", "minute_bar", "minute_price",
     "minute_bar_end_visible_at_bar_close（分钟收盘可见）",
     "RAW_NONE；factor/limit/paused 不在分钟平面，需按 (code,trade_date) join 日频，不得填造"),
    ("PRICE_STOCK_5M", "A股 5 分钟线", [RAW / "P7_stock_minute_raw_none_replacement_5m"],
     STD / "price" / "A股_stock_5m", "minute_bar", "minute_price",
     "minute_bar_end_visible_at_bar_close", "同上（分钟平面无 factor/limit/paused）"),
    ("PRICE_STOCK_30M", "A股 30 分钟线", [RAW / "P7_stock_minute"], STD / "price" / "A股_stock_30m",
     "minute_bar", "minute_price", "minute_bar_end_visible_at_bar_close", "同上"),
    ("PRICE_STOCK_60M", "A股 60 分钟线", [RAW / "P7_stock_minute"], STD / "price" / "A股_stock_60m",
     "minute_bar", "minute_price", "minute_bar_end_visible_at_bar_close", "同上"),
    ("PRICE_ETF_DAILY", "ETF 日线", [RAW / "P8_etf_fund", RAW / "P4_fund_etf_raw_none"],
     STD / "price" / "ETF_daily", "daily_bar", "price_fq_factor",
     "trade_date 收盘后可见", "ETF 日线两套 RAW schema（含/不含 fq 列），clean 以带 fq 者为准"),
    ("PRICE_ETF_1M", "ETF 1 分钟线", [RAW / "P4_fund_etf_raw_none"], STD / "price" / "ETF_1m",
     "minute_bar", "minute_price", "minute_bar_end_visible_at_bar_close", "分钟平面无 factor/limit/paused"),
    ("PRICE_ETF_5M", "ETF 5 分钟线", [RAW / "P4_fund_etf_raw_none"], STD / "price" / "ETF_5m",
     "minute_bar", "minute_price", "minute_bar_end_visible_at_bar_close", "同上"),
    ("PRICE_ETF_30M", "ETF 30 分钟线", [RAW / "P4_fund_etf_raw_none"], STD / "price" / "ETF_30m",
     "minute_bar", "minute_price", "minute_bar_end_visible_at_bar_close", "同上"),
    ("PRICE_ETF_60M", "ETF 60 分钟线", [RAW / "P4_fund_etf_raw_none"], STD / "price" / "ETF_60m",
     "minute_bar", "minute_price", "minute_bar_end_visible_at_bar_close", "同上"),
    ("PRICE_INDEX_DAILY", "指数日线", [RAW / "P3_index", RAW / "P4_index"], STD / "reference" / "index_daily",
     "daily_bar", "price_fq_factor", "trade_date 收盘后可见", "指数无 tradable_status 语义"),
    ("PRICE_INDEX_MINUTE", "指数分钟线", [RAW / "P3_index_minute", RAW / "P9_derivative_aux"], None,
     "minute_bar", "minute_price", "minute_bar_end_visible_at_bar_close", "仅 RAW 层存在；未进本轮 clean 平面"),
]

for ds, title, raws, clean_root, domain, schema_dom, pit, adjust in PRICE_DOMAINS:
    req = (DOMAIN_MATRIX.get(domain) or {}).get("required_fields", "")
    add({
        "dataset_id": ds,
        "title": title,
        "supplier": SUPPLIER_JQ,
        "source_identity": {"vendor": "JQData", "auth": "jqdatasdk 9999 套餐", "api": "get_price"},
        "lineage": "JQ_OFFICIAL_RAW",
        "layers": {
            "RAW": layer(raws[0], kind="RAW", pit_rule=pit, adjust_note=adjust,
                         extra={"alt_roots": [str(r) for r in raws[1:]]}),
            "CLEAN": layer(clean_root, kind="CLEAN", release=CLEAN.get("release_id"),
                           asof=CLEAN_ASOF, pit_rule=pit, adjust_note=adjust),
            "CACHE": layer(CACHE_ROOT, kind="CACHE", release=CACHE.get("cache_release_id"),
                           asof=CACHE.get("asof"),
                           extra={"note": "cache 为派生产品，读取请走 cache 产品名而非目录"})
            if (CACHE_ROOT and clean_root and clean_root.exists()) else {},
        },
        "authority_rule": {
            "engine_data_domain": domain,
            "required_fields": req,
            "admission_stage": "PRE_INGESTION_ONLY",
            "frequency_gate": "daily / 1m / 5m / 15m / 30m / 60m ADMIT_IF_MATCHED；tick NOT_READY_BLOCKED",
        },
        "dictionary": {
            "schema_contract": dict_ref("20_unified_data_schema_contract_freeze_full_R1", FREEZE20 / "02_domain_schema" / "domain_schema_contract.csv"),
            "price_field_dictionary": dict_ref("03_field_dictionary", DICT_ROOT / "03_field_dictionary" / "price_field_dictionary.csv"),
            "unit_dictionary": dict_ref("06_unit_dictionary", DICT_ROOT / "06_unit_dictionary" / "unit_dictionary.csv"),
            "pit_tags": dict_ref("05_pit_field_dictionary", DICT_ROOT / "05_pit_field_dictionary" / "pit_field_tags.csv"),
        },
        "fields": {
            "source_columns_observed": GROUPS1814.get(
                {"PRICE_STOCK_DAILY": "G02_STOCK_DAILY_OHLCV", "PRICE_STOCK_1M": "G03_STOCK_MINUTE",
                 "PRICE_STOCK_5M": "G03_STOCK_MINUTE", "PRICE_STOCK_30M": "G03_STOCK_MINUTE",
                 "PRICE_STOCK_60M": "G03_STOCK_MINUTE", "PRICE_ETF_DAILY": "G04_ETF_PRICE",
                 "PRICE_ETF_1M": "G04_ETF_PRICE", "PRICE_ETF_5M": "G04_ETF_PRICE",
                 "PRICE_ETF_30M": "G04_ETF_PRICE", "PRICE_ETF_60M": "G04_ETF_PRICE",
                 "PRICE_INDEX_DAILY": "G05_INDEX_PRICE", "PRICE_INDEX_MINUTE": "G05_INDEX_PRICE"}.get(ds, ""),
                {}).get("source_schema_actual"),
            "standard_required": [x.strip() for x in req.split(",") if x.strip()],
            "unit": {"price": "元", "volume": "股", "amount": "元"},
        },
        "scope": {
            "download_range": "2014-01-01 → cleaning_asof（RAW 全历史；PAST 不重下）",
            "exclusions": "tick（KG11）/ 期货期权债券（KG03-05）不在本轮范围",
            "increment_rule": "日增量 append；分钟域按 day-file 追加，幂等键 (code,timestamp)",
            "cursor": "CURRENT_CLEANING_RELEASE.cleaning_asof / daily_asof",
        },
        "relations": {"upstream": ["P0_meta(calendar/securities)", "P1_adjust_factor", "P2_security_state"],
                      "downstream": ["CLEAN", "CACHE", "FACTOR_260(输入)"]},
        "status": {
            "accepted": ["26 域 CANONICAL_FILE_LIST 逐路径 exists（1803）",
                         "清洗平面已发布（CURRENT_CLEANING_RELEASE as_of %s）" % CLEAN_ASOF
                         if (clean_root and clean_root.exists()) else "清洗平面未发布（该数据集不在本轮 clean 平面）"],
            "observed": [f"RAW n_parquet={n_parquet(raws[0])}",
                         f"CLEAN n_parquet={n_parquet(clean_root)}" if clean_root and clean_root.exists() else "CLEAN 目录不存在",
                         "实测 RAW/CLEAN 同日同码 close 一致（2026-09-10 000001.XSHE = 11.85）"
                         if ds == "PRICE_STOCK_DAILY" else "",
                         "实测节段 schema 分裂：batch 段 8 列，day-file 段 15 列（含 paused/high_limit/low_limit/avg/pre_close/factor/fq）"
                         if ds == "PRICE_STOCK_DAILY" else ""],
            "unknown": ["分钟平面 factor/limit/paused 的 join 结果是否已落 clean（本轮未验）",
                        "batch 段 factor=null 的复权路径未落地" if ds == "PRICE_STOCK_DAILY" else ""],
            "conflict": [],
        },
        "evidence": [str(PREV / "DICTIONARY_FIELD_MAPPING_R1.json")],
    })

# ---------------------------------------------------------------- 2. reference / status / events
REF = [
    ("CALENDAR_CN_EXCHANGE", "交易日历", RAW / "P0_meta", STD / "reference" / "calendar_cn_exchange",
     "trade_calendar", "calendar_known_before_session", "无复权语义"),
    ("SECURITY_MASTER", "证券主数据（股/ETF/基金/指数/期货）", RAW / "P0_meta", STD / "reference" / "security_master",
     None, "static（start_date/end_date 生效）", "不适用"),
    ("ADJUST_FACTOR", "复权因子（独立列）", RAW / "P1_adjust_factor", STD / "reference" / "adjust_factor",
     "adjustment_factor", "factor 跳变对应 corporate action ex_date", "raw close 保持未复权"),
    ("TRADABLE_STATUS", "涨跌停 / 停牌状态", RAW / "P2_security_state", STD / "reference" / "stock_limit_pause_status",
     "tradable_status", "status_known_at_bar_time", "不适用"),
    ("INDEX_COMPONENTS", "指数成分（快照）", RAW / "P3_index", STD / "reference" / "index_components",
     "benchmark_data", "asof_date 快照", "不适用"),
    ("INDEX_WEIGHTS", "指数权重", RAW / "P3_index", STD / "reference" / "index_weights",
     "benchmark_data", "weight_date 可见；禁止用文件生成时间", "不适用"),
    ("INDUSTRY_CONCEPT", "行业 / 概念成分", RAW / "P5_attributes_events", STD / "reference" / "industry_concept",
     None, "effective_from 生效", "不适用"),
    ("INDUSTRY_CONCEPT_EVENTS", "概念事件", RAW / "P5_attributes_events", STD / "reference" / "industry_concept_events",
     None, "as_of", "不适用"),
    ("BILLBOARD", "龙虎榜", RAW / "P5_attributes_events", STD / "events" / "billboard",
     None, "day 为事件日", "不适用"),
    ("XR_XD", "除权除息事件", RAW / "P5_attributes_events", STD / "events" / "xr_xd",
     "corporate_actions", "announce_date 可见；ex_date 为除权日，二者不得混用", "adj_factor 事件基准"),
    ("CORPORATE_REFERENCE", "公司行为参考", RAW / "P5_attributes_events", STD / "events" / "corporate_reference",
     "corporate_actions", "announce_date", "不适用"),
    ("SHAREHOLDER_TOP10", "十大股东", RAW / "P5_attributes_events", STD / "reference" / "shareholder_top10",
     None, "pub_date 可见 / end_date 报告期", "不适用"),
    ("SHAREHOLDER_FLOATING_TOP10", "十大流通股东", RAW / "P5_attributes_events",
     STD / "reference" / "shareholder_floating_top10", None, "pub_date 可见 / end_date 报告期", "不适用"),
    ("VALUATION", "估值日频", RAW / "P6_factor_reference", STD / "factor" / "valuation",
     None, "day 按日频可见", "不适用"),
    ("FINANCE_PIT", "财务三大表 + 指标（PIT）", RAW / "P3_finance_pit", STD / "fundamentals",
     "factor_pit_rules", "pubDate 可见 / statDate 报告期；禁止用文件生成时间", "不适用"),
    ("MTSS", "融资融券", RAW / "P5_attributes_events", None, None, "date", "不适用"),
]

for ds, title, raw_root, clean_root, domain, pit, adjust in REF:
    req = (DOMAIN_MATRIX.get(domain) or {}).get("required_fields", "") if domain else ""
    add({
        "dataset_id": ds,
        "title": title,
        "supplier": SUPPLIER_JQ,
        "source_identity": {"vendor": "JQData", "auth": "jqdatasdk 9999", "api": "见 raw plane"},
        "lineage": "JQ_OFFICIAL_RAW",
        "layers": {
            "RAW": layer(raw_root, kind="RAW", pit_rule=pit, adjust_note=adjust),
            "CLEAN": layer(clean_root, kind="CLEAN", release=CLEAN.get("release_id"),
                           asof=CLEAN_ASOF, pit_rule=pit, adjust_note=adjust) if clean_root else {},
        },
        "authority_rule": {"engine_data_domain": domain, "required_fields": req,
                           "admission_stage": "PRE_INGESTION_ONLY"},
        "dictionary": {
            "schema_contract": dict_ref("20_freeze/domain_schema", FREEZE20 / "02_domain_schema" / "domain_schema_contract.csv"),
            "pit_schema": dict_ref("20_freeze/pit_schema", FREEZE20 / "04_pit_schema" / "pit_schema_contract.csv"),
            "dtype_schema": dict_ref("20_freeze/dtype", FREEZE20 / "09_dtype_precision_schema" / "dtype_precision_contract.csv"),
        },
        "fields": {"standard_required": [x.strip() for x in req.split(",") if x.strip()] if req else []},
        "scope": {"download_range": "2014-01-01 → cleaning_asof", "exclusions": "",
                  "increment_rule": "按 dataset 增量类（EOD_APPEND / EVENT_UPSERT / DISCLOSURE_UPSERT / REFERENCE_RECONCILE）",
                  "cursor": "CURRENT_CLEANING_RELEASE.cleaning_asof"},
        "relations": {"upstream": [], "downstream": ["CLEAN", "CACHE"]},
        "status": {"accepted": ["目录存在"], "observed": [f"RAW n_parquet={n_parquet(raw_root)}",
                                                          "105 文件 / 56,164 行 / 8 指数 / 2014-2026，component_code 显式存在"
                                                          if ds == "INDEX_WEIGHTS" else ""],
                   "unknown": ["逐指数/逐年 PIT 补证未做（historical_backtest_eligible 全 False）"
                               if ds == "INDEX_WEIGHTS" else ""],
                   "conflict": ["权重文件在 ≠ 权重历史可回测（53,714 行 PARTIAL_OR_UNPROVEN）"
                                if ds == "INDEX_WEIGHTS" else ""]},
        "evidence": [],
    })

# ---------------------------------------------------------------- 3. fund / nav
for ds, title, raw_root, clean_root, naming in [
    ("FUND_ETF_NAV", "ETF 净值（unit/acc）", RAW / "P4_fund_etf" / "fund_etf_nav", STD / "fund" / "ETF_NAV",
     "unit_net_value + acc_net_value（与 fund_fund_net_value 的 net_value/sum_value 为不同命名族）"),
    ("ETF_SHARE", "ETF 份额", RAW / "P4_fund_etf", STD / "fund" / "ETF_SHARE", "shares"),
    ("OPEN_FUND", "场外基金净值", RAW / "P4b_fund_expand", STD / "fund" / "open_fund", "unit_net_value"),
    ("QDII", "QDII 净值", RAW / "P4b_fund_expand", STD / "fund" / "QDII", "unit_net_value"),
    ("FUND_OTHER", "其他基金净值", RAW / "P4b_fund_expand", STD / "fund" / "other", "unit_net_value"),
    ("FUND_TRACKING_INDEX_MAPPING", "基金跟踪指数映射", RAW / "P4_fund_etf",
     STD / "fund" / "fund_tracking_index_mapping", "traced_index_code"),
]:
    add({
        "dataset_id": ds, "title": title, "supplier": SUPPLIER_JQ,
        "source_identity": {"vendor": "JQData", "auth": "9999", "api": "get_extras / finance.run_query"},
        "lineage": "JQ_OFFICIAL_RAW",
        "layers": {
            "RAW": layer(raw_root, kind="RAW", pit_rule="净值 T+1 可见（unit_net_value: PIT_DELAYED_1D）"),
            "CLEAN": layer(clean_root, kind="CLEAN", release=CLEAN.get("release_id"),
                           asof=CLEAN_ASOF),
        },
        "authority_rule": {"engine_data_domain": "daily_bar", "admission_stage": "PRE_INGESTION_ONLY"},
        "dictionary": {"pit_tags": dict_ref("05_pit_field_dictionary", DICT_ROOT / "05_pit_field_dictionary" / "pit_field_tags.csv")},
        "fields": {"naming_note": naming, "standard_required": ["code", "day", "unit_net_value", "acc_net_value"]},
        "scope": {"download_range": "2014 → asof", "exclusions": "FUND_NET_VALUE 整表 5000 静默禁止",
                  "increment_rule": "get_extras(unit)+get_extras(acc) 批量，batch_size=5",
                  "cursor": "CLEAN.FUND_NAV_TIP / cleaning_asof"},
        "relations": {"upstream": ["P4_fund_etf"], "downstream": ["CACHE: FUND_NAV_PIT_R1"]},
        "status": {"accepted": ["NAV 增量 13775 parquet + sidecar（20260713–20260924，1814 实测）"],
                   "observed": [f"RAW n_parquet={n_parquet(raw_root)}"], "unknown": [], "conflict": []},
        "evidence": [str(PREV / "POST_BASELINE_SCOPE_SUPPLEMENT_R1.json")],
    })

# ---------------------------------------------------------------- 4. JQ20 incremental datasets (21)
for ds_id, spec in sorted(SCOPE21.items()):
    raw_dir = Path(spec.get("raw_rel") or "")
    clean_name = spec.get("clean_product")
    clean_dir = None
    if clean_name and (STD / "jq20").is_dir():
        cands = list((STD / "jq20").glob(f"*{clean_name}*"))
        clean_dir = cands[0] if cands else None
    add({
        "dataset_id": ds_id, "title": f"JQ20 扩展：{ds_id}", "supplier": SUPPLIER_JQ,
        "source_identity": {"vendor": "JQData", "auth": "JQ20 扩展权限", "api": spec.get("api") or "finance.run_query / get_extras"},
        "lineage": "JQ_POST_BASELINE_EXTENSION",
        "layers": {
            "RAW": layer(raw_dir, kind="RAW", pit_rule=spec.get("pit_policy")),
            "CLEAN": layer(clean_dir, kind="CLEAN", release=CLEAN.get("release_id"),
                           asof=CLEAN_ASOF) if clean_dir else {},
        },
        "authority_rule": {"engine_data_domain": None, "admission_stage": "PRE_INGESTION_ONLY",
                           "increment_class": spec.get("increment_class")},
        "dictionary": {"schema_contract": dict_ref("20_freeze/domain_schema", FREEZE20 / "02_domain_schema" / "domain_schema_contract.csv")},
        "fields": {"standard_product": clean_name, "cache_product": spec.get("cache_product")},
        "scope": {"download_range": "增量（不自 2014 重下）", "exclusions": "",
                  "increment_rule": spec.get("increment_class"),
                  "cursor": "RAW_MANIFEST.json + cleaning_asof"},
        "relations": {"upstream": [], "downstream": [f"CACHE:{spec.get('cache_product')}"] if spec.get("cache_product") else []},
        "status": {"accepted": ["RAW_MANIFEST.json 存在（1814 实测 20/20）"] if (raw_dir / "RAW_MANIFEST.json").exists() else [],
                   "observed": [f"RAW n_parquet={n_parquet(raw_dir)}"],
                   "unknown": ["逐日增量完整性未对账（不得升级为全部通过）"], "conflict": []},
        "evidence": [str(PREV / "POST_BASELINE_SCOPE_SUPPLEMENT_R1.json")],
    })

# ---------------------------------------------------------------- 5. factor dictionary / value / strategy
FACTOR_FILES = [
    ("FACTOR_260_DICTIONARY", "聚宽 260 因子字典（清单/语义/公式）",
     RULELIB / "blackbox_current_dictionary_R1" / "factor_260_inventory_CURRENT.csv"),
    ("FACTOR_260_SEMANTICS", "因子字段语义", RULELIB / "blackbox_current_dictionary_R1" / "factor_260_field_semantics_CURRENT.csv"),
    ("FACTOR_260_FORMULA", "因子公式", RULELIB / "blackbox_current_dictionary_R1" / "factor_260_formula_CURRENT.csv"),
    ("FACTOR_260_PIT_RULES", "因子 PIT 规则", RULELIB / "blackbox_current_dictionary_R1" / "factor_260_pit_rules_CURRENT.json"),
    ("FACTOR_260_CLEANING_RULES", "因子清洗规则（未激活）", RULELIB / "blackbox_current_dictionary_R1" / "factor_260_cleaning_rules_CURRENT.json"),
    ("FACTOR_260_ENGINE_MAPPING", "因子 → 引擎字段映射", RULELIB / "blackbox_current_dictionary_R1" / "factor_260_engine_mapping_CURRENT.csv"),
]
for ds, title, p in FACTOR_FILES:
    add({
        "dataset_id": ds, "title": title, "supplier": SUPPLIER_JQ,
        "source_identity": {"vendor": "JQData 字典副本", "auth": "无（静态文件）", "api": None},
        "lineage": "BLACKBOX_RULE_LIBRARY_COPY",
        "layers": {"FACTOR_DICTIONARY": layer(p if p.is_file() else p.parent, kind="DICTIONARY",
                                              extra={"file": str(p), "exists": p.is_file(),
                                                     "sha256_16": sha_short(p)})},
        "authority_rule": {"engine_data_domain": "factor_dictionary",
                           "admission_status": "ADMIT_DICTIONARY_ONLY",
                           "factor_value_download_forbidden": (GATE.get("policies") or {}).get("factor_value_download_forbidden"),
                           "factor_cleaning_not_active": (GATE.get("policies") or {}).get("factor_cleaning_not_active")},
        "dictionary": {"self": str(p)},
        "fields": {"standard_required": ["canonical_factor_name"]},
        "scope": {"download_range": "字典 only（不含因子值）", "exclusions": "因子值 API = KG10 paid_module",
                  "increment_rule": "字典随规则库版本发布", "cursor": "rule_library CURRENT"},
        "relations": {"upstream": [], "downstream": ["FACTOR_VALUE（未下载）", "引擎 factor gates"]},
        "status": {"accepted": ["字典准入（ADMIT_DICTIONARY_ONLY）"], "observed": [],
                   "unknown": [], "conflict": ["字典可用 ≠ 因子值可用"]},
        "evidence": [],
    })

add({
    "dataset_id": "FACTOR_VALUE",
    "title": "因子值（260）",
    "supplier": SUPPLIER_JQ,
    "source_identity": {"vendor": "JQData", "auth": "get_factor_values 付费模块", "api": "get_factor_values"},
    "lineage": "NOT_DOWNLOADED_BY_POLICY",
    "layers": {"FACTOR_VALUE": layer(None, kind="VALUE", extra={"status": "NOT_MATERIALIZED_BY_RULE"})},
    "authority_rule": {"engine_data_domain": "factor_pit_rules", "admission_status": "BLOCKED_BY_POLICY",
                       "reason": "DATA_INGESTION_GATE_RULES_R1.policies.factor_value_download_forbidden=true"},
    "dictionary": {"factor_dictionary": "FACTOR_260_DICTIONARY"},
    "fields": {},
    "scope": {"download_range": "无", "exclusions": "KG10", "increment_rule": "不适用（策略禁止）", "cursor": None},
    "relations": {"upstream": ["FACTOR_260_DICTIONARY"], "downstream": []},
    "status": {"accepted": [], "observed": ["规则层显式禁止"], "unknown": ["若未来解禁需权限重探"],
               "conflict": ["不得把字典准入当因子值可用"]},
    "evidence": [str(GATE_RULES)],
})

add({
    "dataset_id": "STRATEGY_OUTPUT",
    "title": "策略/研究输出（非数据底座）",
    "supplier": "BLACKBOX_INTERNAL",
    "source_identity": {"vendor": "内部研究", "auth": "本地", "api": None},
    "lineage": "INTERNAL_RESEARCH_OUTPUT",
    "layers": {"STRATEGY_OUTPUT": layer(BB / "研究系统" / "CURRENT", kind="STRATEGY_OUTPUT",
                                        extra={"note": "指针层；不在本轮扫描/不作为底座"})},
    "authority_rule": {"engine_data_domain": None, "admission_stage": "OUT_OF_DATA_FOUNDATION"},
    "dictionary": {},
    "fields": {},
    "scope": {"download_range": "不适用", "exclusions": "策略/PnL 不作底座前置", "increment_rule": "研究流程", "cursor": None},
    "relations": {"upstream": ["CACHE", "EVIDENCE"], "downstream": []},
    "status": {"accepted": ["本轮不评估"], "observed": [], "unknown": [], "conflict": ["策略经验 ≠ 底层规则"]},
    "evidence": [],
})

# ---------------------------------------------------------------- 6. external suppliers (blood kept separate)
EXTERNAL = [
    ("TS_CBOND_R1", "途施可转债原始 R1", RROOT / "途施可转债官方原始_R1", "Tushare", "RAW",
     "可转债基础/条款/日线/发行/利率/份额（多窗口 receipt 序列）",
     "KG06 在 JQ 侧 out_of_scope；本目录为 Tushare 供应商序列，不套 JQ 命名"),
    ("TS_CBOND_R2", "途施可转债原始 R2", RROOT / "途施可转债官方原始_R2", "Tushare", "RAW",
     "call/rating/share/top10 holders（carryin 续跑）",
     "R1 续跑批；同一供应商序列，不重复计为新来源"),
    ("EXTERNAL_DICT_EVIDENCE", "外部字典证据（朋友 JQData 字典 + Tushare patch）",
     BB / "数据" / "外部补充只读", "Friend_JQData/Tushare", "EVIDENCE",
     "字典交叉核验 / 冲突复核", "仅字典置信度补充，不含值数据"),
    ("EXTERNAL_EVIDENCE_PLANE", "外部证据平面（CANONICAL/COMPANY_PRIMARY/EXCHANGE…）",
     BB / "数据" / "外部证据", "MULTI_EXTERNAL", "EVIDENCE", "研究证据产品（每产品 PRODUCT_META）",
     "独立证据平面，不是 26 域 RAW 清洗输入"),
    ("US_MARKET", "美股研究旁路", BB / "数据" / "美国市场", "EXTERNAL", "EVIDENCE",
     "美股日频/新闻/细粒度利润池", "KG02 美股 out_of_scope；仅研究旁路"),
    ("TUSHARE_INDEX_WEIGHT_ADAPTER", "Tushare 指数权重适配器锁",
     DICT_ROOT / "19_tushare_index_weight_adapter_lock", "Tushare", "EVIDENCE",
     "外源指数权重适配（适配器锁，非值数据）", "与 JQ index_weights 血统不同，不得混用"),
]
for ds, title, root, vendor, layer_name, what, note in EXTERNAL:
    add({
        "dataset_id": ds, "title": title, "supplier": vendor,
        "source_identity": {"vendor": vendor, "auth": "该供应商自有", "api": None},
        "lineage": f"EXTERNAL_{vendor.upper().replace('/', '_')}",
        "layers": {layer_name: layer(root, kind=layer_name)},
        "authority_rule": {"engine_data_domain": None, "admission_stage": "OUTSIDE_JQ_FOUNDATION",
                           "note": note},
        "dictionary": {"own_contract": "该供应商自有字段字典/README，不得套 20_freeze 聚宽契约"},
        "fields": {"what": what},
        "scope": {"download_range": "见各自目录", "exclusions": "不硬套聚宽规则",
                  "increment_rule": "供应商 own-contract", "cursor": "见各自 receipt/lock"},
        "relations": {"upstream": [], "downstream": ["EVIDENCE / RESEARCH"]},
        "status": {"accepted": ["目录与 receipt 结构存在（1814 有界核查）"], "observed": [f"n_parquet={n_parquet(root)}"],
                   "unknown": ["字段级与周期完整性未核"], "conflict": ["不得混血统"]},
        "evidence": [str(PREV / "POST_BASELINE_SCOPE_SUPPLEMENT_R1.json")],
    })

# ---------------------------------------------------------------- 7. preserve undetermined / legacy
for ds, title, root, cls, why in [
    ("LEGACY_JQ_RAW_CN", "旧中文分类聚宽 RAW（行情/财务/ETF/因子/行业）", RROOT, "LEGACY_PRE_BASELINE_RAW_CLASSIFICATION",
     "26 域正式清单对应 P0-P9 平面；旧分类不作正式输入"),
    ("EXPERIMENTAL_WINDOW_RAW", "2026-03-25..05-01 独立窗口 RAW", RROOT / "JQData_9999_WINDOW_FULL_RAW_20260325_20260501",
     "HISTORICAL_EXPERIMENTAL_WINDOW_DO_NOT_USE_AS_MASTER",
     "自带 EXPERIMENTAL_TRIAL_DATA_DO_NOT_USE_AS_MASTER.txt；仅字段证据"),
    ("STRATEGY_DATA_PLANE_ADDITIONS", "策略数据平面增量（17 产品）", RROOT / "strategy_data_plane_additions",
     "FORMAL_POST_BASELINE_INHERITANCE", "自带 REL/MANIFEST/COVERAGE/PROVENANCE/CHECKSUMS 发布结构"),
    ("FORENSIC_CANARY", "取证金丝雀 / 接口盘点", RROOT / "_forensic_canary", "AUDIT_ONLY_NOT_FOUNDATION", ""),
    ("EXPERIMENT_CANARY", "分钟 fq 试验 canary", RROOT / "试验", "EXPERIMENTAL_NOT_FOUNDATION", ""),
    ("UNDETERMINED_SCOPE", "未在有界范围内出现的来源", None, "UNDETERMINED",
     "保持 UNDETERMINED：不据此宣称数据缺失，也不静默遗漏"),
]:
    add({
        "dataset_id": ds, "title": title, "supplier": "VARIOUS",
        "source_identity": {"vendor": "unknown/mixed", "auth": None, "api": None},
        "lineage": cls,
        "layers": ({"RAW": layer(root, kind="RAW")} if root else {}),
        "authority_rule": {"engine_data_domain": None, "admission_stage": "NOT_A_FORMAL_INPUT"},
        "dictionary": {},
        "fields": {},
        "scope": {"download_range": "n/a", "exclusions": why, "increment_rule": "n/a", "cursor": None},
        "relations": {"upstream": [], "downstream": []},
        "status": {"accepted": [], "observed": [f"exists={bool(root and Path(root).exists())}"],
                   "unknown": [why] if cls == "UNDETERMINED" else [], "conflict": []},
        "evidence": [str(PREV / "POST_BASELINE_SCOPE_SUPPLEMENT_R1.json")],
    })

# ---------------------------------------------------------------- 8. field-naming facts (high-impact)
FIELD_FACTS = {
    "code_column_names": {
        "PRICE_STOCK_DAILY": "code",
        "PRICE_STOCK_1M": "code",
        "CALENDAR_CN_EXCHANGE": "trade_date (no code)",
        "SECURITY_MASTER": "index（pandas 索引被保留为列；clean 层即证券代码）",
        "INDEX_COMPONENTS": "index_code + code",
        "INDEX_WEIGHTS_RAW_SNAPSHOT": "index（成分代码）+ index_code（指数代码）",
        "INDEX_WEIGHTS_CLEAN": "index_code + component_code（显式成分列，105 文件 2014→）",
        "INDEX_CONSTITUENT_PIT_R1": "index_code + constituent_code（元数据齐全，920 万行）",
        "FUND_ETF_NAV": "code",
    },
    "index_weights_correction": {
        "prior_1814_claim": "缺 member_code，PK 契约不可满足（基于单个 RAW snapshot 的 schema 摘要）",
        "this_round_evidence": {
            "raw_snapshot_columns": ["index", "date", "weight", "display_name", "index_code",
                                     "query_date", "data_asof", "discovery_asof", "available_at"],
            "raw_pandas_index_columns": [],
            "clean_plane_files": 105,
            "clean_columns": ["index_code", "component_code", "date", "weight", "display_name",
                              "query_date", "historical_backtest_eligible", "historical_coverage_status"],
        },
        "verdict": "CORRECTED：成分代码存在（RAW 为 index 列、CLEAN 为 component_code 列），不是源缺失；"
                   "1814 的缺口结论仅适用于该单个 snapshot 的列名摘要，不适用于 105 文件全范围",
        "remaining_gate": "clean 行标记 historical_backtest_eligible=False / historical_coverage_status="
                          "PARTIAL_OR_UNPROVEN，权重历史可回测性受限（需按指数/年份核）",
    },
    "dtype_facts": {
        "stock_daily.volume": "double，实测 122,500 行非整数计数 = 0（可安全转 int64）；null 8,330（需按 paused 核对后再定）",
        "stock_daily.date": "timestamp[ns]，实测 time_of_day 全为 00:00（日期语义正确，仅 dtype 偏离契约）",
        "fund_etf_nav.day": "large_string，需显式转 date 且不得混格式",
    },
    "segment_schema_split": {
        "fact": "日频 CLEAN/RAW 的『历史 batch 段』与『增量 day-file 段』schema 不同：",
        "history_batch_columns": ["time", "code", "open", "close", "high", "low", "volume", "money", "__index_level_0__"],
        "incremental_dayfile_columns_in_clean": ["time", "code", "open", "close", "high", "low", "volume", "money",
                                                 "paused", "high_limit", "low_limit", "avg", "pre_close", "factor", "fq"],
        "measured": {"2026-09-10 clean day-file": {"factor": 1.0, "paused": 0.0,
                                                 "high_limit": 12.87, "low_limit": 10.53},
                     "2026-06-15 batch segment": {"factor": None}},
        "verdict": "CORRECTED：RAW 并非天然缺 factor/limit/paused；增量 day-file 段自带这四列。"
                   "缺口只在历史 batch 段，且可由 day-file + 日频 join 补齐；本轮不填造、不默认 factor=1",
        "caveat": "batch 段 factor 为 null 而非 1，任何按 factor 计算的复权必须在缺失段显式拒绝而非静默当作 1",
    },
    "duplicate_version_fact": {
        "fact": "同一 (family, 年份/日) 存在多次下载版本（trailing YYYYMMDD_HHMMSS），"
                "如 stock_daily__incremental_gap_20260910__full__20260917_144821 / _145054",
        "rule": "读取必须按 family 去重取最新版本，并按 (code,timestamp) 兜底去重；否则会双计数",
        "implemented": "candidate/local_plane_provider.py::_dedupe_versions + (code,timestamp) 去重",
    },
    "index_weights_eligibility": {
        "measured": {"n_files": 105, "n_rows": 56164, "n_index": 8,
                     "indexes": ["000001.XSHG", "000016.XSHG", "000300.XSHG", "000688.XSHG",
                                 "000852.XSHG", "000905.XSHG", "399001.XSHE", "399006.XSHE"],
                     "years": "2014-2026", "rows_by_year": {"2014": 3024, "2015": 3569, "2016": 3663,
                                                            "2017": 3884, "2018": 3939, "2019": 3988,
                                                            "2020": 4033, "2021": 4250, "2022": 4509,
                                                            "2023": 4655, "2024": 4741, "2025": 4742,
                                                            "2026": 4717},
                     "historical_backtest_eligible_true": 0,
                     "coverage_status_rows": {"PARTIAL_OR_UNPROVEN": 53714},
                     "weight_null": 0,
                     "schema_groups": {"repair_v1_code_preserved": 104,
                                       "clean_tip_snapshot_20260831": 1}},
        "rule": "权重文件齐全且成分代码显式（component_code），但 historical_backtest_eligible 全为 False → "
                "『权重值在』≠『权重历史可回测』；按指数/年份补证 PIT 后才可准入权重回测",
    },
    "minute_fields": {
        "fact": "26 域分钟平面（含 clean A股_stock_1m）均无 factor/high_limit/low_limit/paused",
        "clean_1m_extra": ["fq", "price_basis", "repair_unit_id", "domain_id", "exchange"],
        "rule": "join 日频（按 code+trade_date，PIT=当日可见），不默认 factor=1，不填造涨跌停/停牌",
        "status": "候选映射；本轮未落地 join 结果",
    },
    "finance_facts": {
        "alias": "statDate/pubDate（income/balance/indicator） vs pub_date/report_date/report_type（cash_flow）",
        "duplicate": "balance/indicator 存在 statDate 与 statDate.1",
        "revision": "RAW 无 revision_version；restatement 链是契约（08）而非已实现",
        "rule": "别名相同不证明内容等同；不发明历史修订链；未解决则阻止该字段准入",
    },
}

# ---------------------------------------------------------------- compaction pass
for _d in DATASETS:
    _d["layers"] = {k: v for k, v in (_d.get("layers") or {}).items() if v}
    _d["status"] = {k: [x for x in (v or []) if x] for k, v in (_d.get("status") or {}).items()}
    _d["status"] = {k: v for k, v in _d["status"].items() if v}
    _d["fields"] = {k: v for k, v in (_d.get("fields") or {}).items() if v not in (None, [], {}, "")}
    _d["scope"] = {k: v for k, v in (_d.get("scope") or {}).items() if v not in (None, "")}
    _d["relations"] = {k: [x for x in (v or []) if x] for k, v in (_d.get("relations") or {}).items()}
    _d["relations"] = {k: v for k, v in _d["relations"].items() if v}

registry = {
    "registry_id": "BLACKBOX_ECOLOGY_REGISTRY",
    "version": "R1_ROUND1_20261024",
    "built_at": CN.isoformat(),
    "round": "1/10",
    "FOUNDATION_ACCEPTANCE": False,
    "ORDER_ALLOWED": False,
    "production_write": False,
    "dynamic_sources": {
        "cleaning_current": {"path": str(CLEAN_CUR), "release_id": CLEAN.get("release_id"),
                             "seal_id": CLEAN.get("seal_id"), "cleaning_as_of": CLEAN_ASOF,
                             "daily_asof": CLEAN.get("daily_asof"), "finance_asof": CLEAN.get("finance_asof"),
                             "standard_root": CLEAN.get("standard_root"), "sha256_16": sha_short(CLEAN_CUR),
                             "pointer_observation": {
                                 "release_id_points_to": "R33_FUND_NAV",
                                 "parent_release_id": CLEAN.get("parent_release_id"),
                                 "quarantine_root_release": "R45_DAILY_TIP",
                                 "ledger_path_release": "R45_DAILY_TIP",
                                 "switch_reason": CLEAN.get("switch_reason"),
                                 "note": "release_id/parent/quarantine/ledger 跨 R33 与 R45；按 switch_reason 视为"
                                         "授权回切，但读取必须以 release_id 的 standard_root 为准，"
                                         "不得把 parent(R45) 的 asof 当作本 release 内容",
                             }},
        "cache_current": {"path": str(CACHE_CUR), "cache_release_id": CACHE.get("cache_release_id"),
                          "asof": CACHE.get("asof"), "sha256_16": sha_short(CACHE_CUR)},
        "daily_manifest": {"path": str(DAILY_MANIFEST), "CN_RESEARCH_DATE": DAILY.get("CN_RESEARCH_DATE"),
                           "DAILY_INCREMENTAL_READY": DAILY.get("DAILY_INCREMENTAL_READY"),
                           "DEGRADED_LANES": DAILY.get("DEGRADED_LANES"),
                           "sha256_16": sha_short(DAILY_MANIFEST)},
        "master_rule_registry": {"path": str(MASTER_REG), "master_registry_active": MASTER.get("master_registry_active"),
                                 "formal_backtest_active": MASTER.get("formal_backtest_active"),
                                 "engine_core_active": MASTER.get("engine_core_active"),
                                 "admission_stage": MASTER.get("admission_stage")},
        "ingestion_gate": {"path": str(GATE_RULES), "n_gates": len(GATE.get("gates") or []),
                           "policies": GATE.get("policies")},
        "schema_freeze20": {"path": str(FREEZE20)},
        "reused_from": ["completion_1803/SCOPE_COVERAGE_MAP.json",
                        "completion_1814/DICTIONARY_FIELD_MAPPING_R1.json",
                        "completion_1814/POST_BASELINE_SCOPE_SUPPLEMENT_R1.json",
                        "completion_1814/ENGINE_DATA_INTERFACE_R1.json"],
    },
    "layer_taxonomy": {
        "RAW": "供应商原始下载（只读、不可原地改）",
        "CLEAN": "正式清洗产品（CURRENT_CLEANING_RELEASE.standard）",
        "CACHE": "回测缓存派生产品（CURRENT_CACHE_RELEASE）",
        "FACTOR_DICTIONARY": "因子字典/公式/PIT/清洗规则（值 ≠ 字典）",
        "FACTOR_VALUE": "因子值（当前规则禁止下载）",
        "STRATEGY_OUTPUT": "策略/研究输出（不作底座）",
        "EVIDENCE": "外部证据平面",
    },
    "engine_boundary": {
        "source": str(MASTER_REG),
        "master_registry_active": MASTER.get("master_registry_active"),
        "formal_backtest_active": MASTER.get("formal_backtest_active"),
        "engine_core_active": MASTER.get("engine_core_active"),
        "admission_stage": MASTER.get("admission_stage"),
        "provider_factory_branches": (PREV_ENG.get("provider_chain") or {}).get("branches_found"),
        "local_value_branch_present": (PREV_ENG.get("provider_chain") or {}).get("local_value_plane_branch"),
        "note": "本地值数据接入属后续轮次；本轮只做只读候选并验证接口可包裹，不翻开关",
    },
    "field_facts": FIELD_FACTS,
    "datasets": DATASETS,
    "counts": {
        "n_datasets": len(DATASETS),
        "by_supplier": {s: sum(1 for d in DATASETS if d["supplier"] == s)
                        for s in sorted({d["supplier"] for d in DATASETS})},
        "by_layer_present": {L: sum(1 for d in DATASETS if L in (d.get("layers") or {}))
                             for L in ["RAW", "CLEAN", "CACHE", "FACTOR_DICTIONARY", "FACTOR_VALUE",
                                       "STRATEGY_OUTPUT", "EVIDENCE"]},
    },
}

OUT.joinpath("ECOLOGY_REGISTRY.json").write_text(json.dumps(registry, ensure_ascii=False, indent=1), encoding="utf-8")

index = {
    "registry_id": registry["registry_id"],
    "version": registry["version"],
    "datasets": [
        {"dataset_id": d["dataset_id"], "title": d["title"], "supplier": d["supplier"],
         "lineage": d["lineage"], "layers": sorted((d.get("layers") or {}).keys()),
         "raw_root": (d.get("layers", {}).get("RAW") or {}).get("root"),
         "clean_root": (d.get("layers", {}).get("CLEAN") or {}).get("root"),
         "unknown": (d.get("status") or {}).get("unknown") or [],
         "conflict": (d.get("status") or {}).get("conflict") or []}
        for d in DATASETS
    ],
}
OUT.joinpath("ECOLOGY_REGISTRY_INDEX.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")

print(json.dumps(registry["counts"], ensure_ascii=False, indent=1))
print("WROTE", OUT / "ECOLOGY_REGISTRY.json")
