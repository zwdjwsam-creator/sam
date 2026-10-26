# -*- coding: utf-8 -*-
"""冻结 rcid 产品契约：声明 51 个产品 + 10 个正式必需（来自编译器，独立于被测 release）。

契约一旦冻结即为基准；后续 release 必须对上：
  - 声明里有、实际缺  -> missing_declared（不可宣称完整核验）
  - 实际有、声明里没  -> extra_present（记录，不静默吞掉）
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

BASE = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
REL = BASE / "candidate" / "cc_out" / "releases" / \
    "BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_181019"
COMMIT_ROOT = BASE / "candidate" / "cc_commit"
COMPILER = pathlib.Path(r"E:\BLACKBOX\任务\BLACKBOX_BACKTEST_CACHE_COMPILER_R1"
                        r"\cache_compiler_tip_rebase_from_current_r1.py")

# 正式必需产品：从编译器源码里抽 required = [...] 块，不手抄
src = COMPILER.read_text(encoding="utf-8", errors="replace")
m = re.search(r"\n\s*required\s*=\s*\[(.*?)\]", src, re.S)
if not m:
    raise SystemExit("REQUIRED_BLOCK_NOT_FOUND")
formal_required = re.findall(r'"([A-Z0-9_]+)"', m.group(1))
print(f"compiler formal required = {len(formal_required)}")
for p in formal_required:
    print("   ", p)

# 声明产品集：当前 release 的实体产品目录（排除 _ 前缀与元文件）
declared = sorted(p.name for p in REL.iterdir()
                  if p.is_dir() and not p.name.startswith("_"))
meta_files = sorted(p.name for p in REL.iterdir()
                    if p.is_file() and not p.name.startswith("_"))

print(f"\ndeclared products = {len(declared)}")
print(f"meta files        = {len(meta_files)} -> {meta_files}")

miss = [p for p in formal_required if p not in declared]
if miss:
    raise SystemExit(f"FORMAL_REQUIRED_NOT_IN_DECLARED: {miss}")

contract = {
    "schema": "BLACKBOX_RCID_PRODUCT_CONTRACT_R1",
    "contract_id": None,
    "frozen_from_release_id": REL.name,
    "asof": "2026-09-24",
    "declared_products": declared,
    "formal_required_products": formal_required,
    "formal_required_source":
        "E:/BLACKBOX/任务/BLACKBOX_BACKTEST_CACHE_COMPILER_R1/"
        "cache_compiler_tip_rebase_from_current_r1.py :: required=[...]",
    "excluded_dir_prefix": "_",
    "excluded_meta_files": meta_files,
    "excluded_reason": (
        "_qa and build metadata (SEAL/RELEASE/MANIFEST/POINTER/ASOF/FACTS) carry "
        "timestamps and seals that change every build; including them would make every "
        "rebuild look like a content change and destroy the meaning of NOOP."
    ),
    "junction_content_proven": False,
    "junction_note": (
        "A junction product contributes its target identity (path + target release id), "
        "not borrowed bytes. If the target's files change in place without the target "
        "RELEASE.json id changing, rcid will NOT change. Declared, not hidden."
    ),
    "contract_sha256": None,
}

blob = json.dumps({k: v for k, v in contract.items()
                   if k not in ("contract_id", "contract_sha256")},
                  ensure_ascii=False, sort_keys=True).encode("utf-8")
contract["contract_sha256"] = hashlib.sha256(blob).hexdigest()
contract["contract_id"] = "RCID_C1_" + contract["contract_sha256"][:16]

COMMIT_ROOT.mkdir(parents=True, exist_ok=True)
dest = COMMIT_ROOT / "RCID_PRODUCT_CONTRACT_R1.json"
if dest.exists():
    old = json.loads(dest.read_text(encoding="utf-8"))
    if old.get("contract_id") == contract["contract_id"]:
        print(f"\n[ALREADY_SAME] {dest.name} contract_id={contract['contract_id']}")
        raise SystemExit(0)
    raise SystemExit(
        f"CONTRACT_ALREADY_FROZEN_DIFFERENT: existing={old.get('contract_id')} "
        f"new={contract['contract_id']} — 不覆盖已冻结契约，请显式走版本升级")

dest.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n[FROZEN] {dest}")
print(f"  contract_id    = {contract['contract_id']}")
print(f"  contract_sha256= {contract['contract_sha256']}")
print(f"  declared n     = {len(declared)}")
print(f"  formal n       = {len(formal_required)} (subset ok)")
