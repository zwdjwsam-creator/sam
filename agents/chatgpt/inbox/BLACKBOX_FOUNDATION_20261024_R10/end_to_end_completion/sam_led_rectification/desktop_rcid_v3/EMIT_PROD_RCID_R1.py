# -*- coding: utf-8 -*-
"""为当前生产引用的 release 生成不可变 rcid 侧文件，并验证 COMMIT.json 一字节未变。"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

E2E = pathlib.Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
TOOLS = E2E / "tools"
sys.path.insert(0, str(TOOLS))

import candidate_commit as cc  # noqa: E402

COMMIT = E2E / "candidate" / "cc_commit" / "COMMIT.json"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    before = sha(COMMIT)
    commit = json.loads(COMMIT.read_text(encoding="utf-8"))
    rel = pathlib.Path(commit["release_root"])
    print(f"COMMIT.json sha_before = {before[:16]}")
    print(f"release_root           = {rel.name}")
    print(f"commit_id              = {commit['commit_id'][:16]}")
    print(f"release_content_id     = {commit.get('release_content_id')}")

    print("\n--- verify BEFORE emit ---")
    v_before = cc.verify()
    print(json.dumps({k: v_before.get(k) for k in
                      ("status", "consistent", "content_identity_verified")},
                     ensure_ascii=False))
    print("  rcid_check:", json.dumps(v_before.get("release_content_id_check"),
                                     ensure_ascii=False)[:300])

    print("\n--- emit_release_content_id ---")
    em = cc.emit_release_content_id(rel)
    print(json.dumps(em, ensure_ascii=False, indent=1)[:1200])

    after = sha(COMMIT)
    print(f"\nCOMMIT.json sha_after  = {after[:16]}   UNCHANGED={before == after}")

    print("\n--- verify AFTER emit ---")
    v_after = cc.verify()
    print(json.dumps({k: v_after.get(k) for k in
                      ("status", "consistent", "content_identity_verified")},
                     ensure_ascii=False))
    chk = v_after.get("release_content_id_check") or {}
    print("  rcid_check.status/source:", chk.get("status"), "/", chk.get("source"))
    print("  declared_count          :", chk.get("declared_count"))
    print("  junction_content_proven :", chk.get("junction_content_proven"))

    print("\n--- commit() on the same reference (must not write) ---")
    rc = cc.commit(rel, note="desktop post-install noop probe")
    print(json.dumps({k: rc.get(k) for k in
                      ("status", "commit_id", "release_content_id", "rcid_source",
                       "commit_file_written")}, ensure_ascii=False))
    after2 = sha(COMMIT)
    print(f"COMMIT.json sha_final  = {after2[:16]}   UNCHANGED={before == after2}")

    out = {
        "schema": "BLACKBOX_PROD_RCID_EMIT_R1",
        "commit_json_sha_before": before,
        "commit_json_sha_after": after2,
        "commit_json_unchanged": before == after2,
        "release_id": rel.name,
        "commit_id": commit["commit_id"],
        "emit": em,
        "verify_before": {k: v_before.get(k) for k in
                          ("status", "consistent", "content_identity_verified")},
        "verify_after": {k: v_after.get(k) for k in
                         ("status", "consistent", "content_identity_verified")},
        "rcid_check_after": v_after.get("release_content_id_check"),
        "commit_probe": rc,
    }
    dest = E2E / "sam_led_rectification" / "PROD_RCID_EMIT_R1.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsaved {dest.name}")

    ok = (out["commit_json_unchanged"]
          and em.get("status") in ("EMITTED", "ALREADY_SAME")
          and v_before.get("consistent") is False
          and v_before.get("status") == "CONTENT_IDENTITY_UNVERIFIED"
          and v_after.get("consistent") is True
          and rc.get("status") == "IDEMPOTENT_NOOP")
    print(f"\nOVERALL = {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 8


if __name__ == "__main__":
    raise SystemExit(main())
