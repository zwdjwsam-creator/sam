# START HERE — 台式机 AI 接入 BLACKBOX（5 分钟）

folder: `agents/desktop/inbox/BLACKBOX_DESKTOP_RUNBOOK_20261026/`
owner: 笔记本 SAM
issued_at_cn: 2026-10-26
authority: 磁盘 `E:\BLACKBOX` 上的 HAND / Manifest / CURRENT / Resolver，**不是**本文件

---

## 0. 你要先承认的三件事

1. 本手册是**导航**，不是权威。任何结论以台式机（或权威副本）磁盘上的 `HAND.txt` + `契约/必读/MUST_READ_MANIFEST_CURRENT.json` + 对应 CURRENT JSON 为准。
2. 聊天记忆、上一轮结论、别人贴的哈希，一律作废。
3. 未通过 Manifest 预检 → **禁止执行任何 BLACKBOX 程序**（读文件不算执行）。

---

## 1. 你现在只被授权做「只读接入」

以下四个开关默认全 **FALSE**，没有用户明确授权前不得翻真：

```
COPY_AUTHORIZED=false
NEW_DATA_ACQUISITION_AUTHORIZED=false
CURRENT_SWITCH_ALLOWED=false
ORDER_ALLOWED=false
```

只读接入阶段允许：读契约、跑预检、跑 `--mode status`、读 CURRENT、写回报到 HUB。
**不允许**：下载、清洗、切 CURRENT、回测、任何 QMT 下单、任何 `--run`。

---

## 2. 第一条命令（照抄）

PowerShell：

```powershell
cd E:\BLACKBOX
$env:PYTHONUTF8="1"; chcp 65001 > $null
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\blackbox_must_read_preflight_r1.py --task-class GENERAL
```

期望看到：

```
KERNEL_STATUS = VERIFIED
AUTHORITY_READY = YES
TASK_EXECUTION = ALLOWED
```

出现任一情况 → 立即停，写回报，不要继续：

- `UNKNOWN_TASK_CLASS=...`
- `KERNEL_STATUS != VERIFIED`
- `AUTHORITY_READY != YES`
- 规则 `status != VERIFIED`（= SHA 漂移，FAIL_CLOSED）

---

## 3. 第二条命令

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -u E:\BLACKBOX\脚本\run_blackbox_research_os.py --mode status
```

只读。不要加 `--run`。

---

## 4. 第三条：读当日增量终态（只读）

```powershell
E:\BLACKBOX\.venv\Scripts\python.exe -c "import json,io; d=json.load(io.open(r'E:\BLACKBOX\研究系统\数据平面\CURRENT\DAILY_DATA_MANIFEST_CURRENT.json',encoding='utf-8')); print({k:d.get(k) for k in ['manifest_id','CN_RESEARCH_DATE','ALL_LANES_READY','DAILY_INCREMENTAL_READY','DEGRADED_LANES','DATA_GENERATION_ID']}); print('JQ',{k:d['JQ'].get(k) for k in ['SOURCE_ASOF','CLEAN_ASOF','CACHE_ASOF','PIT_PASS','STATUS']})"
```

判读：

- `SOURCE_ASOF == CLEAN_ASOF == CACHE_ASOF` 才算三层齐
- `PIT_PASS=true` 才算防穿越过
- `ALL_LANES_READY=YES` 且 `DEGRADED_LANES=[]` 才算六 Lane 终态
- `DEGRADED` 非空 → 视为 **未终态**，不得说「数据已就绪」

---

## 5. 十条红线（违反即事故）

1. 禁止 `EMPTY → NO_DATA`。存在性只能由 `脚本/blackbox_data_absence_gate_r1.py` 出封闭枚举。
2. 禁止猜路径、禁止 glob/first_match 代表全产品覆盖。
3. 禁止原地改 `sealed` / `CURRENT` / RAW；只能发 successor 再切指针。
4. 禁止为回测调用 QMT `download_history`。
5. 禁止回测 RAW fallback。
6. 禁止把 `returned_rows == 5000` / `== query_cap` 当 COMPLETE。
7. 禁止把外源证据写进 JQ 产品目录。
8. 禁止打印/提交密钥、账号、token、订阅链接。
9. 无 `LIVE_EXECUTION_SESSION` 不得任何下单。
10. 禁止修改以太网 2 / `192.168.100.2/24` / SMB / 台式机共享。

---

## 6. 完整手册在哪

| 文件 | 用途 |
|---|---|
| `BLACKBOX_DESKTOP_AI_RUNBOOK_R1.md` | **主手册**：所有程序运行前的先前条件 |
| `DAILY_INCREMENTAL_RUNBOOK.md` | 增量数据六 Lane 全流程 + 验收 + 异常处置 |
| `PRECONDITION_MATRIX.csv` | 任务类别 → 必读 → 门 → 红线（速查） |
| `MANIFEST.json` | 本包文件清单 + SHA256 + 权威版本号 |

---

## 7. 回报（必须）

完成后写 `agents/chatgpt/inbox/<你的任务目录>/DESKTOP_REPORT.md`，字段：

```
TASK_ID
EXECUTION_HOST=DESKTOP_ZHANGWEI
ACCESS_MODE=LOCAL_FULL | READ_ONLY_OVER_SMB
TASK_CLASS
PREFLIGHT=KERNEL_STATUS/AUTHORITY_READY/TASK_EXECUTION
MANIFEST_ID
ASOF=SOURCE/CLEAN/CACHE
PIT_PASS
LANES=PASS|DEGRADED(list)
GATES=DATA_ABSENCE/COVERAGE/...
ACTIONS=...
ARTIFACTS=path + sha256
BLOCKERS=...
NEXT=WAITING_FOR_USER | DONE
```

**没跑过的门不许写 PASS。** 没验证过的 asof 不许写 YES。
