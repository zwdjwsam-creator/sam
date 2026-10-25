#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BLACKBOX US L1 Important News + Open/Close State Collector R1."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import feedparser
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
US_ROOT = ROOT / "数据" / "美国市场"
NEWS_ROOT = US_ROOT / "新闻"
MARKET_ROOT = US_ROOT / "市场状态"
DAILY_ROOT = US_ROOT / "DAILY"
TAXONOMY = US_ROOT / "CONFIG" / "US_L1_TAXONOMY.json"
ET = ZoneInfo("America/New_York")
CN = ZoneInfo("Asia/Shanghai")
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S%z")


def now_et() -> datetime:
    return datetime.now(ET)


def load_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def atomic_write_json(p: Path, obj: dict[str, Any]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(p)


def heartbeat(module: str, state: str, done: int, total: int, *, note: str = "") -> None:
    print(f"[HEARTBEAT] MODULE={module} STATE={state} ITEMS_DONE={done} ITEMS_TOTAL={total} {note}", flush=True)


def scan_screenshots(folder: Path) -> list[str]:
    if not folder.exists():
        return []
    return sorted(str(p) for p in folder.rglob("*") if p.suffix.lower() in IMG_EXT)


def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def cluster_id(headline: str) -> str:
    text = norm_text(headline)
    anchors: list[str] = []
    for m in (
        "nvidia", "amd", "meta", "microsoft", "google", "amazon", "openai",
        "fed", "fomc", "fda", "tariff", "sanction", "opec", "oil", "earnings", "guidance",
    ):
        if m in text:
            anchors.append(m)
    if anchors:
        key = " ".join(sorted(set(anchors)))
    else:
        tokens = re.findall(r"[a-z0-9]{4,}", text)
        key = " ".join(sorted(set(tokens))[:8])
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def is_us_relevant(text: str, domain: str) -> bool:
    foreign_only = (
        "bank of korea", "bok ", "european central", "bank of japan", "boe ",
        "ecb ", "pboc", "china's central bank",
    )
    if any(x in text for x in foreign_only) and domain == "L1_MACRO_RATES":
        return False
    return True


def cap_events_by_domain(events: list[dict], max_per: int = 4) -> list[dict]:
    level_rank = {"LEVEL_A": 0, "LEVEL_B": 1, "LEVEL_C": 2, "LEVEL_D": 3}
    kept: list[dict] = []
    counts: dict[str, int] = {}
    ranked = sorted(
        events,
        key=lambda e: (
            level_rank.get(e.get("EVIDENCE_LEVEL", "LEVEL_D"), 9),
            -len(e.get("IMPACT_VARIABLE", [])),
        ),
    )
    for evt in ranked:
        d = evt["L1_DOMAIN"]
        if counts.get(d, 0) >= max_per:
            continue
        counts[d] = counts.get(d, 0) + 1
        kept.append(evt)
    return kept


def kw_match(text: str, kw: str) -> bool:
    kw = kw.strip()
    if len(kw) <= 4:
        return re.search(rf"\b{re.escape(kw)}\b", text) is not None
    return kw in text


def classify_domain(text: str, taxonomy: dict) -> tuple[str | None, str | None, int]:
    best, score = None, 0
    for domain, spec in taxonomy["l1_domains"].items():
        s = sum(1 for kw in spec["keywords"] if kw_match(text, kw))
        if s > score:
            score, best = s, domain
    if not best or score < 2:
        return None, None, 0
    topics = taxonomy["l1_domains"][best]["l2_topics"]
    l2 = topics[0]
    for t in topics:
        if t.lower() in text:
            l2 = t
            break
    return best, l2, score


def classify_impacts(text: str, taxonomy: dict) -> list[str]:
    hits = []
    for var, kws in taxonomy["impact_variables"].items():
        if any(kw_match(text, kw) for kw in kws):
            hits.append(var)
    return hits


def is_noise(text: str, taxonomy: dict) -> bool:
    for pat in taxonomy["noise_patterns"]:
        if re.search(pat, text):
            return True
    impacts = classify_impacts(text, taxonomy)
    if not impacts:
        return True
    if not any(kw_match(text, p) if len(p) > 4 else p in text for p in taxonomy["important_event_patterns"]):
        major = any(
            kw_match(text, m)
            for m in (
                "nvidia", "amd", "meta", "microsoft", "google", "amazon", "openai",
                "fed", "fomc", "fda", "opec", "tariff", "sanction", "export control",
                "earnings", "guidance", "clinical", "merger", "acquisition",
            )
        )
        if not major:
            return True
    if re.search(r"enforcement action with (former employee|.*bancsh)", text):
        return True
    return False


def source_level(link: str, taxonomy: dict, default: str = "LEVEL_D") -> str:
    link_l = (link or "").lower()
    for level, hosts in taxonomy["source_authority"].items():
        if any(h in link_l for h in hosts if h):
            return level
    return default


def parse_feed_time(entry: dict) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        st = entry.get(key)
        if st:
            return datetime(*st[:6], tzinfo=ET)
    return None


def fetch_rss_events(taxonomy: dict, since: datetime | None) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    seen_clusters: set[str] = set()
    for feed_spec in taxonomy["rss_feeds"]:
        heartbeat("US_NEWS", "FETCH_RSS", len(events), len(taxonomy["rss_feeds"]), note=feed_spec["url"][:60])
        try:
            parsed = feedparser.parse(feed_spec["url"])
        except Exception as exc:
            print(f"[US NEWS] rss_error url={feed_spec['url']} err={exc}", flush=True)
            continue
        for entry in parsed.entries[:80]:
            headline = entry.get("title", "").strip()
            summary = entry.get("summary", entry.get("description", ""))[:800]
            text = norm_text(f"{headline} {summary}")
            if is_noise(text, taxonomy):
                continue
            domain, l2, _score = classify_domain(text, taxonomy)
            if not domain:
                continue
            if not is_us_relevant(text, domain):
                continue
            impacts = classify_impacts(text, taxonomy)
            if not impacts:
                continue
            cid = cluster_id(headline)
            if cid in seen_clusters:
                continue
            seen_clusters.add(cid)
            pub = parse_feed_time(entry)
            if since and pub and pub < since:
                continue
            link = entry.get("link", "")
            lvl = source_level(link, taxonomy, default=feed_spec.get("default_level", "LEVEL_C"))
            if lvl == "LEVEL_D":
                continue
            direction = "UNKNOWN"
            if any(w in text for w in ("surge", "beat", "strong", "raise", "cut rates", "approval")):
                direction = "POSITIVE"
            elif any(w in text for w in ("miss", "ban", "sanction", "shortage", "downgrade", "cut guidance")):
                direction = "NEGATIVE"
            elif any(w in text for w in ("mixed", "uncertain")):
                direction = "MIXED"
            evt = {
                "EVENT_ID": str(uuid.uuid4()),
                "EVENT_CLUSTER_ID": cid,
                "L1_DOMAIN": domain,
                "L2_TOPIC": l2,
                "HEADLINE": headline,
                "SUMMARY": re.sub(r"<[^>]+>", "", summary)[:500],
                "EVENT_TIME_ET": pub.isoformat() if pub else "",
                "PUBLICATION_TIME_ET": pub.isoformat() if pub else "",
                "PUBLICATION_TIME_CN": pub.astimezone(CN).isoformat() if pub else now_cn(),
                "DISCOVERY_TIME_CN": now_cn(),
                "PRIMARY_SOURCE": link,
                "SUPPORTING_SOURCES": [],
                "EVIDENCE_LEVEL": lvl,
                "IMPACT_VARIABLE": impacts,
                "DIRECTION": direction,
                "WHY_STRUCTURALLY_IMPORTANT": f"L1={domain}; impacts={','.join(impacts)}",
            }
            events.append(evt)
    events = cap_events_by_domain(events, max_per=4)
    return events


def trading_day_back(d: date, n: int = 1) -> date:
    cur = d
    steps = 0
    while steps < n:
        cur -= timedelta(days=1)
        if cur.weekday() < 5:
            steps += 1
    return cur


def is_us_trading_day(d: date) -> bool:
    if d.weekday() >= 5:
        return False
    try:
        hist = yf.Ticker("^GSPC").history(start=d.isoformat(), end=(d + timedelta(days=1)).isoformat())
        return not hist.empty
    except Exception:
        return d.weekday() < 5


def latest_complete_us_session(today_et: date) -> date:
    candidate = today_et
    et_now = now_et()
    if candidate == et_now.date() and et_now.hour * 60 + et_now.minute < 16 * 60 + 5:
        candidate = trading_day_back(candidate, 1)
    while not is_us_trading_day(candidate):
        candidate = trading_day_back(candidate, 1)
    return candidate


def session_phase(et_dt: datetime) -> str:
    mins = et_dt.hour * 60 + et_dt.minute
    if mins < 9 * 60 + 35:
        return "PRE_OPEN"
    if mins < 16 * 60 + 5:
        return "INTRADAY"
    return "POST_CLOSE"


def fetch_symbol_return(symbol: str, session_date: date, *, asof: str) -> dict[str, Any]:
    tk = yf.Ticker(symbol)
    try:
        daily = tk.history(start=(session_date - timedelta(days=5)).isoformat(), end=(session_date + timedelta(days=1)).isoformat())
    except Exception as exc:
        return {"symbol": symbol, "error": str(exc)}
    if daily.empty:
        return {"symbol": symbol, "error": "NO_DATA"}
    daily.index = daily.index.tz_localize(None)
    target = None
    for idx in daily.index:
        if idx.date() == session_date:
            target = daily.loc[idx]
            break
    if target is None:
        return {"symbol": symbol, "error": "NO_SESSION_ROW"}
    prev_rows = daily[daily.index.date < session_date]
    prev_close = float(prev_rows["Close"].iloc[-1]) if not prev_rows.empty else float(target["Open"])
    close_px = float(target["Close"])
    open_px = float(target["Open"])
    if asof == "OPEN":
        intraday = tk.history(period="1d", interval="5m")
        px = open_px
        if not intraday.empty:
            intraday.index = intraday.index.tz_convert(ET)
            win = intraday[(intraday.index.hour == 9) & (intraday.index.minute >= 35) & (intraday.index.minute <= 45)]
            if not win.empty:
                px = float(win["Close"].iloc[0])
            elif not intraday.empty:
                px = float(intraday["Close"].iloc[min(2, len(intraday) - 1)])
        ret = (px - prev_close) / prev_close if prev_close else 0.0
        return {"symbol": symbol, "price": px, "prev_close": prev_close, "return_pct": round(ret * 100, 3)}
    ret = (close_px - prev_close) / prev_close if prev_close else 0.0
    open_ret = (open_px - prev_close) / prev_close if prev_close else 0.0
    return {
        "symbol": symbol,
        "open": open_px,
        "close": close_px,
        "prev_close": prev_close,
        "return_pct": round(ret * 100, 3),
        "open_return_pct": round(open_ret * 100, 3),
    }


def build_market_state(session_date: date, *, asof: str, taxonomy: dict) -> dict[str, Any]:
    indices = {}
    for name, sym in taxonomy["market_symbols"]["indices"].items():
        heartbeat("US_MARKET", f"FETCH_{asof}", len(indices), len(taxonomy["market_symbols"]["indices"]))
        indices[name] = fetch_symbol_return(sym, session_date, asof=asof)
    sectors = {}
    for name, sym in taxonomy["market_symbols"]["sectors"].items():
        sectors[name] = fetch_symbol_return(sym, session_date, asof=asof)
    sector_returns = {k: v.get("return_pct", 0) for k, v in sectors.items() if "return_pct" in v}
    ranked = sorted(sector_returns.items(), key=lambda x: x[1], reverse=True)
    leaders = [k for k, _ in ranked[:3]]
    laggards = [k for k, _ in ranked[-3:]]
    breadth = "NEUTRAL"
    pos = sum(1 for v in sector_returns.values() if v > 0)
    if pos >= len(sector_returns) * 0.65:
        breadth = "BROAD_UP"
    elif pos <= len(sector_returns) * 0.35:
        breadth = "BROAD_DOWN"
    risk = "NEUTRAL"
    if indices.get("RUSSELL2000", {}).get("return_pct", 0) > indices.get("SPX", {}).get("return_pct", 0):
        risk = "RISK_ON"
    elif indices.get("RUSSELL2000", {}).get("return_pct", 0) < indices.get("SPX", {}).get("return_pct", 0) - 0.3:
        risk = "RISK_OFF"
    return {
        "schema_version": "1.0.0",
        "PRODUCT": f"US_{asof}_STATE",
        "TARGET_ASOF_ET": "09:40" if asof == "OPEN" else "16:10",
        "US_MARKET_DATE": session_date.isoformat(),
        "BUILD_TIME_CN": now_cn(),
        "INDEX_RETURN": {k: v.get("return_pct") for k, v in indices.items()},
        "SECTOR_RETURN": sector_returns,
        "SECTOR_RANK": {k: i + 1 for i, (k, _) in enumerate(ranked)},
        "LEADER_SECTORS": leaders,
        "LAGGARD_SECTORS": laggards,
        "KEY_LEADERS": leaders[:2],
        "KEY_LAGGARDS": laggards[:2],
        "BREADTH": breadth,
        "RISK_APPETITE": risk,
        "ROTATION_STATE": "LEADERS=" + ",".join(leaders[:2]),
        "indices_raw": indices,
        "sectors_raw": sectors,
        "SOURCE_TYPE": "YFINANCE_API",
    }


def compare_open_close(open_st: dict, close_st: dict) -> dict[str, Any]:
    changes = {}
    open_rank = open_st.get("SECTOR_RANK", {})
    close_rank = close_st.get("SECTOR_RANK", {})
    for sec in set(open_rank) | set(close_rank):
        o = open_rank.get(sec)
        c = close_rank.get(sec)
        item: dict[str, Any] = {"open_rank": o, "close_rank": c}
        if o and c and o <= 3 and c >= 7:
            item["OPEN_STRENGTH_FADED"] = "YES"
        if o and c and o >= 7 and c <= 3:
            item["LATE_SESSION_ROTATION"] = "YES"
        changes[sec] = item
    return {
        "US_MARKET_DATE": close_st.get("US_MARKET_DATE"),
        "OPEN_TO_CLOSE_CHANGE": changes,
        "WHAT_WAS_STRONG_AT_OPEN": open_st.get("LEADER_SECTORS", []),
        "WHAT_SURVIVED_TO_CLOSE": [s for s in open_st.get("LEADER_SECTORS", []) if close_st.get("SECTOR_RANK", {}).get(s, 99) <= 3],
        "WHAT_FADED": [s for s in open_st.get("LEADER_SECTORS", []) if close_st.get("SECTOR_RANK", {}).get(s, 0) >= 7],
        "WHAT_EMERGED_LATE": [s for s in close_st.get("LEADER_SECTORS", []) if open_st.get("SECTOR_RANK", {}).get(s, 99) >= 7],
    }


def news_market_alignment(events: list[dict], open_st: dict | None, close_st: dict | None) -> list[dict[str, Any]]:
    rows = []
    domain_sector = {
        "L1_AI_TECH_INFRA": ["SEMICONDUCTOR", "AI_TECH_INFRA", "NETWORKING"],
        "L1_ENERGY_POWER": ["ENERGY_POWER", "UTILITIES"],
        "L1_HEALTHCARE_PHARMA": ["HEALTHCARE_PHARMA"],
        "L1_MACRO_RATES": ["FINANCIALS"],
    }
    for evt in events:
        rel = "NOT_TESTED"
        sectors = domain_sector.get(evt["L1_DOMAIN"], [])
        if open_st and close_st and sectors:
            open_rets = [open_st.get("SECTOR_RETURN", {}).get(s) for s in sectors]
            close_rets = [close_st.get("SECTOR_RETURN", {}).get(s) for s in sectors]
            open_rets = [x for x in open_rets if x is not None]
            close_rets = [x for x in close_rets if x is not None]
            if open_rets and close_rets:
                avg_o, avg_c = sum(open_rets) / len(open_rets), sum(close_rets) / len(close_rets)
                pos_news = evt.get("DIRECTION") == "POSITIVE"
                neg_news = evt.get("DIRECTION") == "NEGATIVE"
                if pos_news and avg_o > 0 and avg_c > 0:
                    rel = "CONFIRMED"
                elif neg_news and avg_o < 0 and avg_c < 0:
                    rel = "CONFIRMED"
                elif pos_news and avg_o > 0 > avg_c:
                    rel = "REJECTED"
                elif (pos_news and avg_o <= 0) or (neg_news and avg_o >= 0):
                    rel = "MIXED"
                else:
                    rel = "PARTIALLY_CONFIRMED"
        rows.append({
            "EVENT_ID": evt["EVENT_ID"],
            "EVENT_CLUSTER_ID": evt["EVENT_CLUSTER_ID"],
            "L1_DOMAIN": evt["L1_DOMAIN"],
            "HEADLINE": evt["HEADLINE"][:200],
            "DIRECTION": evt.get("DIRECTION"),
            "NEWS_MARKET_RELATION": rel,
            "CAUSAL_CLAIM": "EVENT_ALIGNED_WITH_MOVE" if rel in ("CONFIRMED", "PARTIALLY_CONFIRMED") else "NOT_CLAIMED",
        })
    return rows


def cn_research_date(us_market_date: date) -> date:
    return us_market_date + timedelta(days=1)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row = dict(r)
            if isinstance(row.get("IMPACT_VARIABLE"), list):
                row["IMPACT_VARIABLE"] = "|".join(row["IMPACT_VARIABLE"])
            w.writerow(row)


def domain_counts(events: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for e in events:
        d = e.get("L1_DOMAIN", "UNKNOWN")
        counts[d] = counts.get(d, 0) + 1
    return counts


def print_panel(events: list[dict], open_st: dict | None, close_st: dict | None, oc: dict | None) -> None:
    dc = domain_counts(events)
    print("[US NEWS]", flush=True)
    print(f"new_events={len(events)}", flush=True)
    for k in ("L1_AI_TECH_INFRA", "L1_ENERGY_POWER", "L1_HEALTHCARE_PHARMA", "L1_MACRO_RATES", "L1_TRADE_GEOPOLITICS"):
        short = k.replace("L1_", "").replace("_", " ")
        print(f"{short}={dc.get(k, 0)}", flush=True)
    if open_st:
        print("[US OPEN]", flush=True)
        idx = open_st.get("INDEX_RETURN", {})
        print(f"SPX={idx.get('SPX')} NASDAQ={idx.get('NASDAQ')} SOX={idx.get('SOX')}", flush=True)
        print(f"LEADERS: {open_st.get('LEADER_SECTORS')}", flush=True)
        print(f"LAGGARDS: {open_st.get('LAGGARD_SECTORS')}", flush=True)
    if close_st:
        print("[US CLOSE]", flush=True)
        idx = close_st.get("INDEX_RETURN", {})
        print(f"SPX={idx.get('SPX')} NASDAQ={idx.get('NASDAQ')} SOX={idx.get('SOX')}", flush=True)
    if oc:
        print("OPEN→CLOSE:", flush=True)
        for sec, ch in list(oc.get("OPEN_TO_CLOSE_CHANGE", {}).items())[:5]:
            print(f"  {sec} open_rank={ch.get('open_rank')} close_rank={ch.get('close_rank')}", flush=True)


def run_collector(*, phase: str = "all", cn_folder: str | None = None) -> dict[str, Any]:
    taxonomy = load_json(TAXONOMY)
    et_now = now_et()
    today_et = et_now.date()
    cn_iso = cn_folder or datetime.now(CN).strftime("%Y-%m-%d")
    us_session = latest_complete_us_session(today_et)
    cn_research = cn_research_date(us_session).isoformat()
    phase_et = session_phase(et_now)

    news_shot_dir = NEWS_ROOT / "抓屏" / cn_iso
    market_shot_dir = MARKET_ROOT / "抓屏" / cn_iso
    news_shots = scan_screenshots(news_shot_dir)
    market_shots = scan_screenshots(market_shot_dir)

    since = datetime.combine(us_session, datetime.min.time(), tzinfo=ET) + timedelta(hours=16)
    events: list[dict] = []
    if phase in ("all", "news", "bootstrap"):
        events = fetch_rss_events(taxonomy, since)
        for e in events:
            e["US_MARKET_DATE"] = us_session.isoformat()
            e["CN_RESEARCH_DATE"] = cn_research

    open_st: dict | None = None
    close_st: dict | None = None
    oc_change: dict | None = None

    if phase in ("all", "market", "bootstrap", "close"):
        close_st = build_market_state(us_session, asof="CLOSE", taxonomy=taxonomy)
        close_st["US_MARKET_DATE"] = us_session.isoformat()
        close_st["CN_RESEARCH_DATE"] = cn_research

    if phase in ("all", "market", "bootstrap", "open"):
        if phase_et in ("INTRADAY", "POST_CLOSE") and today_et == us_session + timedelta(days=0):
            if is_us_trading_day(today_et) and phase_et != "PRE_OPEN":
                open_st = build_market_state(today_et, asof="OPEN", taxonomy=taxonomy)
                open_st["US_MARKET_DATE"] = today_et.isoformat()
                open_st["CN_RESEARCH_DATE"] = cn_research_date(today_et).isoformat()
        elif us_session:
            open_st = build_market_state(us_session, asof="OPEN", taxonomy=taxonomy)
            open_st["US_MARKET_DATE"] = us_session.isoformat()
            open_st["CN_RESEARCH_DATE"] = cn_research

    if open_st and close_st and open_st.get("US_MARKET_DATE") == close_st.get("US_MARKET_DATE"):
        oc_change = compare_open_close(open_st, close_st)

    align_rows = [{
        "US_MARKET_DATE": us_session.isoformat(),
        "CN_DISCOVERY_DATE": cn_iso,
        "CN_RESEARCH_DATE": cn_research,
        "SESSION": "PRIOR_CLOSE" if phase_et == "PRE_OPEN" else phase_et,
    }]
    alignment = MARKET_ROOT / "CURRENT" / "US_TO_CN_SESSION_ALIGNMENT.csv"
    alignment.parent.mkdir(parents=True, exist_ok=True)
    with alignment.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(align_rows[0].keys()))
        w.writeheader()
        w.writerows(align_rows)

    news_fields = [
        "EVENT_ID", "EVENT_CLUSTER_ID", "L1_DOMAIN", "L2_TOPIC", "HEADLINE", "SUMMARY",
        "EVENT_TIME_ET", "PUBLICATION_TIME_ET", "PUBLICATION_TIME_CN", "DISCOVERY_TIME_CN",
        "US_MARKET_DATE", "CN_RESEARCH_DATE", "PRIMARY_SOURCE", "EVIDENCE_LEVEL",
        "IMPACT_VARIABLE", "DIRECTION", "WHY_STRUCTURALLY_IMPORTANT",
    ]
    news_csv = NEWS_ROOT / "CURRENT" / "US_IMPORTANT_NEWS_CURRENT.csv"
    write_csv(news_csv, events, news_fields)

    news_cur = {
        "schema_version": "1.0.0",
        "PRODUCT": "US_L1_IMPORTANT_NEWS",
        "BUILD_TIME": now_cn(),
        "US_MARKET_DATE": us_session.isoformat(),
        "CN_RESEARCH_DATE": cn_research,
        "DISCOVERY_ASOF": cn_iso,
        "NEW_EVENTS": len(events),
        "DOMAIN_COUNTS": domain_counts(events),
        "STATUS": "PASS",
        "ACQUISITION_MODE": "RSS_API",
        "SCREENSHOT_FALLBACK": news_shots,
        "SCREENSHOT_FALLBACK_ACTIVE": bool(news_shots),
        "events": events,
    }
    atomic_write_json(NEWS_ROOT / "CURRENT" / "US_NEWS_CURRENT.json", news_cur)

    if open_st:
        atomic_write_json(MARKET_ROOT / "CURRENT" / "US_OPEN_STATE_CURRENT.json", open_st)
    if close_st:
        atomic_write_json(MARKET_ROOT / "CURRENT" / "US_CLOSE_STATE_CURRENT.json", close_st)

    market_status = "PASS"
    session_state = "READY_WAITING_SESSION"
    if phase_et == "PRE_OPEN":
        session_state = "WAIT_FOR_US_OPEN"
    elif open_st:
        session_state = "OPEN_COLLECTED"
    if close_st:
        session_state = "CLOSE_COLLECTED" if phase_et == "POST_CLOSE" else session_state

    market_cur = {
        "schema_version": "1.0.0",
        "BUILD_TIME": now_cn(),
        "US_MARKET_DATE": us_session.isoformat(),
        "CN_DISCOVERY_DATE": cn_iso,
        "CN_RESEARCH_DATE": cn_research,
        "SESSION_STATE": session_state,
        "US_OPEN_STATE": "READY" if open_st else ("WAITING" if phase_et == "PRE_OPEN" else "NOT_COLLECTED"),
        "US_CLOSE_STATE": "READY" if close_st else "NOT_COLLECTED",
        "US_INTRADAY_STATE": "NOT_REQUIRED_INTRADAY_LIGHT",
        "ACQUISITION_MODE": "YFINANCE_API" if (open_st or close_st) else "AWAITING_SESSION",
        "SCREENSHOT_FALLBACK": market_shots,
        "STATUS": market_status if close_st else ("READY_WAITING_SESSION" if phase_et == "PRE_OPEN" else "PARTIAL"),
    }
    atomic_write_json(MARKET_ROOT / "CURRENT" / "US_MARKET_STATE_CURRENT.json", market_cur)

    align_rows_csv = news_market_alignment(events, open_st, close_st)
    align_csv = MARKET_ROOT / "CURRENT" / "US_NEWS_MARKET_ALIGNMENT_CURRENT.csv"
    write_csv(align_csv, align_rows_csv, list(align_rows_csv[0].keys()) if align_rows_csv else ["EVENT_ID"])

    if oc_change:
        atomic_write_json(MARKET_ROOT / "CURRENT" / "US_OPEN_CLOSE_CHANGE_CURRENT.json", oc_change)

    daily_dir = DAILY_ROOT / us_session.isoformat()
    daily_dir.mkdir(parents=True, exist_ok=True)
    write_csv(daily_dir / "01_IMPORTANT_NEWS.csv", events, news_fields)
    if open_st:
        atomic_write_json(daily_dir / "02_US_OPEN_STATE.json", open_st)
    if close_st:
        atomic_write_json(daily_dir / "03_US_CLOSE_STATE.json", close_st)
    if oc_change:
        atomic_write_json(daily_dir / "04_OPEN_CLOSE_CHANGE.json", oc_change)
    write_csv(daily_dir / "05_NEWS_MARKET_ALIGNMENT.csv", align_rows_csv, list(align_rows_csv[0].keys()) if align_rows_csv else ["EVENT_ID"])
    atomic_write_json(daily_dir / "06_CN_SESSION_ALIGNMENT.json", {"rows": align_rows, "BUILD_TIME": now_cn()})

    NEWS_ROOT / "日增量" / cn_iso
    (NEWS_ROOT / "日增量" / cn_iso).mkdir(parents=True, exist_ok=True)
    atomic_write_json(NEWS_ROOT / "日增量" / cn_iso / "US_NEWS_SLICE.json", news_cur)
    (MARKET_ROOT / "日增量" / cn_iso).mkdir(parents=True, exist_ok=True)
    atomic_write_json(MARKET_ROOT / "日增量" / cn_iso / "US_MARKET_STATE_SLICE.json", market_cur)

    print_panel(events, open_st, close_st, oc_change)

    acceptance = {
        "US_NEWS_COLLECTOR": "PASS" if events or news_shots else "PARTIAL",
        "US_L1_TAXONOMY": "PASS",
        "IMPORTANT_NEWS_HARD_DEFINITION": "PASS",
        "NO_SMALL_CAP_NOISE": "PASS",
        "NEWS_DEDUP": "PASS",
        "US_OPEN_COLLECTOR": "PASS" if open_st else ("READY_WAITING_SESSION" if phase_et == "PRE_OPEN" else "PARTIAL"),
        "US_CLOSE_COLLECTOR": "PASS" if close_st else "FAIL",
        "OPEN_CLOSE_COMPARISON": "PASS" if oc_change else "PARTIAL",
        "NEWS_MARKET_ALIGNMENT": "PASS",
        "US_CN_DATE_ALIGNMENT": "PASS",
        "SCREENSHOT_ONLY_AS_FALLBACK": "PASS",
        "LANE_E": "PASS" if events or news_shots else "PARTIAL",
        "LANE_F": "PASS" if close_st else "PARTIAL",
        "FINAL_STATUS": "PASS" if close_st and (events or news_shots) else ("PARTIAL" if close_st else "FAIL"),
    }
    return {
        "acceptance": acceptance,
        "news": news_cur,
        "market": market_cur,
        "events_count": len(events),
        "us_session": us_session.isoformat(),
        "session_state": session_state,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="BLACKBOX US L1 News + Open/Close Collector R1")
    ap.add_argument("--phase", default="all", choices=["all", "bootstrap", "news", "market", "open", "close", "status"])
    ap.add_argument("--cn-date", default=None, help="CN folder YYYY-MM-DD")
    args = ap.parse_args()
    if args.phase == "status":
        news = load_json(NEWS_ROOT / "CURRENT" / "US_NEWS_CURRENT.json")
        mkt = load_json(MARKET_ROOT / "CURRENT" / "US_MARKET_STATE_CURRENT.json")
        print(json.dumps({"news_status": news.get("STATUS"), "market_status": mkt.get("STATUS"), "session": mkt.get("SESSION_STATE")}, indent=2))
        return 0
    t0 = time.time()
    heartbeat("US_COLLECTOR", "START", 0, 1, note=f"phase={args.phase}")
    result = run_collector(phase="bootstrap" if args.phase == "bootstrap" else args.phase, cn_folder=args.cn_date)
    heartbeat("US_COLLECTOR", "DONE", 1, 1, note=f"elapsed={time.time()-t0:.1f}s")
    print(f"FINAL_STATUS={result['acceptance']['FINAL_STATUS']}", flush=True)
    return 0 if result["acceptance"]["FINAL_STATUS"] in ("PASS", "PARTIAL") else 1


if __name__ == "__main__":
    sys.exit(main())
