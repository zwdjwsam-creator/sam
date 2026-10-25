#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""台式机结构 vs 笔记本(SAM)结构 只读审计 R1.

口径:
- 蓝图 = SAM 交付包 SOURCE_INDEX.json (90 code + 28 config + 15 entries) + DATA_PLANE_PATH_MAP + 运行时链路图 FOUNDATION_RUNTIME_MAP.md 的路径清单
- 本机 = E:\\BLACKBOX
- 只读: 不改任何 CURRENT / 不跑采集 / 不写生产指针

输出:
- 输出/STRUCTURE_AUDIT_R1.json
- 输出/PATH_REMAP_TABLE.json   (笔记本路径 -> 台式机路径, 含是否需改)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CN = timezone(timedelta(hours=8))
DEFAULT_ROOT = Path(r"E:\BLACKBOX")
DEFAULT_SRC = Path(
    r"\\192.168.100.2\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024"
    r"\end_to_end_completion\source_workflow_from_SAM"
)
ABS_RE = re.compile(r"^[A-Za-z]:[\\/]")
DATE_DIR = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(p: Path) -> Any:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def mojibake_decode(name: str, canonical: set[str] | None = None) -> str | None:
    """UTF-8 字节被 GBK 解读的名字 -> 还原.

    先做严格解码; 尾字节残缺时用 canonical(本机已有目录名) 做前缀匹配。
    """
    canonical = canonical or set()
    if not any("\ue000" <= ch <= "\uf8ff" for ch in name) and name.isascii():
        return None
    try:
        raw = name.encode("gbk", errors="ignore")
    except Exception:
        return None
    if not raw:
        return None
    try:
        d = raw.decode("utf-8", errors="strict")
        if d and d != name:
            return d
    except Exception:
        pass
    # 残缺尾字节: 用可解码前缀 + 已有目录名匹配
    for cut in range(len(raw), 0, -1):
        try:
            pre = raw[:cut].decode("utf-8", errors="strict")
        except Exception:
            continue
        cands = [c for c in canonical if pre and c.startswith(pre) and c != name]
        if len(cands) == 1:
            return cands[0]
        if cands:
            return sorted(cands)[0]
    return None


def find_abs_paths(obj: Any, out: set[str]) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            find_abs_paths(v, out)
    elif isinstance(obj, list):
        for v in obj:
            find_abs_paths(v, out)
    elif isinstance(obj, str) and ABS_RE.match(obj):
        out.add(obj.replace("/", "\\"))


def max_date_dir(p: Path) -> str | None:
    if not p.exists():
        return None
    ds = [c.name for c in p.iterdir() if c.is_dir() and DATE_DIR.match(c.name)]
    return max(ds) if ds else None


def domain_currents(root: Path) -> list[dict[str, Any]]:
    specs = [
        ("C_GLOBAL_SELLSIDE", root / "数据" / "研究报告" / "CURRENT" / "SELLSIDE_DAILY_INCREMENTAL_CURRENT.json",
         root / "数据" / "研究报告" / "日增量"),
        ("D_DOMESTIC_SELLSIDE", root / "数据" / "研究报告" / "国内卖方" / "CURRENT" / "DOMESTIC_SELLSIDE_CURRENT.json",
         root / "数据" / "研究报告" / "国内卖方" / "日增量"),
        ("D_DOMESTIC_NEWS", root / "数据" / "研究报告" / "国内新闻" / "CURRENT" / "DOMESTIC_NEWS_CURRENT.json",
         root / "数据" / "研究报告" / "国内新闻" / "日增量"),
        ("E_US_NEWS", root / "数据" / "美国市场" / "新闻" / "CURRENT" / "US_NEWS_CURRENT.json",
         root / "数据" / "美国市场" / "新闻" / "日增量"),
        ("F_US_MARKET", root / "数据" / "美国市场" / "市场状态" / "CURRENT" / "US_MARKET_STATE_CURRENT.json",
         root / "数据" / "美国市场" / "市场状态" / "日增量"),
    ]
    rows = []
    for rid, cur_p, daily_p in specs:
        cur = load(cur_p) or {}
        asof = None
        for key_order in ("DISCOVERY_ASOF", "US_MARKET_DATE", "CN_DISCOVERY_DATE", "asof", "data_asof"):
            if isinstance(cur.get(key_order), str):
                asof = cur[key_order]
                break
        if asof is None:
            for k, v in cur.items():
                if "ASOF" in k.upper() and isinstance(v, str):
                    asof = v
                    break
        src_slice = cur.get("SOURCE_PATH") or cur.get("daily_slice")
        slice_date = None
        if isinstance(src_slice, str):
            for part in Path(src_slice).parts:
                if DATE_DIR.match(part):
                    slice_date = part
        mx = max_date_dir(daily_p)
        rows.append({
            "id": rid,
            "current_path": str(cur_p),
            "current_exists": cur_p.exists(),
            "current_asof": asof,
            "current_status": cur.get("STATUS"),
            "source_path": src_slice,
            "slice_date": slice_date,
            "daily_root": str(daily_p),
            "max_slice": mx,
            "slice_lag": (slice_date is not None and mx is not None and slice_date < mx),
            "asof_vs_slice_mismatch": (
                slice_date is not None and asof is not None and slice_date != asof[:10]
            ),
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--source", default=str(DEFAULT_SRC))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    root = Path(args.root)
    src = Path(args.source)
    out_dir = Path(args.out) if args.out else root / "任务" / "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1" / "输出"
    out_dir.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []

    def add(cid: str, status: str, detail: str, **extra: Any) -> None:
        checks.append({"id": cid, "status": status, "detail": detail, **extra})

    # ---------- 1. 根与源码身份 ----------
    idx = load(src / "SOURCE_INDEX.json")
    if not idx:
        add("SOURCE_INDEX", "BLOCKED", f"找不到交付索引: {src / 'SOURCE_INDEX.json'}")
        bundle_ok = False
    else:
        bundle_ok = True
        src_root = str(idx.get("source_root") or "")
        same_root = src_root.replace("/", "\\").rstrip("\\").lower() == str(root).rstrip("\\").lower()
        add(
            "ROOT_IDENTITY",
            "PASS" if same_root else "REMAP_REQUIRED",
            f"SAM source_root={src_root} | desktop root={root} | 同根={same_root}",
            remap_required=not same_root,
        )

    # ---------- 2. 90 代码 + 28 配置 SHA ----------
    if bundle_ok:
        for key, label in (("code_files", "CODE"), ("config_files", "CONFIG")):
            same = diff = miss = 0
            diff_list: list[str] = []
            miss_list: list[str] = []
            for e in idx.get(key) or []:
                rel = e.get("rel") if isinstance(e, dict) else str(e)
                p = root / rel
                if not p.exists():
                    miss += 1
                    miss_list.append(rel)
                    continue
                want = e.get("sha256") if isinstance(e, dict) else None
                if want and sha256(p) != want:
                    diff += 1
                    diff_list.append(rel)
                else:
                    same += 1
            add(
                f"{label}_SHA",
                "PASS" if (miss == 0 and diff == 0) else "PARTIAL",
                f"{label}: same={same} diff={diff} missing={miss} (共 {len(idx.get(key) or [])})",
                same=same, diff=diff, missing=miss,
                diff_files=diff_list, missing_files=miss_list,
            )

    # ---------- 3. 固定路径地图 ----------
    pm = load(root / "研究系统" / "数据平面" / "CONFIG" / "DATA_PLANE_PATH_MAP.json") or {}
    pm_paths: set[str] = set()
    find_abs_paths(pm.get("lanes") or {}, pm_paths)
    pm_miss = sorted(p for p in pm_paths if not Path(p).exists())
    add(
        "PATH_MAP_RESOLVE",
        "PASS" if not pm_miss else "PARTIAL",
        f"DATA_PLANE_PATH_MAP: {len(pm_paths)} 条绝对路径, 缺失 {len(pm_miss)}",
        missing=pm_miss,
    )

    # ---------- 4. CURRENT 指针链 ----------
    clean_p = root / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
    cache_p = root / "数据" / "回测缓存" / "CURRENT_CACHE_RELEASE.json"
    scope_p = root / "运行" / "BLACKBOX_FULL_DATA_UPDATE_SCOPE_CURRENT.json"
    man_p = root / "研究系统" / "数据平面" / "CURRENT" / "DAILY_DATA_MANIFEST_CURRENT.json"
    clean = load(clean_p) or {}
    cache = load(cache_p) or {}
    scope = load(scope_p) or {}
    man = load(man_p) or {}

    clean_roots = {
        "standard_root": clean.get("standard_root"),
        "ledger_path": clean.get("ledger_path"),
        "quarantine_root": clean.get("quarantine_root"),
    }
    clean_miss = [f"{k}={v}" for k, v in clean_roots.items() if v and not Path(str(v)).exists()]
    distinct_releases = sorted({
        str(v).split("\\releases\\")[-1].split("\\")[0]
        for v in clean_roots.values() if v and "\\releases\\" in str(v)
    })
    add(
        "CLEANING_CHAIN",
        "PASS" if not clean_miss else "FAIL",
        f"cleaning_as_of={clean.get('cleaning_as_of')} release_id={clean.get('release_id')} "
        f"涉及 release 目录={distinct_releases} 缺失={len(clean_miss)}",
        missing=clean_miss,
        multi_root=len(distinct_releases) > 1,
    )

    cache_root = cache.get("release_root")
    add(
        "CACHE_CHAIN",
        "PASS" if cache_root and Path(str(cache_root)).exists() else "FAIL",
        f"asof={cache.get('asof')} release_root_exists={bool(cache_root and Path(str(cache_root)).exists())} "
        f"root={cache_root}",
    )

    if cache_root and Path(str(cache_root)).exists():
        mm = load(Path(str(cache_root)) / "MANIFEST.json") or {}
        internal_id = mm.get("cache_release_id")
        dir_name = Path(str(cache_root)).name
        add(
            "CACHE_ID_VS_DIRNAME",
            "WARN" if internal_id and str(internal_id) not in dir_name else "PASS",
            f"目录名={dir_name} | MANIFEST.cache_release_id={internal_id} "
            f"(名≠内部 id 时按目录名建指针会指错, 不得用顶层 asof 外推)",
        )

    # ---------- 5. 会话一致性 (manifest vs 数据平面) ----------
    if man:
        jq = man.get("JQ") or {}
        add(
            "SESSION_CONSISTENCY",
            "PASS" if man.get("CN_RESEARCH_DATE") == jq.get("CACHE_ASOF") else "DRIFT",
            f"manifest_id={man.get('manifest_id')} CN_RESEARCH_DATE={man.get('CN_RESEARCH_DATE')} "
            f"JQ cache_asof={jq.get('CACHE_ASOF')} READY={man.get('DAILY_INCREMENTAL_READY')} "
            f"BUILD_TIME={man.get('BUILD_TIME')}",
        )
        d_lane = man.get("DOMESTIC_RESEARCH") or {}
        e_lane = man.get("US_NEWS") or {}
        f_lane = man.get("US_MARKET") or {}
        add(
            "LANE_ASOF_SPREAD",
            "PASS" if len({man.get("CN_RESEARCH_DATE"), d_lane.get("DISCOVERY_ASOF"), e_lane.get("DISCOVERY_ASOF")}) == 1
            else "WARN",
            f"manifest={man.get('CN_RESEARCH_DATE')} D={d_lane.get('DISCOVERY_ASOF')} "
            f"E={e_lane.get('DISCOVERY_ASOF')} F.fine_grained={f_lane.get('US_FINE_GRAINED_STATUS')}",
        )
        if not f_lane.get("FIXED_PATHS"):
            add(
                "LANE_F_PATHS",
                "WARN",
                "Manifest.US_MARKET 缺 FIXED_PATHS(fine_grained_*) —— SAM 侧该键存在, 本机 manifest 由旧 lane dict 拼出后丢失",
            )

    # ---------- 6. 域名 CURRENT vs 实际日增量 ----------
    doms = domain_currents(root)
    lagging = [d for d in doms if d["slice_lag"] or d["asof_vs_slice_mismatch"]]
    add(
        "DOMAIN_CURRENT_VS_SLICE",
        "PASS" if not lagging else "STALE_POINTER",
        f"{len(doms)} 个域 CURRENT; 指针落后/自相矛盾的有 {len(lagging)} 个: "
        + ", ".join(d["id"] for d in lagging),
        domains=doms,
    )

    # ---------- 7. 结构卫生 ----------
    mojibake = []
    canonical_names = {c.name for c in root.iterdir() if c.is_dir()}
    for c in root.iterdir():
        if not c.is_dir():
            continue
        decoded = mojibake_decode(c.name, canonical_names)
        if decoded and (root / decoded).exists():
            files = [str(f.relative_to(root)) for f in c.rglob("*") if f.is_file()]
            mojibake.append({"dir": c.name, "decoded": decoded, "files": files})
    add(
        "MOJIBAKE_DIRS",
        "PASS" if not mojibake else "REPAIRABLE",
        f"疑似乱码目录 {len(mojibake)} 个: " + ", ".join(m["dir"] for m in mojibake),
        found=mojibake,
    )

    empty_dirs = []
    for c in root.iterdir():
        if c.is_dir() and c.name not in {".venv", ".git", ".local", ".vscode", ".cursor"}:
            try:
                if not any(c.iterdir()):
                    empty_dirs.append(c.name)
            except OSError:
                pass
    add("EMPTY_TOP_DIRS", "INFO", f"空顶层目录 {len(empty_dirs)}: {empty_dirs}", dirs=empty_dirs)

    stale_root_docs = []
    for p in list(root.glob("*.md")) + list(root.glob("*.txt")):
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if re.search(r"F:\\BLACKBOX", t, re.I):
            stale_root_docs.append(p.name)
    add(
        "STALE_ROOT_REFS",
        "PASS" if not stale_root_docs else "WARN",
        f"根文档仍引用 F:\\BLACKBOX 的: {stale_root_docs}",
        files=stale_root_docs,
    )

    # ---------- 8. 路径匹配表 ----------
    remap_rows = []
    src_root_val = (idx or {}).get("source_root") or r"E:\BLACKBOX"
    for e in ((idx or {}).get("code_files") or []) + ((idx or {}).get("config_files") or []):
        rel = e.get("rel") if isinstance(e, dict) else str(e)
        remap_rows.append({
            "notebook_path": str(Path(src_root_val) / rel),
            "desktop_path": str(root / rel),
            "rel": rel,
            "action": "NO_REMAP (同根同相对路径)" if str(root).lower() == str(src_root_val).lower() else "REMAP_PREFIX_ONLY",
            "desktop_exists": (root / rel).exists(),
        })
    add("PATH_REMAP", "PASS", f"生成 {len(remap_rows)} 条 笔记本→台式机 路径匹配")

    verdict_counts: dict[str, int] = {}
    for c in checks:
        verdict_counts[c["status"]] = verdict_counts.get(c["status"], 0) + 1

    result = {
        "schema": "BLACKBOX_DESKTOP_STRUCTURE_AUDIT_R1",
        "generated_at_cn": now_cn(),
        "desktop_root": str(root),
        "notebook_source": str(src),
        "notebook_source_root": src_root_val,
        "verdict_counts": verdict_counts,
        "checks": checks,
    }
    (out_dir / "STRUCTURE_AUDIT_R1.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "PATH_REMAP_TABLE.json").write_text(
        json.dumps({
            "schema": "BLACKBOX_PATH_REMAP_TABLE_R1",
            "generated_at_cn": now_cn(),
            "rule": "同一根 E:\\BLACKBOX + 同一相对路径 => 无需改写硬编码; 代码 62 个文件里的 E:/BLACKBOX 常量在本机天然成立",
            "rows": remap_rows,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    for c in checks:
        print(f"[{c['status']:>16}] {c['id']}: {c['detail']}", flush=True)
    print(f"\n输出: {out_dir / 'STRUCTURE_AUDIT_R1.json'}", flush=True)
    print(f"汇总: {verdict_counts}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
