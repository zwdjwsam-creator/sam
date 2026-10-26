# -*- coding: utf-8 -*-
"""v3 针对性测试：证明 release_content_id 真的参与判断，而不只是写了个字符串。

全部在临时沙盒里跑（_rcid_test/），不碰生产 COMMIT.json / 不改任何 release。
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil

import pyarrow as pa
import pyarrow.parquet as pq

RECT = pathlib.Path(__file__).resolve().parent
V3 = RECT / "candidate_commit_v3.py"
V2 = RECT / "_sam_pending" / "PENDING_candidate_commit_v2.py"
SANDBOX = RECT / "_rcid_test"
PROD_REL = (RECT.parents[0] / "candidate" / "cc_out" / "releases"
            / "BLACKBOX_CACHE_R1_TIP_REBASE_ASOF_20260924_20261026_181019")
PROD_COMMIT_ID = "572619c945d48f1b14f41c6f8c94b66dbacab00da4303366bcf2687ff8ec0876"

FIVE = ["ETF_DAILY_PIT_R1", "INDEX_DAILY_R1", "STOCK_DAILY_PIT_R1",
        "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1"]

RESULTS: list[dict] = []


def load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def write_pq(p: pathlib.Path, codes: list[str], closes: list[float]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    t = pa.table({"code": pa.array(codes, pa.string()),
                  "date": pa.array(["2026-09-24"] * len(codes), pa.string()),
                  "close": pa.array(closes, pa.float64())})
    pq.write_table(t, p)


def make_release(root: pathlib.Path, *, idx_codes=None, idx_closes=None,
                 etf_closes=None) -> pathlib.Path:
    rel = root / "rel" / "BLACKBOX_CACHE_R1_TEST_20260924"
    idx_codes = idx_codes or ["000001", "399001", "000300"]
    idx_closes = idx_closes or [1.0, 2.0, 3.0]
    etf_closes = etf_closes or [10.0, 11.0]
    write_pq(rel / "STOCK_DAILY_PIT_R1" / "a.parquet",
             ["600000", "600001"], [5.0, 6.0])
    write_pq(rel / "STOCK_DAILY_RAW_PIT_R1" / "a.parquet",
             ["600000", "600001"], [5.0, 6.0])
    write_pq(rel / "STOCK_FACTOR_DAILY_R1" / "a.parquet",
             ["600000", "600001"], [7.0, 8.0])
    write_pq(rel / "INDEX_DAILY_R1" / "a.parquet", idx_codes, idx_closes)
    write_pq(rel / "ETF_DAILY_PIT_R1" / "a.parquet", ["510300", "510500"], etf_closes)
    (rel / "RELEASE.json").write_text(json.dumps({
        "cache_release_id": rel.name, "release_root": str(rel),
        "asof": "2026-09-24", "build_version": "TEST"}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (rel / "SEAL.json").write_text(json.dumps({
        "release_id": rel.name, "all_pass": True, "asof": "2026-09-24",
        "sealed_at": "2026-09-24T00:00:00+00:00"}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return rel


def make_contract(root: pathlib.Path, declared: list[str]) -> pathlib.Path:
    import hashlib
    c = {"schema": "BLACKBOX_RCID_PRODUCT_CONTRACT_R1",
         "contract_id": None, "declared_products": sorted(declared),
         "formal_required_products": sorted(declared),
         "excluded_dir_prefix": "_", "junction_content_proven": False,
         "contract_sha256": None}
    blob = json.dumps({k: v for k, v in c.items()
                       if k not in ("contract_id", "contract_sha256")},
                      ensure_ascii=False, sort_keys=True).encode("utf-8")
    c["contract_sha256"] = hashlib.sha256(blob).hexdigest()
    c["contract_id"] = "RCID_C1_TEST_" + c["contract_sha256"][:12]
    d = root / "cc_commit"
    d.mkdir(parents=True, exist_ok=True)
    f = d / "RCID_PRODUCT_CONTRACT_R1.json"
    f.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
    return f


def point_at(mod, root: pathlib.Path, contract: pathlib.Path) -> None:
    cc = root / "cc_commit"
    cc.mkdir(parents=True, exist_ok=True)
    mod.COMMIT_ROOT = cc
    mod.COMMIT_FILE = cc / "COMMIT.json"
    mod.VERSIONS = cc / "versions"
    mod.RCID_SIDE_DIR = cc / "rcid"
    mod.RCID_CONTRACT_FILE = contract
    mod.DUPLICATE_LOG = cc / "DUPLICATE_ROOTS.jsonl"


def rec(name: str, ok: bool, detail) -> None:
    RESULTS.append({"test": name, "pass": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"        {json.dumps(detail, ensure_ascii=False)[:400]}")


def fresh(root: pathlib.Path) -> pathlib.Path:
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    return root


def main() -> int:
    SANDBOX.mkdir(parents=True, exist_ok=True)
    v3 = load(V3, "cc_v3_test")
    v2 = load(V2, "cc_v2_test")

    # ---------------- T1/T2/T3/T4: rcid sensitivity -------------------------------
    r1 = fresh(SANDBOX / "t1")
    c1 = make_contract(r1, FIVE)
    point_at(v3, r1, c1)
    rel = make_release(r1)
    base = v3.release_content_digest(rel)
    again = v3.release_content_digest(rel)
    rec("T1 相同内容重复计算 rcid 一致", base["release_content_id"] == again["release_content_id"],
        {"rcid": base["release_content_id"][:16], "twice": again["release_content_id"][:16],
         "declared": base["declared_count"], "present": base["declared_present_count"],
         "complete": base["complete"]})

    write_pq(rel / "INDEX_DAILY_R1" / "a.parquet", ["000001", "399001", "000300"],
             [1.0, 2.0, 3.5])
    idx = v3.release_content_digest(rel)
    stk = v3.build_identity(rel)["commit_id"]
    rec("T2 只改指数 -> rcid 变",
        idx["release_content_id"] != base["release_content_id"],
        {"before": base["release_content_id"][:16], "after": idx["release_content_id"][:16],
         "commit_id_after": stk[:16]})

    write_pq(rel / "ETF_DAILY_PIT_R1" / "a.parquet", ["510300", "510500"], [10.0, 12.5])
    etf = v3.release_content_digest(rel)
    rec("T3 只改 ETF -> rcid 变",
        etf["release_content_id"] != idx["release_content_id"],
        {"before": idx["release_content_id"][:16], "after": etf["release_content_id"][:16]})

    # 等数量换键：3 行 -> 3 行，只是 key 变了
    write_pq(rel / "INDEX_DAILY_R1" / "a.parquet", ["000016", "399006", "000905"],
             [1.0, 2.0, 3.5])
    keyswap = v3.release_content_digest(rel)
    rows_now = sum(pq.ParquetFile(p).metadata.num_rows
                   for p in (rel / "INDEX_DAILY_R1").rglob("*.parquet"))
    rec("T4 等数量换键 -> rcid 变",
        keyswap["release_content_id"] != etf["release_content_id"],
        {"before": etf["release_content_id"][:16],
         "after": keyswap["release_content_id"][:16], "index_rows": rows_now})

    # ---------------- T5: 声明有而缺 -> complete=False -----------------------------
    r5 = fresh(SANDBOX / "t5")
    c5 = make_contract(r5, FIVE + ["ETF_FACTOR_DAILY_R1"])
    point_at(v3, r5, c5)
    rel5 = make_release(r5)
    d5 = v3.release_content_digest(rel5)
    rec("T5 声明有而缺 -> INCOMPLETE 且列出缺项",
        (not d5["complete"]) and d5["missing_declared"] == ["ETF_FACTOR_DAILY_R1"],
        {"complete": d5["complete"], "missing_declared": d5["missing_declared"],
         "declared": d5["declared_count"], "present": d5["declared_present_count"]})

    # ---------------- T6: 旧 commit_id 兼容（fixture，v2 vs v3）--------------------
    r6 = fresh(SANDBOX / "t6")
    c6 = make_contract(r6, FIVE)
    point_at(v3, r6, c6)
    rel6 = make_release(r6)
    v3_id = v3.build_identity(rel6)["commit_id"]
    point_at(v2, r6, c6)
    v2_id = v2.build_identity(rel6)["commit_id"]
    rec("T6 旧 commit_id 兼容（v2 == v3，fixture）", v2_id == v3_id,
        {"v2": v2_id[:16], "v3": v3_id[:16]})

    # ---------------- T7: 生产数据 commit_id 不得变 -------------------------------
    r7 = fresh(SANDBOX / "t7")
    c7 = make_contract(r7, FIVE)
    point_at(v3, r7, c7)
    v3.RCID_CONTRACT_FILE = (RECT.parents[0] / "candidate" / "cc_commit"
                             / "RCID_PRODUCT_CONTRACT_R1.json")
    prod_ident = v3.build_identity(PROD_REL)
    rec("T7 生产 release commit_id 仍是 572619c9（只读）",
        prod_ident["commit_id"] == PROD_COMMIT_ID,
        {"commit_id": prod_ident["commit_id"][:16],
         "rcid_v3": str(prod_ident["release_content_id"])[:16],
         "declared": prod_ident.get("rcid_declared_count"),
         "present": prod_ident.get("rcid_declared_present_count"),
         "complete": prod_ident.get("rcid_complete"),
         "junction_content_proven": prod_ident.get("junction_content_proven")})

    # ---------------- T8/T9/T10: legacy 不报 PASS -> emit -> CONSISTENT ----------
    r8 = fresh(SANDBOX / "t8")
    c8 = make_contract(r8, FIVE)
    rel8 = make_release(r8)
    point_at(v3, r8, c8)
    first = v3.commit(rel8, note="t8 initial")
    cj = r8 / "cc_commit" / "COMMIT.json"
    # 造 legacy：剥掉顶层 rcid
    obj = json.loads(cj.read_text(encoding="utf-8"))
    obj.pop("release_content_id", None)
    cj.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    legacy_sha = v3.sha256_file(cj)
    v_before = v3.verify()
    rec("T8 无 rcid -> 明确未验证且不给 PASS",
        (v_before.get("consistent") is False)
        and v_before.get("status") == "CONTENT_IDENTITY_UNVERIFIED"
        and v_before.get("content_identity_verified") is False,
        {"status": v_before.get("status"), "consistent": v_before.get("consistent"),
         "content_identity_verified": v_before.get("content_identity_verified"),
         "rcid_check": v_before.get("release_content_id_check")})

    em = v3.emit_release_content_id(rel8)
    cj_after_emit = v3.sha256_file(cj)
    rec("T10 emit 不改 COMMIT.json（sha 前后一致）",
        cj_after_emit == legacy_sha and em.get("commit_json_written") is False,
        {"sha_before": legacy_sha[:16], "sha_after": cj_after_emit[:16],
         "emit_status": em.get("status")})

    v_after = v3.verify()
    rec("T9 emit 后 verify 读到侧文件并 CONSISTENT",
        v_after.get("consistent") is True
        and v_after.get("status") == "CONSISTENT"
        and v_after.get("content_identity_verified") is True
        and v_after.get("release_content_id_check", {}).get("source") == "SIDE_FILE",
        {"status": v_after.get("status"), "consistent": v_after.get("consistent"),
         "check": v_after.get("release_content_id_check")})

    em2 = v3.emit_release_content_id(rel8)
    rec("T11 emit 重复调用 = ALREADY_SAME（不可覆盖）", em2.get("status") == "ALREADY_SAME",
        {"status": em2.get("status")})

    # ---------------- T12: legacy 拒绝 NOOP --------------------------------------
    r12 = fresh(SANDBOX / "t12")
    c12 = make_contract(r12, FIVE)
    rel12 = make_release(r12)
    point_at(v3, r12, c12)
    v3.commit(rel12, note="t12 initial")
    cj12 = r12 / "cc_commit" / "COMMIT.json"
    obj12 = json.loads(cj12.read_text(encoding="utf-8"))
    obj12.pop("release_content_id", None)
    cj12.write_text(json.dumps(obj12, ensure_ascii=False, indent=2), encoding="utf-8")
    sha12 = v3.sha256_file(cj12)
    r12_out = v3.commit(rel12, note="t12 retry")
    rec("T12 旧账本无 rcid -> 拒绝 NOOP，不写文件",
        r12_out.get("status") == "CONTENT_IDENTITY_UNVERIFIED"
        and r12_out.get("commit_file_written") is False
        and v3.sha256_file(cj12) == sha12,
        {"status": r12_out.get("status"),
         "commit_file_written": r12_out.get("commit_file_written"),
         "sha_unchanged": v3.sha256_file(cj12) == sha12})

    # ---------------- T13: commit_id 同、rcid 不同 -> 必须报分歧 ------------------
    r13 = fresh(SANDBOX / "t13")
    c13 = make_contract(r13, FIVE)
    rel13 = make_release(r13)
    point_at(v3, r13, c13)
    a = v3.commit(rel13, note="t13 state A")
    cj13 = r13 / "cc_commit" / "COMMIT.json"
    sha13 = v3.sha256_file(cj13)
    idA = v3.build_identity(rel13)
    write_pq(rel13 / "INDEX_DAILY_R1" / "a.parquet", ["000001", "399001", "000300"],
             [1.0, 2.0, 99.0])          # 只动指数
    idB = v3.build_identity(rel13)
    b = v3.commit(rel13, note="t13 index moved")
    rec("T13 commit_id 同但 rcid 不同 -> CONTENT_DIVERGENCE，拒绝 NOOP",
        (idA["commit_id"] == idB["commit_id"])
        and (idA["release_content_id"] != idB["release_content_id"])
        and b.get("status") == "CONTENT_DIVERGENCE_SAME_COMMIT_ID"
        and v3.sha256_file(cj13) == sha13,
        {"commit_id_same": idA["commit_id"] == idB["commit_id"],
         "commit_id": idA["commit_id"][:16],
         "rcid_A": idA["release_content_id"][:16],
         "rcid_B": idB["release_content_id"][:16],
         "commit_status": b.get("status"),
         "commit_json_unchanged": v3.sha256_file(cj13) == sha13})

    # ---------------- 汇总 -------------------------------------------------------
    passed = sum(1 for r in RESULTS if r["pass"])
    total = len(RESULTS)
    print(f"\n=== {passed}/{total} PASS ===")
    out = {"schema": "RCID_V3_TARGETED_TESTS_R1", "passed": passed, "total": total,
           "all_pass": passed == total, "results": RESULTS}
    (RECT / "RCID_V3_TARGETED_TESTS_R1.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if passed == total else 7


if __name__ == "__main__":
    raise SystemExit(main())
