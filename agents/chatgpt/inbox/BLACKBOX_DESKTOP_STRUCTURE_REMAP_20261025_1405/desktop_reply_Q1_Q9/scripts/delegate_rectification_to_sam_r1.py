#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把台式机副本的整顿权移交 SAM 端 Cursor：写冻结旗标 + 状态快照（不改进任何业务文件）。"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
TASK = ROOT / "任务" / "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1"
OUT = TASK / "输出"
MANIFEST = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"
PLANE = ROOT / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_PLANE_CURRENT.json"
VERIFY = OUT / "AFTER_SAM_Q1_Q9_VERIFY.json"
DELEGATION = ROOT / "运行" / "BLACKBOX_DESKTOP_REPAIR_DELEGATION_CURRENT.json"


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else {}


def atomic(p: Path, o: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_name(p.name + f".tmp_{os.getpid()}")
    t.write_text(json.dumps(o, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(t, p)


def main() -> int:
    man, plane, ver = load(MANIFEST), load(PLANE), load(VERIFY)
    ch = ver.get("checks", {})
    manifest_digest = {
        "path": str(MANIFEST),
        "manifest_id": man.get("manifest_id"),
        "CN_RESEARCH_DATE": man.get("CN_RESEARCH_DATE"),
        "BUILD_TIME": man.get("BUILD_TIME"),
        "DATA_GENERATION_ID": man.get("DATA_GENERATION_ID"),
        "MANIFEST_SEMANTIC_SHA256": man.get("MANIFEST_SEMANTIC_SHA256"),
        "lane_state": {
            k: {"MODE": man[k].get("MODE"), "STATUS": man[k].get("STATUS"),
                "DISCOVERY_ASOF": man[k].get("DISCOVERY_ASOF")}
            for k in ("JQ", "T_EXTERNAL", "GLOBAL_SELLSIDE", "DOMESTIC_RESEARCH", "US_NEWS", "US_MARKET")
        },
        "US_MARKET_FIXED_PATHS": sorted((man.get("US_MARKET", {}).get("FIXED_PATHS") or {})),
    }
    snap = {
        "schema": "BLACKBOX_DESKTOP_STATE_SNAPSHOT_FOR_SAM_R1",
        "execution_host": "ZHANGWEI",
        "captured_at_cn": now_cn(),
        "handover": {
            "owner_of_rectification": "SAM 端 Cursor（笔记本原 BLACKBOX）",
            "desktop_role": "只读待命；不自行决定 DG1 / 不改业务代码 / 不重建 manifest",
            "desktop_write_freeze": {
                "manifest_and_plane": True,
                "data_plane_current": True,
                "business_code": True,
                "data_artifacts": True,
            },
            "exception": "仅主人显式指令可解除冻结",
        },
        "manifest": manifest_digest,
        "verification": {
            "verdict": ver.get("verdict"),
            "dg1_state": ver.get("dg1_state"),
            "checks": ch,
            "verified_at_cn": ver.get("verified_at_cn"),
        },
        "open_decisions_for_sam_cursor": [
            {
                "id": "D1_DG1_MODE",
                "question": "MODE 是否应计入 DG1 语义哈希？",
                "facts": [
                    "回退 alignment_csv 后残差仅 3 个 MODE",
                    "把 3 个 MODE 置 INGEST 后 DG1 精确等于 DG1-7fd2bf71…c2b13",
                    "MODE 由源码 219/252/280 行按 ingest 布尔写出，属动作字段",
                ],
                "options": ["A 保留真实 MODE + 登记 DIVERGENT_MODE_ONLY",
                            "B 真跑 ingest 使其成为事实",
                            "C MODE 移出语义哈希（须全仓回归）"],
                "desktop_recommendation": "C（若要 DG1 语义恒等）或 A（若要零改动）；B 需授权采集",
            },
            {
                "id": "D2_DATE_ARG_PATCH",
                "question": "是否修 --date 只吃 YYYYMMDD + --mode status 有写副作用？",
                "facts": ["932 行切片产生 2026--0-9-", "status 会写 CURRENT/STATE/DAILY", "已修复并留账，生产残留 0"],
                "desktop_recommendation": "修，但会改变 SAM 已审计的文件字节，须 SAM 点头后再改",
            },
            {
                "id": "D3_MEMORY_DAYS",
                "question": "研究记忆缺口口径：15 还是 17 个交易日？",
                "facts": ["08-31→09-24 含 09-02/09-03 = 17", "09-04→09-24 = 15", "DAILY_BRIEF 仅 2026-08-30"],
                "desktop_recommendation": "以交易日集合为准，两者不矛盾；回补须人工双写 asof / research_date",
            },
            {
                "id": "D4_D_DRIVE_ARCHIVE",
                "question": "cache 编译器 11 处 D:\\CURSOR_TASK_ARCHIVE 写入是否注入可覆盖的归档根？",
                "facts": ["本机 D: 存在且可写，当前不阻断", "换机/无 D: 会真失败"],
                "desktop_recommendation": "注入 env/参数覆盖，不改业务算法",
            },
        ],
        "ledgers": {
            "verify": str(VERIFY),
            "dg1_revert": str(OUT / "DG1_FIELD_REVERT_LEDGER_CURRENT.json"),
            "bad_date_cleanup": str(OUT / "BAD_DATE_CLEANUP_LEDGER.json"),
            "current_restore": str(OUT / "CURRENT_RESTORE_LEDGER.json"),
            "cross_machine_write": str(OUT / "CROSS_MACHINE_WRITE_LEDGER.json"),
            "package_manifest": str(OUT / "PACKAGE_MANIFEST_R2.json"),
        },
        "counts_baseline_source_of_truth": {
            "cache_product_dirs": ch.get("cache_product_dirs"),
            "cache_top_files": ch.get("cache_top_files"),
            "path_map_entries": ch.get("path_map_entries"),
            "path_map_missing": ch.get("path_map_missing"),
            "note": "产品数只数目录；固定路径口径 = DATA_PLANE_PATH_MAP.json 键数",
        },
    }
    atomic(OUT / "DESKTOP_STATE_SNAPSHOT_FOR_SAM.json", snap)

    deleg = {
        "schema": "BLACKBOX_DESKTOP_REPAIR_DELEGATION_R1",
        "recorded_at_cn": now_cn(),
        "delegated_by": "OWNER",
        "delegated_to": "SAM 端 Cursor（笔记本原 BLACKBOX）",
        "subject": "整顿台式机 BLACKBOX 副本",
        "desktop_write_freeze": snap["handover"]["desktop_write_freeze"],
        "desktop_role": snap["handover"]["desktop_role"],
        "snapshot": str(OUT / "DESKTOP_STATE_SNAPSHOT_FOR_SAM.json"),
        "handoff_doc": str(TASK / "HANDOFF_TO_SAM_CURSOR.md"),
        "hub_dir": "agents/chatgpt/inbox/BLACKBOX_DESKTOP_STRUCTURE_REMAP_20261025_1405/desktop_reply_Q1_Q9",
        "flags": {
            "DESKTOP_SELF_DIRECTED_RECTIFICATION": False,
            "ORDER_ALLOWED": False,
            "NEW_DATA_ACQUISITION_AUTHORIZED": False,
            "COPY_AUTHORIZED": False,
        },
        "open_decisions": [d["id"] for d in snap["open_decisions_for_sam_cursor"]],
    }
    atomic(DELEGATION, deleg)
    print(json.dumps({"snapshot": str(OUT / "DESKTOP_STATE_SNAPSHOT_FOR_SAM.json"),
                      "delegation": str(DELEGATION),
                      "dg1": man.get("DATA_GENERATION_ID"),
                      "freeze": deleg["desktop_write_freeze"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
