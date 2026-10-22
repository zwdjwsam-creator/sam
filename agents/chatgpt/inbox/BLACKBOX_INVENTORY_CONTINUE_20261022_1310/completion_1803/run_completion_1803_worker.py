# -*- coding: utf-8 -*-
"""1803: DIRECTORY_OVERVIEW_L4 + same-set domain join + scope map + engine real/static fix."""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pyarrow.parquet as pq

CN = timezone(timedelta(hours=8))
NOW = datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S+08:00")
OUT = Path(__file__).resolve().parent
PREV1752 = OUT.parent / "completion_1752"
HUB = Path(r"E:\BLACKBOX\运行\外部大脑信箱")
INBOX = HUB / "agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1803"
REPO = "agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1803"
PUSH = HUB / "_hub_push_files.py"
PY = sys.executable
TIP = HUB / "agents/chatgpt/outbox/BLACKBOX_FOUNDATION_1752_REVIEW_DOMAIN_JOIN_AND_DIRECTORY_L4_20261022_1803.md"

REG = Path(
    r"E:\BLACKBOX\任务\BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1\acceptance"
    r"\CLEANING_INPUT_FINAL_REVIEW_R1\01_FORMAL_DOMAIN_REGISTRY\FORMAL_CLEANING_INPUT_DOMAIN_REGISTRY.json"
)
SEALS = Path(
    r"E:\BLACKBOX\任务\BLACKBOX_RAW_NONE_REDOWNLOAD_SEQUENCE_P7_THEN_P4_R1\acceptance"
    r"\ALL_CURRENT_DOWNLOADED_DATA_FINAL_SEAL_R1\07_DOMAIN_LEVEL_SEALS"
)
ENG = Path(r"E:\BLACKBOX_ENGINES\backtest_lab\02_blackbox_jq_compat_engine")
JQ_RULE = Path(r"E:\BLACKBOX\运行\BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json")
ISOLATION = OUT / "isolation_smoke"

# do not recurse into these link/backup names
SKIP_DIR_NAMES = {
    "manifest_backup",
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "venv",
}


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def jdump(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def role_guess(path: Path, depth: int) -> str:
    s = str(path).replace("/", "\\").lower()
    name = path.name.lower()
    if "blackbox_engines" in s or name == "blackbox_jq_engine":
        return "引擎"
    if "原始只读" in s or "\\raw" in s or name.startswith("p0_") or name.startswith("p1_"):
        return "RAW"
    if "reference_dictionary" in s or "dictionary" in name or "字典" in s:
        return "字典"
    if "规则库" in s or "rule_library" in s or name.endswith(".mdc"):
        return "规则"
    if "清洗" in s or "cleaning" in s:
        return "清洗"
    if "回测缓存" in s or "\\cache" in s or "缓存" in s:
        return "缓存"
    if "\\运行" in s or s.endswith("\\运行"):
        return "运行"
    if "_ops" in s or "运维" in s or "watchdog" in s:
        return "运维"
    if "backup" in name or "备份" in s or "sealed_engine_backup" in s:
        return "历史备份"
    if "任务" in s:
        return "任务/验收产物"
    if "外部证据" in s:
        return "外源证据"
    if depth <= 1:
        return "待确认"
    return "待确认"


def is_reparse(path: Path) -> bool:
    try:
        return bool(path.stat().st_file_attributes & 0x400)  # type: ignore[attr-defined]
    except Exception:
        # fallback: junction often reported via os.lstat vs symlink
        try:
            return path.is_symlink()
        except Exception:
            return False


def should_fold(name: str) -> bool:
    low = name.lower()
    if low.startswith("year=") or low.startswith("year_"):
        return True
    if low.startswith("blackbox_formal_cleaning_r") or low.startswith("blackbox_cache_r"):
        return True
    if low.startswith("completion_") or low.startswith("tip_"):
        return True
    if low in {"releases", "history", "logs", "__pycache__"}:
        return True
    return False


def overview_root(root: Path, max_depth: int = 4) -> list[dict]:
    rows = []
    root = root.resolve()
    rows.append(
        {
            "path": str(root),
            "parent_category": "(root)",
            "depth": 0,
            "role": "根",
            "purpose": "待确认/见系统权威指针",
            "link_or_real": "real",
            "key_pointer": None,
            "folded_note": None,
        }
    )

    def walk(cur: Path, depth: int, parent_cat: str):
        if depth > max_depth:
            return
        try:
            children = sorted(cur.iterdir(), key=lambda p: p.name.lower())
        except PermissionError:
            rows.append(
                {
                    "path": str(cur),
                    "parent_category": parent_cat,
                    "depth": depth,
                    "role": role_guess(cur, depth),
                    "purpose": "待确认",
                    "link_or_real": "permission_denied",
                    "key_pointer": None,
                    "folded_note": None,
                }
            )
            return

        # fold mass similar dirs
        fold_groups: dict[str, list[Path]] = defaultdict(list)
        normal: list[Path] = []
        for ch in children:
            if not ch.is_dir():
                continue
            if ch.name in SKIP_DIR_NAMES or ch.name.lower() == "manifest_backup":
                continue
            # do not follow reparse/junctions deeper
            if is_reparse(ch) or ch.is_symlink():
                rows.append(
                    {
                        "path": str(ch),
                        "parent_category": parent_cat,
                        "depth": depth,
                        "role": role_guess(ch, depth),
                        "purpose": "链接/重解析点 — 不穿链展开",
                        "link_or_real": "link_or_reparse",
                        "key_pointer": None,
                        "folded_note": "not_followed",
                    }
                )
                continue
            if should_fold(ch.name):
                key = "releases*" if "release" in ch.name.lower() or ch.name == "releases" else (
                    "year=*" if ch.name.lower().startswith("year") else (
                        "cleaning_R*" if "cleaning_r" in ch.name.lower() else (
                            "cache_R*" if "cache_r" in ch.name.lower() else "batch_like*"
                        )
                    )
                )
                if ch.name == "releases":
                    key = "releases"
                fold_groups[key].append(ch)
            else:
                normal.append(ch)

        for key, group in fold_groups.items():
            # pick current-looking example
            example = None
            for g in group:
                if "CURRENT" in g.name.upper() or g.name.lower() in {"releases"}:
                    example = g
                    break
            if example is None:
                example = sorted(group, key=lambda p: p.name)[-1]
            rows.append(
                {
                    "path": str(example) if key != "releases" else str(cur / "releases"),
                    "parent_category": parent_cat,
                    "depth": depth,
                    "role": role_guess(example, depth),
                    "purpose": "待确认（同类已折叠）",
                    "link_or_real": "real",
                    "key_pointer": "CURRENT/最新示例见 path；其余折叠",
                    "folded_note": f"folded_count={len(group)} class={key} example={example.name}",
                }
            )
            # only descend into releases one level for CURRENT pointer files, not all
            if key == "releases" and depth < max_depth:
                rel = cur / "releases"
                if rel.exists() and not is_reparse(rel):
                    # list only a few CURRENT-like / newest names as examples, do not deep walk all
                    try:
                        subs = [p for p in rel.iterdir() if p.is_dir()]
                        curr = [p for p in subs if "CURRENT" in p.name.upper()]
                        newest = sorted(subs, key=lambda p: p.stat().st_mtime, reverse=True)[:3]
                        shown = {p.name for p in curr + newest}
                        for p in curr + newest:
                            rows.append(
                                {
                                    "path": str(p),
                                    "parent_category": "releases",
                                    "depth": depth + 1,
                                    "role": role_guess(p, depth + 1),
                                    "purpose": "权威/近例（releases 内折叠）",
                                    "link_or_real": "link_or_reparse" if is_reparse(p) else "real",
                                    "key_pointer": None,
                                    "folded_note": f"releases_total_dirs≈{len(subs)}; shown_subset={len(shown)}",
                                }
                            )
                    except PermissionError:
                        pass

        for ch in normal:
            rows.append(
                {
                    "path": str(ch),
                    "parent_category": parent_cat,
                    "depth": depth,
                    "role": role_guess(ch, depth),
                    "purpose": "待确认" if role_guess(ch, depth) == "待确认" else f"角色线索={role_guess(ch, depth)}（目录名非最终证明）",
                    "link_or_real": "real",
                    "key_pointer": None,
                    "folded_note": None,
                }
            )
            if depth < max_depth:
                walk(ch, depth + 1, ch.name)

    walk(root, 1, root.name)
    return rows


def write_directory_overview():
    bb = overview_root(Path(r"E:\BLACKBOX"), 4)
    be = overview_root(Path(r"E:\BLACKBOX_ENGINES"), 4)
    lines = [
        "# DIRECTORY_OVERVIEW_L4",
        "",
        f"generated: {NOW}",
        "roots: E:\\BLACKBOX , E:\\BLACKBOX_ENGINES",
        "rules: depth<=4; fold releases/year/batch; do not follow reparse/manifest_backup; no secrets; purpose 待确认 if not evidenced",
        "",
        "## E:\\BLACKBOX",
        "",
        "| depth | path | role | purpose | link_or_real | folded_note |",
        "|---:|---|---|---|---|---|",
    ]
    for r in bb:
        lines.append(
            f"| {r['depth']} | `{r['path']}` | {r['role']} | {r['purpose']} | {r['link_or_real']} | {r.get('folded_note') or ''} |"
        )
    lines += ["", "## E:\\BLACKBOX_ENGINES", "", "| depth | path | role | purpose | link_or_real | folded_note |", "|---:|---|---|---|---|---|"]
    for r in be:
        lines.append(
            f"| {r['depth']} | `{r['path']}` | {r['role']} | {r['purpose']} | {r['link_or_real']} | {r.get('folded_note') or ''} |"
        )
    (OUT / "DIRECTORY_OVERVIEW_L4.md").write_text("\n".join(lines), encoding="utf-8")
    jdump(OUT / "DIRECTORY_OVERVIEW_L4.json", {"at": NOW, "BLACKBOX": bb, "BLACKBOX_ENGINES": be})


def load_expected(domain_id: str) -> dict:
    seal = SEALS / domain_id
    man_p = seal / "MANIFEST.json"
    fl = seal / "CANONICAL_FILE_LIST.parquet"
    schema_p = seal / "SCHEMA.json"
    out = {
        "domain_id": domain_id,
        "seal_dir": str(seal),
        "manifest": jload(man_p) if man_p.exists() else None,
        "schema": jload(schema_p) if schema_p.exists() else None,
        "expected_paths": [],
        "expected_source": None,
    }
    if fl.exists():
        t = pq.read_table(fl, columns=["absolute_path"])
        paths = [str(x) for x in t.column(0).to_pylist()]
        out["expected_paths"] = paths
        out["expected_source"] = str(fl)
    return out


def index_root_once(root: Path, cache: dict) -> set[str]:
    key = str(root)
    if key in cache:
        return cache[key]
    files: set[str] = set()
    if not root.exists():
        cache[key] = files
        return files
    # only files directly under root and one level? tip says use expected set primarily;
    # for ADDITIONAL use: list parquet names in root non-recursive first, then if needed rglob but tip forbids recount rglob for join.
    # For additional: only check files that exist as siblings matching filter from expected basenames' parent.
    try:
        for p in root.iterdir():
            if p.is_file() and p.suffix == ".parquet":
                files.add(str(p))
            elif p.is_dir() and not is_reparse(p) and p.name not in SKIP_DIR_NAMES:
                # one more level only for year-like — still bounded
                try:
                    for q in p.iterdir():
                        if q.is_file() and q.suffix == ".parquet":
                            files.add(str(q))
                except PermissionError:
                    pass
    except PermissionError:
        pass
    cache[key] = files
    return files


def compare_domain(exp: dict, root_cache: dict) -> dict:
    did = exp["domain_id"]
    expected = exp["expected_paths"]
    man = exp.get("manifest") or {}
    formal_paths = man.get("formal_paths") or []
    schema = exp.get("schema") or {}

    matched = []
    missing = []
    for p in expected:
        if Path(p).exists():
            matched.append(p)
        else:
            missing.append(p)

    # additional: files under formal roots not in expected (bounded shallow index)
    additional = []
    for fp in formal_paths:
        root = Path(fp)
        present = index_root_once(root, root_cache)
        exp_set = set(expected)
        # filter by domain token in filename when shared root
        token = None
        if "30m" in did:
            token = "__30m__"
        elif "60m" in did:
            token = "__60m__"
        elif "5m" in did and "stock" in did.lower():
            token = "__5m__"
        elif did == "ETF_1m":
            token = "fund_etf_price_1m__"
        elif did == "ETF_5m":
            token = "fund_etf_price_5m__"
        elif did == "index_components":
            token = "component"
        elif did == "index_weights":
            token = "weight"

        for p in present:
            if p in exp_set:
                continue
            name = Path(p).name.lower()
            if token and token.lower() not in name and token.replace("__", "") not in name:
                # shared root: skip other-domain files
                if any(x in str(root).lower() for x in ("p7_stock_minute", "p3_index", "p4_fund")):
                    continue
            additional.append(p)

    # classification
    if not expected:
        compare_status = "CANNOT_COMPARE_NO_EXPECTED_FILE_LIST"
    else:
        compare_status = "COMPARED_BY_CANONICAL_FILE_LIST"
    schema_status = "SCHEMA_DOMAIN_KEY_ONLY" if set(schema.keys()) <= {"domain"} else "SCHEMA_FIELDS_PRESENT"

    # prior registry schema fields from FORMAL domain registry (reuse)
    return {
        "domain_id": did,
        "compare_status": compare_status,
        "expected_source": exp.get("expected_source"),
        "formal_paths": formal_paths,
        "EXPECTED_ITEMS": {
            "n": len(expected),
            "note": "from CANONICAL_FILE_LIST.parquet absolute_path; seal-era set",
        },
        "MATCHED_ITEMS": {
            "n": len(matched),
            "sample": matched[:5],
        },
        "MISSING_OR_UNRESOLVED_ITEMS": {
            "n": len(missing),
            "sample": missing[:8],
            "note": "path absent now; may be formal replacement/increment — not auto confirmed gap without replacement evidence",
        },
        "ADDITIONAL_ITEMS": {
            "n": len(additional),
            "sample": additional[:8],
            "note": "shallow index under formal_paths; extras≠auto-error; shared roots filtered by name token when possible",
        },
        "schema_check": {
            "seal_SCHEMA": schema,
            "seal_SCHEMA_status": schema_status,
            "registry_schema_fields": None,  # filled by caller
            "note": "seal SCHEMA only domain key ⇒ cannot claim field schema read from seal",
        },
        "old_count_join_discarded": True,
    }


def build_domain_diff() -> dict:
    reg = jload(REG)
    reg_by = {d["domain_id"]: d for d in reg.get("domains") or []}
    # retain 1752 observation counts as historical only
    old = None
    old_p = PREV1752 / "FOUNDATION_LEDGER.json"
    if old_p.exists():
        old = jload(old_p)

    root_cache: dict = {}
    rows = []
    for did in sorted(reg_by.keys()):
        exp = load_expected(did)
        row = compare_domain(exp, root_cache)
        row["schema_check"]["registry_schema_fields"] = reg_by[did].get("schema")
        row["registry_primary_key"] = reg_by[did].get("primary_key")
        row["registry_fq"] = reg_by[did].get("fq")
        row["registry_event_time"] = reg_by[did].get("event_time")
        row["prior_1752_root_count_observation"] = None
        if old:
            for r in old.get("domains") or []:
                if r.get("domain_id") == did:
                    row["prior_1752_root_count_observation"] = {
                        "join_status_old": r.get("join_status"),
                        "observation_now": r.get("observation_now"),
                        "note": "retained as root-count observation only; NOT acceptance",
                    }
                    break
        # field compare status
        if row["schema_check"]["seal_SCHEMA_status"] == "SCHEMA_DOMAIN_KEY_ONLY":
            if reg_by[did].get("schema"):
                row["dictionary_field_compare"] = {
                    "status": "REUSED_REGISTRY_SCHEMA_DECLARATION_ONLY",
                    "required_optional_split": "NOT_IN_SEAL; registry lists names only — types/units/fq/PIT not fully evidenced here",
                    "fields": reg_by[did].get("schema"),
                }
            else:
                row["dictionary_field_compare"] = {"status": "INSUFFICIENT_EVIDENCE"}
        rows.append(row)

    return {
        "at": NOW,
        "method": "CANONICAL_FILE_LIST exists() + shallow formal_path index; no rglob recount; no 5%/10 tolerance",
        "shared_roots_indexed_once": list(root_cache.keys()),
        "domains": rows,
        "summary": {
            "n": len(rows),
            "compared": sum(1 for r in rows if r["compare_status"] == "COMPARED_BY_CANONICAL_FILE_LIST"),
            "cannot_compare": sum(1 for r in rows if r["compare_status"] != "COMPARED_BY_CANONICAL_FILE_LIST"),
            "domains_with_missing_n_gt_0": sum(
                1 for r in rows if (r["MISSING_OR_UNRESOLVED_ITEMS"]["n"] or 0) > 0
            ),
            "note": "missing_n>0 is unresolved until formal replacement proven; not auto RAW gap",
        },
    }


def build_scope_map() -> dict:
    reg = jload(REG)
    jq = jload(JQ_RULE) if JQ_RULE.exists() else {}
    datasets = jq.get("datasets") or []
    domains = [d["domain_id"] for d in reg.get("domains") or []]
    # known additions from prior tips / inventory (reuse, no search)
    additions = [
        {
            "id": "FUND_NAV_PIT / FUND_ETF_NAV",
            "bucket": "POST_BASELINE_OR_OTHER_CONTRACT",
            "evidence": "JQ incremental FUND_ETF_NAV + completion NAV plane / PRODUCT_META",
            "vendor": "JQData",
        },
        {
            "id": "JQ20 finance/corp packages",
            "bucket": "POST_BASELINE_OR_OTHER_CONTRACT",
            "evidence": "JQ20 HAND/ledger prior completions; not in 26 cleaning-input domains",
            "vendor": "JQData",
        },
        {
            "id": "CBOND / convertible (external)",
            "bucket": "POST_BASELINE_OR_OTHER_CONTRACT",
            "evidence": "prior tip CBOND static closed / external evidence plane",
            "vendor": "external_not_JQ",
        },
    ]
    return {
        "at": NOW,
        "formal_26_domains": domains,
        "jq_incremental_datasets": datasets,
        "granularity_note": "21 datasets vs 26 domains are different grains — do not subtract counts",
        "mapping": {
            "covered_by_26": domains,
            "post_baseline_or_other_vendor_with_own_contract": additions,
            "explicitly_excluded_by_original_rules": [
                {
                    "note": "see registry summary excluded_pseudo / permission blocks in seals; not re-derived this round",
                    "pointer": str(REG),
                }
            ],
            "scope_baseline_undetermined": [
                {
                    "note": "any source neither in 26 nor evidenced post-baseline contracts remains UNDETERMINED; no full-disk search",
                }
            ],
        },
        "cache_75_not_raw_denominator": True,
    }


def find_engine_bindings() -> dict:
    """Map admission domain → local adapter hints without loading .env."""
    master = ENG / "rule_library" / "master_registry_R1"
    dom_csv = master / "DATA_DOMAIN_ADMISSION_MATRIX_R1.csv"
    ingest = master / "DATA_INGESTION_GATE_RULES_R1.json"
    rows = []
    if dom_csv.exists():
        with dom_csv.open(encoding="utf-8", errors="replace", newline="") as f:
            for row in csv.DictReader(f):
                rows.append(dict(row))

    # static AST scan for loaders (no exec)
    pkg = ENG / "blackbox_jq_engine"
    adapters = []
    blockers = []
    if pkg.exists():
        for p in pkg.rglob("*.py"):
            if any(x in p.parts for x in (".git", "__pycache__")):
                continue
            try:
                src = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if "dotenv" in src or "load_dotenv" in src:
                blockers.append({"file": str(p), "issue": "references dotenv/load_dotenv — do not import for smoke"})
            if any(k in src for k in ("read_parquet", "standard_root", "DATA_PATH", "cache_root", "open_dataset")):
                # collect function names via AST
                try:
                    tree = ast.parse(src)
                    fns = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                except SyntaxError:
                    fns = []
                adapters.append(
                    {
                        "file": str(p.relative_to(ENG)),
                        "functions_top_level": fns[:30],
                        "hints": [k for k in ("read_parquet", "standard_root", "cache_root", "open_dataset") if k in src],
                    }
                )
                if len(adapters) >= 40:
                    break

    bindings = []
    for row in rows[:50]:
        # leave local path empty unless we can point to known BLACKBOX paths by name overlap
        domain_name = row.get("domain") or row.get("data_domain") or row.get("DOMAIN") or json.dumps(row, ensure_ascii=False)[:80]
        local = None
        # heuristic known mapping to E:\BLACKBOX data — only if clear
        s = json.dumps(row, ensure_ascii=False).lower()
        if "nav" in s:
            local = r"E:\BLACKBOX\数据\回测缓存\releases\BLACKBOX_CACHE_R1_FUND_NAV_PIT_ASOF_20260924_20260924_200439\FUND_NAV_PIT_R1"
        elif "1m" in s and "etf" in s:
            local = r"E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P4_fund_etf_raw_none\fund_etf_price_1m"
        bindings.append(
            {
                "admission_row": row,
                "adapter_function": None,
                "local_standard_or_raw_path": local,
                "bind_status": "PATH_HEURISTIC_ONLY" if local else "UNBOUND",
                "blocker": "no explicit adapter function wired in scanned files for this row"
                if not local
                else "path guessed by keyword; function still unbound",
            }
        )

    return {
        "admission_matrix_rows_n": len(rows),
        "ingest_gate_exists": ingest.exists(),
        "ingest_gate_keys": list(jload(ingest).keys())[:30] if ingest.exists() else None,
        "adapter_files_scanned": adapters[:25],
        "dotenv_blockers": blockers[:20],
        "type_to_local_entry": bindings,
    }


def engine_check() -> dict:
    bind = find_engine_bindings()
    smoke = {
        "runtime_attempted": False,
        "result": "NOT_RUN_STATIC_ONLY",
        "reason": None,
    }
    ISOLATION.mkdir(parents=True, exist_ok=True)

    # Try isolate: load ONLY pyarrow read of one expected ETF_1m file + compare registry schema names — no engine import
    # If we can find a pure function file without dotenv — still avoid import if blockers exist in package
    dotenv_hits = bind["dotenv_blockers"]
    if dotenv_hits:
        smoke["reason"] = (
            "Engine package contains dotenv references; per tip do not import production package. "
            "Performed data-side isolation read without engine import instead."
        )
    else:
        smoke["reason"] = "No safe dedicated isolated reader entry located; data-side isolation only."

    data_side = {"attempted": False}
    # pick first matched ETF_1m expected file
    etf_list = SEALS / "ETF_1m" / "CANONICAL_FILE_LIST.parquet"
    if etf_list.exists():
        paths = pq.read_table(etf_list, columns=["absolute_path"]).column(0).to_pylist()
        sample = next((p for p in paths if Path(p).exists()), None)
        if sample:
            data_side["attempted"] = True
            data_side["sample_path"] = sample
            # read schema only
            sch = pq.read_schema(sample)
            data_side["parquet_columns"] = sch.names
            reg = jload(REG)
            want = None
            for d in reg["domains"]:
                if d["domain_id"] == "ETF_1m":
                    want = d.get("schema")
            data_side["registry_schema"] = want
            if want:
                data_side["columns_in_registry"] = [c for c in want if c in sch.names]
                data_side["registry_missing_in_file"] = [c for c in want if c not in sch.names]
            jdump(
                ISOLATION / "DATA_SIDE_SCHEMA_SMOKE.json",
                {"at": NOW, **data_side},
            )
            smoke["data_side_isolation"] = "RAN_READ_PARQUET_SCHEMA_ONLY"
        else:
            smoke["data_side_isolation"] = "NO_EXISTING_SAMPLE_FILE"
    else:
        smoke["data_side_isolation"] = "NO_CANONICAL_LIST"

    return {
        "at": NOW,
        "engine_root": str(ENG),
        "runtime_smoke": smoke,
        "bindings": bind,
        "correction_vs_1752": {
            "1752_runtime_attempted_was_mislabeled": True,
            "correct_label": "runtime_attempted=false / NOT_RUN_STATIC_ONLY",
            "not_a_runtime_failure": True,
        },
    }


def curl_http(repo_path: str) -> int:
    token = None
    for line in Path(r"C:\LAN_SHARE_REPORT\配置\secrets\github_hub_token.TXT").read_text(
        encoding="utf-8", errors="ignore"
    ).splitlines():
        line = line.strip().replace("\ufeff", "")
        if line.startswith(("gho_", "ghp_", "github_pat_")):
            token = "".join(ch for ch in line if 32 <= ord(ch) < 127)
            break
    r = subprocess.run(
        [
            "curl.exe",
            "-sS",
            "-o",
            "NUL",
            "-w",
            "%{http_code}",
            "-H",
            f"Authorization: Bearer {token}",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "User-Agent: BLACKBOX-HUB",
            "--connect-timeout",
            "30",
            f"https://api.github.com/repos/zwdjwsam-creator/sam/contents/{repo_path}",
        ],
        capture_output=True,
        text=True,
    )
    try:
        return int((r.stdout or "0").strip() or "0")
    except ValueError:
        return 0


def push() -> dict:
    if INBOX.exists():
        shutil.rmtree(INBOX)
    INBOX.mkdir(parents=True)
    allow = [
        "CLAIM.json",
        "USER_FINAL_REPORT.md",
        "DIRECTORY_OVERVIEW_L4.md",
        "DIRECTORY_OVERVIEW_L4.json",
        "DOMAIN_SAMESET_DIFF.json",
        "SCOPE_COVERAGE_MAP.json",
        "ENGINE_BASELINE_CHECK.json",
        "FOUNDATION_VERDICT_DELTA.json",
        "CURSOR_NOTIFY_1803_COMPLETION.md",
        "TIP_1803.md",
        "run_completion_1803_worker.py",
        "REUSE_NOTE.json",
    ]
    for name in allow:
        src = OUT / name
        if src.exists():
            shutil.copy2(src, INBOX / name)
    if (ISOLATION / "DATA_SIDE_SCHEMA_SMOKE.json").exists():
        (INBOX / "isolation_smoke").mkdir(exist_ok=True)
        shutil.copy2(
            ISOLATION / "DATA_SIDE_SCHEMA_SMOKE.json",
            INBOX / "isolation_smoke" / "DATA_SIDE_SCHEMA_SMOKE.json",
        )
    pairs = [
        f"{p}={REPO}/{p.relative_to(INBOX).as_posix()}"
        for p in sorted(INBOX.rglob("*"))
        if p.is_file()
    ]
    print("PUSHING", len(pairs))
    r = subprocess.run([PY, "-u", str(PUSH), "HUB: completion_1803 domain join L4"] + pairs)
    keys = [
        "DIRECTORY_OVERVIEW_L4.md",
        "DOMAIN_SAMESET_DIFF.json",
        "SCOPE_COVERAGE_MAP.json",
        "ENGINE_BASELINE_CHECK.json",
        "USER_FINAL_REPORT.md",
        "CURSOR_NOTIFY_1803_COMPLETION.md",
    ]
    verify = {k: curl_http(f"{REPO}/{k}") == 200 for k in keys}
    print("VERIFY", verify)
    pointer_updated = False
    if all(verify.values()):
        ptr = HUB / "agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md"
        ptr.write_text(
            f"""# INBOX_FOR_CHATGPT

updated: {NOW}
latest: {REPO}/CURSOR_NOTIFY_1803_COMPLETION.md
checkpoint: COMPLETION_1803
parent: 1745/1752 CONTINUE
FOUNDATION_ACCEPTANCE: false
""",
            encoding="utf-8",
        )
        subprocess.run(
            [PY, "-u", str(PUSH), "HUB: INBOX pointer 1803", f"{ptr}=agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md"]
        )
        pointer_updated = True
    claim = {
        "at": NOW,
        "tip": TIP.name,
        "mode": "CONTINUE_SAME_TASK",
        "status": "PUSHED" if r.returncode == 0 and all(verify.values()) and pointer_updated else "PUSH_PARTIAL",
        "FOUNDATION_ACCEPTANCE": False,
        "PRODUCTION_CHANGE_AUTHORIZED": False,
        "remote_verify_curl": verify,
        "pointer_updated": pointer_updated,
    }
    jdump(OUT / "CLAIM.json", claim)
    jdump(INBOX / "CLAIM.json", claim)
    subprocess.run(
        [PY, "-u", str(PUSH), "HUB: CLAIM 1803", f"{INBOX / 'CLAIM.json'}={REPO}/CLAIM.json"]
    )
    return claim


def main():
    shutil.copy2(TIP, OUT / "TIP_1803.md")
    jdump(
        HUB / "_LAST_RECEIVE.json",
        {
            "at": NOW,
            "items": [{"path": f"agents/chatgpt/outbox/{TIP.name}", "sha256": sha256_file(TIP)}],
            "checkpoint_hint": TIP.name,
        },
    )
    shutil.copy2(HUB / "_LAST_RECEIVE.json", HUB / "_NEW_FROM_GPT.json")

    jdump(
        OUT / "REUSE_NOTE.json",
        {
            "at": NOW,
            "reused": ["completion_1752 ledger as old observation only", "FORMAL registry", "domain seals", "JQ rule"],
            "discarded_methods": ["rglob count join", "5%/10 file tolerance as acceptance"],
        },
    )

    print("L4 overview...")
    write_directory_overview()
    print("domain same-set diff...")
    diff = build_domain_diff()
    jdump(OUT / "DOMAIN_SAMESET_DIFF.json", diff)
    print("scope map...")
    scope = build_scope_map()
    jdump(OUT / "SCOPE_COVERAGE_MAP.json", scope)
    print("engine...")
    eng = engine_check()
    jdump(OUT / "ENGINE_BASELINE_CHECK.json", eng)

    # classify overall
    missing_domains = [
        r["domain_id"]
        for r in diff["domains"]
        if r["MISSING_OR_UNRESOLVED_ITEMS"]["n"] > 0
    ]
    verdict = {
        "at": NOW,
        "FOUNDATION_ACCEPTANCE": False,
        "raw_data_confirmed_gap": "NOT_AUTO_FROM_MISSING_PATHS — need formal replacement proof per domain; see MISSING samples",
        "data_present_entry_not_adapted": "YES_PARTIAL — engine bindings mostly UNBOUND; data-side schema smoke only",
        "evidence_insufficient_only": "field-level types/units/PIT largely insufficient (seal SCHEMA domain-key only)",
        "domain_diff_summary": diff["summary"],
        "engine_runtime": eng["runtime_smoke"],
        "old_9_16_1_not_acceptance": True,
    }
    jdump(OUT / "FOUNDATION_VERDICT_DELTA.json", verdict)

    jdump(OUT / "CLAIM.json", {"at": NOW, "status": "LOCAL_READY", "FOUNDATION_ACCEPTANCE": False})
    (OUT / "USER_FINAL_REPORT.md").write_text(
        "\n".join(
            [
                "# 底座验收续作回执（1803）",
                "",
                f"时间: {NOW}",
                "parent: 1745/1752 CONTINUE_SAME_TASK",
                "FOUNDATION_ACCEPTANCE: **false**",
                "",
                "## 交付",
                "1. DIRECTORY_OVERVIEW_L4.md — 两根目录≤4级，releases/year 等已折叠，不穿链接",
                "2. DOMAIN_SAMESET_DIFF.json — 按 CANONICAL_FILE_LIST 同域对照；废弃 rglob 计数与5%容差",
                f"   - compared={diff['summary']['compared']}；domains_with_missing_n_gt_0={diff['summary']['domains_with_missing_n_gt_0']}（≠自动缺口）",
                "3. SCOPE_COVERAGE_MAP.json — 26域 / 21 dataset 粒度不同；FUND_NAV/JQ20/CBOND 作后基线独立合同",
                "4. ENGINE_BASELINE_CHECK.json — runtime_attempted=false / NOT_RUN_STATIC_ONLY；数据侧隔离读 schema",
                "",
                "## 定性",
                "- 原始数据确有缺口：不由 missing 路径自动升级",
                "- 数据在但入口未适配：引擎绑定多为 UNBOUND",
                "- 仅证据不足：seal SCHEMA 仅 domain 键；字段级类型/单位/PIT 不足",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (OUT / "CURSOR_NOTIFY_1803_COMPLETION.md").write_text(
        f"""# HUB completion_1803 ready

FOUNDATION_ACCEPTANCE: false
deliverables: DIRECTORY_OVERVIEW_L4 / DOMAIN_SAMESET_DIFF / SCOPE_COVERAGE_MAP / ENGINE_BASELINE_CHECK
""",
        encoding="utf-8",
    )

    claim = push()
    print("DONE", claim.get("status"), diff["summary"])


if __name__ == "__main__":
    main()
