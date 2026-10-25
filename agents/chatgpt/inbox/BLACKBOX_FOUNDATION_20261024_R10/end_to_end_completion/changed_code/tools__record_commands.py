"""Record exact commands, exit codes and raw stdout/stderr for the reproducible steps.

The review asked for the real command log rather than a narrative. Each entry runs a
command through the bound recovery runtime, stores the combined output, and records
the exit code. The 16-session backtest is recorded from its actual run artefact
because it is long-running; that is stated explicitly in the entry.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

TASK = r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
PY = r"E:\BLACKBOX\.venv\Scripts\python.exe"
LOGS = os.path.join(TASK, "evidence", "command_logs")
OUT = os.path.join(TASK, "evidence", "COMMAND_LOG.json")

STEPS = [
    ("must_read_preflight",
     [r"E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py", "--task-class", "BACKTEST", "--json"],
     r"E:\BLACKBOX"),
    ("environment_verify", [os.path.join(TASK, "tools", "verify_environment.py")], TASK),
    ("raw_status_field_inventory", [os.path.join(TASK, "tools", "raw_status_field_inventory.py")], TASK),
    ("build_tradeability_candidate", [os.path.join(TASK, "tools", "build_tradeability_candidate.py")], TASK),
    ("build_dataset_state", [os.path.join(TASK, "tools", "build_dataset_state.py")], TASK),
    ("run_connected_pipeline", [os.path.join(TASK, "tools", "run_connected_pipeline.py")], TASK),
    ("build_checkpoint_bindings", [os.path.join(TASK, "tools", "build_checkpoint_bindings.py")], TASK),
]


def main() -> int:
    os.makedirs(LOGS, exist_ok=True)
    entries = []
    for name, argv, cwd in STEPS:
        log_path = os.path.join(LOGS, f"{name}.log")
        proc = subprocess.run([PY, "-X", "utf8", *argv], cwd=cwd, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")
        with open(log_path, "w", encoding="utf-8") as fh:
            fh.write("$ " + " ".join([PY, "-X", "utf8", *argv]) + "\n\n")
            fh.write("--- STDOUT ---\n" + (proc.stdout or ""))
            fh.write("\n--- STDERR ---\n" + (proc.stderr or ""))
            fh.write(f"\n--- EXIT {proc.returncode} ---\n")
        entries.append({
            "name": name,
            "command": " ".join([PY, "-X", "utf8", *argv]),
            "cwd": cwd,
            "exit_code": proc.returncode,
            "stdout_tail": (proc.stdout or "").strip().splitlines()[-6:],
            "stderr_tail": (proc.stderr or "").strip().splitlines()[-4:],
            "log": log_path,
        })

    # The long backtest: record the real command and the real artefact of that run.
    bt_dir = os.path.join(TASK, "engine_runs", "v4_r21_20260903_20260924_R11_TRADEABILITY_RECON")
    bt_result = os.path.join(bt_dir, "run_result.json")
    bt_entry = {
        "name": "v4_backtest_requested_scope",
        "command": (
            " ".join([
                PY, "-X", "utf8", os.path.join(TASK, "candidate", "run_engine_backtest.py"),
                "--start", "2026-09-03", "--end", "2026-09-24",
                "--strategy", r"E:\BLACKBOX\参考资料\聚宽策略写法\聚宽范本_日频模拟盘_V4_R21_HOTSTART_R5.py",
                "--cash", "1000000", "--benchmark", "000300.XSHG",
                "--out", os.path.join("engine_runs", "v4_r21_20260903_20260924_R11_TRADEABILITY_RECON"),
                "--allow-candidate-override", "--strict-inputs",
                "--local-dictionary", r"D:\BB_LOCAL_DICTIONARY\R10_ASOF_20260924",
            ])
        ),
        "cwd": TASK,
        "env": {
            "BLACKBOX_CANDIDATE_TRADEABILITY": (
                r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion\candidate"
                r"\data\R11_TRADEABILITY\STOCK_TRADEABILITY_PIT_R1\year=2026\part_2026.parquet"
            )
        },
        "exit_code": None,
        "recorded_from": bt_result,
        "note": "long-running (about 70 minutes); exit code and status are read from the run's "
        "own artefact instead of re-executing it for the log",
    }
    if os.path.exists(bt_result):
        res = json.load(open(bt_result, encoding="utf-8"))
        bt_entry["exit_code"] = 0 if res.get("status") == "COMPLETED" else (
            3 if res.get("status") == "BLOCKED_INPUT_INCOMPLETE" else 1)
        bt_entry["status"] = res.get("status")
        bt_entry["input_blockers"] = res.get("input_blockers")
        bt_entry["strategy_input_warnings"] = res.get("strategy_input_warnings")
        bt_entry["tradeability_binding"] = res.get("tradeability_binding")
        bt_entry["started_at"] = res.get("started_at")
        bt_entry["finished_at"] = res.get("finished_at")
        bt_entry["required_input_failures"] = res.get("required_input_failures")
        bt_entry["n_mark_price_starved"] = res.get("n_mark_price_starved")
        bt_entry["n_trades"] = res.get("n_trades")
        bt_entry["n_orders"] = res.get("n_orders")
    entries.append(bt_entry)
    # Input-plane sweep evidence is regenerated on every recording pass so the
    # numbers in the report can never drift from the numbers in the log.
    sweep = subprocess.run(
        [PY, "-X", "utf8", os.path.join(TASK, "tools", "build_input_plane_repair_evidence.py")],
        cwd=TASK, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    entries.append({
        "name": "input_plane_sweep",
        "command": " ".join([PY, "-X", "utf8",
                             os.path.join(TASK, "tools", "build_input_plane_repair_evidence.py")]),
        "cwd": TASK,
        "exit_code": sweep.returncode,
        "stdout_tail": (sweep.stdout or "").strip().splitlines()[-3:],
        "stderr_tail": (sweep.stderr or "").strip().splitlines()[-3:],
        "artifact": os.path.join(TASK, "evidence", "INPUT_PLANE_REPAIR.json"),
    })

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"artifact": "COMMAND_LOG", "python": PY, "entries": entries}, fh,
                  ensure_ascii=False, indent=2)
    for e in entries:
        print(f"{e['name']:32s} exit={e['exit_code']!s:5s} log={os.path.basename(str(e.get('log')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
