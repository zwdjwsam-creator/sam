# -*- coding: utf-8 -*-
"""Finalize completion_1600 artifacts, ledger, reports; mirror to local HUB inbox."""
from __future__ import annotations

import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
now = datetime.now(CN).isoformat(timespec="seconds")
OUT = Path(
    r"E:\BLACKBOX\_OPS\SYSTEM_INVENTORY_20261020_2150\v2\continue_0010"
    r"\correction_0650\continue_1310\completion_1600"
)
PREV = OUT.parent
INBOX = Path(
    r"E:\BLACKBOX\运行\外部大脑信箱\agents\chatgpt\inbox"
    r"\BLACKBOX_INVENTORY_CONTINUE_20261022_1310\completion_1600"
)
HUB = Path(r"E:\BLACKBOX\运行\外部大脑信箱")


def main() -> int:
    jq = json.loads((OUT / "JQ20_GROUP_LINEAGE.json").read_text(encoding="utf-8"))
    hits = json.loads(
        (OUT / "source_reads" / "cleaning_release_shallow_hits.json").read_text(encoding="utf-8")
    )["hits"]
    for g in jq["groups"]:
        rid = (g.get("cleaning_release_ids") or [None])[0]
        matched = [h for h in hits if rid and rid in h]
        g["release_dirs_found"] = matched
        if matched:
            g["stages"]["Cleaning_build"] = "RELEASE_DIR_PRESENT"
            p = Path(matched[0])
            if p.exists():
                kids = [x.name for x in list(p.iterdir())[:30]]
                g["release_top_entries"] = kids
                g["has_manifest"] = any(
                    "MANIFEST" in k.upper() or k.endswith(".json") for k in kids
                )
        g["builder_line_bound"] = False
    (OUT / "JQ20_GROUP_LINEAGE.json").write_text(
        json.dumps(jq, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    ledger = json.loads((PREV / "completion_1543" / "OBJECT_LEDGER_75.json").read_text(encoding="utf-8"))
    if isinstance(ledger, list):
        objs = ledger
    else:
        objs = ledger.get("rows") or ledger.get("objects") or ledger.get("items") or []
    print("LEDGER_TYPE", type(ledger).__name__, "n", len(objs))

    reg = json.loads((OUT / "REGISTER_REPLACEMENT_REVIEW.json").read_text(encoding="utf-8"))
    directed = json.loads((OUT / "DIRECTED_LINEAGE_REMAINING.json").read_text(encoding="utf-8"))
    eng = json.loads((OUT / "LIMITED_ENGINE_AUTHORITY_STATIC.json").read_text(encoding="utf-8"))

    for o in objs:
        pid = str(o.get("product_id") or o.get("id") or o.get("object_id") or "")
        prs = o.get("producer_review_status") or ""
        if pid in (
            "CACHE_PRODUCT_CATALOG",
            "CACHE_MANIFEST_REGISTRY_R1",
            "CACHE_DEPENDENCY_REGISTRY_R1",
        ) or "REGISTRY" in pid:
            o["registry_replacement_risk"] = "FIXED_TEMPLATE_REGISTRY_REPLACEMENT"
            o["registry_cause_REQUIRED4"] = "CAUSE_UNPROVEN"
        if pid.startswith("JQ20_"):
            for g in jq["groups"]:
                if pid in g["products"]:
                    o["jq20_lineage_group"] = g["group"]
                    o["cleaning_release_dir_present"] = bool(g.get("release_dirs_found"))
                    o["lineage_stages"] = g["stages"]
                    if (
                        g["stages"].get("Cleaning_build") == "RELEASE_DIR_PRESENT"
                        and prs == "LINEAGE_FROM_PRODUCT_META_PARTIAL"
                    ):
                        o["producer_review_status"] = "LINEAGE_GROUPED_PARTIAL"
                    break
        if "CBOND" in pid or "TUSHARE_CBOND" in pid:
            o["static_scope"] = "CLOSED_ACCEPTED"
            o["R1_daily_entry"] = "UNPROVEN"
        if pid in ("STOCK_MINUTE_5M", "STOCK_5M") or "STOCK_MINUTE_5" in pid:
            o["producer_review_status"] = "KNOWN_UNLOCATED"
        if any(x in pid for x in ("ETF_MINUTE_5", "ETF_MINUTE_30", "ETF_MINUTE_60")):
            o["producer_review_status"] = "KNOWN_UNLOCATED"
        if "SW_L1_STRUCTURE" in pid or pid == "SW_STRUCTURE":
            o["producer_review_status"] = "BLOCKED_CONFIRMED"
            o["note_1600"] = "compiler BLOCKED; densify candidates separate"
        if "BILLBOARD" in pid:
            o["producer_review_status"] = "KNOWN_UNLOCATED"
        if "ENGINE" in pid or pid == "LIMITED_ENGINE_AUTHORITY":
            o["producer_review_status"] = "STATIC_SEED_MAPPED_ACTIVE_UNPROVEN"
            o["engine_seed_present"] = eng["summary"]["file_present"]

        if "content_integrity" not in o:
            o["content_integrity"] = {
                "verified_range": o.get("verified_range") or "RETAIN_PRIOR_OR_UNKNOWN",
                "unverified_range": o.get("unverified_range") or "UNKNOWN",
                "independent_expectation": o.get("independent_expectation") or "UNKNOWN",
                "note": "producer_static_status_must_not_override_content_status",
            }
        if "rules_consumption" not in o:
            o["rules_consumption"] = {
                "authority_file": o.get("authority_file") or "UNKNOWN",
                "consumer": o.get("consumer") or "UNKNOWN",
                "pit_or_license_limits": o.get("pit_limits") or "UNKNOWN",
                "unresolved_ref_impact": o.get("unresolved_ref_impact") or "UNKNOWN",
            }
        if "update_chain" not in o:
            o["update_chain"] = {
                "history_build_vs_incremental": o.get("update_chain_note") or "UNKNOWN",
                "idempotency_key": "UNKNOWN",
                "failure_recovery_publish_boundary": "UNKNOWN",
            }

    new_ledger = {
        "at": now,
        "checkpoint": "COMPLETION_1600",
        "n": len(objs),
        "rows": objs,
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
    }
    (OUT / "OBJECT_LEDGER_75.json").write_text(
        json.dumps(new_ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    with (OUT / "OBJECT_LEDGER_75.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "object_key",
                "producer_review_status",
                "jq20_lineage_group",
                "static_scope",
                "registry_risk",
                "content_verified",
                "notes",
            ]
        )
        for o in objs:
            key = o.get("product_id") or o.get("id") or o.get("object_id") or o.get("name") or ""
            w.writerow(
                [
                    key,
                    o.get("producer_review_status", ""),
                    o.get("jq20_lineage_group", ""),
                    o.get("static_scope", ""),
                    o.get("registry_replacement_risk", ""),
                    (o.get("content_integrity") or {}).get("verified_range", ""),
                    o.get("note_1600") or o.get("follow_hint") or "",
                ]
            )

    stats = Counter(o.get("producer_review_status") or "UNKNOWN" for o in objs)
    (OUT / "LEDGER_STATS.json").write_text(
        json.dumps({"at": now, "n": len(objs), "producer_review_status": dict(stats)}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    remaining = [
        {
            "id": "FIXED_TEMPLATE_REGISTRY_REPLACEMENT",
            "status": "STATIC_KNOWN_RISK",
            "cause_REQUIRED4": "CAUSE_UNPROVEN",
        },
        {
            "id": "JQ20_RAW_AND_DAILY_ENTRY",
            "status": "PARTIAL",
            "note": "cleaning release dirs present; RAW builder + daily entry unproven",
        },
        {"id": "CBOND_R1_AND_DAILY_ENTRY", "status": "OPEN"},
        {"id": "STOCK_MINUTE_5M", "status": "KNOWN_UNLOCATED"},
        {"id": "ETF_MINUTE_5M_30M_60M", "status": "KNOWN_UNLOCATED"},
        {
            "id": "SW_STRUCTURE_DENSIFY",
            "status": "BLOCKED_PLUS_CANDIDATES",
            "candidates": directed["SW_STRUCTURE"]["densify_candidates"],
        },
        {"id": "BILLBOARD", "status": "KNOWN_UNLOCATED"},
        {"id": "LIMITED_ENGINE_ACTIVE", "status": "UNPROVEN", "seeds_present": 17},
        {"id": "KNOWN_GAPS_1519", "status": "KNOWN_GAP_ACCEPTED", "reuse": True},
    ]
    (OUT / "REMAINING_PRIORITIZED.json").write_text(
        json.dumps({"at": now, "items": remaining}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    blockers = [
        "REGISTRY: fixed 19-template write_static_registries can whole-file-replace catalog "
        "(current has +22 rows incl FUND_NAV/ADJUST/CBOND/minutes) — risk registered; "
        "historical REQUIRED4 cause UNPROVEN",
        "JQ20: Cleaning release dirs exist for R19/R20/R22/R29 but RAW download builder + "
        "daily incremental entry still unproven by script/line",
        "CBOND R1 birth + daily entry still unproven (static scope closed only)",
        "STOCK_5M and ETF non-1m downloaders KNOWN_UNLOCATED (not same as no data)",
        "Limited engines: 17/17 seed files present; active runtime UNPROVEN "
        "(docs/pointers ≠ instances)",
        "Content integrity / consumer PIT / update-chain fields still largely UNKNOWN for "
        "most of 75 — producer static ≠ content verified",
    ]

    report = f"""# 数据管理阶段报告（1600）— PARTIAL / 可收口盘点推进

时间: {now}
tip: BLACKBOX_DATA_MANAGEMENT_ACCEPT_1543_AND_CLOSE_REMAINING_EVIDENCE_20261022_1600
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL
COPY_AUTHORIZED: false
PRODUCTION: READONLY

## 本轮接受（继承1543）
- CBOND 静态范围关闭维持；R1/日更仍未证
- full-history / jq_expand / ETF_1m 边界维持，不重复找不存在分支
- JQ20 元数据血缘升级为四组 Cleaning 批量收口（release 目录已命中）

## 1. REGISTER_REPLACEMENT_REVIEW
- 文件: `任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/cache_compiler_daily_incremental_r1.py`
- SHA256: `{reg["files"]["daily_incremental"]["sha256"]}`
- `wtext` L63: tmp+os.replace → **整文件替换**（无 merge）
- `REGISTRY` L30 = CACHE_ROOT/registry；`ARCHIVE` L26 = D:\\CURSOR_TASK_ARCHIVE\\...
- `write_static_registries` L124–232：固定 **19** 产品模板写入 CACHE_PRODUCT_CATALOG.csv 等
- 调用: full_history `main` L241；`build_release` **L405 函数入口即调用**（早于 canary/publish 门槛 L411+）
- 当前 catalog **41** 行 vs 模板 19；差集 +22（含 FUND_NAV_PIT_R1 / ADJUST_FACTOR_PIT_R1 / CBOND* / MINUTE* 等）
- 登记风险: **FIXED_TEMPLATE_REGISTRY_REPLACEMENT**
- REQUIRED4 历史归因: **CAUSE_UNPROVEN**（只证能力，无运行/时序证据）

## 2. JQ20 四组血缘
| 组 | n | Cleaning release 目录 | RAW | CACHE | 日更 |
|---|---|---|---|---|---|
| R19_JQ20 | 13 | 命中 | UNPROVEN | META+PRODUCT | UNPROVEN |
| R20_FUND_MF | 1 | 命中 | UNPROVEN | META+PRODUCT | UNPROVEN |
| R22_FINANCE_SCOPE(PARENT) | 3 | 命中 | UNPROVEN | META+PRODUCT | UNPROVEN |
| R29_RAWPIT(CONSOLIDATED) | 3 | 命中 | PARTIAL(authority名) | META+PRODUCT | UNPROVEN |

元数据 n_rows/asof ≠ 内容完整性合同。

## 3. 定向剩余
- STOCK_5M / ETF_5m_30m_60m: **KNOWN_UNLOCATED**（保留分频证据；缺下载器≠无数据）
- SW: compiler **BLOCKED**；densify 候选脚本已列（见 DIRECTED）
- BILLBOARD: **KNOWN_UNLOCATED**（浅层无命中）
- 有限引擎: 17/17 种子文件在盘；**活跃未证明**；迁移96≠实例

## 4. 仍阻止整体验收的证据缺口
{chr(10).join("- " + b for b in blockers)}

## 统计
{json.dumps(dict(stats), ensure_ascii=False, indent=2)}

产物: REGISTER_REPLACEMENT_REVIEW.json / JQ20_GROUP_LINEAGE.json / DIRECTED_LINEAGE_REMAINING.json / LIMITED_ENGINE_AUTHORITY_STATIC.json / OBJECT_LEDGER_75.* / USER_FINAL_REPORT.md
"""
    (OUT / "USER_FINAL_REPORT.md").write_text(report, encoding="utf-8")
    (OUT / "MASTER_PROGRESS.md").write_text(
        "# MASTER_PROGRESS 1600\n\n"
        + json.dumps(
            {
                "at": now,
                "checkpoint": "COMPLETION_1600",
                "SYSTEM_INVENTORY_ACCEPTANCE": False,
                "status": "PARTIAL",
                "stats": dict(stats),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "STATUS_PROGRESS.json").write_text(
        json.dumps(
            {"at": now, "checkpoint": "COMPLETION_1600", "status": "PARTIAL", "acceptance": False},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    notify = f"""# CURSOR 回传：1600 注册表风险 + 分组血缘收口

时间: {now}
host: ZHANGWEI
reply_to: agents/chatgpt/outbox/BLACKBOX_DATA_MANAGEMENT_ACCEPT_1543_AND_CLOSE_REMAINING_EVIDENCE_20261022_1600.md
phase: COMPLETION_1600
SYSTEM_INVENTORY_ACCEPTANCE: **false**
status: PARTIAL

## 交付
1. REGISTER_REPLACEMENT_REVIEW（整文件替换风险；CAUSE_UNPROVEN）
2. JQ20 四组 Cleaning 血缘（release 目录命中；RAW/日更仍缺口）
3. 分钟/CBOND/SW/BILLBOARD/有限引擎定向收口
4. 更新75账本 + 收口报告

详见 USER_FINAL_REPORT.md / LEDGER_STATS.json
"""
    (OUT / "CURSOR_NOTIFY_1600_COMPLETION.md").write_text(notify, encoding="utf-8")

    claim = {
        "at": now,
        "tip": "BLACKBOX_DATA_MANAGEMENT_ACCEPT_1543_AND_CLOSE_REMAINING_EVIDENCE_20261022_1600",
        "status": "DONE_LOCAL",
        "SYSTEM_INVENTORY_ACCEPTANCE": False,
        "PRODUCTION_CHANGE_AUTHORIZED": False,
        "COPY_AUTHORIZED": False,
        "finished_at": now,
    }
    (OUT / "CLAIM.json").write_text(json.dumps(claim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    tip = HUB / "staging" / "BLACKBOX_DATA_MANAGEMENT_ACCEPT_1543_AND_CLOSE_REMAINING_EVIDENCE_20261022_1600.md"
    if tip.exists():
        shutil.copy2(tip, OUT / "TIP_1600.md")

    if INBOX.exists():
        shutil.rmtree(INBOX)
    shutil.copytree(OUT, INBOX, ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
    print("LEDGER_STATS", dict(stats))
    print("OUT_FILES", len(list(OUT.rglob("*"))))
    print("INBOX", INBOX)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
