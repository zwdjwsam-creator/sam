# -*- coding: utf-8 -*-
"""台机独立 fixture 负控：验证 FILE_SET_IDENTITY 语义 + 两个盲点。只读，不碰任何产品。"""
from __future__ import annotations

import json
import pathlib
import sys

COMP = pathlib.Path(r"E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1")
sys.path.insert(0, str(COMP))
import cache_compiler_daily_incremental_r1 as cc  # noqa: E402

R = {"schema": "DESKTOP_FILE_SET_IDENTITY_FIXTURE_R1", "cases": {}}


def run(name, fn):
    try:
        out = fn()
        R["cases"][name] = {"raised": None, "result": out}
        return f"NO_RAISE  {json.dumps(out, ensure_ascii=False)[:150]}"
    except Exception as e:  # noqa: BLE001
        R["cases"][name] = {"raised": f"{type(e).__name__}", "message": str(e)[:200]}
        return f"RAISED    {type(e).__name__}: {str(e)[:130]}"


def rep(*paths, status="READ"):
    return [{"file": str(p), "status": status} for p in paths]


A, B, C = r"E:\x\a.parquet", r"E:\x\b.parquet", r"E:\x\c.parquet"

cases = {
    # 1. 等数量但换一个键 —— SAM 声称会被 FILE_SET_IDENTITY 拦
    "equal_count_swapped_key": lambda: cc.assert_read_closure(
        product="FIX", expected_files=[A, B], enumerated_files=[A, C],
        read_files=[A, C], report=rep(A, C)),
    # 2. 少一个
    "missing_one": lambda: cc.assert_read_closure(
        product="FIX", expected_files=[A, B], enumerated_files=[A],
        read_files=[A], report=rep(A)),
    # 3. 完全正常
    "healthy": lambda: cc.assert_read_closure(
        product="FIX", expected_files=[A, B], enumerated_files=[A, B],
        read_files=[A, B], report=rep(A, B)),
    # 4. 源根不存在：expected=[] enumerated=[] read=[]（负控实际走的就是这条）
    "empty_source_root": lambda: cc.assert_read_closure(
        product="FIX", expected_files=[], enumerated_files=[],
        read_files=[], report=[]),
    # 5. scan_parquet_independent 对不存在路径的返回值
    "scan_nonexistent_root": lambda: {
        "files": len(cc.scan_parquet_independent(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024"
                                                 r"\end_to_end_completion\nope"))},
    # 6. 读失败必须拦
    "read_failed": lambda: cc.assert_read_closure(
        product="FIX", expected_files=[A, B], enumerated_files=[A, B],
        read_files=[A], report=rep(A) + [{"file": str(B), "status": "READ_FAILED",
                                          "error": "boom"}]),
    # 7. expected_keys_from_frames 收到空 frame（检查 p 未定义缺陷）
    "empty_frame_in_expected_keys": lambda: len(cc.expected_keys_from_frames(
        [None], asof="2026-09-24", start="2026-01-01")),
}

print(f"{'case':<30} outcome")
for n, fn in cases.items():
    print(f"{n:<30} {run(n, fn)}")

R["verdict"] = {
    "detects_swapped_key": R["cases"]["equal_count_swapped_key"]["raised"] is not None,
    "detects_missing_one": R["cases"]["missing_one"]["raised"] is not None,
    "healthy_passes": R["cases"]["healthy"]["raised"] is None,
    "empty_root_is_blind": R["cases"]["empty_source_root"]["raised"] is None,
    "read_failed_blocks": R["cases"]["read_failed"]["raised"] is not None,
    "empty_frame_bug": R["cases"]["empty_frame_in_expected_keys"]["raised"] is not None,
}
print()
print(json.dumps(R["verdict"], ensure_ascii=False, indent=2))
out = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
                   r"\sam_led_rectification\DESKTOP_FILE_SET_IDENTITY_FIXTURE.json")
out.write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8")
print("saved", out.name)
