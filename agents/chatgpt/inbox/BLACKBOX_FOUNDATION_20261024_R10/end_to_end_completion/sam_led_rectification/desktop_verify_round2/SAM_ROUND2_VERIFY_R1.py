# -*- coding: utf-8 -*-
"""验 SAM 本轮 6/6 交付 + 4 补丁的加法性（不改 COMMIT.json）。"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys

OPS = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion"
                   r"\sam_led_rectification")
sys.path.insert(0, str(OPS))
from HUB_READ_R1 import api  # noqa: E402

REMOTE = ("agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R10"
          "/end_to_end_completion/sam_led_rectification")

# 先列目录，看实到几份
listing = api(f"contents/{REMOTE}")
names = {it["name"]: it.get("size") for it in listing}
print(f"HUB dir objects = {len(names)}")

WANT = [
    "RECONCILE_AND_FIX_DESKTOP_DEVIATION.md",
    "patch_duplicate_roots_r2.py",
    "patch_verify_disk_scan_r3.py",
    "patch_verify_identity_fallback_r4.py",
    "patch_release_content_id_r1.py",
    "PENDING_candidate_commit_v2.py",
]
print("\n=== 6 份到位情况 ===")
present = []
for n in WANT:
    ok = n in names
    if ok:
        present.append(n)
    print(f"  {'YES' if ok else 'NO '}  {n:<40} {names.get(n, '-')}")

# 拉取并哈希
print("\n=== 拉取校验 ===")
res = {"present": {}, "content_checks": {}}
for n in present:
    raw = api(f"contents/{REMOTE}/{n}", raw=True)
    b = raw.encode("utf-8")
    res["present"][n] = {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
                         "text": raw}
    print(f"  {n:<40} {len(b):>7} B  {res['present'][n]['sha256'][:16]}")

# --- 补丁内容审查 ---
print("\n=== 补丁加法性审查 ===")
checks = {}

# 1) patch_duplicate_roots_r2：不得写 COMMIT.json
t = res["present"].get("patch_duplicate_roots_r2.py", {}).get("text", "")
writes_commit = bool(re.search(r'COMMIT_FILE\s*\.\s*write_text|write_text\([^)]*COMMIT', t))
guards = re.findall(r'(COMMIT_[A-Z_]*UNCHANGED|unchanged|sha256_before|sha256_after|NO_COMMIT_MUTATION)', t)
checks["duplicate_roots_appends_jsonl"] = "DUPLICATE_ROOTS" in t
checks["duplicate_roots_does_not_rewrite_COMMIT"] = not writes_commit
checks["duplicate_roots_guards"] = sorted(set(guards))[:6]
print(f"  写 DUPLICATE_ROOTS.jsonl : {'DUPLICATE_ROOTS' in t}")
print(f"  改写 COMMIT.json?        : {writes_commit}  (期望 False)")
print(f"  守卫关键字               : {checks['duplicate_roots_guards']}")

# 2) patch_verify_disk_scan_r3：精度标注
t3 = res["present"].get("patch_verify_disk_scan_r3.py", {}).get("text", "")
checks["r3_has_precision_label"] = "IDENTITY_LEVEL_NOT_CONTENT_PROVEN" in t3
checks["r3_scan_sibling"] = bool(re.search(r'sibling|glob|iterdir', t3))
print(f"  精度标注                  : {checks['r3_has_precision_label']}")

# 3) patch_verify_identity_fallback_r4：HOST_SCOPE_MISMATCH
t4 = res["present"].get("patch_verify_identity_fallback_r4.py", {}).get("text", "")
checks["r4_identity_fallback"] = "checkpoint" in t4 and "identity" in t4
checks["r4_host_scope_guard"] = "HOST_SCOPE_MISMATCH" in t4
print(f"  checkpoint.identity 回落 : {checks['r4_identity_fallback']}")
print(f"  HOST_SCOPE_MISMATCH 守卫  : {checks['r4_host_scope_guard']}")

# 4) patch_release_content_id：是否排除 _ 开头
t1 = res["present"].get("patch_release_content_id_r1.py", {}).get("text", "")
underscore = re.findall(r"startswith\(['\"]_['\"]\)|startswith\(['\"]_", t1)
checks["rcid_excludes_underscore"] = bool(underscore)
checks["rcid_coverage_flag"] = "COVERAGE_PARTIAL" in t1
print(f"  排除 `_` 开头产品         : {bool(underscore)}  {sorted(set(underscore))[:3]}")
print(f"  COVERAGE_PARTIAL 标注     : {checks['rcid_coverage_flag']}")

# 5) PENDING v2 是否 37725 且含 rcid
tv = res["present"].get("PENDING_candidate_commit_v2.py", {}).get("text", "")
vb = res["present"].get("PENDING_candidate_commit_v2.py", {}).get("bytes")
print(f"\n  PENDING_v2 bytes         : {vb}  (SAM 声明 37725)  match={vb == 37725}")
checks["pending_v2_bytes_37725"] = (vb == 37725)
checks["pending_v2_has_rcid"] = "release_content_id" in tv
checks["pending_v2_has_junction_audit"] = "junction_audit" in tv
print(f"  含 release_content_id    : {checks['pending_v2_has_rcid']}")
print(f"  含 junction_audit        : {checks['pending_v2_has_junction_audit']}")

res["checks"] = checks
res.pop("present", None)
out = {k: v for k, v in res.items()}
dest = OPS / "SAM_ROUND2_VERIFY_R1.json"

# 重新组织可落盘结构
save = {"remote_dir": REMOTE, "hub_objects": len(names),
        "want": WANT, "present": present,
        "missing": [n for n in WANT if n not in names],
        "checks": checks}
dest.write_text(json.dumps(save, ensure_ascii=False, indent=2), encoding="utf-8")

print("\n=== 汇总 ===")
print(f"  6/6 到位      : {'PASS' if len(present) == 6 else 'FAIL ' + str(len(present))}")
print(f"  missing       : {save['missing']}")
print(f"saved {dest.name}")
