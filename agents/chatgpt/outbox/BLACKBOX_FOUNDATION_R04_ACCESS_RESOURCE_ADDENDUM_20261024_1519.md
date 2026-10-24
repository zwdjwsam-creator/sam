# R04 addendum: source access, credential locations and realistic acquisition capability

HOST: ZHANGWEI
PARENT_TASK: BLACKBOX_FOUNDATION_R04_OF_10_GPT_PATCH_AND_COMPLETE_CONTRACT_HANDOFF_20261024_1455
BUDGET_SLOT: 4/10 (same task; NO additional cycle)
REMAINING_CYCLES_AFTER_R04: 6
DELIVERY: append to agents/chatgpt/inbox/BLACKBOX_FOUNDATION_20261024_R04/access_resources/
FOUNDATION_ACCEPTANCE: false
ORDER_ALLOWED: false
PRODUCTION_CHANGE_AUTHORIZED: false
LANGUAGE: en

## 1. User goal and precedence

Merge this addendum with the preceding R04 contract. GPT owns semantic fixes and integration code. The local operator inventories and queries evidence and executes explicit contracts. Do not design a new download mechanism, invent an authentication route, buy a subscription, obtain a new paid API, bypass permissions, or redefine the required data universe.

The objective is the same functioning desktop foundation with repeatable updates. Resource limits mean work with demonstrably available data and existing entitlements; disclose gaps and exclusions accurately. Do not spend remaining cycles trying to obtain every imaginable dataset.

R04 has already uploaded its first delivery. Preserve that delivery and append these findings to the same round. Do not rerun the completed patch or native read, create another round ID, or wait for a new approval per provider. GPT can review the existing contract sources while this bounded supplement is collected.

## 2. Receipt of R04, and limits of current evidence

GPT received ROUND_STATUS, PATCH_EXECUTION, DELTA_REPORT_R4, NEXT_MISSING_EVIDENCE_R4, CONTRACT_CONFLICTS and CONTRACT_SOURCE_MANIFEST. The recorded normalized candidate hashes match GPT's patch output, the nine synthetic checks pass, and the native three-day daily diagnostic returns a DataFrame. This acknowledges the reported bounded patch execution, not full engine/data/update acceptance.

The manifest records 98 resolved declared items, but agent_read_status is FULL=11, PARTIAL=16, NOT_READ=71. Zero missing declared paths does not prove every authoritative dependency is resolved or read. Retain these honest fields; do not rename hashed/staged bodies as fully reviewed contracts.

R04-C10 reports missing CLEAN rows for 000001.XSHE on 2026-08-31 and 2026-09-01. This is not yet proof that RAW is absent, that the entire market is absent, that migration lost files, or that the supplier cannot provide the dates. Trace only the relevant existing RAW/CLEAN records, established producer manifests and admission decisions for these exact dates. Record which layer is missing and whether the reason is proven. Do not launch another full scan or repair by guess.

## 3. Existing sources to reuse

Read the actual downloader sources/configuration references before claiming that credentials are located or a source is usable. Reuse:
- R03 ecology registry (54 dataset entries) and existing source/provenance/coverage findings.
- R04 source_contracts/S1_ENGINE_RULE_LIBRARY/jqdata_download_route_CURRENT.json.
- R04 source_contracts/S1_ENGINE_RULE_LIBRARY/jqdata_official_permission_matrix_CURRENT.csv.
- R04 source_contracts/S4_UPDATE_PUBLICATION/BLACKBOX_HAND_FULL_DATA_UPDATE_SCOPE_R2.json.
- R04 source_contracts/S4_UPDATE_PUBLICATION/BLACKBOX_HAND_DAILY_INCREMENTAL_UPDATE_WITH_SW_L123_CACHE_R1.json.
- R04 source_contracts/S4_UPDATE_PUBLICATION/BLACKBOX_HAND_JQ_INCREMENTAL_DOWNLOAD_RULE_R1.json.
- R04 source_contracts/S4_UPDATE_PUBLICATION/DATA_PLANE_PATH_MAP.json.
- Existing full external-evidence, Tushare convertible-bond, FUND_NAV and incremental updater code already in HUB; copy only missing directly referenced helper bodies.
- Existing known configuration and secret-store references from the active workspace; do not scan unrelated disks or extract browser cookies.

The staged engine env_loader.py names JQDATA_USERNAME, JQDATA_PASSWORD, JQDATA_SERVER, JQDATA_PORT, TUSHARE_TOKEN and TUSHARE_CUSTOM_URL. Its load_env() can search upward from CWD and the module auto-loads on import. This proves configuration names/loader behavior only. It does NOT prove those variables are populated, identify the downloader's actual configuration, validate an endpoint, or prove account permissions. Inspect it statically; do not import it just to inventory credentials.

The historical permission matrix includes a successful FUND_NET_VALUE response with zero rows and an unsupported refactor_net_value info parameter. Neither means a complete downloadable dataset. FUND_NAV's allowed route remains the evidenced get_extras contract; do not substitute an unrestricted whole-table query.

## 4. Deliver one source-access register, without secret values

Create SOURCE_ACCESS_REGISTER.json plus a concise English ACCESS_AND_DOWNLOAD_RUNBOOK.md.
One source entry may serve many datasets; link them by source_id instead of duplicating credential information.

For each actual source used by the required ecology, record:

- source_id, supplier, source/provenance category and covered dataset IDs.
- Actual official website/login page, API/base endpoint or local-terminal route as declared by installed SDK/configuration or existing trusted source documentation. Record evidence and observation time. A public website and the actual configured API endpoint may differ. Unknown URLs remain null with a named reason.
- Authentication method: username/password, token, existing web session, local terminal session, public/no-auth, or manual document import. Distinguish web login from SDK/API authentication.
- Desktop credential_locator: exact config/secret-store path and key names or environment variable names, with the host and execution account context; record existence, readability by the intended runtime, nonempty value presence and explicit loader precedence. Keep username/account values masked.
- Whether the credential is present only on the notebook or referenced through a retained D/C configuration. A path pointing to another machine is not desktop-ready. Record the existing authorized access route, if any, rather than copying secrets.
- Actual loader function and downloader script/callable, required interpreter/dependencies, necessary configuration keys, login/auth initialization and intended download command with placeholders or locator references, never literal passwords.
- Entitlement/product scope, historical depth, update lag, expiry if observed, quota/rate/pagination limits and pricing only where already evidenced. Unobserved facts stay UNKNOWN.
- Latest existing successful/failed authentication, entitlement and bounded read evidence with timestamps, host, exact dataset/window and scope. An old result is historical, not current proof.
- Current blocker and precise remedy: missing credential, desktop path binding, dependency, endpoint/network, expired entitlement, quota, unsupported API, data not offered, policy exclusion, manual-only source, or unresolved evidence.
- Secrets must be resolvable locally by the intended loader without being printed. Inventory may read key names and determine presence/loader readability locally; do not send values, tokens, passwords, cookies, auth headers or signed URLs to HUB or GPT. Do not hash password/token values or display even a short secret prefix. Use an opaque credential_id and locator reference.
- If the operator cannot safely confirm a dynamic secret reference without executing configuration code, report DYNAMIC_RESOLUTION_NOT_VERIFIED and provide the static loader/source for GPT review. Do not execute unknown credential scripts.

Do not assume an engine credential is also the updater credential. Explicitly identify the actual downloader configuration. Do not use browser authentication success as proof that the API or a paid table is available.

The runbook must enable an authorized local operator to locate the credential, start the correct runtime, connect/login, check entitlement, choose a bounded date scope and download through the approved candidate workflow. Write exact commands only when source-proven and safe; otherwise provide the exact missing callable/configuration needed for GPT to author the command. Unproven routes must not be labelled executable.

## 5. Dataset possession, acquisition and policy are separate axes

Create DATA_ACQUISITION_MATRIX.json, joining the existing registry and required update scopes. Include the already-required/external sources; do not add unrelated products merely because they exist online.

Each row must include:
dataset_id, source_id, asset/domain/frequency, authority/contract references, declared required scope, existing RAW/CLEAN/CACHE/FACTOR_DICTIONARY/FACTOR_VALUES/STRATEGY_OUTPUT layer roots, previous validated coverage evidence, known gaps, schema/provenance/engine eligibility status, acquisition status, policy status, resource constraints, and next contracted action.

A. Possession:
- PRESENT_COMPLETE_FOR_DECLARED_SCOPE: only with scope-specific existing proof.
- PRESENT_PARTIAL: evidence of a bounded missing interval/field/security/layer.
- PRESENT_COVERAGE_UNVERIFIED: files or an observed min/max are insufficient.
- NOT_PRESENT_IN_CHECKED_SCOPE: name the bounded checked scope; do not assert global absence.
- DERIVED_OR_VIRTUAL: list real source dependencies rather than requesting a nonexistent raw table.

B. Acquisition status:
- VERIFIED_CURRENT_ACCESS: recent desktop authentication + relevant entitlement + successful bounded retrieval are all evidenced; state the exact tested scope and timestamp. This does not prove unlimited/full-history capability.
- HISTORICAL_ACCESS_ONLY: prior successful evidence, current access not tested.
- CONFIGURED_NOT_VERIFIED: locator/script/endpoint present; current access unknown.
- AVAILABLE_AFTER_LOCAL_FIX: precise evidenced local configuration/dependency repair, entitlement still separately stated.
- DENIED_BY_CURRENT_ENTITLEMENT: concrete permission response; no purchase in this task.
- QUOTA_OR_RATE_LIMITED: observed remaining constraint, resumable plan needed.
- AUTH_OR_SESSION_UNAVAILABLE: actual missing/inaccessible/expired local authentication evidence.
- SOURCE_UNSUPPORTED_OR_NOT_OFFERED: supplier/documented API evidence, not an empty response.
- MANUAL_OR_LICENSED_DOCUMENT_ONLY: distinguish metadata/summary/full text permissions.
- UNVERIFIED: do not force a can/cannot label without evidence.

C. Policy:
REQUIRED / CONDITIONAL / DEFERRED / NOT_REQUIRED / FORBIDDEN / AUTHORITY_CONFLICT.
A technically accessible dataset may still be forbidden or unnecessary.
A currently inaccessible required dataset is an explicit capability exception, not a silent PASS.
A free alternative is not equivalent lineage/fields/PIT coverage until GPT approves its exact mapping.
A formula/recomputed factor is not the supplier's downloaded factor value; label it derived.

No response with zero rows, cap-hit, partial pagination, failed request or timeout may be used as proof of NO_DATA or supplier impossibility. No unobserved entitlement should be guessed from a token file.

## 6. Preserve and clarify conflicting policies; do not choose by guess

The full R2 scope body now visible in HUB contains amendments requiring full_factor_values_library and TARGET_REQUIRED+REPROBE for jq260, with old blanket forbids described as obsolete. The daily child rule also contains permission_blocked_skip_sealed/permission_skip_domains for these products and money_flow, while the engine MASTER still blocks factor-value ingestion. The route snapshot is dated June and has many old pending/paused statuses.

Do not reduce all of these to 'permanently impossible' or 'now approved'. Add the exact clauses, referenced amendment/source and observed entitlement evidence to CONTRACT_CONFLICTS as AUTHORITY_CONFLICT. Distinguish:
- target need;
- download permission and current practical availability;
- local acquisition authorization;
- permission to admit values into the engine.

Find the exact referenced BLACKBOX_HAND_FULL_DATA_DOMAIN_STATUS_AMEND_R3 and any later permission seal through existing indexes; upload the missing full bodies only. GPT will reconcile applicable authority from full evidence. This supplement does not itself lift any factor-value prohibition or authorize a permission probe of blocked modules.

## 7. Bounded execution and resource discipline

This addendum authorizes local read-only configuration/credential-locator inventory and an English runbook/resource matrix only. It does not authorize dumping credentials, new login attempts, quota consumption, paid API probes, business-data download, global dependency installation, secret migration, QMT brokerage access, or production writes. Reuse existing authenticated-test evidence and mark its date; untested current access remains UNVERIFIED/HISTORICAL.

For sources lacking current proof, provide the already-existing safe probe entry and full source or the exact missing interface. GPT will write one bounded source-access verification contract together with the forthcoming updater integration, before downloading. This prevents arbitrary probing and is not a request for the user to manually manage accounts.

Prioritize currently present data and confirmed existing resources. No new subscription, no price comparison project, no whole-history redownload, no repeated permission retries, no silent switch of provider, no idle polling for unavailable sources. A resource blocker must not prevent work on independent available domains.

## 8. Supplement delivery and concise completion

Append these five small artifacts, plus only missing relevant source bodies:
- SOURCE_ACCESS_REGISTER.json
- DATA_ACQUISITION_MATRIX.json
- ACCESS_AND_DOWNLOAD_RUNBOOK.md
- ACCESS_EVIDENCE_INDEX.json (evidence time/host/scope; secret-free)
- SUPPLEMENT_STATUS.json (parent R04, additional_rounds_consumed=0, current-proof versus historical counts)

Keep the original R04 evidence unchanged. Update the HUB pointer to this supplement and identify which files are new. Read back the uploaded files. Do not label an unknown source 'available' to make the table complete. Do not rewrite original contracts or downloaded data.

New narratives, status text, comments and reports are English; literal paths and original contract evidence retain their original bytes/language with English annotations. No large report in Cursor chat. After successful upload and readback, the final response is exactly END.
