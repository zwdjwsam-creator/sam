"""Consume the GPT final review (REVIEWED_FINAL_PASS_BLOCKED) and correct what it refuted.

This receipt dispatches no new repair round. What it does:

1. archives the staged tip and stages the new revision (the reviewer appended a
   leading review section to the same file);
2. records the review verbatim-by-point in evidence/, including the five concrete
   reasons the delivery was rejected;
3. corrects the claims the reviewer refuted, because a refuted causal claim must not
   stay standing in a published report:
   * "supplier-side defect / must re-issue the plane" -> "cause NOT established"
     (integer-date files and constant-1.0 planes are observations; they cannot by
     themselves separate the requested fq/normalisation basis, the SDK return shape,
     local serialisation, and the supplier content);
   * "the real chain executes R15 -> compiler -> publish" -> the components were
     exercised separately: CONNECTED_PIPELINE's compiler argv reads
     candidate/cc/CC_REPLAY_20260924/RELEASE.json, and the R15 output is
     candidate/r15_releases/R15_REPLAY_20260924_R2; no single-product chain is proven;
   * "V4 has 0 minute get_price calls so minute input is irrelevant" -> direct minute
     calls are 0, but get_current_data snapshot dependence is not resolved;
4. adds review_status to the acceptance file and a §11 receipt section to the report.

Nothing is re-run: the reviewer explicitly said the upload-wait phase is over and no new
round is dispatched.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

TASK = Path(r"E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\end_to_end_completion")
D = TASK / "deliverables"
E = TASK / "evidence"
MB = Path(r"E:\BLACKBOX\运行\外部大脑信箱")
TIPS = TASK / "hub_tips"
REV = "R13_REVIEW_CONSUMED"
CN = timezone(timedelta(hours=8))
TIP = "BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025.md"


def now_cn() -> str:
    return datetime.now(CN).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ 1. stage the tip
incoming = TIPS / ("_INCOMING_" + TIP)
stage = TIPS / TIP
prev = TIPS / (TIP + ".prev_20261025_1300")
if stage.exists() and not prev.exists():
    prev.write_bytes(stage.read_bytes())
if incoming.exists():
    stage.write_bytes(incoming.read_bytes())
    incoming.unlink()
staged_bytes = stage.read_bytes()
MBT = MB / "agents" / "chatgpt" / "outbox" / TIP
MBT.parent.mkdir(parents=True, exist_ok=True)
MBT.write_bytes(staged_bytes)

review_head = staged_bytes.decode("utf-8", "replace").split("\n")[:60]

review = {
    "artifact": "GPT_REVIEW_R13_FINAL_CONSUMED",
    "consumed_at_cn": now_cn(),
    "tip": "agents/chatgpt/outbox/" + TIP,
    "tip_bytes": len(staged_bytes),
    "tip_previous_bytes": 48946,
    "review_status": "REVIEWED_FINAL_PASS_BLOCKED",
    "verdict_as_read": {
        "FOUNDATION_ACCEPTANCE": False,
        "FORMAL_ENGINE_ADMISSION": False,
        "NEW_DATA_ACQUISITION_AUTHORIZED": False,
        "CURRENT_SWITCH_ALLOWED": False,
        "ORDER_ALLOWED": False,
        "new_repair_round_dispatched": False,
        "upload_wait_phase": "ENDED",
        "instruction": "本次不派发新的修复轮；不得由本回执或旧READY段自动续开执行",
    },
    "accepted_bounded_results": [
        "原分钟 reader 已接入；单代码探测 2026-09-11..09-24 共 10 个交易日各 30 行；09-03..09-10 六日 NO_DAY_SHARDS。认证范围仅限已测请求，不外推全证券/分钟完整性",
        "R15_REPLAY_20260924_R2 实际调用 load_staging/ingest_item/seal_release 与原 antileak，两批共 10,426 行，输出字节身份与输入对应，生产 CLEAN 指针与 SSOT 前后摘要相同。认证两批候选调用能力，不认证继承完整库/供应商完整性/全部 PIT 语义",
        "原 tip compiler 的候选调用、两个缺日出现在其输出，证据可保留",
        "原 publish_atomic 非 dry-run 已在重绑定任务目录指针上执行，published=true。仅证明本次隔离演练成功",
        "内容身份修复后，同输入 NOOP 与 9 项提交恢复情景有记录，无需为收据重跑",
    ],
    "rejection_reasons_as_read": [
        {"n": 1, "title": "原 R15 和编译器尚无同一产物贯通证明",
         "detail": "R15 真实输出 candidate/r15_releases/R15_REPLAY_20260924_R2；CONNECTED_PIPELINE 的 compiler argv 仍读 candidate/cc/CC_REPLAY_20260924/RELEASE.json；run_connected_pipeline.py 未调用 R15 runner；publish 演练另行执行。现有证据只支持各原组件分别运行",
         "status": "UNFIXED_IN_THIS_ROUND"},
        {"n": 2, "title": "V4 正式结果仍被必需输入阻断",
         "detail": "严格运行 BLOCKED_INPUT_INCOMPLETE、16 日、0 成交、0 订单、diagnostic_only=true；复权同日输入、基准/锚点一致性、历史股票池/ST、正式语义未满足；writer 游标未落地，供应商分页完整性 UNKNOWN",
         "status": "UNFIXED_IN_THIS_ROUND"},
        {"n": 3, "title": "“因子全 1 -> 供应商造假/占位 -> 必须重下”的归因不成立",
         "detail": "全 1、17 份整数日期、CACHE 稀疏只是观察事实，不能独立区分 请求复权参数/归一化基准、SDK 返回结构、本地序列化、供应商内容；源机 aux_billboard_adjust_index_minute_r15.py:110-115 为单日起止、fields=['factor']、fq=None，多年批次与单日增量横截面不同，基准可拼接性未证；provider._constant_plane_sessions 的 nunique==1 置空是本地阻断机制，不是供应商错误证书；DAILY_RAW_FACTOR_COVERAGE 目标窗标 08-05..09-24 但 per_session 仅 08-05/08-06 各 10 行，不支持整窗无可用日线来源的结论",
         "status": "CORRECTED_IN_THIS_PACKAGE"},
        {"n": 4, "title": "“V4 没有 minute get_price”不等于“不依赖盘中数据”",
         "detail": "源码同时有 get_current_data 调用，其快照字段的读取时刻与 engine 映射未判定；直接分钟调用为 0 不足以排除盘中 last_price/限价/停牌与撮合输入",
         "status": "CORRECTED_IN_THIS_PACKAGE"},
        {"n": 5, "title": "生产 CURRENT 未切换属于未开启的后续动作",
         "detail": "不作为本轮失败的唯一原因；即使立即允许切换，真实输入与同产物流转缺口不会自动消失；原发布门按最大日期放行不等于因子/历史覆盖有效",
         "status": "CORRECTED_IN_THIS_PACKAGE"},
    ],
    "corrections_applied": [
        {"target": "REPORT.md §2 / §7 / §8", "was": "supply defect; re-issue the plane (asserted necessity)",
         "now": "cause NOT established; only 'the current adjustment input and its basis are not proven to satisfy the contract' is claimed; re-acquisition is offered as one option after the contract is declared"},
        {"target": "FINAL_REQUIREMENT_MATRIX.json R2", "was": "two source-side defects + 're-issue the plane'",
         "now": "observations kept, attribution removed, cause listed as NOT_ESTABLISHED with the four candidate explanations"},
        {"target": "FINAL_REQUIREMENT_MATRIX.json / B1_B7_STATUS.json / ACCEPTANCE.json R5-B5",
         "was": "'the real chain executes (R15 -> compiler -> commit -> publish)'",
         "now": "components ran separately; R15 output is candidate/r15_releases/R15_REPLAY_20260924_R2 while the compiler consumed candidate/cc/CC_REPLAY_20260924/RELEASE.json, so no single-product chain is proven"},
        {"target": "REPORT.md §1 / §7, MINUTE_PLANE claim",
         "was": "'V4 makes 0 minute calls, so minute input is irrelevant to V4'",
         "now": "direct minute calls are 0; get_current_data snapshot dependence is unresolved and not claimed as passing"},
        {"target": "B1_B7_STATUS.json B1", "was": "constant-1.0 plane described as the supplier's identity fallback",
         "now": "the nunique==1 withhold rule is described as the local blocking mechanism, not as a vendor error certificate"},
    ],
    "what_is_not_claimed_now": [
        "that any vendor content was fabricated or is a placeholder",
        "that 2026-08-10..2026-09-24 must be re-downloaded",
        "that R15 output has flowed through the compiler",
        "that V4's intraday semantics pass",
        "that the candidate published=true supports production admission",
    ],
    "review_header_excerpt": [l for l in review_head if l.strip()][:24],
}
E.mkdir(exist_ok=True)
dump(E / "GPT_REVIEW_R13_FINAL_CONSUMED.json", review)


# --------------------------------------------------------------------- 2. the report
rp = D / "REPORT.md"
t = rp.read_text(encoding="utf-8")

t = t.replace(
    '| factor lineage | `tools/trace_factor_source.py`, `classify_factor_series.py`, '
    '`find_factor_nondate_rows.py`, `profile_corrupt_factor_dates.py` over P1/P6/CACHE | '
    'two source-side defects found, bigger than "12 sparse days" | `evidence/FACTOR_*.json` |',
    '| factor lineage | `tools/trace_factor_source.py`, `classify_factor_series.py`, '
    '`find_factor_nondate_rows.py`, `profile_corrupt_factor_dates.py` over P1/P6/CACHE | '
    'two measured anomalies (integer-date files; constant-1.0 planes) wider than "12 sparse '
    'days"; **cause not established** | `evidence/FACTOR_*.json` |'
)

t = t.replace(
    "* **Incremental adjust-factor plane 2026-08-10 … 2026-09-24**: wrong date encoding for 17 files and\n"
    "  constant `1.0` values throughout. This is the single largest blocker and it is a **supply** defect;\n"
    "  re-issuing it is an acquisition the current authority does not cover.",
    "* **Incremental adjust-factor plane 2026-08-10 … 2026-09-24**: 17 files carry a positional integer\n"
    "  `date` and the planes are constant `1.0`. This is the single largest blocker, and the **cause is\n"
    "  not established** — the same observations are compatible with the requested `fq` parameters and\n"
    "  normalisation basis, the SDK return shape, local serialisation, or the supplier content, and this\n"
    "  package does not separate them. What is established is narrower: the current adjustment input\n"
    "  and its basis are **not proven to satisfy the contract**. See §11."
)

t = t.replace(
    "1. **Re-issue the incremental adjust-factor plane** for 2026-08-10 … 2026-09-24 with a real date\n"
    "   column and real factors (acquisition), or declare the anchor-based pre-adjustment contract you\n"
    "   want. Both are recorded as measured options; neither is silently chosen here.",
    "1. **Declare the pre-adjustment contract** (anchor basis, `fq` semantics, and whether a multi-year\n"
    "   batch cross-section may be concatenated with a single-day incremental). Only after that is\n"
    "   settled does \"re-acquire 2026-08-10 … 2026-09-24\" become a meaningful action; neither branch is\n"
    "   silently chosen here, and re-download is **not** asserted as required."
)

t = t.replace(
    "* **Minute coverage**: real but only 2026-09-11 … 2026-09-24; 2026-09-03 … 09-10 is blocked.\n"
    "  Irrelevant to V4 (0 minute calls) but relevant to any intraday caller.",
    "* **Minute coverage**: real but only 2026-09-11 … 2026-09-24; 2026-09-03 … 09-10 is blocked.\n"
    "  V4 issues **direct** minute `get_price` calls: 0. That does **not** prove V4 is independent of\n"
    "  intraday data — it also makes 9 `get_current_data` snapshot calls, and the read timing of those\n"
    "  snapshot fields plus the engine's mapping of them is unresolved, so no intraday semantic passes."
)

t = t.replace(
    "| R15 ingest/clean | `formal_cleaning_r15_build_and_seal_r1.py` (`load_staging`/`ingest_item`/`seal_release`) + `r15_antileak_and_ssot_r1.py` | `R15_REPLAY_20260924_R2`, GATE PASS, production CURRENT/SSOT byte-identical | `evidence/R15_CLEANING_REPLAY.json` |",
    "| R15 ingest/clean | `formal_cleaning_r15_build_and_seal_r1.py` (`load_staging`/`ingest_item`/`seal_release`) + `r15_antileak_and_ssot_r1.py` | `R15_REPLAY_20260924_R2`, GATE PASS, production CURRENT/SSOT byte-identical. **Its output is not the compiler's input** (see §11 item 1) | `evidence/R15_CLEANING_REPLAY.json` |"
)

t = t.replace(
    "## 11. Review receipt", "## 11. Review receipt"  # no-op guard
)

if "## 11. Review receipt" not in t:
    t = t.rstrip("\n") + """

## 11. Review receipt — GPT final review `REVIEWED_FINAL_PASS_BLOCKED` (consumed 2026-10-25 13:26 +08)

The reviewer appended a leading review section to
`agents/chatgpt/outbox/BLACKBOX_FOUNDATION_R10_END_TO_END_COMPLETION_20261025.md`
(48,946 → 54,700 bytes). It **accepts the bounded results** listed in §0 and **rejects overall
acceptance**, and it explicitly dispatches **no new repair round** and closes the upload-wait phase.
Full transcription: `evidence/GPT_REVIEW_R13_FINAL_CONSUMED.json`.

Its five reasons, with what this package now says instead of what it said before:

1. **No single-product pass-through proof for R15 → compiler.** Correct, and now stated as such:
   the R15 output is `candidate/r15_releases/R15_REPLAY_20260924_R2`, while
   `CONNECTED_PIPELINE.json`'s compiler `argv` reads `candidate/cc/CC_REPLAY_20260924/RELEASE.json`;
   `run_connected_pipeline.py` never calls the R15 runner, and the publish rehearsal ran separately.
   The package proves that several original components **each** run, not that they run **as one chain**.
   This is an unfixed item of the original task, kept open as `R5_CHAIN_INTEGRITY`.
2. **V4 formally blocked.** Unchanged and agreed: `BLOCKED_INPUT_INCOMPLETE`, 16 sessions, 0 trades,
   0 orders, `diagnostic_only=true`; a completed 16-session loop is not a strategy verdict.
3. **The "all-1.0 → vendor fabrication → must re-download" attribution is withdrawn.** The
   integer-date files, the constant-1.0 planes and the sparse CACHE rows are **observations**; they
   cannot by themselves separate (a) the requested `fq` parameters and normalisation basis,
   (b) the SDK return shape, (c) local serialisation, (d) the supplier content. Two specific
   corrections: the source machine's `aux_billboard_adjust_index_minute_r15.py:110-115` requests a
   single day with `fields=['factor']`, `fq=None`, so a multi-year batch cross-section and a
   one-day incremental are **not proven concatenable**; and `provider._constant_plane_sessions`
   (`nunique == 1` → withhold) is **our** blocking rule, not a certificate that the vendor erred.
   `DAILY_RAW_FACTOR_COVERAGE.json` marks 2026-08-05…09-24 but its `per_session` holds only 08-05
   and 08-06 at 10 rows each, so it does not support "no usable daily source across the window".
   Refusing an unproven adjustment is kept; the asserted cause and the re-download remedy are not.
4. **"0 minute calls" is not "no intraday dependence".** Reworded in §1 and §7: direct minute
   calls are 0, `get_current_data` is called 9 times, and its snapshot fields' read timing and
   engine mapping are unresolved.
5. **Production `CURRENT` not switched is a later action, not this round's failure cause.** The
   gate's date-based `ALLOWED` does not make the factor/history coverage valid, so a candidate
   `published=true` supports no production admission.

Where this leaves the package: the bounded results in §0 stand as scoped; the overall verdict stays
`BLOCKED_PARTIAL_EXECUTION`; `R2` stays BLOCKED; `R5` stays PARTIAL with the chain-integrity gap now
named explicitly; `B5` keeps PARTIALLY_REPAIRED for the isolated rehearsal only. Nothing here is
re-run, and no acquisition, `CURRENT` switch or order is opened.
"""

rp.write_text(t, encoding="utf-8")


# ----------------------------------------------------------------- 3. matrix / B1..B7
matrix = load(D / "FINAL_REQUIREMENT_MATRIX.json")
r2 = matrix["requirements"]["R2_engine_data_contract_and_actual_runtime"]
r2["blocking_gap"] = (
    "ADJUST_FACTOR_PIT_R1 is not a **proven** adjustment series in the tested window. Measured "
    "observations: 17 incremental files for 2026-08-12..2026-09-02 carry a positional integer "
    "'date' (0..299) so they cannot be joined by date; every sampled incremental payload from "
    "2026-08-10 onward is factor=1.0 for every row, including files whose date dtype is correct; "
    "CACHE shows 7..89 rows for 2026-08-17..2026-09-01 and a full 5,215..5,222-row 1.0 plane for "
    "2026-09-02..2026-09-24. **Cause NOT established**: those observations cannot by themselves "
    "separate (a) the requested fq parameters and normalisation basis, (b) the SDK return shape, "
    "(c) local serialisation, (d) the supplier content. The source machine's "
    "aux_billboard_adjust_index_minute_r15.py:110-115 requests a single day with fields=['factor'], "
    "fq=None, so concatenating a multi-year batch cross-section with a one-day incremental is "
    "unproven. The formal claim is therefore limited to: the current adjustment input and its "
    "basis are not proven to satisfy the contract"
)
r2["attribution_status"] = "NOT_ESTABLISHED"
r2["withdrawn_claims"] = [
    "'the supplier fabricated a placeholder plane'",
    "'2026-08-10..2026-09-24 must be re-downloaded'",
    "'the historical batch and the incremental share one proven basis'",
]
r2["withheld_by_design"] = (
    "provider._constant_plane_sessions withholds a single-valued plane (nunique == 1). That is the "
    "local blocking mechanism, not a vendor error certificate; a genuine all-1.0 session would also "
    "be withheld, by design, rather than silently consumed"
)
r2["repair_needed"] = (
    "declare the pre-adjustment contract (anchor basis, fq semantics, batch/incremental "
    "concatenability) first; only then is a re-acquisition meaningful. No value is invented meanwhile"
)

r5 = matrix["requirements"]["R5_pipeline_reuse_and_candidate_commit"]
r5["measured"] = (
    "the original components each execute on real input, but **not as one chain**: retained "
    "transport -> original acquisition_absence_gate (PROVENANCE_GATE=PASS, "
    "SUPPLIER_COMPLETENESS=UNKNOWN) -> original inherit_tree/"
    "read_price_frame/antileak_gate -> real R15 load_staging/ingest_item/seal_release/antileak "
    "producing candidate/r15_releases/R15_REPLAY_20260924_R2 (GATE PASS) — while the connected "
    "pipeline's compiler argv consumes candidate/cc/CC_REPLAY_20260924/RELEASE.json and "
    "run_connected_pipeline.py never calls the R15 runner; the original compiler then produces a "
    "candidate release (SEAL.all_pass=true) and an immutable versioned commit (8/8 pipeline "
    "verdicts, 9/9 recovery scenarios); ORIGINAL publish_atomic was executed non-dry-run in a "
    "separate step on bound task-local targets (published=true, 0 unbound writes)"
)
r5["unproven"] = (
    "R5_CHAIN_INTEGRITY: no run in this package feeds the R15 output into the compiler and then "
    "into the publisher as one product. The source machine's R13 cleaning stage is not adopted "
    "(desktop R15 is the current entry), and a production CURRENT switch is not authorised"
)
r5["open_sub_item"] = {
    "id": "R5_CHAIN_INTEGRITY",
    "statement": "R15_REPLAY_20260924_R2 is not the compiler's --cleaning-json input",
    "reported_by": "GPT final review 2026-10-25 (REVIEWED_FINAL_PASS_BLOCKED, reason 1)",
    "would_require": "a single run whose compiler argv names the R15 release and whose publish step "
                     "consumes that same compiler release",
}
matrix["review"] = {
    "reviewed_by": "GPT",
    "review_status": "REVIEWED_FINAL_PASS_BLOCKED",
    "consumed_at_cn": now_cn(),
    "no_new_round_dispatched": True,
    "evidence": "evidence/GPT_REVIEW_R13_FINAL_CONSUMED.json",
}
matrix["revised_at"] = now_cn()
matrix["revision"] = REV
dump(D / "FINAL_REQUIREMENT_MATRIX.json", matrix)

b17 = load(D / "B1_B7_STATUS.json")
b1 = b17["items"]["B1"]
b1["failed_predicate"] = (
    "the factor plane is not a proven adjustment series in the tested window. Observed: 17 "
    "incremental source files carry a positional integer date (0..299), every sampled incremental "
    "payload from 2026-08-10 onward is a constant 1.0, CACHE holds 7..89 rows for "
    "2026-08-17..2026-09-01 and a 5,215..5,222-row 1.0 plane for 2026-09-02..2026-09-24. The cause "
    "of those observations is NOT established by this package"
)
lin = b1.get("source_lineage_measured", {})
lin["attribution_status"] = "NOT_ESTABLISHED"
lin["withdrawn_attribution"] = (
    "the earlier reading named this a supplier defect and proposed re-downloading the window. "
    "Withdrawn: the observations are equally consistent with the requested fq parameters and "
    "normalisation basis, the SDK return shape, local serialisation, or supplier content"
)
lin["cross_section_concatenation"] = {
    "source_site": "source machine aux_billboard_adjust_index_minute_r15.py:110-115",
    "request_shape": "single-day start/end, fields=['factor'], fq=None",
    "issue": "a multi-year batch cross-section and a one-day incremental are different cross "
             "sections; their basis is not proven directly concatenable",
}
lin["local_blocking_mechanism"] = (
    "provider._constant_plane_sessions nulls a plane whose factor has nunique == 1. This is a "
    "local refusal rule, not evidence about the vendor: a genuinely all-1.0 session is withheld too"
)
lin["coverage_file_limit"] = (
    "DAILY_RAW_FACTOR_COVERAGE.json marks 2026-08-05..2026-09-24 but its per_session holds only "
    "2026-08-05 and 2026-08-06 at 10 rows each, so it cannot support 'no usable daily source across "
    "the window'"
)
b1["source_lineage_measured"] = lin
b5 = b17["items"]["B5"]
b5["scope_limit"] = (
    "the rehearsal is isolated from the compiler run: it published a candidate pair seeded from "
    "production, and the compiler it graded was the cc_out release, not the R15 release. "
    "published=true therefore supports no production admission"
)
b17["review"] = matrix["review"]
b17["chain_integrity_gap"] = r5["open_sub_item"]
b17["revised_at"] = now_cn()
b17["revision"] = REV
dump(D / "B1_B7_STATUS.json", b17)


# ---------------------------------------------------------------------- 4. acceptance
acc = load(D / "ACCEPTANCE.json")
acc["generated_at_cn"] = now_cn()
acc["revision"] = REV
acc["five_requirements"] = matrix["requirements"]
acc["B1_B7"] = b17["items"]
acc["review"] = {
    **matrix["review"],
    "overall_after_review": "REVIEWED_FINAL_PASS_BLOCKED",
    "bounded_results_accepted": review["accepted_bounded_results"],
    "rejection_reasons": review["rejection_reasons_as_read"],
    "corrections_applied": review["corrections_applied"],
    "new_round_dispatched": False,
}
acc["r13_round2"]["review_items"]["2_real_r15_cleaning_and_response_gate"]["scope_limit"] = (
    "the R15 replay proves those functions run on the retained batches; it is not the compiler's "
    "input in the connected pipeline (see five_requirements.R5_pipeline_reuse_and_candidate_commit"
    ".open_sub_item)"
)
acc["r13_round2"]["review_items"]["1_minute_reader_connected_and_factor_gap_traced"]["scope_limit"] = (
    "minute: single-code probes only, no whole-universe or completeness claim; factor: observations "
    "are measurements, the cause is NOT established and re-download is not asserted"
)
acc["withdrawn_claims"] = r2["withdrawn_claims"] + [
    "'V4 is independent of intraday data because it makes 0 direct minute calls' (get_current_data "
    "snapshot dependence is unresolved)",
    "'R15 output flowed through the compiler and publisher as one chain'",
]
dump(D / "ACCEPTANCE.json", acc)

print(json.dumps({
    "review_status": "REVIEWED_FINAL_PASS_BLOCKED",
    "tip_bytes": len(staged_bytes),
    "corrections": len(review["corrections_applied"]),
    "withdrawn_claims": len(acc["withdrawn_claims"]),
    "open_sub_item": r5["open_sub_item"]["id"],
}, ensure_ascii=False, indent=2))
