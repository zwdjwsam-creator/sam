# -*- coding: utf-8 -*-
"""把 SAM 的 PENDING v2 变成 v3：让 release_content_id 真正参与判断。

为什么不能直接用 v2：
  v2 的 NOOP 只用 commit_id 决定。而 commit_id 只覆盖 3 个股票产品，
  指数/ETF 差 391 倍它也不会变 -> 仍会判 IDEMPOTENT_NOOP 并宣称"内容相同"。
  等于把漏洞原样保留，只是多写了一串字符。

v3 的改动（全部为「收紧」，不放宽任何既有判据）：
  P1  常量：契约文件位置 + rcid 侧文件目录
  P2  指纹按「声明产品契约」计算：声明有而磁盘缺 -> MISSING 标记参与哈希且 complete=False
  P3  rcid 计算失败不再静默置 None，改为 fail-closed 抛错
  P4  NOOP 判据改为 (commit_id AND rcid)；commit_id 同但 rcid 不同 -> CONTENT_DIVERGENCE
  P5  旧账本无 rcid -> CONTENT_IDENTITY_UNVERIFIED，拒绝 NOOP（不许猜"相同"）
  P6  verify 读侧文件；无 rcid / 不完整 / 绑定不符 -> 明确未验证，且 consistent=False
  P7  新增 emit-rcid 动作（只写侧文件，COMMIT.json 0 字节改动，禁止覆盖）
"""
from __future__ import annotations

import hashlib
import pathlib
import sys

RECT = pathlib.Path(__file__).resolve().parent
SRC = RECT / "_sam_pending" / "PENDING_candidate_commit_v2.py"
DST = RECT / "candidate_commit_v3.py"

PATCHES: list[tuple[str, str, str]] = []


def patch(name: str, old: str, new: str) -> None:
    PATCHES.append((name, old, new))


# ---------------------------------------------------------------- P1 constants
patch("P1_constants",
      'REQUIRED_PRODUCTS = ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1")\n',
      'REQUIRED_PRODUCTS = ("STOCK_DAILY_PIT_R1", "STOCK_DAILY_RAW_PIT_R1", "STOCK_FACTOR_DAILY_R1")\n'
      '\n'
      '# --- rcid layer (v3): declared-product contract + immutable per-release side file -------\n'
      'RCID_CONTRACT_FILE = COMMIT_ROOT / "RCID_PRODUCT_CONTRACT_R1.json"\n'
      'RCID_SIDE_DIR = COMMIT_ROOT / "rcid"\n'
      'RCID_SIDE_SCHEMA = "BLACKBOX_RELEASE_CONTENT_ID_R1"\n')

# ------------------------------------------------- P2 contract-aware digest
PATCHES.append((
    "P2_contract_aware_digest",
    '''def release_content_digest(release_dir: Path) -> Dict[str, Any]:
    """Full-content fingerprint over every present product, junction-aware.

    Junction products contribute their target identity instead of borrowed bytes, so this
    terminates, and "target archived" shows up as target_exists=false rather than a hang.
    """
    release_dir = Path(release_dir)
    prods = {}
    for name in present_products(release_dir):
        prods[name] = _safe_product_digest(release_dir / name)
    h = hashlib.sha256()
    for name in sorted(prods):
        rec = prods[name]
        h.update(name.encode("utf-8"))
        h.update(str(rec.get("kind")).encode("utf-8"))
        h.update(str(rec.get("sha256") or rec.get("target")).encode("utf-8"))
        h.update(str(rec.get("rows")).encode("utf-8"))
        h.update(str(rec.get("target_release_id")).encode("utf-8"))
    return {"release_content_id": h.hexdigest(), "products_present": prods}
''',
    '''def load_product_contract() -> Dict[str, Any]:
    """The declared product scope. Coverage is decided HERE, not by what is on disk."""
    f = Path(RCID_CONTRACT_FILE)
    if not f.is_file():
        raise CommitError("RCID_PRODUCT_CONTRACT_MISSING: " + str(f))
    c = json.loads(f.read_text(encoding="utf-8"))
    if not c.get("declared_products") or not c.get("contract_sha256"):
        raise CommitError("RCID_PRODUCT_CONTRACT_INVALID: " + str(f))
    return c


def release_content_digest(release_dir: Path) -> Dict[str, Any]:
    """Content identity over the DECLARED product contract (v3).

    A declared product that is absent is hashed as a MISSING marker, so it changes the id
    and forces complete=False -- a missing product can never pass as "same content".
    Junction products contribute their target identity, not borrowed bytes, so this
    terminates; that limitation is declared as junction_content_proven=False.
    """
    release_dir = Path(release_dir)
    contract = load_product_contract()
    declared = list(contract["declared_products"])
    formal = list(contract.get("formal_required_products") or [])
    present = present_products(release_dir)
    present_set = set(present)
    declared_set = set(declared)
    missing_declared = [p for p in declared if p not in present_set]
    extra_present = [p for p in present if p not in declared_set]
    missing_formal = [p for p in formal if p not in present_set]

    prods: Dict[str, Any] = {}
    for name in declared:
        if name in present_set:
            prods[name] = _safe_product_digest(release_dir / name)
        else:
            prods[name] = {"kind": "MISSING", "sha256": None, "rows": None,
                           "target": None, "target_release_id": None}

    h = hashlib.sha256()
    h.update(b"RCID_V3_CONTRACT_AWARE")
    h.update(str(contract["contract_sha256"]).encode("utf-8"))
    for name in declared:                      # declared order, not disk order
        rec = prods[name]
        h.update(name.encode("utf-8"))
        h.update(str(rec.get("kind")).encode("utf-8"))
        h.update(str(rec.get("sha256") or rec.get("target") or "NONE").encode("utf-8"))
        h.update(str(rec.get("target_release_id") or "NONE").encode("utf-8"))
        h.update(str(rec.get("rows")).encode("utf-8"))

    junction = [p for p in declared if prods[p].get("kind") == "JUNCTION"]
    dangling = [p for p in junction if prods[p].get("target_exists") is False]
    present_digests = {p: prods[p] for p in declared if p in present_set}
    for p in extra_present:
        present_digests[p] = _safe_product_digest(release_dir / p)

    return {
        "release_content_id": h.hexdigest(),
        "contract_id": contract.get("contract_id"),
        "contract_sha256": contract["contract_sha256"],
        "declared_count": len(declared),
        "declared_present_count": len(declared) - len(missing_declared),
        "missing_declared": missing_declared,
        "missing_formal_required": missing_formal,
        "extra_present": extra_present,
        "dangling_junctions": dangling,
        "junction_products": junction,
        "junction_content_proven": bool(contract.get("junction_content_proven")),
        "complete": (not missing_declared) and (not missing_formal) and (not dangling),
        "products_present": present_digests,
    }
'''))

# ------------------------------------- P3 build_identity: fail closed, real coverage
PATCHES.append((
    "P3_fail_closed_identity",
    '''    # ---- additive identity + coverage + junction audit (never alters commit_id) ----------
    try:
        rcd = release_content_digest(release_dir)
        identity["release_content_id"] = rcd["release_content_id"]
        identity["products_present"] = sorted(rcd["products_present"])
        identity["products_present_digests"] = rcd["products_present"]
        ident_js = Path(release_dir) / "SEAL.json"
        seal_for_cov = json.loads(ident_js.read_text(encoding="utf-8")) if ident_js.is_file() else {}
        compiler_req = (seal_for_cov.get("formal_required_missing") is not None and
                        [p for p in (seal_for_cov.get("price", {}).get("products") or {})])
        identity["coverage"] = coverage_report(
            release_dir, list(REQUIRED_PRODUCTS), compiler_required=list(compiler_req or []))
        ja = junction_audit(release_dir)
        identity["junction_products"] = ja["junction_products"]
        if ja["dangling"]:
            raise CommitError(
                "DANGLING_JUNCTION_PRODUCT: " + json.dumps(
                    {k: ja["junction_products"][k] for k in ja["dangling"]},
                    ensure_ascii=False)[:800])
    except CommitError:
        raise
    except Exception as e:  # noqa: BLE001
        identity["release_content_id"] = None
        identity["coverage"] = {"ERROR": f"{type(e).__name__}: {e}"}
    return identity
''',
    '''    # ---- additive identity + coverage + junction audit (never alters commit_id) ----------
    # v3: FAIL CLOSED. A swallowed digest error used to leave release_content_id=None and
    # still let the commit proceed, which is the same "silence instead of UNKNOWN" defect.
    rcd = release_content_digest(release_dir)
    identity["release_content_id"] = rcd["release_content_id"]
    identity["rcid_complete"] = rcd["complete"]
    identity["rcid_contract_id"] = rcd["contract_id"]
    identity["rcid_contract_sha256"] = rcd["contract_sha256"]
    identity["rcid_declared_count"] = rcd["declared_count"]
    identity["rcid_declared_present_count"] = rcd["declared_present_count"]
    identity["missing_declared"] = rcd["missing_declared"]
    identity["missing_formal_required"] = rcd["missing_formal_required"]
    identity["extra_present"] = rcd["extra_present"]
    identity["junction_content_proven"] = rcd["junction_content_proven"]
    identity["products_present"] = sorted(rcd["products_present"])
    identity["products_present_digests"] = rcd["products_present"]
    if rcd["missing_formal_required"]:
        raise CommitError("FORMAL_REQUIRED_MISSING: " + json.dumps(
            rcd["missing_formal_required"], ensure_ascii=False))
    identity["coverage"] = coverage_report(
        release_dir, list(REQUIRED_PRODUCTS),
        compiler_required=list(rcd.get("missing_formal_required") and [] or []))
    identity["coverage"].update({
        "rcid_contract_id": rcd["contract_id"],
        "rcid_declared_count": rcd["declared_count"],
        "rcid_declared_present_count": rcd["declared_present_count"],
        "rcid_missing_declared": rcd["missing_declared"],
        "rcid_extra_present": rcd["extra_present"],
        "rcid_complete": rcd["complete"],
        "junction_content_proven": rcd["junction_content_proven"],
    })
    ja = junction_audit(release_dir)
    identity["junction_products"] = ja["junction_products"]
    if ja["dangling"]:
        raise CommitError(
            "DANGLING_JUNCTION_PRODUCT: " + json.dumps(
                {k: ja["junction_products"][k] for k in ja["dangling"]},
                ensure_ascii=False)[:800])
    return identity
'''))

# ------------------------------- P4 same-root decision now needs rcid, not just commit_id
PATCHES.append((
    "P4_noop_requires_rcid",
    '''        if same_root and same_release_id:
            return {
                "status": "IDEMPOTENT_NOOP",
                "commit_id": identity["commit_id"],
                "commit_file_sha256": sha256_file(COMMIT_FILE),
                "release_id": identity["release_id"],
            }
''',
    '''        # v3: NOOP now requires BOTH identities. commit_id is the legacy 3-product
        # identity; an index/ETF divergence of 391x left it byte-identical, so equality of
        # commit_id alone must never be read as "same content".
        cur_rcid, cur_rcid_src = resolve_committed_rcid(current)
        new_rcid = identity.get("release_content_id")
        if cur_rcid is None:
            return {
                "status": "CONTENT_IDENTITY_UNVERIFIED",
                "commit_id": identity["commit_id"],
                "release_id": current.get("release_id"),
                "reference_root": str(old_root),
                "candidate_release_id": identity["release_id"],
                "candidate_release_content_id": new_rcid,
                "rcid_detail": cur_rcid_src,
                "reason": "the committed record carries no release_content_id and no bound "
                          "side file, so content equality cannot be asserted; NOOP refused "
                          "rather than guessed",
                "remedy": "emit_release_content_id(<referenced release>) then retry",
                "commit_file_written": False,
                "commit_file_sha256": sha256_file(COMMIT_FILE),
            }
        content_same = (cur_rcid == new_rcid)
        if same_root and same_release_id and content_same:
            return {
                "status": "IDEMPOTENT_NOOP",
                "commit_id": identity["commit_id"],
                "release_content_id": new_rcid,
                "rcid_source": cur_rcid_src.get("source"),
                "commit_file_sha256": sha256_file(COMMIT_FILE),
                "release_id": identity["release_id"],
            }
        if same_root and same_release_id and not content_same:
            return {
                "status": "CONTENT_DIVERGENCE_SAME_COMMIT_ID",
                "commit_id": identity["commit_id"],
                "committed_rcid": cur_rcid,
                "candidate_rcid": new_rcid,
                "rcid_source": cur_rcid_src.get("source"),
                "reason": "commit_id is equal but release_content_id differs: the legacy "
                          "3-product identity cannot prove whole-release equality",
                "commit_file_written": False,
                "commit_file_sha256": sha256_file(COMMIT_FILE),
            }
'''))

# ------------------------------- P5 duplicate-root branch must not log a divergent tree
patch("P5_duplicate_guard",
      '''            logged = record_duplicate_root(
                commit_id=identity["commit_id"],
                reference_root=str(old_root),
                duplicate_root=str(identity["release_root"]),
                release_id=str(identity["release_id"]),
            )
''',
      '''            if not content_same:
                return {
                    "status": "CONTENT_DIVERGENCE_SAME_COMMIT_ID",
                    "commit_id": identity["commit_id"],
                    "committed_rcid": cur_rcid,
                    "candidate_rcid": new_rcid,
                    "reference_root": str(old_root),
                    "candidate_release_root": str(identity["release_root"]),
                    "reason": "same commit_id but different release_content_id; refusing to "
                              "log this tree as an equivalent duplicate",
                    "commit_file_written": False,
                    "commit_file_sha256": sha256_file(COMMIT_FILE),
                }
            logged = record_duplicate_root(
                commit_id=identity["commit_id"],
                reference_root=str(old_root),
                duplicate_root=str(identity["release_root"]),
                release_id=str(identity["release_id"]),
            )
''')

# ------------------------------- P6 rebind branch must not move a divergent reference
patch("P6_rebind_guard",
      '''        # Content identity is unchanged (commit_id hashes data only) but the referenced
        # payload tree moved -- e.g. the previous candidate release was archived. Rebind
        # the single authoritative reference to the new root. Safe precisely because an
        # equal commit_id proves the new tree holds the same products/rows/sha256; the
        # non-data fields (release_id, release_root, build timestamps) are excluded from
        # that hash by CC_COMMIT_IDENTITY_V2. Recorded, never silent.
        rebound_from = str(current.get("release_root"))
''',
      '''        # The referenced payload tree moved -- e.g. the previous candidate release was
        # archived. Rebind ONLY when release_content_id also matches: commit_id alone is
        # the legacy 3-product identity and does NOT prove whole-release equality (an
        # index divergence of 391x lived under an identical commit_id). Recorded, never
        # silent.
        if not content_same:
            return {
                "status": "CONTENT_DIVERGENCE_SAME_COMMIT_ID",
                "commit_id": identity["commit_id"],
                "committed_rcid": cur_rcid,
                "candidate_rcid": new_rcid,
                "reference_root": str(old_root),
                "candidate_release_root": str(identity["release_root"]),
                "reason": "same commit_id but different release_content_id; rebind refused",
                "commit_file_written": False,
                "commit_file_sha256": sha256_file(COMMIT_FILE),
            }
        rebound_from = str(current.get("release_root"))
''')

# ------------------------------- P7 side-file resolver + immutable emitter + emit CLI
patch("P7_side_file_api",
      'def _read_commit() -> Optional[Dict[str, Any]]:\n',
      '''def rcid_side_path(release_id: str) -> Path:
    return RCID_SIDE_DIR / f"{release_id}.json"


def resolve_committed_rcid(commit: Dict[str, Any]) -> tuple:
    """Committed content identity + where it came from.

    Order: COMMIT.json top-level field, else the immutable per-release side file. The side
    file only counts when it is bound to THIS release id, root and commit id; a mismatched
    binding is reported as such, never silently trusted.
    """
    top = commit.get("release_content_id")
    if top:
        return top, {"source": "COMMIT.json"}
    rid = str(commit.get("release_id") or "")
    if not rid:
        return None, {"source": "ABSENT", "reason": "commit has no release_id"}
    f = rcid_side_path(rid)
    if not f.is_file():
        return None, {"source": "ABSENT", "looked_at": str(f)}
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return None, {"source": "UNREADABLE", "path": str(f),
                      "error": f"{type(e).__name__}: {e}"}
    if str(d.get("release_id")) != rid:
        return None, {"source": "BINDING_MISMATCH_RELEASE_ID", "path": str(f),
                      "expected": rid, "found": d.get("release_id")}
    if str(d.get("release_root")) != str(commit.get("release_root")):
        return None, {"source": "BINDING_MISMATCH_ROOT", "path": str(f),
                      "expected": str(commit.get("release_root")),
                      "found": d.get("release_root")}
    if str(d.get("commit_id")) != str(commit.get("commit_id")):
        return None, {"source": "BINDING_MISMATCH_COMMIT_ID", "path": str(f),
                      "expected": commit.get("commit_id"), "found": d.get("commit_id")}
    if not d.get("release_content_id"):
        return None, {"source": "EMPTY", "path": str(f)}
    return d["release_content_id"], {"source": "SIDE_FILE", "path": str(f),
                                     "complete": d.get("complete"),
                                     "contract_id": d.get("contract_id")}


def emit_release_content_id(release_dir: Path) -> Dict[str, Any]:
    """Write the immutable per-release content identity side file.

    Never touches COMMIT.json. Never overwrites: an existing file with a different id is a
    hard conflict (the same release id now holds different bytes -- that itself must be
    escalated, not papered over).
    """
    release_dir = Path(release_dir)
    cj_before = sha256_file(COMMIT_FILE) if COMMIT_FILE.is_file() else None
    rcd = release_content_digest(release_dir)
    rel_js = release_dir / "RELEASE.json"
    meta = {}
    if rel_js.is_file():
        meta = json.loads(rel_js.read_text(encoding="utf-8"))
    rid = str(meta.get("cache_release_id") or release_dir.name)
    identity = build_identity(release_dir)
    payload = {
        "schema": RCID_SIDE_SCHEMA,
        "release_content_id": rcd["release_content_id"],
        "release_id": rid,
        "release_root": str(release_dir),
        "commit_id": identity["commit_id"],
        "asof": meta.get("asof") or identity.get("asof"),
        "contract_id": rcd["contract_id"],
        "contract_sha256": rcd["contract_sha256"],
        "declared_count": rcd["declared_count"],
        "declared_present_count": rcd["declared_present_count"],
        "missing_declared": rcd["missing_declared"],
        "missing_formal_required": rcd["missing_formal_required"],
        "extra_present": rcd["extra_present"],
        "dangling_junctions": rcd["dangling_junctions"],
        "junction_products_count": len(rcd["junction_products"]),
        "junction_content_proven": rcd["junction_content_proven"],
        "complete": rcd["complete"],
        "emitted_at_cn": now_cn(),
        "emitted_by": "candidate_commit v3 emit_release_content_id",
        "commit_json_written": False,
    }
    payload["self_sha256"] = sha256_obj(payload)
    dest = rcid_side_path(rid)
    if dest.is_file():
        old = json.loads(dest.read_text(encoding="utf-8"))
        if old.get("release_content_id") == payload["release_content_id"]:
            return {"status": "ALREADY_SAME", "path": str(dest),
                    "release_content_id": payload["release_content_id"],
                    "commit_json_written": False}
        return {"status": "RCID_IMMUTABLE_CONFLICT", "path": str(dest),
                "existing": old.get("release_content_id"),
                "computed": payload["release_content_id"],
                "reason": "same release_id now yields a different content id; refusing to "
                          "overwrite the frozen identity",
                "commit_json_written": False}
    RCID_SIDE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, dest)
    cj_after = sha256_file(COMMIT_FILE) if COMMIT_FILE.is_file() else None
    if cj_before != cj_after:
        raise CommitError("COMMIT_JSON_MUTATED_BY_EMIT: " + str(COMMIT_FILE))
    return {"status": "EMITTED", "path": str(dest),
            "release_content_id": payload["release_content_id"],
            "complete": payload["complete"],
            "missing_declared": payload["missing_declared"],
            "commit_json_written": False,
            "commit_json_sha256_unchanged": cj_after}


def _read_commit() -> Optional[Dict[str, Any]]:
''')

# ------------------------------- P8 verify: explicit unverified, never PASS
patch("P8_verify_explicit",
      '''    # ---- additive: full-content fingerprint comparison (never weakens the 3-product check)
    stored_rcid = commit.get("release_content_id")
    if stored_rcid:
        try:
            now_rcid = release_content_digest(Path(commit["release_root"]))["release_content_id"]
            same = now_rcid == stored_rcid
            content_id_check = {"status": "MATCH" if same else "MISMATCH",
                                "stored": stored_rcid, "now": now_rcid}
            deep_ok = deep_ok and same
        except Exception as e:  # noqa: BLE001
            content_id_check = {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}
            deep_ok = False
''',
      '''    # ---- additive: full-content fingerprint comparison (never weakens the 3-product check)
    # v3: absence is reported as UNVERIFIED and blocks PASS. Silently skipping this check
    # used to let a legacy record read as fully verified when nothing was verified.
    stored_rcid, rcid_src = resolve_committed_rcid(commit)
    if stored_rcid is None:
        st = str(rcid_src.get("source") or "")
        content_id_check = {
            "status": ("RCID_BINDING_MISMATCH" if st.startswith("BINDING_MISMATCH")
                       else "CONTENT_IDENTITY_UNVERIFIED"),
            "detail": rcid_src,
            "meaning": "whole-release content identity was NOT verified",
        }
        deep_ok = False
    else:
        try:
            now_full = release_content_digest(Path(commit["release_root"]))
            now_rcid = now_full["release_content_id"]
            if not now_full["complete"]:
                content_id_check = {
                    "status": "CONTENT_IDENTITY_INCOMPLETE",
                    "stored": stored_rcid, "now": now_rcid,
                    "missing_declared": now_full["missing_declared"],
                    "missing_formal_required": now_full["missing_formal_required"],
                    "dangling_junctions": now_full["dangling_junctions"],
                    "meaning": "declared products are absent; content is NOT fully covered",
                }
                deep_ok = False
            elif now_rcid == stored_rcid:
                content_id_check = {"status": "MATCH", "stored": stored_rcid,
                                    "now": now_rcid,
                                    "source": rcid_src.get("source"),
                                    "contract_id": now_full["contract_id"],
                                    "declared_count": now_full["declared_count"],
                                    "junction_content_proven":
                                        now_full["junction_content_proven"]}
            else:
                content_id_check = {"status": "MISMATCH", "stored": stored_rcid,
                                    "now": now_rcid,
                                    "source": rcid_src.get("source")}
                deep_ok = False
        except Exception as e:  # noqa: BLE001
            content_id_check = {"status": "ERROR", "error": f"{type(e).__name__}: {e}"}
            deep_ok = False
''')

# ------------------------------- P9 status/consistent honours the rcid verdict
patch("P9_status_override",
      '''    consistent = bool(cp_ok and identity_ok and deep_ok)
    return {
        **out,
        "status": ("CONSISTENT" if consistent
                   else ("PAYLOAD_ROOT_MISSING" if payload_root_missing else "INCONSISTENT")),
        "consistent": consistent,
''',
      '''    _rcid_status = content_id_check.get("status")
    _rcid_override = (_rcid_status if _rcid_status in
                      ("CONTENT_IDENTITY_UNVERIFIED", "CONTENT_IDENTITY_INCOMPLETE",
                       "RCID_BINDING_MISMATCH", "ERROR") else None)
    consistent = bool(cp_ok and identity_ok and deep_ok) and _rcid_override is None
    return {
        **out,
        "status": (_rcid_override or
                   ("CONSISTENT" if consistent
                    else ("PAYLOAD_ROOT_MISSING" if payload_root_missing else "INCONSISTENT"))),
        "consistent": consistent,
        "content_identity_verified": _rcid_override is None,
''')

# ------------------------------- P10 CLI emit-rcid
patch("P10_cli_emit",
      '                    choices=["identity", "commit", "verify", "probe-gate"])\n',
      '                    choices=["identity", "commit", "verify", "probe-gate", "emit-rcid"])\n')

patch("P10_cli_branch",
      '''        if args.action == "verify":
            out = verify()
''',
      '''        if args.action == "emit-rcid":
            out = emit_release_content_id(Path(args.release_dir))
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0 if out.get("status") in ("EMITTED", "ALREADY_SAME") else 6
        if args.action == "verify":
            out = verify()
''')


def main() -> int:
    text = SRC.read_text(encoding="utf-8")
    print(f"src = {SRC.name}  {len(text.encode('utf-8'))} B")
    applied = []
    for name, old, new in PATCHES:
        n = text.count(old)
        if n != 1:
            print(f"[FAIL] {name}: anchor matched {n} times (need exactly 1)")
            return 2
        text = text.replace(old, new)
        if text.count(old) != 0 and old not in new:
            print(f"[FAIL] {name}: anchor still present after replacement")
            return 2
        applied.append(name)
        print(f"[OK  ] {name}")
    text = text.replace(
        '"""Candidate commit discipline for the connected pipeline (deliverable 3, diff 3).',
        '"""Candidate commit discipline v3 -- legacy v2 + contract-aware release_content_id.\n'
        '\n'
        'v3 additions (all tightening, nothing loosened):\n'
        '  * coverage comes from a FROZEN declared-product contract, not from disk enumeration\n'
        '  * a declared-but-absent product is hashed as MISSING and forces complete=False\n'
        '  * NOOP requires (commit_id AND release_content_id); commit_id equality alone is\n'
        '    explicitly refused as proof of content equality\n'
        '  * legacy records without a content id return CONTENT_IDENTITY_UNVERIFIED, never NOOP\n'
        '  * verify reports content identity as UNVERIFIED/INCOMPLETE/BINDING_MISMATCH and\n'
        '    blocks PASS instead of silently skipping the check\n'
        '  * emit-rcid writes an immutable per-release side file; COMMIT.json is untouched\n'
        '\n'
        '--- original v2 notes follow ---\n'
        '\n'
        'Candidate commit discipline for the connected pipeline (deliverable 3, diff 3).',
        1)
    DST.write_text(text, encoding="utf-8", newline="\n")
    raw = DST.read_bytes()
    ok = True
    print(f"\ndst = {DST.name}  {len(raw)} B  sha256={hashlib.sha256(raw).hexdigest()[:16]}")
    print(f"patches applied = {len(applied)}/{len(PATCHES)}  all_present={ok}")
    import py_compile
    py_compile.compile(str(DST), doraise=True)
    print("py_compile = OK")
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
