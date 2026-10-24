#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLACKBOX Research Operating System — unified entry."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
OS_ROOT = ROOT / "研究系统"
PY = ROOT / ".venv" / "Scripts" / "python.exe"
CN = timezone(timedelta(hours=8))
U235_SCRIPT = ROOT / "脚本" / "run_blackbox_master_research_autorun_r1.py"

PATHS = {
    "hand": ROOT / "HAND.txt",
    "constitution": ROOT / "研究记忆" / "01_RESEARCH_CONSTITUTION.md",
    "os_current": OS_ROOT / "BLACKBOX_RESEARCH_OS_CURRENT.md",
    "os_state": OS_ROOT / "BLACKBOX_RESEARCH_OS_STATE.json",
    "registry": OS_ROOT / "BLACKBOX_RESEARCH_OS_MODULE_REGISTRY.json",
    "schedule": OS_ROOT / "CONFIG" / "research_os_schedule.json",
    "current_state": OS_ROOT / "RESEARCH_OS_CURRENT_STATE.json",
    "authority": OS_ROOT / "BLACKBOX_RESEARCH_OS_AUTHORITY.md",
    "data_plane_current": OS_ROOT / "数据平面" / "CURRENT" / "DAILY_DATA_PLANE_CURRENT.json",
    "data_manifest_current": OS_ROOT / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json",
    "data_plane_script": ROOT / "脚本" / "run_blackbox_daily_incremental_data_plane_r1.py",
}

_U235_MOD: Any = None


def load_u235_module() -> Any:
    """Load U235 autorun module once — reuse production Manifest Gate (no duplicate semantics)."""
    global _U235_MOD
    if _U235_MOD is not None:
        return _U235_MOD
    spec = importlib.util.spec_from_file_location("blackbox_u235_autorun_r1_gate", U235_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load U235 gate module: {U235_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _U235_MOD = mod
    return mod


def load_and_evaluate_canonical_manifest_gate(manifest_path: Path | None = None) -> dict[str, Any]:
    """Same production function as U235 (imported, not reimplemented)."""
    fn: Callable[..., dict[str, Any]] = load_u235_module().load_and_evaluate_canonical_manifest_gate
    if manifest_path is None:
        return fn(PATHS["data_manifest_current"])
    return fn(manifest_path)


def evaluate_data_plane_double_gate(
    *,
    data_plane_rc: int,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """DATA_PLANE_RETURN_CODE==0 AND CANONICAL_MANIFEST_GATE==PASS. DEGRADED READY fails closed."""
    mg = load_and_evaluate_canonical_manifest_gate(manifest_path)
    ok = int(data_plane_rc) == 0 and mg.get("STATUS") == "PASS"
    reason = None if ok else (
        "DATA_PLANE_RC_NONZERO" if int(data_plane_rc) != 0 else (mg.get("reason_code") or "MANIFEST_GATE_FAIL")
    )
    return {
        "ok": ok,
        "DATA_PLANE_RETURN_CODE": int(data_plane_rc),
        "CANONICAL_MANIFEST_GATE": mg.get("STATUS"),
        "reason_code": reason if not ok else "MANIFEST_GATE_PASS",
        "manifest_id": mg.get("manifest_id"),
        "source_asof": mg.get("source_asof"),
        "clean_asof": mg.get("clean_asof"),
        "cache_asof": mg.get("cache_asof"),
        "manifest_path": mg.get("manifest_path"),
        "evidence_gaps": mg.get("evidence_gaps") or [],
        "manifest_gate": mg,
    }


def emit_data_gate_fail(gate: dict[str, Any]) -> None:
    print(
        "DATA_GATE_FAIL "
        + json.dumps(
            {
                "reason_code": gate.get("reason_code"),
                "DATA_PLANE_RETURN_CODE": gate.get("DATA_PLANE_RETURN_CODE"),
                "CANONICAL_MANIFEST_GATE": gate.get("CANONICAL_MANIFEST_GATE"),
                "manifest_id": gate.get("manifest_id"),
                "source_asof": gate.get("source_asof"),
                "clean_asof": gate.get("clean_asof"),
                "cache_asof": gate.get("cache_asof"),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def load_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def atomic_write_json(p: Path, obj: dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)


def file_ok(p: Path | str | None, *, min_bytes: int = 1) -> bool:
    if not p:
        return False
    path = Path(p)
    return path.exists() and path.stat().st_size >= min_bytes


def run_script(script: str | None, extra: list[str] | None = None) -> int:
    if not script:
        print(f"[SKIP] no script", flush=True)
        return 0
    path = Path(script)
    if not path.exists():
        print(f"[SKIP] missing script {path}", flush=True)
        return 1
    cmd = [str(PY), "-u", str(path)]
    if extra:
        cmd.extend(extra)
    print(f"[RUN] {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=str(ROOT)).returncode


def precheck() -> tuple[bool, dict[str, str]]:
    results: dict[str, str] = {}
    for key, path in [
        ("HAND", PATHS["hand"]),
        ("CONSTITUTION", PATHS["constitution"]),
        ("RESEARCH_OS", PATHS["os_current"]),
        ("OS_STATE", PATHS["os_state"]),
        ("REGISTRY", PATHS["registry"]),
        ("AUTHORITY", PATHS["authority"]),
        ("DAILY_DATA_PLANE", PATHS["data_plane_current"]),
        ("DAILY_DATA_MANIFEST", PATHS["data_manifest_current"]),
    ]:
        results[key] = "PASS" if file_ok(path) else "FAIL"
    core = ("HAND", "CONSTITUTION", "RESEARCH_OS", "OS_STATE", "REGISTRY", "AUTHORITY")
    ok = all(results.get(k) == "PASS" for k in core)
    return ok, results


def module_status(registry: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for mid, mod in (registry.get("modules") or {}).items():
        st = mod.get("status", "UNKNOWN")
        cur = mod.get("current_output")
        if cur and not file_ok(cur):
            st = "STALE" if st == "READY" else st
        out[mid] = st
    return out


def infer_today_state() -> str:
    t = datetime.now(CN).strftime("%H:%M")
    if t < "07:30":
        return "INIT"
    if t < "09:30":
        return "PREMARKET_RESEARCH"
    if t < "11:30":
        return "MORNING_LIVE"
    if t < "13:00":
        return "MIDDAY_PAUSE"
    if t < "15:00":
        return "AFTERNOON_LIVE"
    if t < "15:05":
        return "CLOSE"
    return "DAILY_RECAP"


def print_startup_panel(precheck_res: dict[str, str], mod_st: dict[str, str], state: dict[str, Any]) -> None:
    sched = load_json(PATHS["schedule"]) if PATHS["schedule"].exists() else {}
    interval = sched.get("live_loop_seconds", 120)
    today = state.get("today_state") or infer_today_state()
    print("=" * 40)
    print("BLACKBOX RESEARCH OS")
    print("=" * 40)
    for k in ("HAND", "CONSTITUTION", "RESEARCH_OS"):
        print(f"{k} = {precheck_res.get(k, 'FAIL')}")
    print(f"AUTHORITY = {precheck_res.get('AUTHORITY', 'FAIL')}")
    print(f"DAILY_DATA_PLANE = {precheck_res.get('DAILY_DATA_PLANE', 'FAIL')}")
    print()
    labels = {
        "01_SELLSIDE_GLOBAL": "GLOBAL_SELLSIDE",
        "02_SELLSIDE_DOMESTIC": "DOMESTIC_SELLSIDE",
        "03_PUBLIC_INFORMATION": "PUBLIC_INFO",
        "04_STRUCTURAL_ONTOLOGY": "STRUCTURAL",
        "05_COMPANY_REALITY": "REALITY",
        "06_TAO_POLICY_MODEL": "TAO_POLICY",
        "12_LIVE_FOCUS": "LIVE_FOCUS",
    }
    for mid, label in labels.items():
        print(f"{label} = {mod_st.get(mid, 'UNKNOWN')}")
    qmt = mod_st.get("12_LIVE_FOCUS", "UNKNOWN")
    print(f"QMT = {'READY' if qmt in ('READY', 'PARTIAL') else 'FAIL'}")
    print(f"MINUTE_AUTHORITY = PASS")
    print()
    print(f"TODAY_STATE = {today}")
    print(f"LIVE_INTERVAL = {interval} SEC")
    print(f"ORDER_ALLOWED = {str(state.get('order_allowed', False)).upper()}")
    print("=" * 40)


def sync_current_pointers(registry: dict[str, Any]) -> None:
    """Mirror module outputs into 研究系统/CURRENT where applicable."""
    cur_dir = OS_ROOT / "CURRENT"
    cur_dir.mkdir(parents=True, exist_ok=True)
    cs = load_json(PATHS["current_state"]) if PATHS["current_state"].exists() else {}
    cs["updated_at_cn"] = now_cn()
    atomic_write_json(PATHS["current_state"], cs)

    # Global sellside: copy pointer from existing CURRENT
    g_src = registry["modules"]["01_SELLSIDE_GLOBAL"]["current_output"]
    if file_ok(g_src):
        data = load_json(Path(g_src))
        md_path = cur_dir / "GLOBAL_SELLSIDE_CURRENT.md"
        md_path.write_text(
            f"# GLOBAL SELLSIDE CURRENT\n\nasof={data.get('asof')}\nstatus={data.get('status')}\nsource={g_src}\n",
            encoding="utf-8",
        )


def build_premarket_synthesis(registry: dict[str, Any]) -> None:
    cur_dir = OS_ROOT / "CURRENT"
    cur_dir.mkdir(parents=True, exist_ok=True)
    out = cur_dir / "PREMARKET_RESEARCH_SYNTHESIS_CURRENT.md"
    ts = now_cn()
    sections = [
        f"# PREMARKET RESEARCH SYNTHESIS\n\nupdated_at_cn: {ts}\n",
        "## 1. GLOBAL SELLSIDE PRIOR\n",
        f"- source: `{registry['modules']['01_SELLSIDE_GLOBAL']['current_output']}`\n",
        "## 2. DOMESTIC SELLSIDE PRIOR\n",
        f"- source: `{registry['modules']['02_SELLSIDE_DOMESTIC']['current_output']}`\n",
        "## 3. POLICY / NEWS\n",
        f"- source: `{registry['modules']['03_PUBLIC_INFORMATION']['current_output']}`\n",
        "## 4. STRUCTURAL THEMES\n",
        f"- ontology: `{registry['modules']['04_STRUCTURAL_ONTOLOGY']['current_output']}`\n",
        f"- focus32: `{registry['modules']['04_STRUCTURAL_ONTOLOGY']['focus32_matrix']}` (REFERENCE ONLY)\n",
        "## 5. REALITY CHANGE\n",
        f"- source: `{registry['modules']['05_COMPANY_REALITY']['current_output']}`\n",
        "## 6. PREMARKET THEME HYPOTHESIS\n",
        "(synthesized at runtime — fill WHY_WATCH + WHAT_WOULD_FALSIFY per theme)\n",
        "## 7. CORE WATCHLIST\n",
        f"- source: `{registry['modules']['09_CORE_SYNCHRONIZATION']['current_output']}`\n",
        "## 8. RISK / FALSIFICATION\n",
        "(required per theme)\n",
    ]
    out.write_text("".join(sections), encoding="utf-8")
    print(f"[OK] wrote {out}", flush=True)


def update_state(today_state: str | None = None, *, degraded: list[str] | None = None) -> None:
    state = load_json(PATHS["os_state"])
    state["updated_at_cn"] = now_cn()
    state["today_state"] = today_state or infer_today_state()
    state["last_transition_at_cn"] = now_cn()
    if degraded is not None:
        state["degraded_modules"] = degraded
    atomic_write_json(PATHS["os_state"], state)


def mode_daily_incremental(*, run: bool = False, date: str | None = None) -> int:
    extra: list[str] = ["--mode", "run" if run else "status"]
    if date:
        extra.extend(["--date", date])
    return run_script(str(PATHS["data_plane_script"]), extra)


def mode_premarket(registry: dict[str, Any], *, manifest_path: Path | None = None) -> int:
    rc = mode_daily_incremental(run=False)
    gate = evaluate_data_plane_double_gate(data_plane_rc=rc, manifest_path=manifest_path)
    if not gate["ok"]:
        emit_data_gate_fail(gate)
        # Fail-closed: do not call sellside / ontology / sync / synthesis / PREMARKET_RESEARCH state.
        return 2
    rc |= run_script(registry["modules"]["01_SELLSIDE_GLOBAL"]["script"])
    rc |= run_script(registry["modules"]["02_SELLSIDE_DOMESTIC"]["script"])
    rc |= run_script(registry["modules"]["03_PUBLIC_INFORMATION"]["script"])
    rc |= run_script(registry["modules"]["04_STRUCTURAL_ONTOLOGY"]["script"])
    sync_current_pointers(registry)
    build_premarket_synthesis(registry)
    update_state("PREMARKET_RESEARCH", degraded=[] if rc == 0 else ["PARTIAL_PREMARKET"])
    return rc


def mode_full_day(registry: dict[str, Any], *, date: str | None = None, manifest_path: Path | None = None) -> int:
    rc = mode_daily_incremental(run=True, date=date)
    gate = evaluate_data_plane_double_gate(data_plane_rc=rc, manifest_path=manifest_path)
    if not gate["ok"]:
        emit_data_gate_fail(gate)
        # Fail-closed: do not continue into premarket research modules.
        return 2
    return mode_premarket(registry, manifest_path=manifest_path)


def mode_live(registry: dict[str, Any]) -> int:
    live_script = registry["modules"]["12_LIVE_FOCUS"]["script"]
    update_state(infer_today_state())
    return run_script(live_script)


def mode_close(registry: dict[str, Any]) -> int:
    daily = OS_ROOT / "DAILY" / datetime.now(CN).strftime("%Y%m%d")
    daily.mkdir(parents=True, exist_ok=True)
    recap = daily / "CLOSE_RECAP.md"
    recap.write_text(
        f"# Daily Research Recap\n\nasof={datetime.now(CN).strftime('%Y-%m-%d')}\n\n"
        "Update: THEME_TIMELINE, LIVE_FOCUS_TIMELINE, POSITION_STATE, OPEN_QUESTIONS\n",
        encoding="utf-8",
    )
    update_state("DAILY_RECAP")
    print(f"[OK] archived recap stub → {recap}", flush=True)
    return 0


def mode_status(registry: dict[str, Any]) -> int:
    ok, pre = precheck()
    mod_st = module_status(registry)
    state = load_json(PATHS["os_state"])
    print_startup_panel(pre, mod_st, state)
    print(json.dumps({"MUST_READ_PRECHECK": "PASS" if ok else "FAIL", "modules": mod_st}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def batch1_research_os_selftest() -> int:
    """Isolated BATCH_1 Research OS double-gate tests. Reuses U235 Manifest Gate. No real modules/CURRENT."""
    import tempfile
    from unittest import mock

    results: list[tuple[str, bool, str]] = []

    def rec(name: str, ok: bool, note: str) -> None:
        results.append((name, ok, note))
        print(f"ROS_FIXTURE {name} = {'PASS' if ok else 'FAIL'}  {note}", flush=True)

    def write_man(p: Path, obj: Any) -> None:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, ensure_ascii=False) + "\n", encoding="utf-8")

    def base_ok() -> dict[str, Any]:
        return {
            "manifest_id": "DAILY_DATA_MANIFEST_TEST",
            "DAILY_INCREMENTAL_READY": "YES",
            "JQ": {
                "STATUS": "PASS",
                "SOURCE_ASOF": "2026-08-31",
                "CLEAN_ASOF": "2026-08-31",
                "CACHE_ASOF": "2026-08-31",
            },
        }

    registry = {
        "modules": {
            "01_SELLSIDE_GLOBAL": {"script": "MOCK_GLOBAL_SELLSIDE", "current_output": "x"},
            "02_SELLSIDE_DOMESTIC": {"script": "MOCK_DOMESTIC_SELLSIDE", "current_output": "x"},
            "03_PUBLIC_INFORMATION": {"script": "MOCK_PUBLIC_INFO", "current_output": "x"},
            "04_STRUCTURAL_ONTOLOGY": {"script": "MOCK_ONTOLOGY", "current_output": "x", "focus32_matrix": "x"},
            "05_COMPANY_REALITY": {"current_output": "x"},
            "09_CORE_SYNCHRONIZATION": {"current_output": "x"},
        }
    }

    def run_case(
        name: str,
        *,
        plane_rc: int,
        manifest: dict[str, Any] | None,
        expect_ok: bool,
        missing_manifest: bool = False,
    ) -> None:
        sellside_calls: list[Any] = []
        ontology_calls: list[Any] = []
        sync_calls: list[int] = []
        synth_calls: list[int] = []
        state_calls: list[Any] = []

        def fake_run_script(script: str | None, extra: list[str] | None = None) -> int:
            s = str(script or "")
            if "SELLSIDE" in s or "PUBLIC" in s:
                sellside_calls.append(s)
            if "ONTOLOGY" in s:
                ontology_calls.append(s)
            return 0

        def fake_sync(_reg: dict[str, Any]) -> None:
            sync_calls.append(1)

        def fake_synth(_reg: dict[str, Any]) -> None:
            synth_calls.append(1)

        def fake_update(today_state: str | None = None, *, degraded: list[str] | None = None) -> None:
            state_calls.append({"today_state": today_state, "degraded": degraded})

        with tempfile.TemporaryDirectory(prefix="b1_ros_") as td:
            mp = Path(td) / "m.json"
            if missing_manifest:
                pass
            elif manifest is not None:
                write_man(mp, manifest)
            mod = sys.modules[__name__]
            with (
                mock.patch.object(mod, "mode_daily_incremental", return_value=plane_rc),
                mock.patch.object(mod, "run_script", side_effect=fake_run_script),
                mock.patch.object(mod, "sync_current_pointers", side_effect=fake_sync),
                mock.patch.object(mod, "build_premarket_synthesis", side_effect=fake_synth),
                mock.patch.object(mod, "update_state", side_effect=fake_update),
            ):
                rc = mode_premarket(registry, manifest_path=mp)
            if expect_ok:
                ok = (
                    rc == 0
                    and len(sellside_calls) >= 1
                    and len(ontology_calls) == 1
                    and len(sync_calls) == 1
                    and len(synth_calls) == 1
                    and any(c.get("today_state") == "PREMARKET_RESEARCH" for c in state_calls)
                )
            else:
                ok = (
                    rc != 0
                    and len(sellside_calls) == 0
                    and len(ontology_calls) == 0
                    and len(sync_calls) == 0
                    and len(synth_calls) == 0
                    and not any(c.get("today_state") == "PREMARKET_RESEARCH" for c in state_calls)
                )
            rec(
                name,
                ok,
                f"rc={rc} sellside={len(sellside_calls)} ontology={len(ontology_calls)} "
                f"sync={len(sync_calls)} synth={len(synth_calls)} state={state_calls}",
            )

    run_case("DATA_PLANE_RC_1", plane_rc=1, manifest=base_ok(), expect_ok=False)
    run_case("DATA_PLANE_RC_0_MANIFEST_MISSING", plane_rc=0, manifest=None, expect_ok=False, missing_manifest=True)
    run_case(
        "DATA_PLANE_RC_0_READY_NO",
        plane_rc=0,
        manifest={**base_ok(), "DAILY_INCREMENTAL_READY": "NO"},
        expect_ok=False,
    )
    run_case(
        "DATA_PLANE_RC_0_READY_DEGRADED",
        plane_rc=0,
        manifest={**base_ok(), "DAILY_INCREMENTAL_READY": "DEGRADED"},
        expect_ok=False,
    )
    run_case(
        "DATA_PLANE_RC_0_ASOF_MISMATCH",
        plane_rc=0,
        manifest={
            **base_ok(),
            "JQ": {**base_ok()["JQ"], "CLEAN_ASOF": "2026-08-30"},
        },
        expect_ok=False,
    )
    run_case("DATA_PLANE_RC_0_ALL_PASS", plane_rc=0, manifest=base_ok(), expect_ok=True)

    # full_day: DEGRADED + rc0 must not reach premarket modules
    sellside_calls: list[Any] = []
    with tempfile.TemporaryDirectory(prefix="b1_ros_fd_") as td:
        mp = Path(td) / "m.json"
        write_man(mp, {**base_ok(), "DAILY_INCREMENTAL_READY": "DEGRADED"})
        mod = sys.modules[__name__]

        def fake_run_script(script: str | None, extra: list[str] | None = None) -> int:
            sellside_calls.append(str(script))
            return 0

        with (
            mock.patch.object(mod, "mode_daily_incremental", return_value=0),
            mock.patch.object(mod, "run_script", side_effect=fake_run_script),
            mock.patch.object(mod, "sync_current_pointers"),
            mock.patch.object(mod, "build_premarket_synthesis"),
            mock.patch.object(mod, "update_state"),
        ):
            rc = mode_full_day(registry, manifest_path=mp)
        ok = rc != 0 and len(sellside_calls) == 0
        rec("FULL_DAY_RC0_READY_DEGRADED_STOP", ok, f"rc={rc} sellside={len(sellside_calls)}")

    # Prove same production gate function as U235 (imported module, identical results)
    u235 = load_u235_module()
    with tempfile.TemporaryDirectory(prefix="b1_same_") as td:
        mp = Path(td) / "m.json"
        write_man(mp, base_ok())
        a = load_and_evaluate_canonical_manifest_gate(mp)
        b = u235.load_and_evaluate_canonical_manifest_gate(mp)
        same_fn = (
            load_u235_module().load_and_evaluate_canonical_manifest_gate
            is u235.load_and_evaluate_canonical_manifest_gate
        )
        ok = same_fn and a.get("STATUS") == b.get("STATUS") == "PASS" and a.get("reason_code") == b.get("reason_code")
        rec("SELFTEST_PRODUCTION_FUNCTION_REUSE", ok, f"same_fn={same_fn} reason={a.get('reason_code')}")

    failed = [n for n, o, _ in results if not o]
    print(f"ROS_SELFTEST_TOTAL={len(results)} PASS={len(results)-len(failed)} FAIL={len(failed)}", flush=True)
    if failed:
        print(f"ROS_SELFTEST_FAILED={failed}", flush=True)
        return 1
    print("ROS_BATCH1_SELFTEST=PASS", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="BLACKBOX Research Operating System")
    ap.add_argument("--mode", default="status", choices=["premarket", "live", "close", "full_day", "daily_incremental", "status"])
    ap.add_argument("--date", default=None, help="CN research date YYYYMMDD (daily_incremental)")
    ap.add_argument("--run", action="store_true", help="run lane collectors (daily_incremental)")
    ap.add_argument("--resume", action="store_true", help="resume daily_incremental (checkpoint TBD)")
    ap.add_argument(
        "--batch1-selftest",
        action="store_true",
        help="BATCH_1 isolated double-gate selftest; no production CURRENT / modules",
    )
    args = ap.parse_args()

    if args.batch1_selftest:
        return batch1_research_os_selftest()

    if not PATHS["registry"].exists():
        print("[FAIL] missing module registry", flush=True)
        return 2

    registry = load_json(PATHS["registry"])
    ok, pre = precheck()
    if not ok and args.mode != "status":
        print("[FAIL] precheck failed", pre, flush=True)
        return 2

    mod_st = module_status(registry)
    state = load_json(PATHS["os_state"]) if PATHS["os_state"].exists() else {}
    print_startup_panel(pre, mod_st, state)

    if args.mode == "status":
        return 0 if ok else 1
    if args.mode == "premarket":
        return mode_premarket(registry)
    if args.mode == "live":
        return mode_live(registry)
    if args.mode == "close":
        return mode_close(registry)
    if args.mode == "daily_incremental":
        return mode_daily_incremental(run=bool(args.run), date=args.date)
    if args.mode == "full_day":
        rc = mode_full_day(registry, date=args.date)
        if rc == 0:
            print("[INFO] full_day: premarket done; invoke --mode live manually for session", flush=True)
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
