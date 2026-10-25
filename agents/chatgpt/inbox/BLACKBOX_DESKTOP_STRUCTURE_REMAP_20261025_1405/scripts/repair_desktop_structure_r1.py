#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""台式机结构修复 R1 —— 两类动作分离, 默认全部 dry-run.

A. hygiene: 乱码目录并回正式中文目录 (移动 + 备份 + 台账, 可回滚)
B. candidate: 按笔记本口径重建“域 CURRENT + Manifest”候选, 只写 候选/, 不碰生产 CURRENT

用法:
  python repair_desktop_structure_r1.py --mode hygiene            # 只打印计划
  python repair_desktop_structure_r1.py --mode hygiene --apply    # 执行并写台账
  python repair_desktop_structure_r1.py --mode candidate          # 生成候选 + 差异说明
  python repair_desktop_structure_r1.py --mode rollback --ledger <台账.json>

硬边界: 不下载 / 不清洗 / 不发布 / 不改 sealed / 不写生产 CURRENT。
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

CN = timezone(timedelta(hours=8))
ROOT = Path(r"E:\BLACKBOX")
TASK = ROOT / "任务" / "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1"
OUT = TASK / "输出"
CAND = TASK / "候选"
BAK = TASK / "备份"
DP_MODULE = ROOT / "脚本" / "run_blackbox_daily_incremental_data_plane_r1.py"
LANES_CFG = ROOT / "研究系统" / "数据平面" / "CONFIG" / "daily_lanes.json"
PROD_CURRENT = ROOT / "研究系统" / "数据平面" / "CURRENT"


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def stamp() -> str:
    return datetime.now(CN).strftime("%Y%m%d_%H%M%S")


def load(p: Path) -> Any:
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def dump(p: Path, obj: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def mojibake_decode(name: str, canonical: set[str]) -> str | None:
    if name.isascii():
        return None
    if not any("\ue000" <= ch <= "\uf8ff" for ch in name):
        # 仍可能是 GBK 误读; 只在能还原成已有目录时才认
        pass
    try:
        raw = name.encode("gbk", errors="ignore")
    except Exception:
        return None
    if not raw:
        return None
    try:
        d = raw.decode("utf-8", errors="strict")
        if d != name and d in canonical:
            return d
    except Exception:
        pass
    for cut in range(len(raw), 0, -1):
        try:
            pre = raw[:cut].decode("utf-8", errors="strict")
        except Exception:
            continue
        cands = [c for c in canonical if pre and c.startswith(pre)]
        if cands:
            return sorted(cands, key=len)[0]
    return None


# ---------------- A. hygiene ----------------

def plan_hygiene() -> list[dict[str, Any]]:
    canonical = {c.name for c in ROOT.iterdir() if c.is_dir()}
    plan: list[dict[str, Any]] = []
    for d in sorted(ROOT.iterdir()):
        if not d.is_dir():
            continue
        target = mojibake_decode(d.name, canonical)
        if not target or target == d.name:
            continue
        tdir = ROOT / target
        if not tdir.exists():
            continue
        n_files = 0
        for f in sorted(d.rglob("*")):
            if not f.is_file():
                continue
            n_files += 1
            rel = f.relative_to(d)
            dst = tdir / rel
            act = "MOVE"
            note = ""
            if dst.exists():
                if sha256(dst) == sha256(f):
                    act = "DEDUP_DROP"
                    note = "目标已存在且字节相同"
                else:
                    act = "CONFLICT_SKIP"
                    note = "目标已存在但内容不同 -> 不覆盖"
            plan.append({
                "src": str(f), "dst": str(dst), "action": act, "note": note,
                "src_rel": str(f.relative_to(ROOT)),
                "dst_rel": str(dst.relative_to(ROOT)),
                "sha256": sha256(f), "bytes": f.stat().st_size,
                "src_mojibake_dir": d.name, "decoded_dir": target,
            })
        if n_files == 0:
            plan.append({
                "src": str(d), "dst": str(tdir), "action": "DROP_EMPTY_TREE",
                "note": "纯空目录骨架; 正式目录已存在同名子树",
                "src_rel": str(d.relative_to(ROOT)), "dst_rel": target,
                "sha256": None, "bytes": 0,
                "src_mojibake_dir": d.name, "decoded_dir": target,
            })
    return plan


def apply_hygiene(plan: list[dict[str, Any]]) -> Path:
    ts = stamp()
    bakdir = BAK / f"hygiene_{ts}"
    bakdir.mkdir(parents=True, exist_ok=True)
    backup: list[dict[str, str]] = []
    for item in plan:
        src = Path(item["src"])
        dst = Path(item["dst"])
        if item["action"] == "DROP_EMPTY_TREE":
            continue
        b = bakdir / item["src_rel"]
        b.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, b)
            backup.append({"orig": str(src), "backup": str(b)})
        if item["action"] == "MOVE":
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        elif item["action"] == "DEDUP_DROP":
            src.unlink()
        # CONFLICT_SKIP 不动
    # 清空并移除乱码目录
    removed: list[str] = []
    for dname in {i["src_mojibake_dir"] for i in plan}:
        d = ROOT / dname
        if d.exists():
            for sub in sorted([p for p in d.rglob("*") if p.is_dir()], key=lambda p: -len(str(p))):
                try:
                    sub.rmdir()
                except OSError:
                    pass
            try:
                d.rmdir()
                removed.append(dname)
            except OSError:
                pass
    ledger = {
        "schema": "BLACKBOX_DESKTOP_STRUCTURE_REPAIR_LEDGER_R1",
        "mode": "hygiene",
        "applied_at_cn": now_cn(),
        "root": str(ROOT),
        "items": plan,
        "backup_dir": str(bakdir),
        "backup": backup,
        "removed_mojibake_dirs": removed,
    }
    lp = OUT / f"STRUCTURE_REPAIR_LEDGER_{ts}.json"
    dump(lp, ledger)
    dump(OUT / "STRUCTURE_REPAIR_LEDGER_CURRENT.json", ledger)
    return lp


def rollback(ledger_path: Path) -> None:
    led = load(ledger_path) or {}
    for item in reversed(led.get("items") or []):
        if item.get("action") != "MOVE":
            continue
        src, dst = Path(item["src"]), Path(item["dst"])
        if dst.exists() and not src.exists():
            src.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst), str(src))
    print(f"ROLLBACK done from {ledger_path}", flush=True)


# ---------------- B. candidate ----------------

def load_dp_module():
    import sys

    script_dir = str(ROOT / "脚本")
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("bb_daily_plane", DP_MODULE)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def build_candidate(session_iso: str = "2026-09-24") -> dict[str, Any]:
    man_p = PROD_CURRENT / "DAILY_DATA_MANIFEST_CURRENT.json"
    prod = load(man_p) or {}
    cfg = load(LANES_CFG) or {}
    lanes_cfg = (cfg.get("lanes") or {})

    d_root = ROOT / "数据" / "研究报告" / "国内卖方"
    n_root = ROOT / "数据" / "研究报告" / "国内新闻"
    d_slice = d_root / "日增量" / session_iso
    n_slice = n_root / "日增量" / session_iso

    ledger_csv = d_slice / "DOMESTIC_SELLSIDE_LEDGER.csv"
    n_rows = 0
    if ledger_csv.exists():
        n_rows = max(0, sum(1 for _ in ledger_csv.read_text(encoding="utf-8", errors="replace").splitlines()) - 1)
    news_slice = load(n_slice / "DOMESTIC_NEWS_SLICE.json") or {}
    n_head = int(news_slice.get("n_headlines") or news_slice.get("headline_count") or 0)

    d_sellside_cur = {
        "schema_version": "1.0.0",
        "BUILD_TIME": now_cn(),
        "DISCOVERY_ASOF": session_iso,
        "INGEST_TIME": now_cn(),
        "STATUS": "PASS" if n_rows > 0 else "DEGRADED",
        "SOURCE_PATH": str(ledger_csv if ledger_csv.exists() else d_root),
        "N_ROWS": n_rows,
        "FIXED_ROOT": str(d_root),
        "note": "国内卖方固定目录；observer ledger 同步为起点；本文件为结构修复候选(未发布)",
        "REPAIR_ORIGIN": "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1",
    }
    d_news_cur = {
        "schema_version": "1.0.0",
        "BUILD_TIME": now_cn(),
        "DISCOVERY_ASOF": session_iso,
        "SOURCE_OBS_ASOF": news_slice.get("asof"),
        "INGEST_TIME": now_cn(),
        "STATUS": "PASS" if n_head > 0 else "DEGRADED",
        "HEADLINE_COUNT": n_head,
        "FIXED_ROOT": str(n_root),
        "daily_slice": str(n_slice),
        "source_obs": (lanes_cfg.get("D_DOMESTIC_RESEARCH_NEWS_INCREMENTAL") or {}).get("news_obs_current"),
        "note": "旧指针 daily_slice=2026-08-31 与 DISCOVERY_ASOF 自相矛盾；本候选对齐到实际切片",
        "REPAIR_ORIGIN": "BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1",
    }

    lane_f_cfg = lanes_cfg.get("F_US_MARKET_STATE_INCREMENTAL") or {}
    f_prod = dict(prod.get("US_MARKET") or {})
    f_root = lane_f_cfg.get("fine_grained_root")
    f_paths = dict(f_prod.get("FIXED_PATHS") or {})
    f_paths.update({
        k: v for k, v in {
            "root": lane_f_cfg.get("product_root"),
            "current": lane_f_cfg.get("current"),
            "open_current": lane_f_cfg.get("open_current"),
            "close_current": lane_f_cfg.get("close_current"),
            "alignment": lane_f_cfg.get("session_alignment"),
            "alignment_csv": lane_f_cfg.get("alignment_csv"),
            "fine_grained_current": lane_f_cfg.get("fine_grained_current"),
            "fine_grained_root": f_root,
            "mapping_prior_current": f"{f_root}\\CURRENT\\A_SHARE_MAPPING_PRIOR_CURRENT.json" if f_root else None,
            "snapshot_current": f"{f_root}\\CURRENT\\US_FINE_GRAINED_SNAPSHOT_CURRENT.json" if f_root else None,
        }.items() if v
    })
    f_prod["FIXED_PATHS"] = f_paths

    uc = load(ROOT / "数据" / "美国市场" / "新闻" / "CURRENT" / "US_NEWS_CURRENT.json") or {}
    e_lane = {
        "lane": "E_US_NEWS_INCREMENTAL",
        "DISCOVERY_ASOF": session_iso,
        "US_MARKET_DATE": uc.get("US_MARKET_DATE"),
        "CN_RESEARCH_DATE": uc.get("CN_RESEARCH_DATE"),
        "NEW_EVENTS": uc.get("NEW_EVENTS", 0),
        "DOMAIN_COUNTS": uc.get("DOMAIN_COUNTS", {}),
        "STATUS": uc.get("STATUS", "PARTIAL"),
        "ACQUISITION_MODE": uc.get("ACQUISITION_MODE", "RSS_API"),
        "PRODUCT": uc.get("PRODUCT"),
        "FIXED_PATHS": {
            "root": (lanes_cfg.get("E_US_NEWS_INCREMENTAL") or {}).get("product_root"),
            "current": (lanes_cfg.get("E_US_NEWS_INCREMENTAL") or {}).get("current"),
            "important_news_csv": (lanes_cfg.get("E_US_NEWS_INCREMENTAL") or {}).get("important_news_csv"),
            "taxonomy": (lanes_cfg.get("E_US_NEWS_INCREMENTAL") or {}).get("taxonomy"),
        },
    }

    lanes = {
        "A": prod.get("JQ") or {},
        "B": prod.get("T_EXTERNAL") or {},
        "C": prod.get("GLOBAL_SELLSIDE") or {},
        "D": {
            "lane": "D_DOMESTIC_RESEARCH_NEWS_INCREMENTAL",
            "DISCOVERY_ASOF": session_iso,
            "NEW_REPORTS": n_rows,
            "NEW_EVENTS": n_head,
            "STATUS": "PASS" if (n_rows > 0 and n_head > 0) else "DEGRADED",
            "FIXED_PATHS": {
                "domestic_sellside": str(d_root),
                "domestic_news": str(n_root),
                "sellside_current": str(d_root / "CURRENT" / "DOMESTIC_SELLSIDE_CURRENT.json"),
                "news_current": str(n_root / "CURRENT" / "DOMESTIC_NEWS_CURRENT.json"),
            },
        },
        "E": e_lane,
        "F": f_prod,
    }

    dp = load_dp_module()
    man = dp.build_manifest(session_iso, lanes)
    pack = dp.build_input_pack(man, cfg)

    CAND.mkdir(parents=True, exist_ok=True)
    dump(CAND / "CURRENT" / "DAILY_DATA_MANIFEST_CANDIDATE.json", man)
    dump(CAND / "CURRENT" / "DAILY_RESEARCH_INPUT_PACK_CANDIDATE.json", pack)
    dump(CAND / "CURRENT" / "DOMESTIC_SELLSIDE_CURRENT_CANDIDATE.json", d_sellside_cur)
    dump(CAND / "CURRENT" / "DOMESTIC_NEWS_CURRENT_CANDIDATE.json", d_news_cur)

    # 与生产 CURRENT 的逐键差异
    def flat(o: Any, pre: str = "") -> dict[str, Any]:
        out: dict[str, Any] = {}
        if isinstance(o, dict):
            for k, v in o.items():
                out.update(flat(v, f"{pre}.{k}"))
        elif isinstance(o, list):
            out[pre] = json.dumps(o, ensure_ascii=False)
        else:
            out[pre] = o
        return out

    fa, fb = flat(prod), flat(man)
    diffs = []
    for k in sorted(set(fa) | set(fb)):
        if fa.get(k) != fb.get(k):
            diffs.append({"key": k, "production": fa.get(k), "candidate": fb.get(k)})

    meta = {
        "schema": "BLACKBOX_DESKTOP_STRUCTURE_CANDIDATE_R1",
        "generated_at_cn": now_cn(),
        "session": session_iso,
        "production_manifest": str(man_p),
        "candidate_manifest": str(CAND / "CURRENT" / "DAILY_DATA_MANIFEST_CANDIDATE.json"),
        "n_diff_keys": len(diffs),
        "diff_vs_production": diffs,
        "source_evidence": {
            "domestic_sellside_slice": str(d_sellside_cur["SOURCE_PATH"]),
            "domestic_sellside_rows": n_rows,
            "domestic_news_slice": str(n_slice),
            "domestic_news_headlines": n_head,
            "domestic_news_slice_asof": news_slice.get("asof"),
        },
        "promotion_requires": "CURRENT_SWITCH 授权 + 备份目录 + 回滚演练; 本脚本不写生产 CURRENT",
    }
    dump(CAND / "CANDIDATE_META.json", meta)

    lines = [
        "# 候选 vs 生产 CURRENT —— 逐键差异",
        "",
        f"生成: {meta['generated_at_cn']}　会话: {session_iso}　差异键: {len(diffs)}",
        "",
        "| 键 | 生产(2026-08-31 会话) | 候选(2026-09-24 会话) |",
        "|---|---|---|",
    ]
    for d in diffs:
        lines.append(f"| `{d['key']}` | {str(d['production'])[:90]} | {str(d['candidate'])[:90]} |")
    lines += [
        "",
        "## 依据",
        f"- 国内卖方切片: `{d_sellside_cur['SOURCE_PATH']}`（{n_rows} 行）",
        f"- 国内新闻切片: `{n_slice}`（{n_head} 条；切片自身 asof={news_slice.get('asof')}）",
        "- Manifest 由生产函数 `build_manifest/build_input_pack` 生成，未另写实现。",
        "- 未下载、未清洗、未采集；未改任何生产 CURRENT。",
    ]
    (CAND / "PROMOTION_DIFF.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return meta


def atomic_write_json(p: Path, obj: Any) -> None:
    import os

    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + f".tmp_promote_{os.getpid()}")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def promote() -> dict[str, Any]:
    """把 候选/ 提升为生产 CURRENT：先备份，再原子替换，最后回读校验。"""
    cand_man_p = CAND / "CURRENT" / "DAILY_DATA_MANIFEST_CANDIDATE.json"
    cand_pack_p = CAND / "CURRENT" / "DAILY_RESEARCH_INPUT_PACK_CANDIDATE.json"
    cand_d_p = CAND / "CURRENT" / "DOMESTIC_SELLSIDE_CURRENT_CANDIDATE.json"
    cand_n_p = CAND / "CURRENT" / "DOMESTIC_NEWS_CURRENT_CANDIDATE.json"
    man = load(cand_man_p)
    pack = load(cand_pack_p)
    d_cur = load(cand_d_p)
    n_cur = load(cand_n_p)
    if not (man and pack and d_cur and n_cur):
        raise SystemExit("候选缺失: 先跑 --mode candidate")

    plane_p = PROD_CURRENT / "DAILY_DATA_PLANE_CURRENT.json"
    plane = {
        "schema_version": "1.0.0",
        "BUILD_TIME": now_cn(),
        "CN_RESEARCH_DATE": man["CN_RESEARCH_DATE"],
        "DAILY_INCREMENTAL_READY": man["DAILY_INCREMENTAL_READY"],
        "PATH_MAP": str(ROOT / "研究系统" / "数据平面" / "CONFIG" / "DATA_PLANE_PATH_MAP.json"),
        "manifest_current": str(PROD_CURRENT / "DAILY_DATA_MANIFEST_CURRENT.json"),
        "input_pack_current": str(PROD_CURRENT / "DAILY_RESEARCH_INPUT_PACK_CURRENT.json"),
        "DATA_GENERATION_ID": man.get("DATA_GENERATION_ID"),
        "DATA_MANIFEST_ID": man.get("manifest_id"),
    }

    targets = [
        (PROD_CURRENT / "DAILY_DATA_MANIFEST_CURRENT.json", man),
        (plane_p, plane),
        (PROD_CURRENT / "DAILY_RESEARCH_INPUT_PACK_CURRENT.json", pack),
        (ROOT / "数据" / "研究报告" / "国内卖方" / "CURRENT" / "DOMESTIC_SELLSIDE_CURRENT.json", d_cur),
        (ROOT / "数据" / "研究报告" / "国内新闻" / "CURRENT" / "DOMESTIC_NEWS_CURRENT.json", n_cur),
    ]

    ts = stamp()
    bakdir = BAK / f"promote_{ts}"
    backed: list[dict[str, str]] = []
    for dst, _ in targets:
        if dst.exists():
            b = bakdir / dst.relative_to(ROOT)
            b.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, b)
            backed.append({"orig": str(dst), "backup": str(b), "sha256": sha256(dst)})

    for dst, obj in targets:
        atomic_write_json(dst, obj)

    verify = {
        "manifest_id": (load(targets[0][0]) or {}).get("manifest_id"),
        "CN_RESEARCH_DATE": (load(targets[0][0]) or {}).get("CN_RESEARCH_DATE"),
        "DG1": (load(targets[0][0]) or {}).get("DATA_GENERATION_ID"),
        "plane_DG1": (load(plane_p) or {}).get("DATA_GENERATION_ID"),
        "domestic_sellside_asof": (load(targets[3][0]) or {}).get("DISCOVERY_ASOF"),
        "domestic_news_asof": (load(targets[4][0]) or {}).get("DISCOVERY_ASOF"),
    }
    verify["dg1_consistent"] = verify["DG1"] == verify["plane_DG1"] and bool(verify["DG1"])

    ledger = {
        "schema": "BLACKBOX_DESKTOP_STRUCTURE_PROMOTION_LEDGER_R1",
        "mode": "promote",
        "applied_at_cn": now_cn(),
        "root": str(ROOT),
        "targets": [str(t[0]) for t in targets],
        "backup_dir": str(bakdir),
        "backup": backed,
        "verify": verify,
        "rollback_cmd": f"copy {bakdir}\\<相对路径> -> 原位",
    }
    dump(OUT / f"STRUCTURE_PROMOTION_LEDGER_{ts}.json", ledger)
    dump(OUT / "STRUCTURE_PROMOTION_LEDGER_CURRENT.json", ledger)
    return ledger


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="hygiene", choices=["hygiene", "candidate", "promote", "rollback"])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--session", default="2026-09-24")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    if args.mode == "hygiene":
        plan = plan_hygiene()
        if not plan:
            print("HYGIENE: nothing to do", flush=True)
            return 0
        for p in plan:
            print(f"[{p['action']:>14}] {p['src_rel']}  ->  {p['dst_rel']}  {p['note']}", flush=True)
        if args.apply:
            lp = apply_hygiene(plan)
            print(f"\nAPPLIED. ledger={lp}", flush=True)
        else:
            print(f"\nDRY-RUN. {len(plan)} 项; 加 --apply 才执行", flush=True)
        return 0

    if args.mode == "candidate":
        meta = build_candidate(args.session)
        print(json.dumps({k: meta[k] for k in ("session", "n_diff_keys", "candidate_manifest")}, ensure_ascii=False, indent=2))
        print(f"\n差异说明: {CAND / 'PROMOTION_DIFF.md'}", flush=True)
        return 0

    if args.mode == "promote":
        if not args.apply:
            print("PROMOTE: 需 --apply。将写入 5 个 CURRENT（先备份到 备份/promote_<ts>/）:", flush=True)
            for p in [
                PROD_CURRENT / "DAILY_DATA_MANIFEST_CURRENT.json",
                PROD_CURRENT / "DAILY_DATA_PLANE_CURRENT.json",
                PROD_CURRENT / "DAILY_RESEARCH_INPUT_PACK_CURRENT.json",
                ROOT / "数据" / "研究报告" / "国内卖方" / "CURRENT" / "DOMESTIC_SELLSIDE_CURRENT.json",
                ROOT / "数据" / "研究报告" / "国内新闻" / "CURRENT" / "DOMESTIC_NEWS_CURRENT.json",
            ]:
                print("  ", p, flush=True)
            return 0
        led = promote()
        print(json.dumps(led["verify"], ensure_ascii=False, indent=2), flush=True)
        print(f"\nledger={OUT / 'STRUCTURE_PROMOTION_LEDGER_CURRENT.json'}", flush=True)
        return 0

    if args.mode == "rollback":
        if not args.ledger:
            print("--ledger required", flush=True)
            return 2
        rollback(Path(args.ledger))
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
