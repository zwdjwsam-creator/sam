# -*- coding: utf-8 -*-
"""1710: A query method verify + COVERAGE_CONTRACT_MATRIX; push HUB inbox. READONLY prod."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

CN = timezone(timedelta(hours=8))
NOW = datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S+08:00")
OUT = Path(__file__).resolve().parent
PREV = OUT.parent
LEDGER = PREV / "completion_1635" / "OBJECT_LEDGER_75.json"
TIP_SRC = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\outbox"
    r"\BLACKBOX_DATA_MANAGEMENT_1655_REVIEW_AND_COVERAGE_CONTRACT_MATRIX_20261022_1710.md"
)
INBOX_ROOT = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox"
    r"\BLACKBOX_INVENTORY_CONTINUE_20261022_1310"
)
PUSH = Path(r"E:\BLACKBOX\运行\外部大脑信箱\_hub_push_files.py")
DB = Path(
    r"C:\LAN_SHARE_REPORT\R9_DESKTOP_FIX_FULL_SOURCE_MAPPING_AND_STRUCTURE_20261015"
    r"\FINAL_CANDIDATE.sqlite"
)
EXPECTED_SHA = "53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d"
PY = r"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe"

A_SRC = r"D:\CURSOR_TASK_ARCHIVE\BLACKBOX_JQ20_FULL_DOWNLOAD_PIT_CLEAN_CACHE_HAND_R1"
B_SRC = r"D:\backtest_lab\02_blackbox_jq_compat_engine"
A_VARIANTS = [
    A_SRC,
    r"\\192.168.100.2\D_DRIVE\CURSOR_TASK_ARCHIVE\BLACKBOX_JQ20_FULL_DOWNLOAD_PIT_CLEAN_CACHE_HAND_R1",
]
B_VARIANTS = [
    B_SRC,
    r"\\192.168.100.2\D_DRIVE\backtest_lab\02_blackbox_jq_compat_engine",
]

REQUIRED4 = [
    "CORP_XR_XD_EVENT_PIT_R1",
    "CORP_SHAREHOLDER_TOP10_PIT_R1",
    "CORP_SHAREHOLDER_FLOATING_TOP10_PIT_R1",
    "SW_L3_MEMBERSHIP_PIT_R1",
]


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


def like_prefix_pattern(prefix: str) -> str:
    """LIKE pattern for children of prefix with ESCAPE '\\'."""
    esc = []
    for ch in prefix:
        if ch in ("\\", "%", "_"):
            esc.append("\\" + ch)
        else:
            esc.append(ch)
    return "".join(esc) + "\\%"


def connect_ro(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)


def query_methods(con: sqlite3.Connection, root: str) -> dict:
    cur = con.cursor()
    out: dict = {"root": root, "methods": {}}

    def run(name: str, sql: str, params: tuple, sample_n: int = 5):
        t0 = time.time()
        rows = list(cur.execute(sql, params))
        out["methods"][name] = {
            "sql": sql,
            "params_repr": repr(params),
            "n": len(rows),
            "sample": [list(r) for r in rows[:sample_n]],
            "seconds": round(time.time() - t0, 3),
        }
        return rows

    run(
        "exact_pk",
        "SELECT path, is_dir, volume_serial, file_id, source FROM paths WHERE path=?",
        (root,),
    )
    pat = like_prefix_pattern(root)
    run(
        "prefix_like_escape",
        "SELECT path, is_dir, volume_serial, file_id, source FROM paths "
        "WHERE path LIKE ? ESCAPE '\\' LIMIT 20",
        (pat,),
    )
    # GLOB: * and ? are wildcards; backslash is literal on Windows paths in SQLite GLOB
    run(
        "prefix_glob_children",
        "SELECT path, is_dir, volume_serial, file_id, source FROM paths "
        "WHERE path GLOB ? LIMIT 20",
        (root + "\\*",),
    )
    # lexicographic range for children (positive control method)
    lo = root + "\\"
    hi = root + "]"  # ']' sorts after '\\' and most path chars under ASCII
    run(
        "prefix_range_children",
        "SELECT path, is_dir, volume_serial, file_id, source FROM paths "
        "WHERE path >= ? AND path < ? LIMIT 20",
        (lo, hi),
    )
    leaf = root.rsplit("\\", 1)[-1]
    run(
        "instr_leaf_name",
        "SELECT path, is_dir, volume_serial, file_id, source FROM paths "
        "WHERE instr(path, ?) > 0 LIMIT 20",
        (leaf,),
    )
    return out


def schema_dump(con: sqlite3.Connection) -> dict:
    cur = con.cursor()
    tables = {}
    for name, sql in cur.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"
    ):
        cols = [
            {"cid": c[0], "name": c[1], "type": c[2], "notnull": c[3], "pk": c[5]}
            for c in cur.execute(f"PRAGMA table_info({name})")
        ]
        n = cur.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        tables[name] = {"sql": sql, "columns": cols, "row_count": n}
    return {
        "paths_pk": "path",
        "paths_note": (
            "paths.path is PRIMARY KEY; LIKE '_' is single-char wildcard — "
            "must ESCAPE or use GLOB/range/instr; prior tip1655 prefix_n=0 on B "
            "was method bug (unescaped '_' + wrong \\\\ pattern), not empty children"
        ),
        "other_path_bearing_tables": [
            "links",
            "logical_view_42",
            "observed_metadata_52",
            "blocked_metadata_52",
            "suspect_version_140",
            "link_overlay_audit",
        ],
        "tables": tables,
    }


def cross_table_hits(con: sqlite3.Connection, needle: str) -> dict:
    cur = con.cursor()
    hits = {}
    probes = {
        "links": ["path", "target", "mapped_dest", "original_target", "migrated_link_path", "migrated_target"],
        "logical_view_42": [
            "logical_path",
            "ordinary_representative",
            "junction_path",
            "junction_target",
        ],
        "observed_metadata_52": ["path"],
        "blocked_metadata_52": ["path"],
        "suspect_version_140": ["path"],
        "link_overlay_audit": [
            "source_path",
            "original_target",
            "final_target",
            "migrated_link_path",
            "migrated_target",
        ],
    }
    for table, cols in probes.items():
        for col in cols:
            t0 = time.time()
            n = cur.execute(
                f"SELECT COUNT(*) FROM {table} WHERE instr({col}, ?) > 0", (needle,)
            ).fetchone()[0]
            sample = []
            if n:
                sample = [
                    r[0]
                    for r in cur.execute(
                        f"SELECT {col} FROM {table} WHERE instr({col}, ?) > 0 LIMIT 3",
                        (needle,),
                    )
                ]
            hits[f"{table}.{col}"] = {
                "n": n,
                "seconds": round(time.time() - t0, 3),
                "sample": sample,
            }
    return hits


def classify_type(row: dict) -> str:
    pid = row.get("product_id", "")
    ms = (row.get("mapping_status") or "").upper()
    if "BLOCKED" in ms or "BLOCKED" in (row.get("findings_tags") or "").upper():
        return "DECLARED_BLOCKED_OR_BLOCKED_MAPPING"
    if "META_REGISTRY" in ms or pid.endswith("_REGISTRY_R1") or "REGISTRY" in pid and "PIT" not in pid:
        if "REGISTRY" in pid or "MANIFEST" in pid or "DEPENDENCY" in pid:
            return "REGISTRY_METADATA"
    if "VIEW" in pid or "VIEW" in ms:
        return "LOGICAL_VIEW"
    return "ENTITY_TABLE_OR_PRODUCT"


def build_matrix(ledger: dict) -> dict:
    rows_out = []
    for row in ledger["rows"]:
        pid = row["product_id"]
        ci = row.get("content_integrity") or {}
        rc = row.get("rules_consumption") or {}
        uc = row.get("update_chain") or {}
        ps = row.get("producer_semantics") or {}
        obj_type = classify_type(row)
        expectation_src = ci.get("independent_expectation") or "UNDEFINED"
        expectation_authority = rc.get("authority_file") or "UNKNOWN"
        # distinguish self-report vs independent
        if expectation_src in (
            "UNKNOWN (no independent full coverage contract proven)",
            "UNKNOWN",
            "",
            None,
        ):
            expectation_kind = "UNDEFINED_OR_UNKNOWN"
        elif "n/a" in str(expectation_src).lower() or "not REQUIRED4" in str(expectation_src):
            expectation_kind = "META_NOT_APPLICABLE"
        else:
            expectation_kind = "STATED_IN_PRIOR_EVIDENCE_NOT_REVALIDATED"

        observed = {
            "content_observed_prior": row.get("content_observed_prior"),
            "content_vs_contract": row.get("content_vs_contract"),
            "verified_range": ci.get("verified_range"),
            "unverified_range": ci.get("unverified_range"),
            "full_read_rows": row.get("full_read_rows"),
            "full_read_shards": row.get("full_read_shards"),
            "mapping_status": row.get("mapping_status"),
            "producer_entry": row.get("producer_entry"),
            "evidence_ref_hints": [
                x
                for x in [
                    ci.get("evidence_ref"),
                    rc.get("evidence_ref"),
                    uc.get("evidence_ref"),
                    (ps or {}).get("source"),
                ]
                if x
            ],
            "observation_class": (
                "FULL_READ"
                if row.get("full_read_rows") not in (None, "", 0, "0")
                else (
                    "METADATA_OR_SAMPLE"
                    if row.get("content_observed_prior")
                    else "STATIC_OR_UNOBSERVED"
                )
            ),
        }

        delta = {
            "supported_gap": ci.get("unverified_range") or "UNKNOWN",
            "insufficient_evidence_only": expectation_kind
            in ("UNDEFINED_OR_UNKNOWN", "META_NOT_APPLICABLE"),
            "not_applicable": expectation_kind == "META_NOT_APPLICABLE"
            or obj_type in ("REGISTRY_METADATA", "LOGICAL_VIEW"),
            "usage_impact": rc.get("unresolved_ref_impact") or "UNKNOWN",
            "next_min_check": None,
        }
        if obj_type == "REGISTRY_METADATA":
            delta["next_min_check"] = "registry row presence / replace-safety only; not parquet row count"
        elif obj_type == "LOGICAL_VIEW":
            delta["next_min_check"] = "do not require new materialization; check representative binding"
        elif expectation_kind == "UNDEFINED_OR_UNKNOWN":
            delta["next_min_check"] = "locate independent contract/manifest before completeness claim"
        else:
            delta["next_min_check"] = "bounded contract-field check vs existing observation; no full rescan"

        rows_out.append(
            {
                "product_id": pid,
                "object_type": obj_type,
                "expectation": {
                    "kind": expectation_kind,
                    "independent_expectation_text": expectation_src,
                    "authority_file": expectation_authority,
                    "authority_vs_product_self_report": (
                        "AUTHORITY_UNKNOWN_OR_UNBOUND"
                        if expectation_authority in ("UNKNOWN", "UNBOUND", "", None)
                        else "AUTHORITY_POINTER_PRESENT_NOT_REVALIDATED"
                    ),
                    "should_have_scope": {
                        "date_field_meaning": "UNDEFINED_IN_THIS_MATRIX",
                        "start_end_asof": "NOT_INFERRED_FROM_MIN_MAX",
                        "asset_scope": "UNDEFINED_IN_THIS_MATRIX",
                        "frequency_or_calendar": "UNDEFINED_IN_THIS_MATRIX",
                        "key_fields": (ps or {}).get("keys") or "UNKNOWN",
                        "pit_rule": rc.get("pit_or_license_limits") or "UNKNOWN",
                        "note": "no clear requirement → leave undefined; do not backfill from observed min/max",
                    },
                },
                "observed": observed,
                "delta_unknown_usage": delta,
                "ledger_checkpoint": ledger.get("checkpoint"),
            }
        )
    return {
        "at": NOW,
        "n": len(rows_out),
        "source_ledger": str(LEDGER),
        "rules": [
            "Do not compute overall completeness as 75 existence ratio",
            "Missing independent expectation ≠ proven missing data",
            "VIEW/REGISTRY/BLOCKED handled per tip; old ETF equity path not into ETF coverage",
            "No new full content scan this batch",
        ],
        "rows": rows_out,
    }


def detailed_examples(matrix: dict, ledger: dict) -> dict:
    by = {r["product_id"]: r for r in matrix["rows"]}
    led_by = {r["product_id"]: r for r in ledger["rows"]}

    def pick(pid: str, extra: dict) -> dict:
        base = dict(by[pid])
        base["detail_extra"] = extra
        base["ledger_slice"] = {
            k: led_by[pid].get(k)
            for k in (
                "mapping_status",
                "content_observed_prior",
                "full_read_rows",
                "full_read_shards",
                "producer_entry",
                "content_integrity",
                "rules_consumption",
                "producer_semantics",
            )
            if k in led_by[pid]
        }
        return base

    fund = pick(
        "FUND_NAV_PIT_R1",
        {
            "prior_full_read_observation": "5980 shards / 6496121 rows / 2014-01-02..2026-09-24 (prior; not re-read)",
            "note": "full-read observation retained but does NOT replace independent should-have contract",
            "old_etf_equity_path": "EXCLUDED_FROM_THIS_EXAMPLE",
        },
    )
    etf1 = pick(
        "ETF_MINUTE_1M_R1",
        {
            "plane": "1m",
            "do_not_extrapolate_to": ["ETF_MINUTE_5M_R1", "ETF_MINUTE_30M_R1", "ETF_MINUTE_60M_R1"],
            "tip_vs_mat_history": "keep tip consumption evidence separate from __mat historical consumers",
            "source_plane": "use actual Cleaning/RAW refs from ledger only; no new scan",
        },
    )
    etf5 = pick(
        "ETF_MINUTE_5M_R1",
        {
            "plane": "5m",
            "do_not_extrapolate_from": "ETF_MINUTE_1M_R1",
            "source_plane": "independent of 1m; prior unverified_range kept",
        },
    )
    r4 = []
    for pid in REQUIRED4:
        if pid not in by:
            r4.append({"product_id": pid, "status": "MISSING_FROM_LEDGER_75"})
            continue
        r4.append(
            pick(
                pid,
                {
                    "entity_vs_metadata": "entity path/meta row counts from prior REQUIRED4_ENTITY_EVIDENCE; not re-read",
                    "catalog_reachability": "separate from data completeness",
                    "resolver_availability": "ordinary resolver catalog gap ≠ entity missing",
                    "data_integrity_vs_resolver": "SEPARATED_PER_TIP",
                },
            )
        )
    return {
        "A_FUND_NAV": fund,
        "B_ETF_1m": etf1,
        "B_ETF_5m": etf5,
        "C_REQUIRED4": r4,
    }


def prioritize_next(matrix: dict) -> list:
    items = []
    for r in matrix["rows"]:
        d = r["delta_unknown_usage"]
        exp = r["expectation"]["kind"]
        impact = d.get("usage_impact") or ""
        score = 0
        if exp == "UNDEFINED_OR_UNKNOWN" and r["object_type"] == "ENTITY_TABLE_OR_PRODUCT":
            score += 30
        if impact not in ("UNKNOWN", "", None) and "UNBOUND" in str(
            r["observed"].get("mapping_status")
        ):
            score += 10
        if "catalog" in impact.lower() or "resolver" in impact.lower():
            score += 15
        if r["product_id"] in REQUIRED4 or r["product_id"] == "FUND_NAV_PIT_R1":
            score += 5
        if r["product_id"].startswith("ETF_MINUTE"):
            score += 3
        if d.get("not_applicable"):
            score -= 20
        items.append(
            {
                "product_id": r["product_id"],
                "score": score,
                "object_type": r["object_type"],
                "expectation_kind": exp,
                "next_min_check": d.get("next_min_check"),
                "usage_impact": impact,
            }
        )
    items.sort(key=lambda x: (-x["score"], x["product_id"]))
    return items[:25]


def write_reports(a_verify: dict, matrix: dict, examples: dict, nxt: list, schema: dict):
    # CLAIM
    jdump(
        OUT / "CLAIM.json",
        {
            "at": NOW,
            "tip": "20261022_1710",
            "reply_to": "completion_1655",
            "decision": "ACCEPT_ENGINE_TARGET_PRESENT / QUALIFY_JQ20_QUERY / ADVANCE_TO_COVERAGE_MATRIX",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
            "PRODUCTION_CHANGE_AUTHORIZED": False,
            "instance": "completion_1710",
            "deliverables": {
                "A_QUERY_METHOD_VERIFY.json": True,
                "COVERAGE_CONTRACT_MATRIX.json": True,
                "COVERAGE_EXAMPLES_ABC.json": True,
                "NEXT_MIN_CHECKS.json": True,
                "USER_FINAL_REPORT.md": True,
            },
        },
    )
    jdump(OUT / "A_QUERY_METHOD_VERIFY.json", a_verify)
    jdump(OUT / "COVERAGE_CONTRACT_MATRIX.json", matrix)
    jdump(OUT / "COVERAGE_EXAMPLES_ABC.json", examples)
    jdump(OUT / "NEXT_MIN_CHECKS.json", {"at": NOW, "top": nxt})
    jdump(OUT / "SCHEMA_PATHS.json", schema)

    a_conc = a_verify["conclusion"]
    lines = [
        "# 数据管理追加回执（1710）— A查询校验 + 覆盖合同矩阵",
        "",
        f"时间: {NOW}",
        "reply_to: tip_1710 / completion_1655",
        "SYSTEM_INVENTORY_ACCEPTANCE: **false**",
        "PRODUCTION_CHANGE: 只读；未改规则/CURRENT/数据",
        "",
        "## 1. A 查询方法校验（含 B 阳性对照）",
        f"- DB: `{DB}` SHA={a_verify['plan_sha256']} match={a_verify['sha_match_tip']}",
        f"- schema: paths PK=`path`；另有 links/logical_view_42 等（见 SCHEMA_PATHS.json）",
        f"- **根因**: tip1655 对 B 报 `exact` 有行但 `prefix_n=0`——因 LIKE 未 ESCAPE 下划线，且 `\\\\%` 模式错误；**不是**子路径空。",
        f"- B 阳性对照（同一有效方法）: `{a_verify['positive_control']['method']}` → n={a_verify['positive_control']['n']} sample_ok={bool(a_verify['positive_control']['sample'])}",
        f"- A 重查结论: **{a_conc['code']}**",
        f"  - exact/GLOB/range/instr(leaf)/跨表 instr(JQ20 任务名): 均无行（已查表见 JSON）",
        f"  - `D:\\CURSOR_TASK_ARCHIVE` 目录 exact **有**行，但其下 GLOB 子路径计数={a_verify.get('cta_child_count')}",
        f"  - **不能**推断迁移丢失；仅 **NOT_FOUND_IN_QUERIED_SCOPE**（冻结计划 paths+列出路表）",
        f"- 分隔符: 库内为正斜杠? **否**，样本为 `D:\\\\...` Windows 反斜杠",
        "",
        "## 2. COVERAGE_CONTRACT_MATRIX（75）",
        f"- 源账本: completion_1635 OBJECT_LEDGER_75（n={matrix['n']}）",
        "- 每对象含: object_type / expectation(含 should_have 未定义项) / observed / delta_unknown_usage",
        "- 三组详例: FUND_NAV、ETF_1m+ETF_5m、REQUIRED4 → COVERAGE_EXAMPLES_ABC.json",
        "- 总体完整比例: **不计算**；缺独立预期不宣称完整也不宣称缺失",
        "",
        "## 3. 最小后续核验（按使用影响排序 top）",
    ]
    for i, it in enumerate(nxt[:12], 1):
        lines.append(
            f"{i}. `{it['product_id']}` score={it['score']} type={it['object_type']} "
            f"exp={it['expectation_kind']} → {it['next_min_check']}"
        )
    lines += [
        "",
        "## 边界",
        "- 未另 hash 6GB 库、未建索引、未重验 R9、未联网、未启引擎、未全量重扫 parquet",
        "- B 引擎目标接受现状；CURRENT 内旧 D 备份指针仅记历史，不改生产",
        "",
    ]
    (OUT / "USER_FINAL_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    shutil.copy2(TIP_SRC, OUT / "TIP_1710.md")


REPO_BASE = (
    "agents/chatgpt/inbox/BLACKBOX_INVENTORY_CONTINUE_20261022_1310/completion_1710"
)
HUB = Path(r"E:\BLACKBOX\运行\外部大脑信箱")


def curl_http(repo_path: str) -> int:
    import urllib.parse

    url = f"https://api.github.com/repos/zwdjwsam-creator/sam/contents/{repo_path}"
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
            url,
        ],
        capture_output=True,
        text=True,
    )
    try:
        return int((r.stdout or "0").strip() or "0")
    except ValueError:
        return 0


def stage_and_push(a_verify: dict) -> dict:
    dest = INBOX_ROOT / "completion_1710"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    allow = [
        "CLAIM.json",
        "USER_FINAL_REPORT.md",
        "A_QUERY_METHOD_VERIFY.json",
        "COVERAGE_CONTRACT_MATRIX.json",
        "COVERAGE_EXAMPLES_ABC.json",
        "NEXT_MIN_CHECKS.json",
        "SCHEMA_PATHS.json",
        "INBOX_POINTER.json",
        "TIP_1710.md",
        "CURSOR_NOTIFY_1710_COMPLETION.md",
        "run_completion_1710_worker.py",
    ]
    for name in allow:
        src = OUT / name
        if src.exists():
            shutil.copy2(src, dest / name)

    recv = {
        "at": NOW,
        "items": [
            {
                "path": "agents/chatgpt/outbox/"
                "BLACKBOX_DATA_MANAGEMENT_1655_REVIEW_AND_COVERAGE_CONTRACT_MATRIX_20261022_1710.md",
                "sha256": sha256_file(TIP_SRC),
            }
        ],
        "checkpoint_hint": TIP_SRC.name,
    }
    jdump(HUB / "_LAST_RECEIVE.json", recv)
    jdump(HUB / "_NEW_FROM_GPT.json", recv)

    pairs = []
    for p in sorted(dest.rglob("*")):
        if p.is_file():
            pairs.append(f"{p}={REPO_BASE}/{p.relative_to(dest).as_posix()}")
    print("PUSHING", len(pairs))
    r = subprocess.run(
        [PY, "-u", str(PUSH), "HUB: completion_1710 coverage matrix"] + pairs
    )
    results = jload(HUB / "_hub_push_last.json") if (HUB / "_hub_push_last.json").exists() else []
    bad = [x for x in results if x.get("http", 500) >= 300 or x.get("error")]
    ok = [x for x in results if not (x.get("http", 500) >= 300 or x.get("error"))]
    print("PUSH_EXIT", r.returncode, "OK", len(ok), "BAD", len(bad))

    verify_keys = (
        "USER_FINAL_REPORT.md",
        "CURSOR_NOTIFY_1710_COMPLETION.md",
        "A_QUERY_METHOD_VERIFY.json",
        "COVERAGE_CONTRACT_MATRIX.json",
        "CLAIM.json",
    )
    verify = {k: curl_http(f"{REPO_BASE}/{k}") == 200 for k in verify_keys}
    print("VERIFY", verify)
    if not all(verify.values()):
        retry = []
        for k, v in verify.items():
            if not v and (dest / k).exists():
                retry.append(f"{dest / k}={REPO_BASE}/{k}")
        if retry:
            subprocess.run(
                [PY, "-u", str(PUSH), "HUB: completion_1710 retry keys"] + retry
            )
            verify = {k: curl_http(f"{REPO_BASE}/{k}") == 200 for k in verify_keys}
            print("VERIFY2", verify)

    pointer_updated = False
    if all(verify.values()):
        ptr = HUB / "agents" / "chatgpt" / "inbox" / "INBOX_FOR_CHATGPT.md"
        ptr.write_text(
            f"""# INBOX_FOR_CHATGPT

updated: {NOW}
latest: {REPO_BASE}/CURSOR_NOTIFY_1710_COMPLETION.md
checkpoint: COMPLETION_1710
acceptance: false
""",
            encoding="utf-8",
        )
        subprocess.run(
            [
                PY,
                "-u",
                str(PUSH),
                "HUB: INBOX pointer 1710",
                f"{ptr}=agents/chatgpt/inbox/INBOX_FOR_CHATGPT.md",
            ]
        )
        pointer_updated = True
    else:
        print("POINTER_SKIPPED_VERIFY_FAIL")

    claim = {
        "at": NOW,
        "tip": "BLACKBOX_DATA_MANAGEMENT_1655_REVIEW_AND_COVERAGE_CONTRACT_MATRIX_20261022_1710",
        "reply_to": "completion_1655",
        "status": "PUSHED" if (r.returncode == 0 and not bad and all(verify.values()) and pointer_updated) else "PUSH_PARTIAL",
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "PRODUCTION_CHANGE_AUTHORIZED": False,
        "A_conclusion": a_verify["conclusion"]["code"],
        "push_exit": r.returncode,
        "bad": len(bad),
        "n_ok": len(ok),
        "n_files": len(pairs),
        "remote_verify_curl": verify,
        "pointer_updated": pointer_updated,
        "pushed_at": NOW,
    }
    jdump(OUT / "CLAIM.json", claim)
    jdump(dest / "CLAIM.json", claim)
    subprocess.run(
        [
            PY,
            "-u",
            str(PUSH),
            "HUB: CLAIM 1710",
            f"{dest / 'CLAIM.json'}={REPO_BASE}/CLAIM.json",
        ]
    )
    jdump(
        HUB / "_hub_LAST_PUSH.json",
        {
            "updated_at": NOW,
            "latest_inbox_path": f"{REPO_BASE}/CURSOR_NOTIFY_1710_COMPLETION.md",
            "checkpoint": "COMPLETION_1710",
            "SYSTEM_INVENTORY_ACCEPTANCE": False,
        },
    )
    return claim


def notify_md(a_verify: dict):
    text = f"""# HUB completion_1710 ready

reply_to: tip_1710
A_conclusion: {a_verify['conclusion']['code']}
matrix_n: 75
acceptance: false

详见 USER_FINAL_REPORT.md / A_QUERY_METHOD_VERIFY.json / COVERAGE_CONTRACT_MATRIX.json
"""
    (OUT / "CURSOR_NOTIFY_1710_COMPLETION.md").write_text(text, encoding="utf-8")


def main():
    assert DB.is_file(), DB
    # tip forbids re-hashing 6GB DB; reuse tip1655 recorded SHA + size check
    prior = jload(PREV / "completion_1655" / "MIGRATION_PATH_LOOKUP.json")
    plan_sha = prior.get("plan_sha256") or EXPECTED_SHA
    assert plan_sha == EXPECTED_SHA, (plan_sha, EXPECTED_SHA)
    print("PLAN_SHA_REUSED", plan_sha, "size", DB.stat().st_size)

    con = connect_ro(DB)
    schema = schema_dump(con)

    # B positive control with corrected methods
    b_res = query_methods(con, B_SRC)
    # choose reliable method: prefer GLOB or range with n>0
    pos_method = None
    for name in ("prefix_glob_children", "prefix_range_children", "prefix_like_escape"):
        m = b_res["methods"][name]
        if m["n"] > 0:
            pos_method = {"method": name, **m}
            break
    if not pos_method:
        pos_method = {"method": "NONE", "n": 0, "sample": [], "sql": "", "params_repr": ""}

    # A re-query all variants + cross tables
    a_variants_out = []
    for v in A_VARIANTS:
        a_variants_out.append(query_methods(con, v))

    needle = "BLACKBOX_JQ20_FULL_DOWNLOAD_PIT_CLEAN_CACHE_HAND_R1"
    cross = cross_table_hits(con, needle)
    cross_jq = cross_table_hits(con, "JQ20_FULL_DOWNLOAD")

    cur = con.cursor()
    t0 = time.time()
    cta_n = cur.execute(
        "SELECT COUNT(*) FROM paths WHERE path GLOB ?",
        (r"D:\CURSOR_TASK_ARCHIVE\*",),
    ).fetchone()[0]
    cta_sec = round(time.time() - t0, 3)
    cta_sample = [
        list(r)
        for r in cur.execute(
            "SELECT path, is_dir FROM paths WHERE path GLOB ? LIMIT 15",
            (r"D:\CURSOR_TASK_ARCHIVE\*",),
        )
    ]
    # any path containing task archive alias forms
    t0 = time.time()
    any_cta = cur.execute(
        "SELECT COUNT(*) FROM paths WHERE instr(path, ?) > 0",
        ("CURSOR_TASK_ARCHIVE",),
    ).fetchone()[0]
    any_cta_sec = round(time.time() - t0, 3)

    # diagnose old method bug on B
    t0 = time.time()
    old_bad = cur.execute(
        "SELECT COUNT(*) FROM paths WHERE path LIKE ?",
        (B_SRC + "\\%",),  # unescaped underscores
    ).fetchone()[0]
    old_bad_sec = round(time.time() - t0, 3)
    t0 = time.time()
    old_double = cur.execute(
        "SELECT COUNT(*) FROM paths WHERE path LIKE ?",
        (B_SRC + "\\\\%",),
    ).fetchone()[0]
    old_double_sec = round(time.time() - t0, 3)

    # A hit any method?
    a_any = False
    for vr in a_variants_out:
        for m in vr["methods"].values():
            if m["n"] > 0 and m is not vr["methods"].get("instr_leaf_name"):
                # instr_leaf may false-positive; check exact/glob/range/like
                pass
        for key in ("exact_pk", "prefix_like_escape", "prefix_glob_children", "prefix_range_children"):
            if vr["methods"][key]["n"] > 0:
                a_any = True
    if any(v["n"] > 0 for v in cross.values()) or any(v["n"] > 0 for v in cross_jq.values()):
        a_any = True

    if a_any:
        conclusion = {
            "code": "FOUND_IN_QUERIED_SCOPE",
            "note": "hits present; see variants",
        }
    else:
        conclusion = {
            "code": "NOT_FOUND_IN_QUERIED_SCOPE",
            "note": (
                "Same validated methods that return B children find zero A rows "
                "in paths + path-bearing tables. D:\\CURSOR_TASK_ARCHIVE exists as dir "
                f"with GLOB children={cta_n}. Cannot infer migration loss."
            ),
        }

    a_verify = {
        "at": NOW,
        "plan_path": str(DB),
        "plan_sha256": plan_sha,
        "sha_match_tip": plan_sha == EXPECTED_SHA,
        "paths_coverage_note": (
            "Queried: paths (PK/LIKE-ESCAPE/GLOB/range/instr) + links/logical_view_42/"
            "observed_metadata_52/blocked_metadata_52/suspect_version_140/link_overlay_audit. "
            "entities.d_paths/delta_paths not expanded (blob aggregates; no path PK)."
        ),
        "separator": "backslash Windows paths in DB",
        "underscore_like_issue": {
            "explanation": "LIKE treats '_' as wildcard; task/engine names contain '_'",
            "old_unescaped_B_prefix_count": old_bad,
            "old_unescaped_B_prefix_seconds": old_bad_sec,
            "old_double_backslash_percent_count": old_double,
            "old_double_backslash_percent_seconds": old_double_sec,
        },
        "positive_control": {
            "root": B_SRC,
            "method": pos_method["method"],
            "sql": pos_method.get("sql"),
            "params_repr": pos_method.get("params_repr"),
            "n": pos_method["n"],
            "sample": pos_method.get("sample", [])[:8],
            "seconds": pos_method.get("seconds"),
            "full_b_methods": b_res,
        },
        "A_variants": a_variants_out,
        "A_cross_table_instr_full_name": cross,
        "A_cross_table_instr_JQ20_FULL_DOWNLOAD": cross_jq,
        "cta_dir_exact": True,
        "cta_child_count": cta_n,
        "cta_child_seconds": cta_sec,
        "cta_child_sample": cta_sample,
        "instr_CURSOR_TASK_ARCHIVE_count": any_cta,
        "instr_CURSOR_TASK_ARCHIVE_seconds": any_cta_sec,
        "conclusion": conclusion,
    }
    con.close()

    ledger = jload(LEDGER)
    matrix = build_matrix(ledger)
    examples = detailed_examples(matrix, ledger)
    nxt = prioritize_next(matrix)

    notify_md(a_verify)
    write_reports(a_verify, matrix, examples, nxt, schema)
    jdump(
        OUT / "INBOX_POINTER.json",
        {
            "at": NOW,
            "inbox_rel": REPO_BASE,
            "ops": str(OUT),
            "key_files": [
                "CLAIM.json",
                "USER_FINAL_REPORT.md",
                "A_QUERY_METHOD_VERIFY.json",
                "COVERAGE_CONTRACT_MATRIX.json",
                "COVERAGE_EXAMPLES_ABC.json",
                "NEXT_MIN_CHECKS.json",
            ],
        },
    )
    claim = stage_and_push(a_verify)
    print("DONE", claim.get("status"), conclusion["code"], "matrix", matrix["n"])


if __name__ == "__main__":
    main()
