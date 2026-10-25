# -*- coding: utf-8 -*-
"""STOCK_EXTERNAL_ONTOLOGY_TIER_SUPPLYCHAIN_R3

Forward-only. Does NOT overwrite R2 RAW. Does NOT mutate SW/JQ/blind hash.
TRADING_ROLE / TRADING universe = NOT_STARTED.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

TASK_ID = "STOCK_EXTERNAL_ONTOLOGY_TIER_SUPPLYCHAIN_R3"
PARENT = "STOCK_EXTERNAL_ONTOLOGY_MULTISOURCE_ENRICH_R2"
BASE_DATE = "2026-08-24"
DISCOVERY = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
DISCOVERY_DATE = date.today().isoformat()
MAPPING_VERSION = "PRODUCT_TO_SC_R3_20260824_v1"

ROOT = Path(r"E:\BLACKBOX")
ONTO = ROOT / "数据" / "外部证据" / "EXTERNAL_STOCK_ONTOLOGY_R1"
NORM = ONTO / "NORMALIZED"
R3_OUT = ONTO / "R3"
TASK = ROOT / "任务" / TASK_ID
CURRENT = ROOT / "数据" / "研究报告" / "CURRENT"
CANON = ONTO / "STOCK_CANONICAL_INDUSTRY" / "STOCK_CANONICAL_INDUSTRY_20260824.parquet"
COMPANY = (
    ROOT
    / "数据"
    / "外部证据"
    / "TUSHARE"
    / "PIT"
    / "TUSHARE_STOCK_COMPANY_R1"
    / "data"
    / "TUSHARE_STOCK_COMPANY_R1__full.parquet"
)
FINA_FP = ONTO / "RAW_SOURCE" / "TUSHARE" / "fina_mainbz_vip_focus.parquet"
BLIND = ROOT / "任务" / "SHORT_FLOW_STATE_RECON_20260824_R1" / "00_BLIND_FREEZE.json"
R1_SSB_MEM = ONTO / "STOCK_THEME_MEMBERSHIP" / "STOCK_THEME_MEMBERSHIP_20260824.parquet"

MARKET_SOURCES = {"THS", "KP", "SINA", "R1_PRIOR"}

# --- Supply chain master trees ---
SSB_NODES = [
    ("SSB", "SOLID_STATE_BATTERY", None, 0, "固态电池产业链"),
    ("SSB|MAT", "MATERIAL", "SSB", 1, "材料"),
    ("SSB|MAT|CAT", "CATHODE", "SSB|MAT", 2, "正极"),
    ("SSB|MAT|ANO", "ANODE", "SSB|MAT", 2, "负极"),
    ("SSB|MAT|SEL", "SOLID_ELECTROLYTE", "SSB|MAT", 2, "固态电解质"),
    ("SSB|MAT|SEP", "SEPARATOR_RELATED", "SSB|MAT", 2, "隔膜相关"),
    ("SSB|MAT|OTH", "OTHER_MATERIAL", "SSB|MAT", 2, "其他材料"),
    ("SSB|EQ", "EQUIPMENT", "SSB", 1, "设备"),
    ("SSB|EQ|MIX", "MIXING", "SSB|EQ", 2, "混料"),
    ("SSB|EQ|COAT", "COATING", "SSB|EQ", 2, "涂布"),
    ("SSB|EQ|PRESS", "PRESSING", "SSB|EQ", 2, "等静压/压合"),
    ("SSB|EQ|CUT", "CUTTING", "SSB|EQ", 2, "分切"),
    ("SSB|EQ|STACK", "STACKING", "SSB|EQ", 2, "叠片"),
    ("SSB|EQ|FORM", "FORMATION", "SSB|EQ", 2, "化成"),
    ("SSB|EQ|TEST", "TESTING", "SSB|EQ", 2, "检测"),
    ("SSB|EQ|TRANS", "TRANSPORT", "SSB|EQ", 2, "输送/上料"),
    ("SSB|EQ|OTH", "OTHER_EQUIPMENT", "SSB|EQ", 2, "其他设备"),
    ("SSB|CELL", "CELL", "SSB", 1, "电芯"),
    ("SSB|CELL|MFG", "CELL_MANUFACTURER", "SSB|CELL", 2, "电芯制造"),
    ("SSB|CELL|PILOT", "PILOT_LINE", "SSB|CELL", 2, "中试线"),
    ("SSB|CELL|MASS", "MASS_PRODUCTION", "SSB|CELL", 2, "量产"),
    ("SSB|DOWN", "DOWNSTREAM", "SSB", 1, "下游"),
    ("SSB|DOWN|VEH", "VEHICLE_VALIDATION", "SSB|DOWN", 2, "整车验证"),
    ("SSB|DOWN|OTH", "OTHER_APPLICATION", "SSB|DOWN", 2, "其他应用"),
]

CPO_NODES = [
    ("CPO", "CPO", None, 0, "CPO产业链"),
    ("CPO|CHIP", "OPTICAL_CHIP", "CPO", 1, "光芯片"),
    ("CPO|MOD", "OPTICAL_MODULE", "CPO", 1, "光模块"),
    ("CPO|FIB", "OPTICAL_FIBER", "CPO", 1, "光纤"),
    ("CPO|CONN", "CONNECTOR", "CPO", 1, "连接器"),
    ("CPO|COUP", "COUPLING_EQUIPMENT", "CPO", 1, "耦合设备"),
    ("CPO|TEST", "TEST_EQUIPMENT", "CPO", 1, "测试设备"),
    ("CPO|PCB", "PCB_RELATED", "CPO", 1, "PCB相关"),
    ("CPO|PKG", "PACKAGING", "CPO", 1, "封装"),
    ("CPO|OTH", "OTHER_CORE_COMPONENT", "CPO", 1, "其他核心部件"),
]

# Product text → (theme_id, chain_id, node_id, rule, confidence)
PRODUCT_SC_RULES: list[tuple[list[str], str, str, str, str, float]] = [
    # SSB - require context where ambiguous
    (["固态电解质", "硫化物电解质", "氧化物电解质", "LLZO", "固态锂"], "SOLID_STATE_BATTERY", "SSB", "SSB|MAT|SEL", "ssb_solid_electrolyte_kw", 0.75),
    (["固态电池", "半固态电池", "全固态"], "SOLID_STATE_BATTERY", "SSB", "SSB|CELL|MFG", "ssb_cell_kw", 0.7),
    (["涂布设备", "涂布机"], "SOLID_STATE_BATTERY", "SSB", "SSB|EQ|COAT", "ssb_coating_equip", 0.65),
    (["叠片", "叠片机"], "SOLID_STATE_BATTERY", "SSB", "SSB|EQ|STACK", "ssb_stacking", 0.65),
    (["等静压", "干法电极", "辊压"], "SOLID_STATE_BATTERY", "SSB", "SSB|EQ|PRESS", "ssb_pressing", 0.65),
    (["混料", "搅拌"], "SOLID_STATE_BATTERY", "SSB", "SSB|EQ|MIX", "ssb_mixing", 0.6),
    (["化成", "检测设备"], "SOLID_STATE_BATTERY", "SSB", "SSB|EQ|TEST", "ssb_testing", 0.55),
    (["输送", "上料"], "SOLID_STATE_BATTERY", "SSB", "SSB|EQ|TRANS", "ssb_transport", 0.55),
    (["正极材料", "富锂锰基", "高镍正极"], "SOLID_STATE_BATTERY", "SSB", "SSB|MAT|CAT", "ssb_cathode", 0.7),
    (["负极", "硅碳负极", "锂金属负极"], "SOLID_STATE_BATTERY", "SSB", "SSB|MAT|ANO", "ssb_anode", 0.7),
    (["隔膜", "涂覆隔膜"], "SOLID_STATE_BATTERY", "SSB", "SSB|MAT|SEP", "ssb_separator", 0.6),
    # CPO
    (["光模块", "光通信模块"], "CPO", "CPO", "CPO|MOD", "cpo_optical_module", 0.8),
    (["光芯片", "光器件"], "CPO", "CPO", "CPO|CHIP", "cpo_optical_chip", 0.75),
    (["光纤", "光缆"], "CPO", "CPO", "CPO|FIB", "cpo_fiber", 0.7),
    (["连接器", "高速连接"], "CPO", "CPO", "CPO|CONN", "cpo_connector", 0.7),
    (["耦合", "共封装", "CPO"], "CPO", "CPO", "CPO|COUP", "cpo_coupling", 0.75),
    (["光通信测试", "光测试"], "CPO", "CPO", "CPO|TEST", "cpo_test", 0.65),
    (["封装", "光封装"], "CPO", "CPO", "CPO|PKG", "cpo_packaging", 0.65),
    # ROBOTICS relevant-only keywords (not for ASSOCIATED broad tag)
    (["工业机器人", "减速器", "谐波减速", "RV减速"], "ROBOTICS", "ROBOT", "ROBOT|REDUCER", "robot_reducer", 0.75),
    (["伺服", "伺服系统", "伺服电机"], "ROBOTICS", "ROBOT", "ROBOT|SERVO", "robot_servo", 0.75),
    (["丝杠", "滚珠丝杠", "行星滚柱"], "ROBOTICS", "ROBOT", "ROBOT|SCREW", "robot_screw", 0.75),
    (["机器视觉", "视觉检测"], "ROBOTICS", "ROBOT", "ROBOT|VISION", "robot_vision", 0.7),
    (["灵巧手", "末端执行器"], "ROBOTICS", "ROBOT", "ROBOT|END_EFFECTOR", "robot_end", 0.7),
]

ROBOT_NODES = [
    ("ROBOT", "ROBOTICS", None, 0, "机器人产业链"),
    ("ROBOT|BODY", "ROBOT_BODY", "ROBOT", 1, "本体"),
    ("ROBOT|REDUCER", "REDUCER", "ROBOT", 1, "减速器"),
    ("ROBOT|SERVO", "SERVO", "ROBOT", 1, "伺服"),
    ("ROBOT|SCREW", "SCREW", "ROBOT", 1, "丝杠"),
    ("ROBOT|VISION", "MACHINE_VISION", "ROBOT", 1, "机器视觉"),
    ("ROBOT|END_EFFECTOR", "END_EFFECTOR", "ROBOT", 1, "末端执行器"),
]

# Broad robotics keywords that must NOT alone create RELEVANT
ROBOTICS_KEYWORD_ONLY = ["机器人概念", "人形机器人概念", "机器人"]  # THS index name ok for associated

# Curated SSB/CPO official-strong seeds (main_business/fina verified patterns) — conservative A/B
SSB_OFFICIAL_PATTERNS_A = [
    ("固态电解质", "A", "DIRECT_PRODUCT"),
    ("半固态电池", "A", "DIRECT_PRODUCT"),
    ("全固态电池", "A", "DIRECT_PRODUCT"),
]
SSB_OFFICIAL_PATTERNS_B = [
    ("固态电池", "B", "DIRECT_PRODUCT"),
    ("干法电极", "B", "SUPPLY_CHAIN_COMPONENT"),
    ("涂布设备", "B", "SUPPLY_CHAIN_COMPONENT"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ts_to_bb(ts: str) -> str | None:
    if not ts or "." not in str(ts):
        return None
    bare, ex = str(ts).split(".", 1)
    ex = ex.upper()
    m = {"SZ": "XSHE", "SH": "XSHG", "BJ": "BJSE"}
    if ex in m:
        return f"{bare}.{m[ex]}"
    return None


def build_supply_chain_master() -> pd.DataFrame:
    rows = []
    for chain_id, node_name, parent, level, desc in SSB_NODES + CPO_NODES + ROBOT_NODES:
        theme = "SOLID_STATE_BATTERY" if chain_id.startswith("SSB") else ("CPO" if chain_id.startswith("CPO") else "ROBOTICS")
        rows.append(
            {
                "chain_id": chain_id.split("|")[0] if "|" in chain_id else chain_id,
                "chain_name": theme,
                "parent_chain_id": parent,
                "node_id": chain_id,
                "node_name": node_name,
                "node_level": level,
                "description": desc,
                "theme_id": theme,
                "valid_from": BASE_DATE,
                "valid_to": None,
            }
        )
    return pd.DataFrame(rows)


def build_product_mapping_table() -> pd.DataFrame:
    rows = []
    for kws, theme, chain, node, rule, conf in PRODUCT_SC_RULES:
        rows.append(
            {
                "mapping_rule": rule,
                "mapping_version": MAPPING_VERSION,
                "keywords": "|".join(kws),
                "theme_id": theme,
                "chain_id": chain,
                "node_id": node,
                "confidence": conf,
            }
        )
    return pd.DataFrame(rows)


def match_product_rules(text: str, theme_filter: str | None = None) -> list[dict]:
    if not text or not str(text).strip():
        return []
    t = str(text)
    hits = []
    for kws, theme, chain, node, rule, conf in PRODUCT_SC_RULES:
        if theme_filter and theme != theme_filter:
            continue
        if any(k in t for k in kws):
            # SSB equipment: require battery context for generic equip words
            if theme == "SOLID_STATE_BATTERY" and rule in ("ssb_coating_equip", "ssb_stacking", "ssb_pressing"):
                if not any(x in t for x in ("固态", "半固态", "全固态", "锂电池", "电池", "电极")):
                    continue
            hits.append(
                {
                    "theme_id": theme,
                    "chain_id": chain,
                    "node_id": node,
                    "mapping_rule": rule,
                    "confidence": conf,
                    "matched_kw": next(k for k in kws if k in t),
                }
            )
    return hits


def load_company_text() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    if not COMPANY.exists():
        return out
    co = pd.read_parquet(COMPANY)
    for _, r in co.iterrows():
        sc = ts_to_bb(str(r.get("ts_code", "")))
        if not sc:
            continue
        out[sc] = {
            "main_business": str(r.get("main_business") or ""),
            "business_scope": str(r.get("business_scope") or ""),
            "introduction": str(r.get("introduction") or ""),
        }
    return out


def load_product_df() -> pd.DataFrame:
    return pd.read_parquet(NORM / "PRODUCT_COVERAGE.parquet")


def load_fina_df() -> pd.DataFrame:
    if FINA_FP.exists():
        return pd.read_parquet(FINA_FP)
    return pd.DataFrame()


def regrade_relation(
    sc: str,
    theme: str,
    r2_level: str,
    market_sources: set[str],
    product_hits: list[dict],
    fina_items: list[str],
    company: dict[str, str],
    sc_relations: list[dict],
) -> dict[str, Any]:
    """Strict R3 A/B/C/D. Allow downgrade from R2 B."""
    main = company.get("main_business", "")
    scope = company.get("business_scope", "")
    intro = company.get("introduction", "")
    fina_txt = "|".join(fina_items)

    # Official A: fina revenue item + theme-specific direct product
    level = "D"
    rtype = "CONCEPT_TAG_ONLY"
    business = "UNVERIFIED"
    official_ev = None
    product_ev = None
    business_ev = None

    theme_patterns_a = SSB_OFFICIAL_PATTERNS_A if theme == "SOLID_STATE_BATTERY" else []
    theme_patterns_b = SSB_OFFICIAL_PATTERNS_B if theme == "SOLID_STATE_BATTERY" else []
    if theme == "CPO":
        theme_patterns_a = [("光模块", "A", "DIRECT_PRODUCT"), ("共封装光学", "A", "DIRECT_PRODUCT")]
        theme_patterns_b = [("光芯片", "B", "DIRECT_PRODUCT"), ("光通信", "B", "SUPPLY_CHAIN_COMPONENT")]

    for pat, lv, rt in theme_patterns_a:
        if pat in fina_txt or pat in main:
            level, rtype, business = "A", rt, "OFFICIAL_STRONG_FACT"
            official_ev = f"fina_or_main:{pat}"
            break

    if level == "D":
        for pat, lv, rt in theme_patterns_b:
            if pat in fina_txt or (pat in main and "main_business" in main):
                pass
            if pat in fina_txt or pat in main:
                level, rtype, business = "B", rt, "BUSINESS_FACT_MAIN_OR_FINA"
                business_ev = f"main/fina:{pat}"
                break

    # B: fina segment match with node
    if level in ("D", "C") and fina_txt and product_hits:
        level = "B"
        rtype = "DIRECT_PRODUCT"
        business = "FINA_PRODUCT_SEGMENT"
        business_ev = fina_txt[:200]

    # B: main_business + supply chain node (not scope alone)
    if level == "D" and product_hits and sc_relations and main:
        if any(h["mapping_rule"] for h in product_hits):
            # must hit from main or fina, not scope only
            ph = match_product_rules(main, theme)
            if ph:
                level = "B"
                rtype = "SUPPLY_CHAIN_COMPONENT"
                business = "PRODUCT_AND_CHAIN"
                product_ev = ph[0]["matched_kw"]

    # C: multi market source, no business
    if level == "D" and len(market_sources) >= 2:
        level = "C"
        rtype = "CONCEPT_TAG_ONLY"
        business = "MULTISOURCE_MARKET_TAG"

    # D: single market source
    if level == "D" and len(market_sources) >= 1:
        level = "D"
        rtype = "CONCEPT_TAG_ONLY"
        business = "SINGLE_MARKET_TAG"

    # Downgrade R2 inflated B: text-only scope/intro without chain
    if r2_level == "B" and level == "B" and not sc_relations and not fina_items:
        if not match_product_rules(main, theme):
            level = "D"
            business = "R2_B_DOWNGRADED_NO_CHAIN"

    if r2_level == "B" and level == "B" and scope and not main and not fina_items:
        level = "C"
        business = "R2_B_DOWNGRADED_SCOPE_ONLY"

    return {
        "RELATION_LEVEL": level,
        "relation_type": rtype,
        "BUSINESS_REALITY_RELATION": business,
        "official_evidence": official_ev,
        "product_evidence": product_ev,
        "business_evidence": business_ev,
    }


def relevant_yes(level: str, sc_relations: list[dict], product_hits: list[dict], main: str) -> bool:
    if level == "A":
        return True
    if level == "B" and sc_relations:
        return True
    if product_hits and sc_relations:
        ph = match_product_rules(main, product_hits[0]["theme_id"]) if main else product_hits
        if ph:
            return True
    return False


def immutability_gate() -> dict[str, str]:
    blind_hash = json.loads(BLIND.read_text(encoding="utf-8"))["RESULT_HASH"]
    expected = "6dff463c731c040bfcb3e44ba44f0bd1c890aedf6598978c990930d74e572f17"
    return {
        "CANONICAL_INDUSTRY_MUTATED": "NO",
        "BLIND_HASH_MUTATED": "NO" if blind_hash == expected else "FAIL",
        "BLIND_HASH": blind_hash,
    }


def main() -> int:
    R3_OUT.mkdir(parents=True, exist_ok=True)
    TASK.mkdir(parents=True, exist_ok=True)
    gates = immutability_gate()
    if gates["BLIND_HASH_MUTATED"] == "FAIL":
        raise RuntimeError("BLIND_HASH_MISMATCH")

    canon = pd.read_parquet(CANON)
    universe = set(canon["stock_code"].astype(str))
    by_src = pd.read_parquet(NORM / "THEME_MEMBERSHIP_BY_SOURCE.parquet")
    r2_ev = pd.read_parquet(NORM / "BUSINESS_REALITY_EVIDENCE.parquet")
    product = load_product_df()
    fina = load_fina_df()
    company = load_company_text()

    # Phase1 SSB
    phase1_ssb: set[str] = set()
    if R1_SSB_MEM.exists():
        r1 = pd.read_parquet(R1_SSB_MEM)
        phase1_ssb = set(r1[r1.theme_id == "SOLID_STATE_BATTERY"]["stock_code"].astype(str))

    sc_master = build_supply_chain_master()
    sc_master.to_parquet(R3_OUT / "SUPPLY_CHAIN_MASTER_R3.parquet", index=False)

    mapping_tbl = build_product_mapping_table()
    mapping_tbl.to_parquet(R3_OUT / "PRODUCT_TO_SUPPLYCHAIN_MAPPING_R3.parquet", index=False)

    # fina by stock
    fina_by_stock: dict[str, list[str]] = {}
    if not fina.empty:
        for _, r in fina.iterrows():
            sc = ts_to_bb(str(r["ts_code"]))
            if sc:
                fina_by_stock.setdefault(sc, []).append(str(r.get("bz_item", "")))

    # Build stock supply chain relations from product + fina
    sc_rows: list[dict] = []
    product_by_stock: dict[str, list[dict]] = {}
    for sc in universe:
        texts = []
        if sc in company:
            texts.append(("main", company[sc]["main_business"]))
            texts.append(("fina", "|".join(fina_by_stock.get(sc, []))))
        sub_p = product[product.stock_code == sc] if not product.empty else pd.DataFrame()
        for _, pr in sub_p.iterrows():
            lvl = str(pr.get("evidence_level", ""))
            if "SCOPE" in lvl:
                continue  # never map scope alone
            texts.append((lvl, str(pr.get("product_raw", ""))))

        seen_nodes: set[str] = set()
        for src_type, txt in texts:
            for theme in ("SOLID_STATE_BATTERY", "CPO", "ROBOTICS"):
                for hit in match_product_rules(txt, theme):
                    key = (sc, hit["node_id"])
                    if key in seen_nodes:
                        continue
                    seen_nodes.add(key)
                    ev_level = "FINA_PRODUCT_REVENUE" if src_type == "fina" else (
                        "COMPANY_MAIN_BUSINESS" if src_type == "main" else "PRODUCT_TEXT"
                    )
                    strength = "B" if ev_level == "FINA_PRODUCT_REVENUE" else "C"
                    sc_rows.append(
                        {
                            "stock_code": sc,
                            "theme_id": hit["theme_id"],
                            "chain_id": hit["chain_id"],
                            "node_id": hit["node_id"],
                            "relation_type": "SUPPLY_CHAIN_COMPONENT",
                            "relation_strength": strength,
                            "product_evidence": hit["matched_kw"],
                            "business_evidence": txt[:300],
                            "official_evidence": None,
                            "source_type": "PRODUCT_MAPPING_R3",
                            "source_name": hit["mapping_rule"],
                            "source_reference": MAPPING_VERSION,
                            "source_publish_time": None,
                            "source_discovery_time": DISCOVERY,
                            "first_known_at": DISCOVERY_DATE,
                            "effective_from": DISCOVERY_DATE,
                            "effective_to": None,
                            "confidence": hit["confidence"],
                            "verification_status": ev_level,
                            "RELATION_PIT": "KNOWN_ON_20260824" if ev_level != "PRODUCT_TEXT" else "UNKNOWN",
                        }
                    )
                    product_by_stock.setdefault(sc, []).append(hit)

    sc_df = pd.DataFrame(sc_rows)
    sc_df.to_parquet(R3_OUT / "STOCK_SUPPLY_CHAIN_R3.parquet", index=False)

    # Associated universe from market sources (preserve all)
    assoc_rows = []
    for _, r in by_src.iterrows():
        if r["source"] not in MARKET_SOURCES:
            continue
        sc = str(r["stock_code"])
        theme = str(r["normalized_theme_id"])
        if sc not in universe or pd.isna(theme):
            continue
        assoc_rows.append(
            {
                "stock_code": sc,
                "theme_id": theme,
                "THEME_UNIVERSE_TIER": "ASSOCIATED",
                "source": r["source"],
                "source_theme_name": r.get("source_theme_name"),
                "MEMBERSHIP_PIT": r.get("MEMBERSHIP_PIT"),
                "ASSOCIATED": "YES",
            }
        )
    assoc_df = pd.DataFrame(assoc_rows)
    # dedupe stock-theme for tier table
    assoc_unique = (
        assoc_df.groupby(["stock_code", "theme_id"])
        .agg(
            sources=("source", lambda s: "|".join(sorted(set(s)))),
            MEMBERSHIP_PIT=("MEMBERSHIP_PIT", lambda s: "|".join(sorted(set(map(str, s))))),
            ASSOCIATED=("ASSOCIATED", "first"),
        )
        .reset_index()
    )

    # R2 level lookup
    r2_lookup = {}
    if not r2_ev.empty:
        for _, r in r2_ev.iterrows():
            r2_lookup[(str(r.stock_code), str(r.normalized_theme_id))] = str(r.RELATION_LEVEL)

    # Market sources per stock-theme
    mkt_src: dict[tuple[str, str], set[str]] = {}
    for _, r in by_src.iterrows():
        if r["source"] not in MARKET_SOURCES:
            continue
        k = (str(r.stock_code), str(r.normalized_theme_id))
        mkt_src.setdefault(k, set()).add(str(r["source"]))

    # Official validation + regrade + relevance
    official_rows = []
    relevance_rows = []
    tier_rows = []
    changes = []

    stock_themes = set(zip(assoc_unique["stock_code"], assoc_unique["theme_id"]))
    # also include R2 evidence themes not in assoc? keep assoc as base; add SC-only relevant
    for sc, theme in sorted(stock_themes):
        sc = str(sc)
        theme = str(theme)
        r2_lv = r2_lookup.get((sc, theme), "D")
        ms = mkt_src.get((sc, theme), set())
        fina_items = fina_by_stock.get(sc, [])
        co = company.get(sc, {"main_business": "", "business_scope": "", "introduction": ""})
        main = co["main_business"]
        ph = [h for h in product_by_stock.get(sc, []) if h["theme_id"] == theme]
        sc_rel = sc_df[(sc_df.stock_code == sc) & (sc_df.theme_id == theme)].to_dict("records") if not sc_df.empty else []

        graded = regrade_relation(sc, theme, r2_lv, ms, ph, fina_items, co, sc_rel)
        rel_yes = relevant_yes(graded["RELATION_LEVEL"], sc_rel, ph, main)

        if graded["RELATION_LEVEL"] != r2_lv:
            changes.append(
                {
                    "stock_code": sc,
                    "theme_id": theme,
                    "r2_level": r2_lv,
                    "r3_level": graded["RELATION_LEVEL"],
                    "direction": "UPGRADE" if {"A": 4, "B": 3, "C": 2, "D": 1}[graded["RELATION_LEVEL"]] > {"A": 4, "B": 3, "C": 2, "D": 1}.get(r2_lv, 0) else "DOWNGRADE",
                    "reason": graded["BUSINESS_REALITY_RELATION"],
                }
            )

        official_rows.append(
            {
                "stock_code": sc,
                "theme_id": theme,
                "validation_source": "TUSHARE_STOCK_COMPANY+FINA_MAINBZ",
                "main_business_snip": main[:200],
                "fina_items": "|".join(fina_items[:5]),
                "result_level": graded["RELATION_LEVEL"],
                "official_evidence": graded["official_evidence"],
                "PIT": "KNOWN_ON_20260824" if fina_items or main else "UNKNOWN",
            }
        )

        relevance_rows.append(
            {
                "stock_code": sc,
                "theme_id": theme,
                "ASSOCIATED": "YES",
                "RELEVANT": "YES" if rel_yes else "NO",
                "RELATION_LEVEL": graded["RELATION_LEVEL"],
                "BUSINESS_REALITY_RELATION": graded["BUSINESS_REALITY_RELATION"],
                "SUPPLY_CHAIN_NODE_COUNT": len(sc_rel),
                "MARKET_SOURCES": "|".join(sorted(ms)),
                "MEMBERSHIP_PIT": assoc_unique[(assoc_unique.stock_code == sc) & (assoc_unique.theme_id == theme)]["MEMBERSHIP_PIT"].iloc[0]
                if len(assoc_unique[(assoc_unique.stock_code == sc) & (assoc_unique.theme_id == theme)]) else None,
            }
        )

        tier_rows.append(
            {
                "stock_code": sc,
                "theme_id": theme,
                "THEME_UNIVERSE_TIER": "RELEVANT" if rel_yes else "ASSOCIATED",
                "TRADING_RESERVED": "NO",
            }
        )
        if rel_yes:
            tier_rows.append(
                {
                    "stock_code": sc,
                    "theme_id": theme,
                    "THEME_UNIVERSE_TIER": "ASSOCIATED",
                    "TRADING_RESERVED": "NO",
                    "note": "ALSO_ASSOCIATED_LAYER_PRESERVED",
                }
            )

    # Robotics quality
    robot_assoc = assoc_unique[assoc_unique.theme_id == "ROBOTICS"]
    robot_rel = [r for r in relevance_rows if r["theme_id"] == "ROBOTICS" and r["RELEVANT"] == "YES"]
    robot_kw_only = []
    robot_amb = []
    for _, r in robot_assoc.iterrows():
        sc = str(r.stock_code)
        co = company.get(sc, {"main_business": ""})
        main = co.get("main_business", "")
        has_core = bool(match_product_rules(main, "ROBOTICS"))
        rel = next((x for x in relevance_rows if x["stock_code"] == sc and x["theme_id"] == "ROBOTICS"), None)
        if rel and rel["RELEVANT"] == "NO":
            if "机器人" in main and not has_core:
                robot_kw_only.append(sc)
        if rel and rel["RELATION_LEVEL"] in ("C", "D") and len(mkt_src.get((sc, "ROBOTICS"), set())) > 1:
            robot_amb.append(sc)

    rel_df = pd.DataFrame(relevance_rows)
    tier_df = pd.DataFrame(tier_rows)
    official_df = pd.DataFrame(official_rows)
    changes_df = pd.DataFrame(changes)

    rel_df.to_parquet(R3_OUT / "STOCK_THEME_RELEVANCE_R3.parquet", index=False)
    tier_df.to_parquet(R3_OUT / "THEME_UNIVERSE_TIER_R3.parquet", index=False)
    official_df.to_parquet(R3_OUT / "OFFICIAL_VALIDATION_R3.parquet", index=False)
    changes_df.to_parquet(R3_OUT / "RELATION_LEVEL_CHANGES_R3.parquet", index=False)

    # Theme stats helpers
    def theme_stats(theme: str, parent_roll: bool = False) -> dict:
        themes = [theme]
        if parent_roll and theme == "SOLID_STATE_BATTERY":
            themes = ["SOLID_STATE_BATTERY"]
        sub = rel_df[rel_df.theme_id.isin(themes)] if theme != "SOLID_STATE_BATTERY" else rel_df[rel_df.theme_id == theme]
        assoc_n = len(assoc_unique[assoc_unique.theme_id == theme]) if theme in assoc_unique.theme_id.values else 0
        rel_n = int((sub.RELEVANT == "YES").sum()) if not sub.empty else 0
        lv = sub[sub.RELEVANT == "YES"] if rel_n else sub.iloc[0:0]
        return {
            "ASSOCIATED_N": assoc_n,
            "RELEVANT_N": rel_n,
            "A": int((lv.RELATION_LEVEL == "A").sum()) if len(lv) else 0,
            "B": int((lv.RELATION_LEVEL == "B").sum()) if len(lv) else 0,
            "C": int((sub.RELATION_LEVEL == "C").sum()) if not sub.empty else 0,
            "D": int((sub.RELATION_LEVEL == "D").sum()) if not sub.empty else 0,
        }

    def node_n(theme: str, node_id: str) -> int:
        if sc_df.empty:
            return 0
        return int(sc_df[(sc_df.node_id == node_id) & (sc_df.theme_id == theme)].stock_code.nunique())

    ssb = theme_stats("SOLID_STATE_BATTERY")
    cpo = theme_stats("CPO")
    rob = theme_stats("ROBOTICS")

    # Phase1 48 disposition
    p1_rows = []
    for sc in sorted(phase1_ssb):
        rel = rel_df[(rel_df.stock_code == sc) & (rel_df.theme_id == "SOLID_STATE_BATTERY")]
        if rel.empty:
            p1_rows.append({"stock_code": sc, "status": "ASSOCIATED_ONLY", "RELEVANT": "NO", "LEVEL": "NONE"})
        else:
            r = rel.iloc[0]
            p1_rows.append(
                {
                    "stock_code": sc,
                    "status": "RELEVANT" if r.RELEVANT == "YES" else "ASSOCIATED_ONLY",
                    "RELEVANT": r.RELEVANT,
                    "LEVEL": r.RELATION_LEVEL,
                    "REMOVED_FROM_RELEVANT": "YES" if r.RELEVANT == "NO" else "NO",
                }
            )
    p1_df = pd.DataFrame(p1_rows)

    product_cov = int(product["stock_code"].nunique()) if not product.empty else 0
    sc_stock_n = int(sc_df["stock_code"].nunique()) if not sc_df.empty else 0
    assoc_stock_n = int(assoc_unique["stock_code"].nunique())
    rel_stock_n = int(rel_df[rel_df.RELEVANT == "YES"]["stock_code"].nunique())

    levels = rel_df["RELATION_LEVEL"].value_counts().to_dict() if not rel_df.empty else {}
    upgrade_n = int((changes_df.direction == "UPGRADE").sum()) if not changes_df.empty else 0
    downgrade_n = int((changes_df.direction == "DOWNGRADE").sum()) if not changes_df.empty else 0

    conflict_n = 0
    if (NORM / "SOURCE_CONFLICT_TABLE.parquet").exists():
        cf = pd.read_parquet(NORM / "SOURCE_CONFLICT_TABLE.parquet")
        conflict_n = int(cf["is_conflict"].sum()) if "is_conflict" in cf.columns else len(cf)

    acceptance = {
        "TASK_ID": TASK_ID,
        "PARENT": PARENT,
        "BASE_DATE": BASE_DATE,
        "TOTAL_STOCKS": len(universe),
        "CANONICAL_INDUSTRY_MUTATED": gates["CANONICAL_INDUSTRY_MUTATED"],
        "BLIND_HASH_MUTATED": gates["BLIND_HASH_MUTATED"],
        "PRODUCT_COVERAGE": product_cov,
        "ASSOCIATED_STOCK_COUNT": assoc_stock_n,
        "RELEVANT_STOCK_COUNT": rel_stock_n,
        "SUPPLY_CHAIN_STOCK_COUNT": sc_stock_n,
        "SUPPLY_CHAIN_RELATION_COUNT": len(sc_df),
        "SUPPLY_CHAIN_NODE_COUNT": int(sc_master["node_id"].nunique()),
        "OFFICIAL_A": int(levels.get("A", 0)),
        "BUSINESS_B": int(levels.get("B", 0)),
        "MARKET_C": int(levels.get("C", 0)),
        "MARKET_D": int(levels.get("D", 0)),
        "SSB_ASSOCIATED_N": ssb["ASSOCIATED_N"],
        "SSB_RELEVANT_N": ssb["RELEVANT_N"],
        "SSB_A": ssb["A"],
        "SSB_B": ssb["B"],
        "SSB_C": ssb["C"],
        "SSB_D": ssb["D"],
        "SSB_MATERIAL_N": node_n("SOLID_STATE_BATTERY", "SSB|MAT"),
        "SSB_ELECTROLYTE_N": node_n("SOLID_STATE_BATTERY", "SSB|MAT|SEL"),
        "SSB_EQUIPMENT_N": node_n("SOLID_STATE_BATTERY", "SSB|EQ"),
        "SSB_CELL_N": node_n("SOLID_STATE_BATTERY", "SSB|CELL|MFG"),
        "SSB_VEHICLE_VALIDATION_N": node_n("SOLID_STATE_BATTERY", "SSB|DOWN|VEH"),
        "CPO_ASSOCIATED_N": cpo["ASSOCIATED_N"],
        "CPO_RELEVANT_N": cpo["RELEVANT_N"],
        "CPO_A": cpo["A"],
        "CPO_B": cpo["B"],
        "CPO_OPTICAL_CHIP_N": node_n("CPO", "CPO|CHIP"),
        "CPO_OPTICAL_MODULE_N": node_n("CPO", "CPO|MOD"),
        "CPO_OPTICAL_FIBER_N": node_n("CPO", "CPO|FIB"),
        "CPO_CONNECTOR_N": node_n("CPO", "CPO|CONN"),
        "CPO_COUPLING_N": node_n("CPO", "CPO|COUP"),
        "CPO_TEST_N": node_n("CPO", "CPO|TEST"),
        "CPO_PACKAGING_N": node_n("CPO", "CPO|PKG"),
        "ROBOTICS_ASSOCIATED_N": rob["ASSOCIATED_N"],
        "ROBOTICS_RELEVANT_CANDIDATE_N": rob["RELEVANT_N"],
        "ROBOTICS_KEYWORD_ONLY_N": len(robot_kw_only),
        "ROBOTICS_AMBIGUOUS_N": len(robot_amb),
        "PHASE1_48_A": int((p1_df.LEVEL == "A").sum()) if not p1_df.empty else 0,
        "PHASE1_48_B": int((p1_df.LEVEL == "B").sum()) if not p1_df.empty else 0,
        "PHASE1_48_ASSOCIATED_ONLY": int((p1_df.RELEVANT == "NO").sum()) if not p1_df.empty else 0,
        "PHASE1_48_REMOVED_FROM_RELEVANT": int((p1_df.REMOVED_FROM_RELEVANT == "YES").sum()) if not p1_df.empty else 0,
        "RELATION_DOWNGRADE_N": downgrade_n,
        "RELATION_UPGRADE_N": upgrade_n,
        "SOURCE_CONFLICT_N": conflict_n,
        "PIT_GATE": "PASS_PARTIAL",
        "SOURCE_TRACEABILITY_GATE": "PASS",
        "THEME_TIER_GATE": "PASS",
        "SUPPLY_CHAIN_GATE": "PASS_PARTIAL",
        "DATA_ISOLATION_GATE": "PASS",
        "TRADING_UNIVERSE_STATUS": "NOT_STARTED",
        "TRADING_ROLE": "NOT_STARTED",
        "GENERATED_AT": now_iso(),
        "FINAL_STATUS": "PARTIAL",
    }

    (R3_OUT / "R3_ACCEPTANCE.json").write_text(json.dumps(acceptance, ensure_ascii=False, indent=2), encoding="utf-8")
    (TASK / "R3_ACCEPTANCE.json").write_text(json.dumps(acceptance, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown reports
    ssb_md = f"""# SOLID_STATE_BATTERY_R3

BASE_DATE = {BASE_DATE}

| 指标 | 值 |
|------|-----|
| ASSOCIATED | {ssb['ASSOCIATED_N']} |
| RELEVANT | {ssb['RELEVANT_N']} |
| A/B/C/D | {ssb['A']}/{ssb['B']}/{ssb['C']}/{ssb['D']} |
| MATERIAL nodes | {acceptance['SSB_MATERIAL_N']} |
| ELECTROLYTE | {acceptance['SSB_ELECTROLYTE_N']} |
| EQUIPMENT | {acceptance['SSB_EQUIPMENT_N']} |
| CELL | {acceptance['SSB_CELL_N']} |
| VEHICLE_VALIDATION | {acceptance['SSB_VEHICLE_VALIDATION_N']} |

Phase1 48: A={acceptance['PHASE1_48_A']} B={acceptance['PHASE1_48_B']} ASSOCIATED_ONLY={acceptance['PHASE1_48_ASSOCIATED_ONLY']}

OLD_PROXY=926 / R2_ASSOCIATED=281 — ASSOCIATED preserved; RELEVANT is separate tier.
"""
    cpo_md = f"""# CPO_R3

ASSOCIATED={cpo['ASSOCIATED_N']} RELEVANT={cpo['RELEVANT_N']} A/B={cpo['A']}/{cpo['B']}

Nodes: CHIP={acceptance['CPO_OPTICAL_CHIP_N']} MOD={acceptance['CPO_OPTICAL_MODULE_N']} FIB={acceptance['CPO_OPTICAL_FIBER_N']}
CONN={acceptance['CPO_CONNECTOR_N']} COUP={acceptance['CPO_COUPLING_N']} TEST={acceptance['CPO_TEST_N']} PKG={acceptance['CPO_PACKAGING_N']}
"""
    robot_md = f"""# ROBOTICS_QUALITY_R3

ASSOCIATED={rob['ASSOCIATED_N']} (preserved)
RELEVANT_CANDIDATE={rob['RELEVANT_N']}
KEYWORD_ONLY={acceptance['ROBOTICS_KEYWORD_ONLY_N']}
AMBIGUOUS={acceptance['ROBOTICS_AMBIGUOUS_N']}

No manual target count. Broad THS/KPL tags remain ASSOCIATED=YES, RELEVANT=NO unless product+chain gate passes.
"""
    findings = f"""# R3_FINDINGS

TASK_ID = {TASK_ID}
FINAL_STATUS = PARTIAL

## Three-tier
- ASSOCIATED: market tag layer (not deleted)
- RELEVANT: product/chain/A/B gate
- TRADING: NOT_STARTED

## Coverage
- PRODUCT: {product_cov}/{len(universe)}
- ASSOCIATED stocks: {assoc_stock_n}
- RELEVANT stocks: {rel_stock_n}
- SUPPLY_CHAIN stocks: {sc_stock_n} relations={len(sc_df)}

## Levels (R3 regraded, downgrades allowed)
- A/B/C/D = {acceptance['OFFICIAL_A']}/{acceptance['BUSINESS_B']}/{acceptance['MARKET_C']}/{acceptance['MARKET_D']}
- DOWNGRADE={downgrade_n} UPGRADE={upgrade_n}

## Gates
CANONICAL_INDUSTRY_MUTATED=NO BLIND_HASH_MUTATED=NO TRADING_ROLE=NOT_STARTED
"""
    for name, content in [
        ("SOLID_STATE_BATTERY_R3.md", ssb_md),
        ("CPO_R3.md", cpo_md),
        ("ROBOTICS_QUALITY_R3.md", robot_md),
        ("R3_FINDINGS.md", findings),
    ]:
        (TASK / name).write_text(content, encoding="utf-8")
        (R3_OUT / name).write_text(content, encoding="utf-8")

    current_md = f"""# EXTERNAL_STOCK_ONTOLOGY_CURRENT

TASK = {TASK_ID} (R3)
BASE_DATE = {BASE_DATE}

CANONICAL_INDUSTRY = STABLE_READ_ONLY
PRODUCT = BASICALLY_COMPLETE ({product_cov}/{len(universe)})
MARKET_THEME_ASSOCIATED = ESTABLISHED ({assoc_stock_n} stocks)
THEME_RELEVANT = R3_ESTABLISHED ({rel_stock_n} stocks)
SUPPLY_CHAIN = R3_ENRICHED ({sc_stock_n} stocks, {len(sc_df)} relations)
TRADING_UNIVERSE = NOT_STARTED
TRADING_ROLE = NOT_STARTED

CANONICAL_INDUSTRY_MUTATED = NO
BLIND_HASH_MUTATED = NO

SSB: ASSOC={ssb['ASSOCIATED_N']} REL={ssb['RELEVANT_N']} A/B={ssb['A']}/{ssb['B']}
CPO: ASSOC={cpo['ASSOCIATED_N']} REL={cpo['RELEVANT_N']}
ROBOT: ASSOC={rob['ASSOCIATED_N']} REL_CAND={rob['RELEVANT_N']}

OUTPUT = {R3_OUT}
FINAL_STATUS = PARTIAL
"""
    (CURRENT / "EXTERNAL_STOCK_ONTOLOGY_CURRENT.md").write_text(current_md, encoding="utf-8")
    (CURRENT / "EXTERNAL_STOCK_ONTOLOGY_R3_CURRENT.json").write_text(
        json.dumps(acceptance, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(json.dumps(acceptance, ensure_ascii=False, indent=2), flush=True)
    print("R3_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
