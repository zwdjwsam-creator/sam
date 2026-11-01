# BLACKBOX_HISTORICAL_CALENDAR_FREEZE_20261101 — EXECUTED, FROZEN_OBSERVATION_AWAITING_GPT

execution_host = ZHANGWEI
TASK_CLASS     = DATA
STATUS         = EXECUTED_NATIVE_SUCCESS_PENDING_GPT
ORDER_ALLOWED  = false
calendar_admission = false
policy_calendar_replaced = false

## 1. 结论

单次本地原生读取**已执行成功**（非推断）：launcher 与 capture 子进程实际退出均为 0，
`CAPTURE_RESULT.status = FROZEN_OBSERVATION_AWAITING_GPT`。这是原生成功，按契约不等同于
GPT 已接受；`calendar_admission` / `historical_availability_established` / `orders_allowed` 全为 false。

源件 24,616 B / full SHA256 `d044d628279d48c1644eb7913af9e45d27d17b04b086f6d316936e31d6eddcea`，
与登记前缀 `d044d628279d48c1` 一致；读取前后字节相同，size/dev/ino/mtime_ns 稳定。
行数 3,097，首 2014-01-02，末 2026-09-24，与历史登记观测（3097/2014-01-02/2026-09-24）一致。

契约里全量 SHA256 标注为 `NOT_YET_MEASURED`；本次首次测得完整值，仅为本次观测结果，
不构成重新钉选（未写入任何 pin 文件）。按契约，这是一个待 GPT 独立核对的观测，不是完整性证明。

## 2. 不可变调度提交

- 调度提交：`046bf0a8dd615f20800499918ec5d3fee9a8086e`（committer 时间 2026-11-01T14:18:37Z）
- 该提交同时包含 outbox 任务 TXT 与 production package，取交集后唯一。
- 暂存时 main 头 == `046bf0a8…`；全部运行时字节按 `?ref=046bf0a8…` 取，未用 main/raw 移动地址。
- 评审基线：`7cde25187428957f372e9a80d8967d660b53c9f3`（原始 draft 未变）。

## 3. 包暂存（C: only，未预建运行根）

目录：`C:\LAN_SHARE_REPORT\BLACKBOX_HISTORICAL_CALENDAR_FREEZE_20261101_PACKAGE\package`

| 文件 | bytes | SHA256 |
|---|---|---|
| PACKAGE.json | 1267 | `0c2959a70c8d2c4e6db78143dd525ec1b46e246c6fa3ac5a9fedd579519782ec` |
| CALENDAR_FREEZE_CONTRACT.json | 1501 | `379aaa5de7972f02979fc87d60dc41824c232c74ba8e7150d31093f30ceb69d1` |
| RULE_PINS.json | 1165 | `860f224dfc1382b8f71d9c64333b2170c891694dc3d541a9b34c870a3a3f448d` |
| freeze_calendar.py | 6793 | `80f1001272f4a5ae2dc1c83cb195dada9af97a9647b063e676b1aecef62ea300` |
| launch_calendar.py | 1325 | `99086af16579eaad0907c91b47429a4bb02c725edfa4d2802a9866b66226ca2e` |
| package_guard.py | 2194 | `a5ab28fee07f1ad9cb6ef09e8f60aeb205d38e212475ab15d81cc71cb6fab194` |
| prepare_ack.py | 913 | `f845724d75ab3e0cb76e62f1dd8f47efe0b8b2c9e0eabbe8d871dbf2ca7d5814` |
| test_calendar.py | 6617 | `73d5869c6aa02d46c5d6fe9c88eaeb01f6f4b795178f47b8b4c118a9fd98c961` |

PACKAGE.json 实得 bytes/SHA256 与契约钉选逐字节相同；目录精确为这 8 个文件，无 extras、无缺失；
7 个 payload 逐一按清单长度/SHA256 校验全 PASS。未做换行/编码归一化，未本地重生成 pin。

## 4. 命令与实际退出（均为实测，非推断）

| 步骤 | 命令 | 实际退出 | 区间（UTC） |
|---|---|---|---|
| ACK | `…\package\prepare_ack.py` | **0** | 2026-11-01T14:21:31.053Z（落盘），elapsed 589 ms |
| 启动 | `…\package\launch_calendar.py` | **0**（shell 观测） | 14:21:53.681 → 14:21:54.964，elapsed 1440 ms |
| capture 子进程 | `…\package\freeze_calendar.py` | **0** | 14:21:53.681 → 14:21:54.964 |
| preflight | `脚本\blackbox_must_read_preflight_r1.py --task-class DATA` | **0** | 14:21:53.833 → 14:21:53.909 |
| 原生测试 | `…\package\test_calendar.py` | **0** | 14:21:53.916 → 14:21:54.925 |

执行前两次确认两个运行根均不存在；执行后未删除、未重建、未加后缀、未重跑。

## 5. 两道门

preflight 原文（`preflight.stdout.txt`，未改写）：
```
MUST_READ_PRECHECK = PASS
TASK_CLASS = DATA
KERNEL_SHA256 = b05a69958e29f7c90cf1ea794a4c437d36120bb960515ce9e26d3f4d5bdf197a
KERNEL_STATUS = VERIFIED
KERNEL_BYTES = 1167
HAND_READ = NOT_SUFFICIENT
AUTHORITY_READY = YES
TASK_EXECUTION = ALLOWED
TASK_EXECUTION_FORBIDDEN = FALSE
```
`HAND_READ = NOT_SUFFICIENT` 按原文保留，其含义未被重写。BOOTSTRAP / DATA_ACCESS 两个 expected 与 actual SHA256 相同，均 VERIFIED。

原生测试：`Ran 25 tests in 0.781s` → `OK`，0 failures / 0 errors / 0 skips，实际退出 0。
测试隔离在 C: `result_001/fixture_tmp`，运行后该目录存在且为空（未删除、未复用、未当文件计数）。

## 6. 六个运行 pin（RULES_BEFORE == RULES_AFTER）

| 路径 | bytes | SHA256 | 执行前 | 执行后 |
|---|---|---|---|---|
| `脚本\blackbox_must_read_preflight_r1.py` | 11767 | `3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217` | OK | OK |
| `脚本\_base.py` | 11800 | `b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258` | OK | OK |
| `.cursor\rules\BLACKBOX_KERNEL_ALWAYS_APPLY.mdc` | 1167 | `b05a69958e29f7c90cf1ea794a4c437d36120bb960515ce9e26d3f4d5bdf197a` | OK | OK |
| `契约\必读\MUST_READ_MANIFEST_CURRENT.json` | 2943 | `572309831371bd5171afad5ca5ef5a70900b8a151245af0174e773ff04102c08` | OK | OK |
| `契约\必读\BLACKBOX_BOOTSTRAP_MUST_READ.md` | 1570 | `704527e0ee7545680cbc3d23962843e4827e0bf380e18b6dd31dfc631ed5c406` | OK | OK |
| `契约\必读\BLACKBOX_DATA_ACCESS_MUST_READ.md` | 6911 | `0903551847881b0c04d9502fe49c4361e9799a69ba327cccd15b6fbacdf4f1c8` | OK | OK |

`RULES_BEFORE.json` 与 `RULES_AFTER.json` 字节相同（942 B，`3a443a3dfd04c93186f4449a741a0a046b563111ed1cc3beeb9427f98d88fea7`）。
未触及 ACQUISITION / BACKTEST / QMT 规则，未运行额外程序。

## 7. 源件与序列

- 路径（唯一，未发现/未选择其他日历）：`E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw\P0_meta\calendar_cn_exchange\calendar_cn_exchange_v2_asof_20260924\CALENDAR_TRADE_DAYS.parquet`
- bytes 24,616（上限 67,108,864，远低于），full SHA256 `d044d628279d48c1644eb7913af9e45d27d17b04b086f6d316936e31d6eddcea`
- 读取前后严格字节相等，且 `(size, st_dev, st_ino, st_mtime_ns)` 四元组不变
- 行数 3,097；首 2014-01-02；末 2026-09-24
- 仅读 `trade_date` 列，物理行序原样保留；无别名、无 ordinal 日期轴猜测、无排序/去重/补缺/时区换算
- 校验：非空、无 NULL、无重复（3097 唯一）、严格升序、全部为午夜、tz 未绑定或 +08:00 均放行、类型合法
- Arrow schema：`trade_date: timestamp[ms]`
- 原始 Parquet body 未被复制或上传（`no_original_body_copy = true`）

2026 尾部连续序列：`09-15, 09-16, 09-17, 09-18, 09-21, 09-22, 09-23, 09-24`。
`2026-09-25`（周五）**不在**日历中，`09-24` 位于物理位置 3096/3096（末行）。

## 8. 与 09-25 休市的外部核验

上交所 2025-12-22 年度休市公告：中秋 09-25..09-27 休市、09-28 恢复交易。
这与本节第 7 段冻结序列一致（09-24 为末个交易日，09-25 缺位）。
按契约，该公告**只是印证**，不是新的原生输入，也未据此修改供应商日历或扩展政策日历。
日历仅止于 09-24，本身无法证明其后续；接缝需另行钉选的后续序列，未在此推断。

## 9. 产出文件（emitted / not-emitted）

已产出 11 个（`capture/result_001/`）：RULES_BEFORE.json, PREFLIGHT_RUN.json, preflight.stdout.txt,
preflight.stderr.txt (0 B), TEST_RUN.json, tests.stdout.txt (0 B), tests.stderr.txt, SOURCE_IDENTITY.json,
TRADE_DAY_SEQUENCE.json, CAPTURE_RESULT.json, RULES_AFTER.json，另加 LOCAL_READBACK.json（本地回读，共 12 个文件名；UPLOAD 前 11 个被自述）。

条件文件 `FAILED.json`：**not emitted**（成功路径无该文件，非缺失、非丢失）。
`fixture_tmp` 为空目录，不作为文件上传。

OUTER 四件（`outer/`）：RUN_ONCE.json (81 B), OUTER.stdout.txt (0 B), OUTER.stderr.txt (0 B), OUTER_RUN.json (284 B)。

## 10. 作用域偏离与仍未准入

未发生偏离：未清洗、未读价格、未做获取/认证/配额探测、未重跑 P1/P2/P3、未激活 consumer、
未做研究/回测、未改 CURRENT/HAND/watchdog、未发布、未下单。SAM 未参与。E: 侧仅读那 1 个日历与 6 个已钉选操作文件。

仍未准入：POLICY_P1 未修订；供应商历史可用性未被证明；10-27 未解决；
历史费率表、公司行动、证券/带日期手数/最小变动价位规则、字段单位仍为独立待办。
回测、研究、CURRENT/发布、RCID 缺陷关闭、下单全部保持关闭。

## 11. 证据边界

本报告区分“原生源件重读证据”（源字节相等 + 四元组稳定 + 哈希/行数/序）与“全系统写入/进程审计”。
**未主张**任何全系统审计：未对进程表做跨会话检查、未对全盘写入做旁路监控，仅用已知本地进程
元数据确认无同任务进程，并以运行根是否存在作单次执行判据。

## 12. 传输

ACK 于执行前上传至 `agents/chatgpt/inbox/BLACKBOX_HISTORY_CALENDAR_FREEZE_20261101/ZHANGWEI/ACK.json`
（1,420 B，SHA256 `f3226c765d06930f3dd9ea19ced909bb59856cf8ac06e47e76a3508265d9e13a`，blob `22f9c87f63f403e0845c6bb91ce9fd4ae973f31a`），
回读字节相等后**才**启动。未记录任何口令/token/cookie 或其派生哈希。
