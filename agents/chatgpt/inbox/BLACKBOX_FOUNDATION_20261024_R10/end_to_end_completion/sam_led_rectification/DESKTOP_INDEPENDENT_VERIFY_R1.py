#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""台机独立复验：逐字段核验 SAM 交付的 CONNECTED_PIPELINE.json 与目录/日期副作用。

不复用 RUN_CHAIN_R1 的 verdicts，全部从产物与文件系统重新推导。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CN = timezone(timedelta(hours=8))
BB = Path(r"E:\BLACKBOX")
E2E = BB / "_OPS" / "FOUNDATION_RECOVERY_20261024" / "end_to_end_completion"
RECT = E2E / "sam_led_rectification"
PY = str(BB / ".venv" / "Scripts" / "python.exe")
OUT = RECT / "DESKTOP_INDEPENDENT_VERIFY.json"

WATCH = [
    BB / "研究系统/数据平面/CURRENT/DAILY_DATA_MANIFEST_CURRENT.json",
    BB / "研究系统/数据平面/CURRENT/DAILY_DATA_PLANE_CURRENT.json",
    BB / "研究系统/数据平面/CURRENT/DAILY_RESEARCH_INPUT_PACK_CURRENT.json",
    BB / "研究系统/数据平面/STATE/JQ_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/T_EXTERNAL_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/GLOBAL_SELLSIDE_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/DOMESTIC_RESEARCH_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/US_NEWS_INCREMENTAL_STATE.json",
    BB / "研究系统/数据平面/STATE/US_MARKET_STATE_INCREMENTAL_STATE.json",
]


def sha(p: Path):
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def get(d, *keys, default=None):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return default
    return cur


def main() -> int:
    R: dict = {"artifact": "DESKTOP_INDEPENDENT_VERIFY_R1",
               "hostname": os.environ.get("COMPUTERNAME"),
               "at_cn": datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z"),
               "checks": {}, "notes": [], "blockers": []}

    def chk(name: str, ok: bool, detail=None) -> None:
        R["checks"][name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            R["blockers"].append(name)

    # ---------- 1. 证据身份 ----------
    ev = json.loads((RECT / "LOCAL_RUN_EVIDENCE.json").read_text(encoding="utf-8"))
    chk("evidence_hostname_is_ZHANGWEI",
        get(ev, "identity", "hostname") == "ZHANGWEI",
        get(ev, "identity", "hostname"))
    chk("evidence_python_is_venv",
        "E:\\\\BLACKBOX\\\\.venv" in str(get(ev, "identity", "sys_executable", default="")).upper()
        or "e:\\blackbox\\.venv" in str(get(ev, "identity", "sys_executable", default="")).lower(),
        get(ev, "identity", "sys_executable"))
    chk("evidence_started_after_190000",
        str(get(ev, "identity", "started_at_cn", default="")).startswith("2026-10-25T19:1")
        or str(get(ev, "identity", "started_at_cn", default="")).startswith("2026-10-25T19:2"),
        get(ev, "identity", "started_at_cn"))

    # ---------- 2. steps ----------
    st = ev.get("steps", {})
    chk("A_chain_exit_zero", get(st, "A_chain", "exit_code") == 0, get(st, "A_chain", "exit_code"))
    chk("B_status_iso_exit_zero", get(st, "B_status_iso", "exit_code") == 0)
    chk("C_bad_date_exit_nonzero", get(st, "C_bad_date", "exit_code") not in (0, None),
        get(st, "C_bad_date", "exit_code"))
    chk("D_status_compact_exit_zero", get(st, "D_status_compact", "exit_code") == 0)
    chk("elapsed_A_under_1200s", (get(st, "A_chain", "elapsed_sec", default=99999) or 0) < 1200,
        get(st, "A_chain", "elapsed_sec"))

    # C 日志必须含 INVALID_DATE_FAIL_CLOSED
    ctail = str(get(st, "C_bad_date", "stdout_tail", default=""))
    chk("C_bad_date_message_fail_closed", "INVALID_DATE_FAIL_CLOSED" in ctail,
        ctail.strip().splitlines()[-1] if ctail.strip() else "(empty)")
    # B/D 必须显式只读
    btail = str(get(st, "B_status_iso", "stdout_tail", default=""))
    dtail = str(get(st, "D_status_compact", "stdout_tail", default=""))
    chk("B_declares_read_only", "STATUS_MODE_READ_ONLY_OK" in btail or '"READ_ONLY": true' in btail)
    chk("D_declares_read_only", "STATUS_MODE_READ_ONLY_OK" in dtail or '"READ_ONLY": true' in dtail)

    # ---------- 3. digests（status 不写盘） ----------
    dg = ev.get("digests", {})
    chk("digest_after_status_equals_after_chain", dg.get("after_status_iso") == dg.get("after_chain"))
    chk("digest_after_bad_date_equals_after_status", dg.get("after_bad_date") == dg.get("after_status_iso"))
    chk("digest_end_equals_after_bad_date", dg.get("end") == dg.get("after_bad_date"))
    chk("digest_watch_count_9", len(dg.get("start") or {}) == 9, len(dg.get("start") or {}))

    # 现态再算一次：CURRENT/STATE 必须与 run 结束时一致
    now = {str(p.relative_to(BB)).replace("\\", "/"): sha(p) for p in WATCH}
    chk("watch_files_unchanged_since_run", now == (dg.get("end") or {}),
        [k for k in now if now.get(k) != (dg.get("end") or {}).get(k)])

    # ---------- 4. CONNECTED_PIPELINE.json 交付物 ----------
    cp_path = E2E / "deliverables" / "CONNECTED_PIPELINE.json"
    chk("CONNECTED_PIPELINE_json_exists", cp_path.exists(), str(cp_path))
    cp = json.loads(cp_path.read_text(encoding="utf-8")) if cp_path.exists() else {}
    chk("CONNECTED_PIPELINE_RESULT_PASS", get(cp, "CONNECTED_PIPELINE_RESULT") == "PASS",
        get(cp, "CONNECTED_PIPELINE_RESULT"))
    for k in ("lineage_same_artifact", "compiler_read_r15_tree", "transport_gate_pass",
              "tampered_date_blocked", "self_cert_blocked", "r15_cleaning_pass",
              "original_compiler_all_pass", "commit_consistent", "same_input_replay_noop",
              "production_current_untouched", "compiler_hard_block_propagated",
              "replay_days_present_in_release"):
        chk(f"cp_verdict_{k}", get(cp, "verdicts", k) is True, get(cp, "verdicts", k))

    chk("cp_compiler_seal_all_pass", get(cp, "stages", "compiler", "seal_all_pass") is True,
        get(cp, "stages", "compiler", "seal_all_pass"))
    chk("cp_cleaning_release_id",
        get(cp, "stages", "cleaning_r15", "release_id") == "R15_REPLAY_20260924_R3",
        get(cp, "stages", "cleaning_r15", "release_id"))
    chk("cp_same_input_replay_PASS", get(cp, "stages", "same_input_replay", "status") == "PASS",
        get(cp, "stages", "same_input_replay", "status"))
    chk("cp_commit_PASS", get(cp, "stages", "commit", "status") == "PASS",
        get(cp, "stages", "commit", "status"))
    chk("PRODUCTION_CURRENT_WRITE_NONE",
        get(cp, "PRODUCTION_CURRENT_WRITE") in ("NONE", None),
        get(cp, "PRODUCTION_CURRENT_WRITE"))

    retained = get(cp, "LINEAGE", "retained_batches", default=[]) or []
    chk("LINEAGE_retained_nonempty", len(retained) > 0, len(retained))
    bad = [b.get("name") for b in retained if b.get("retained_equals_r15_sealed") is not True]
    chk("LINEAGE_all_retained_equal_r15_sealed", len(bad) == 0, bad)

    # ---------- 5. R15 封版确实存在于磁盘且封版标记完整 ----------
    rel = E2E / "candidate" / "r15_releases" / "R15_REPLAY_20260924_R3"
    chk("r15_R3_dir_exists", rel.exists(), str(rel))
    rj = json.loads((rel / "RELEASE.json").read_text(encoding="utf-8")) if rel.exists() else {}
    chk("r15_R3_release_id", rj.get("release_id") == "R15_REPLAY_20260924_R3")
    chk("r15_R3_sealed_marker", (rel / ".BLACKBOX_SEALED").exists())
    chk("r15_R3_no_production_write", rj.get("PRODUCTION_CURRENT_WRITE") in ("NONE", None),
        rj.get("PRODUCTION_CURRENT_WRITE"))
    chk("r15_R3_switch_current_not_called", rj.get("switch_current") in ("NOT_CALLED", None))
    files = list(rel.rglob("*")) if rel.exists() else []
    nf = sum(1 for p in files if p.is_file())
    chk("r15_R3_file_count_reasonable", nf >= 300, nf)

    # ---------- 6. 无非法日期目录 ----------
    bad_dirs = []
    for base in (BB / "数据", BB / "运行"):
        if base.exists():
            for p in base.rglob("2026--*"):
                bad_dirs.append(str(p))
    chk("no_bad_date_dirs", len(bad_dirs) == 0, bad_dirs[:10])

    # ---------- 7. 生产 CURRENT 未被写入（按 mtime 判） ----------
    run_start = datetime.fromisoformat(str(get(ev, "identity", "started_at_cn")).replace("+0800", "+08:00"))
    touched = []
    for p in WATCH[:3]:
        if p.exists():
            mt = datetime.fromtimestamp(p.stat().st_mtime, CN)
            if mt > run_start:
                touched.append(f"{p.name}@{mt.isoformat()}")
    chk("production_CURRENT_not_touched_by_run", len(touched) == 0, touched)

    # ---------- 8. 回滚备份在位 ----------
    baks = {
        "run_r15_cleaning_replay.py.bak_sam_led_r6": E2E / "candidate" / "run_r15_cleaning_replay.py.bak_sam_led_r6",
        "run_connected_pipeline.py.bak_sam_led_r7": E2E / "tools" / "run_connected_pipeline.py.bak_sam_led_r7",
        "data_plane.bak_sam_led_20261025": BB / "脚本" / "run_blackbox_daily_incremental_data_plane_r1.py.bak_sam_led_20261025",
    }
    chk("rollback_backups_present", all(p.exists() for p in baks.values()),
        {k: v.exists() for k, v in baks.items()})

    # ---------- 9. 交付文件身份（含 EOL 归一说明） ----------
    ids = {}
    for rel_p, decl in (("candidate/run_r15_cleaning_replay.py", "2719c17eec5589ac"),
                        ("tools/run_connected_pipeline.py", "4964f27cc325c8e8")):
        b = (E2E / rel_p).read_bytes()
        raw = hashlib.sha256(b).hexdigest()[:16]
        lf = hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()[:16]
        ids[rel_p] = {"raw": raw, "lf_norm": lf, "declared": decl,
                      "match": decl in (raw, lf)}
    dp = BB / "脚本" / "run_blackbox_daily_incremental_data_plane_r1.py"
    ids["脚本/data_plane"] = {"raw": hashlib.sha256(dp.read_bytes()).hexdigest()[:16],
                             "declared": "949e95c758b2064c"}
    ids["脚本/data_plane"]["match"] = ids["脚本/data_plane"]["raw"] == "949e95c758b2064c"
    chk("delivered_identity_match", all(v["match"] for v in ids.values()), ids)

    R["identity_of_delivered_files"] = ids
    R["summary"] = {
        "total_checks": len(R["checks"]),
        "passed": sum(1 for v in R["checks"].values() if v["ok"]),
        "failed": len(R["blockers"]),
    }
    R["status"] = "PASS" if not R["blockers"] else "BLOCKED"
    OUT.write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": R["status"], "summary": R["summary"],
                      "blockers": R["blockers"], "out": str(OUT)},
                     ensure_ascii=False, indent=2))
    return 0 if R["status"] == "PASS" else 5


if __name__ == "__main__":
    raise SystemExit(main())
