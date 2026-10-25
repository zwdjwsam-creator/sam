"""Run the ORIGINAL tip-rebase cache compiler in candidate mode.

The original entry point is kept intact (`cache_compiler_tip_rebase_from_current_r1.py`,
real function bodies, real gates).  Only the paths that would touch production are
injected, and only through values the module already exposes:

  * `--out-root`            -> candidate releases dir (module uses it for `rel`)
  * `--parent-root`         -> sealed release, read-only
  * `--cleaning-json`       -> candidate cleaning RELEASE.json
  * `--no-publish`          -> module never calls `publish_atomic`
  * module `OUT`            -> candidate acceptance dir, because the original code
                               writes `OUT/TIP_REBASE_LAST.json` unconditionally
                               (this is the side path the review asked to relocate)

Every other write the module performs lands inside `rel`, which is new and empty.
`CACHE_ROOT` / `POINTER` / `CLEAN` production constants are read-only here: the
module only reads them when the corresponding CLI argument is absent.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import traceback
from pathlib import Path

COMPILER_PATH = Path(
    r"E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1"
    r"\cache_compiler_tip_rebase_from_current_r1.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("tip_rebase_candidate", COMPILER_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cleaning-json", required=True)
    ap.add_argument("--parent-root", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--acceptance-out", required=True)
    ap.add_argument("--run-target-date", required=True)
    ap.add_argument("--receipt", required=True)
    args = ap.parse_args()

    acceptance = Path(args.acceptance_out)
    acceptance.mkdir(parents=True, exist_ok=True)
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    mod = load_module()
    prod_out = mod.OUT
    mod.OUT = acceptance
    mod.RELEASES = out_root  # used only if --out-root is absent; kept consistent

    argv = [
        str(COMPILER_PATH),
        "--run-target-date", args.run_target_date,
        "--cleaning-json", args.cleaning_json,
        "--parent-root", args.parent_root,
        "--out-root", args.out_root,
        "--no-publish",
    ]
    saved_argv = sys.argv
    sys.argv = argv
    t0 = time.time()
    rc = 0
    err = None
    try:
        rc = int(mod.main() or 0)
    except SystemExit as e:
        rc = int(e.code or 0) if isinstance(e.code, (int, type(None))) else 1
        if rc not in (0, 2):
            err = f"SystemExit({e.code!r})"
    except Exception as e:  # noqa: BLE001  (propagate the failure, do not mask it)
        rc = 1
        err = f"{type(e).__name__}: {e}"
        traceback.print_exc()
    finally:
        sys.argv = saved_argv
        mod.OUT = prod_out
    elapsed = round(time.time() - t0, 1)

    produced = sorted(p.name for p in out_root.iterdir() if p.is_dir()) if out_root.exists() else []
    receipt = {
        "compiler_module": str(COMPILER_PATH),
        "argv": argv,
        "exit_code": rc,
        "error": err,
        "elapsed_sec": elapsed,
        "redirected_OUT": str(acceptance),
        "production_OUT_untouched": str(prod_out),
        "publish_called": False,
        "no_publish": True,
        "releases_root": str(out_root),
        "releases_present": produced,
        "running_python": sys.executable,
    }
    Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(args.receipt).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
