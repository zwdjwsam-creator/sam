# -*- coding: utf-8 -*-
"""SELLSIDE_REPORT_DAILY_INCREMENTAL_R1

默认每日执行：大摩 / 高盛 / 里昂。
- 有官方正文 → INGESTED
- 无正文 → 允许 EXTERNAL_SUMMARY / THIRD_PARTY_SUMMARY（概况入库）
- 时间对齐：asof=运行日；possible_report_date=原文/转载发布日（禁止用运行日冒充研报日）
- UBS/其他券商禁止；CLSA 官方全文禁止。
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

PRODUCT = Path(r"E:\BLACKBOX\数据\研究报告")
TASK = Path(r"E:\BLACKBOX\任务\BLACKBOX_SELLSIDE_THESIS_TIMELINE_R1")
ENR_PY = TASK / "脚本" / "run_discovery_enrichment_r1.py"
ENGINE_PY = TASK / "脚本" / "run_sellside_backfill_r1.py"

ALLOWED_INSTITUTIONS = ("MORGAN_STANLEY", "GOLDMAN_SACHS", "CLSA")
FIRM_CN = {
    "MORGAN_STANLEY": "大摩",
    "GOLDMAN_SACHS": "高盛",
    "CLSA": "里昂",
}
CN_TZ = timezone(timedelta(hours=8))


def today_cn() -> date:
    return datetime.now(CN_TZ).date()


def load_mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def extend_engine_window(eng, end: date) -> None:
    eng.DATE_END = end
    if hasattr(eng, "in_window"):
        start = eng.DATE_START

        def _in(d, _s=start, _e=end):
            return d is not None and _s <= d <= _e

        eng.in_window = _in


def last_success_date() -> date | None:
    p = PRODUCT / "日增量" / "LAST_SUCCESSFUL_UPDATE.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8")).get("last_successful_date")
        return date.fromisoformat(d) if d else None
    except Exception:
        return None


def seed_payload(asof: date) -> list[dict]:
    """本轮发现种子（按 asof 日更新；报告日=原文/转载日，非 asof）。

    规范：每日先 Exa 发现，再写入本清单；旧 URL 由引擎 DEDUP。
    时间对齐：possible_report_date = 原文/转载发布日，禁止用 asof 冒充。
    """
    # 2026-08-27 R2：补录 8/24–8/26 新发现 + 保留窗口内主种子（DEDUP 安全）
    return [
        # --- GS NEW external (2026-08-24/25) ---
        {
            "institution": "GOLDMAN_SACHS",
            "title": "China advanced chip supply +46% CAGR through 2035; deficit 92%→34% (Caixin / GS)",
            "source_url": "https://www.caixinglobal.com/2026-08-25/chinas-advanced-chip-supply-to-surge-46-annually-through-2035-goldman-says-102477668.html",
            "possible_report_date": "2026-08-25",
            "priority": "P0",
            "possible_theme": "SEMICONDUCTOR",
        },
        {
            "institution": "GOLDMAN_SACHS",
            "title": "China still 34% short of chip self-sufficiency in 2035; SMIC yield fragile (TechTimes / GS)",
            "source_url": "https://www.techtimes.com/articles/325392/20260824/goldman-sees-china-34-short-chip-self-sufficiency-2035-smic-yield-fragile-key.htm",
            "possible_report_date": "2026-08-24",
            "priority": "P0",
            "possible_theme": "SEMICONDUCTOR",
        },
        {
            "institution": "GOLDMAN_SACHS",
            "title": "GS on potential US ban of Chinese optical modules: leaders' moat deeper (HTX / GS Aug10)",
            "source_url": "https://www.htx.com/news/goldman-sachs-research-report-analysis-potential-us-ban-on-c-M8jBznOz/",
            "possible_report_date": "2026-08-10",
            "priority": "P1",
            "possible_theme": "OPTICAL_NETWORKING",
        },
        # --- GS official fulltext (window / DEDUP) ---
        {
            "institution": "GOLDMAN_SACHS",
            "title": "GS SUSTAIN: AI/Data Centers Power Demand, Cyclical Progression, Sustainability",
            "source_url": "https://www.goldmansachs.com/insights/goldman-sachs-research/gs-sustain-ai-data-centers-power-demand-cyclical-progresison-and-sustainability-implications",
            "possible_report_date": "2026-08-19",
            "priority": "P0",
            "possible_theme": "DATA_CENTER_POWER",
        },
        {
            "institution": "GOLDMAN_SACHS",
            "title": "Global AI Investment Is Forecast to Exceed $1 Trillion in 2026",
            "source_url": "https://www.goldmansachs.com/insights/articles/global-investment-is-forecast-to-exceed-1-trillion-in-2026",
            "possible_report_date": "2026-08-07",
            "priority": "P0",
            "possible_theme": "AI_SERVER_CAPEX",
        },
        {
            "institution": "GOLDMAN_SACHS",
            "title": "Why ETFs Are Expected to Draw $2 Trillion in Investments in 2026",
            "source_url": "https://www.goldmansachs.com/insights/articles/why-etfs-are-expected-to-draw-2-trillion-in-investments-in-2026",
            "possible_report_date": "2026-08-18",
            "priority": "P1",
            "possible_theme": "AI_SERVER_CAPEX",
        },
        {
            "institution": "GOLDMAN_SACHS",
            "title": "How AI Debt Is Reshaping Credit Markets",
            "source_url": "https://www.goldmansachs.com/insights/goldman-sachs-exchanges/how-ai-debt-is-reshaping-the-credit-market",
            "possible_report_date": "2026-08-05",
            "priority": "P1",
            "possible_theme": "AI_SERVER_CAPEX",
        },
        {
            "institution": "GOLDMAN_SACHS",
            "title": "Goldman moves China AI trade onshore to A-share hardware (power/PCB/optical/physical AI)",
            "source_url": "https://theclarity.today/story/goldman-sachs-identifies-china-stocks-set-to-benefit-from-ai-hardware-exports-509f284d",
            "possible_report_date": "2026-08-16",
            "priority": "P1",
            "possible_theme": "AI_INFRA_PHASE2",
        },
        # --- MS NEW / refresh external summaries ---
        {
            "institution": "MORGAN_STANLEY",
            "title": "MS: DRAM supply shortage may persist to 2028; hyperscaler+NVDA/AVGO >$3.1T infra commitments (10jqka cite)",
            "source_url": "https://news.10jqka.com.cn/20260826/c679300942.shtml",
            "possible_report_date": "2026-08-26",
            "priority": "P0",
            "possible_theme": "MEMORY_SHORTAGE",
        },
        {
            "institution": "MORGAN_STANLEY",
            "title": "MS: AI services commoditizing; cloud giants & compute tenants cannot both win (36Kr / MS)",
            "source_url": "https://eu.36kr.com/en/p/3944693729295752",
            "possible_report_date": "2026-08-18",
            "priority": "P0",
            "possible_theme": "ENTERPRISE_AI",
        },
        {
            "institution": "MORGAN_STANLEY",
            "title": "MS: AI financing is the 2026 summer story; Big Tech capex +57% (Longbridge / MS)",
            "source_url": "https://longbridge.com/zh-CN/news/296104411",
            "possible_report_date": "2026-08-17",
            "priority": "P0",
            "possible_theme": "AI_SERVER_CAPEX",
        },
        {
            "institution": "MORGAN_STANLEY",
            "title": "Capital alone no longer clears a site: data centers big-money era over (Fortune / MS)",
            "source_url": "https://fortune.com/2026/08/20/data-centers-money-era-morgan-stanley/",
            "possible_report_date": "2026-08-20",
            "priority": "P0",
            "possible_theme": "DATA_CENTER_POWER",
        },
        {
            "institution": "MORGAN_STANLEY",
            "title": "AI data centers face a 38-GW power gap (Motley Fool citing MS)",
            "source_url": "https://www.fool.com/investing/2026/08/20/morgan-stanley-says-ai-data-centers-face-a-38-giga/",
            "possible_report_date": "2026-08-20",
            "priority": "P0",
            "possible_theme": "DATA_CENTER_POWER",
        },
        {
            "institution": "MORGAN_STANLEY",
            "title": "China AI cloud ROIC 13%-20%, ~3y payback; Alibaba Cloud leads (36Kr / MS)",
            "source_url": "https://eu.36kr.com/en/p/3945832937307273",
            "possible_report_date": "2026-08-19",
            "priority": "P0",
            "possible_theme": "ENTERPRISE_AI",
        },
        # --- CLSA third-party metadata ---
        {
            "institution": "CLSA",
            "title": "里昂：内存回调是买入机会，看好三星/SK海力士/美光（HBM供给滞后）",
            "source_url": "https://longbridge.com/zh-CN/news/296436359",
            "possible_report_date": "2026-08-20",
            "priority": "P0",
            "possible_theme": "MEMORY_SHORTAGE",
        },
        {
            "institution": "CLSA",
            "title": "里昂上调中芯国际目标价至97.5港元，AI需求驱动Q3指引超预期",
            "source_url": "https://longbridge.com/zh-CN/news/296045398",
            "possible_report_date": "2026-08-17",
            "priority": "P0",
            "possible_theme": "SEMICONDUCTOR",
        },
        {
            "institution": "CLSA",
            "title": "里昂重申世芯-KY优於大盘，目标价5600台币（报告日2026-08-17）",
            "source_url": "https://vocus.cc/article/6a83a31dfd89780001fbf31c",
            "possible_report_date": "2026-08-17",
            "priority": "P1",
            "possible_theme": "SEMICONDUCTOR",
        },
    ]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    TODAY = today_cn()
    prev = last_success_date()
    # 发现回看：上次成功日−7 天，保证漏抓补录；研报日仍用原文日
    DEFAULT_SINCE = (prev - timedelta(days=7)) if prev else date(2026, 8, 1)

    enr = load_mod(ENR_PY, "enr_daily")
    eng = load_mod(ENGINE_PY, "eng_daily")
    extend_engine_window(eng, TODAY)
    enr.DATE_END = TODAY
    enr.load_engine = lambda: eng  # type: ignore

    day = TODAY.isoformat()
    out_dir = PRODUCT / "日增量" / day
    out_dir.mkdir(parents=True, exist_ok=True)

    q = enr.load_queue()
    seeds = seed_payload(TODAY)
    for item in seeds:
        inst = item["institution"]
        assert inst in ALLOWED_INSTITUTIONS, f"FORBIDDEN_INSTITUTION:{inst}"
        # 时间对齐硬检查：研报日不得晚于 asof+1（时区），也不得为空
        rd = item.get("possible_report_date") or ""
        assert rd, f"MISSING_REPORT_DATE:{item.get('title')}"
        rdd = date.fromisoformat(rd[:10])
        assert rdd <= TODAY + timedelta(days=1), f"FUTURE_REPORT_DATE:{rd}>{day}"
        item["discovery_engine"] = "EXA_DAILY_INCREMENTAL"
        item["search_query"] = f"DAILY_{day}_{inst}"
        item["verification_status"] = "EXA_CANDIDATE"
        item["market_available_at"] = rd
        q = enr.add_candidate(q, item)
    mask_other = ~q["institution"].isin(ALLOWED_INSTITUTIONS)
    if mask_other.any():
        q.loc[mask_other & (q["ingest_status"] == ""), "ingest_status"] = "SKIPPED_NOT_IN_FIRM_SCOPE"
    enr.save_queue(q)

    today_urls = {x["source_url"] for x in seeds}
    for i, row in q.iterrows():
        if row.get("source_url") not in today_urls:
            continue
        # 允许重试：窗口外 / 旧版非官方拦截 / 待处理
        if row.get("ingest_status") in (
            "",
            "PENDING",
            "OUT_OF_WINDOW",
            "RIGHTS_BLOCKED",
            "FAIL_DOWNLOAD",
            "FAIL_HTTP",
        ):
            # 用最新 rights 规则重分类
            rights, ai_ok, stype = enr.rights_classify(row["institution"], row["source_url"])
            q.at[i, "rights_status"] = rights
            q.at[i, "source_type_guess"] = stype
            q.at[i, "fulltext_allowed"] = str(ai_ok and rights == "PUBLIC_FULLTEXT").upper()
            q.at[i, "ingest_status"] = ""
            q.at[i, "verification_status"] = "EXA_CANDIDATE"
            if not row.get("possible_report_date"):
                # 从 seed 补日期
                for s in seeds:
                    if s["source_url"] == row.get("source_url"):
                        q.at[i, "possible_report_date"] = s["possible_report_date"]
                        q.at[i, "market_available_at"] = s["possible_report_date"]
                        break
    enr.save_queue(q)

    rc = enr.main_ingest_from_queue(verified_only=False)

    q2 = enr.load_queue()
    man = eng.load_manifest()
    clsa = eng.load_clsa_views() if hasattr(eng, "load_clsa_views") else pd.DataFrame()
    ext = eng.load_external_summaries() if hasattr(eng, "load_external_summaries") else pd.DataFrame()

    today_rows = q2[q2["source_url"].isin(today_urls)].copy()
    by_inst = (
        today_rows.groupby(["institution", "ingest_status"]).size().reset_index(name="n")
        if len(today_rows)
        else pd.DataFrame(columns=["institution", "ingest_status", "n"])
    )

    new_full = int((today_rows["ingest_status"] == "INGESTED").sum()) if len(today_rows) else 0
    new_meta = int((today_rows["ingest_status"] == "METADATA_CAPTURED").sum()) if len(today_rows) else 0
    dedup = int(today_rows["ingest_status"].isin(["DEDUP_URL", "DEDUP_SHA"]).sum()) if len(today_rows) else 0
    blocked = int((today_rows["ingest_status"] == "RIGHTS_BLOCKED").sum()) if len(today_rows) else 0
    out_win = int((today_rows["ingest_status"] == "OUT_OF_WINDOW").sum()) if len(today_rows) else 0
    failed = (
        today_rows[
            ~today_rows["ingest_status"].isin(
                [
                    "INGESTED",
                    "METADATA_CAPTURED",
                    "DEDUP_URL",
                    "DEDUP_SHA",
                    "RIGHTS_BLOCKED",
                    "OUT_OF_WINDOW",
                    "",
                ]
            )
        ]
        if len(today_rows)
        else today_rows
    )

    # 时间对齐审计
    time_align = []
    for _, r in today_rows.iterrows():
        rd = str(r.get("possible_report_date") or "")[:10]
        time_align.append(
            {
                "institution": r.get("institution"),
                "title": (r.get("title") or "")[:80],
                "report_date": rd,
                "asof": day,
                "aligned": bool(rd and rd <= day),
                "ingest_status": r.get("ingest_status"),
                "rights_status": r.get("rights_status"),
                "source_type": r.get("source_type_guess"),
            }
        )

    report = {
        "task_id": "SELLSIDE_REPORT_DAILY_INCREMENTAL_R1",
        "asof": day,
        "firm_scope": list(ALLOWED_INSTITUTIONS),
        "firm_scope_cn": [FIRM_CN[x] for x in ALLOWED_INSTITUTIONS],
        "window": {
            "discovery_lookback_since": str(DEFAULT_SINCE),
            "until": str(TODAY),
            "last_successful_date": str(prev) if prev else None,
        },
        "TIME_ALIGN_POLICY": "report_date=source_publication_date; asof=run_date; no_backfill_as_today",
        "NEW_REPORT_COUNT": new_full,
        "NEW_METADATA_OR_EXTERNAL_SUMMARY_COUNT": new_meta,
        "NEW_CLSA_METADATA_COUNT": int(
            ((today_rows["institution"] == "CLSA") & (today_rows["ingest_status"] == "METADATA_CAPTURED")).sum()
        )
        if len(today_rows)
        else 0,
        "DEDUP_COUNT": dedup,
        "RIGHTS_BLOCKED_COUNT": blocked,
        "OUT_OF_WINDOW_COUNT": out_win,
        "FAILED_COUNT": int(len(failed)),
        "manifest_n": int(len(man)),
        "clsa_view_n": int(len(clsa)) if clsa is not None else 0,
        "external_summary_n": int(len(ext)) if ext is not None else 0,
        "by_institution_status": by_inst.to_dict(orient="records"),
        "time_align_audit": time_align,
        "candidates": today_rows[
            [
                "institution",
                "title",
                "source_url",
                "possible_report_date",
                "rights_status",
                "ingest_status",
                "source_type_guess",
            ]
        ].to_dict(orient="records")
        if len(today_rows)
        else [],
        "TASK_STATUS": "PASS" if rc == 0 else "FAIL",
        "NOTE": "仅大摩/高盛/里昂；无正文可用外部转载概况；里昂禁止官方全文；每日默认执行",
        "probed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ingest_rc": rc,
    }
    if new_full + new_meta == 0 and dedup > 0 and len(failed) == 0:
        report["TASK_STATUS"] = "PASS_NO_CHANGE"
    if new_full + new_meta > 0 and rc == 0:
        report["TASK_STATUS"] = "PASS"
    if any(not x["aligned"] for x in time_align):
        report["TASK_STATUS"] = "FAIL_TIME_ALIGN"

    (out_dir / "DAILY_INCREMENTAL_STATUS.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    today_rows.to_csv(out_dir / "NEW_CANDIDATES.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(time_align).to_csv(out_dir / "TIME_ALIGN_AUDIT.csv", index=False, encoding="utf-8-sig")
    if len(failed):
        failed.to_csv(out_dir / "FAILED_DOWNLOADS.csv", index=False, encoding="utf-8-sig")

    lines = [
        f"# 卖方研报日增量 {day}",
        "",
        f"**机构范围（硬约束）**: 大摩 / 高盛 / 里昂 — 仅此三家",
        f"**窗口**: discovery_lookback {DEFAULT_SINCE} → {TODAY}（上次成功={prev}）",
        f"**时间对齐**: report_date=原文/转载发布日；asof={day}",
        f"**TASK_STATUS**: {report['TASK_STATUS']}",
        "",
        f"- NEW_FULLTEXT (MS/GS 官方) = **{new_full}**",
        f"- NEW_METADATA / EXTERNAL_SUMMARY = **{new_meta}**",
        f"- DEDUP = {dedup}",
        f"- RIGHTS_BLOCKED = {blocked}",
        f"- OUT_OF_WINDOW = {out_win}",
        f"- FAILED = {report['FAILED_COUNT']}",
        f"- REPORT_MASTER n = {report['manifest_n']}",
        f"- CLSA_PUBLIC_VIEW n = {report['clsa_view_n']}",
        f"- EXTERNAL_SUMMARY_VIEW n = {report['external_summary_n']}",
        "",
        "## 本轮候选（按研报日）",
        "",
    ]
    for r in sorted(report["candidates"], key=lambda x: x.get("possible_report_date") or ""):
        lines.append(
            f"- [{FIRM_CN.get(r['institution'], r['institution'])}] "
            f"report_date={r.get('possible_report_date','')} · {r.get('ingest_status')} · "
            f"{r.get('rights_status')} · {r.get('source_type_guess','')} · "
            f"{(r.get('title') or '')[:80]}"
        )
    lines += [
        "",
        "RIGHTS: CLSA 官方/PDF转载全文=不入库；第三方概况=METADATA。",
        "MS/GS 无官方正文时，允许 Fortune/Fool/36Kr 等 EXTERNAL_SUMMARY。",
        "",
    ]
    (out_dir / "DAILY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    cur = PRODUCT / "CURRENT" / "SELLSIDE_DAILY_INCREMENTAL_CURRENT.json"
    cur.parent.mkdir(parents=True, exist_ok=True)
    cur.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PRODUCT / "CURRENT" / "SELLSIDE_DAILY_INCREMENTAL_CURRENT.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    (PRODUCT / "日增量" / "LAST_SUCCESSFUL_UPDATE.json").write_text(
        json.dumps(
            {
                "last_successful_date": day,
                "firms": list(ALLOWED_INSTITUTIONS),
                "status": report["TASK_STATUS"],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if str(report["TASK_STATUS"]).startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
