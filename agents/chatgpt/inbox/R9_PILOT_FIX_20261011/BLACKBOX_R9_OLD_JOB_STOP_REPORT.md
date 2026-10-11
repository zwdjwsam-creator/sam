# BLACKBOX R9 — 旧 R8 任务停止核验报告（复核）

| 项 | 值 |
|----|-----|
| 核验时间 | **2026-10-11T09:01:37+08:00** |
| 主机 | **ZHANGWEI**（台式机 Cursor） |
| 旧 RUN_ID | `20261010_173201_R8_3B85D677` |
| 运行目录 | `C:\LAN_SHARE_REPORT\BLACKBOX_MIGRATION_RUN_20261010_173201_R8_3B85D677` |
| 既有停止动作时间 | 2026-10-11T08:00:28+08:00（见 `R9_STOP_SNAPSHOT\`） |
| 本轮动作 | **仅核验与补充证据；未重复停止；未启动复制/1GiB 实验/全量迁移** |

```text
OLD_R8_FULL_COPY_ALLOWED=FALSE
R9_PILOT_ALLOWED=TRUE
FULL_MIGRATION_ALLOWED=FALSE
SOURCE_OLD_FREEZE_READY_REUSE=FALSE
```

复核 JSON：`...\R9_STOP_REVERIFY.json`

---

## 1. 目标卷身份

| 项 | 值 |
|----|-----|
| 盘符 | E: |
| FileSystemLabel | **MarketData** |
| FileSystem | NTFS |
| UniqueId | `\\?\Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}\` |
| Size | 4000769372160 |
| SizeRemaining | 4000538427392（**3725.792 GiB**） |
| HealthStatus | Healthy |
| E:\ 顶层（非递归） | 仅 `System Volume Information` |

与 R8 Stage A / 开拷前记录的 MarketData 卷一致。

---

## 2. 已识别旧进程及识别依据（命令行 / 父子，非盲杀 PID）

### 2.1 历史身份（2026-10-11 08:00 停止前快照）

识别规则：完整 `CommandLine` 必须匹配角色脚本路径 **且** 含 RUN_ID，或 ln 匹配  
`--traditional` + `\\192.168.100.2\E_DRIVE\BLACKBOX` + `E:\BLACKBOX`。

| 角色 | PID | PPID（快照时） | 启动/状态（停止前） | 识别依据 |
|------|-----|----------------|---------------------|----------|
| ln.exe | 40756 | （wrapper 树） | CPU≈989s / WS≈2274MB | `C:\Tools\ln\ln.exe --traditional --progress --anchor E:\BLACKBOX --destination E:\BLACKBOX --copy \\192.168.100.2\E_DRIVE\BLACKBOX E:\BLACKBOX` |
| wrapper | 33076 | — | powershell | `...\BLACKBOX_R8_E_COPY_PROGRESS_WRAPPER.ps1` + RUN_ID |
| Watchdog | 14732 | — | powershell | `...\BLACKBOX_R8_E_COPY_WATCHDOG.ps1` + RUN_ID |
| Capacity Observer | 39044 | — | powershell | `...\BLACKBOX_R8_E_COPY_CAPACITY_OBSERVER.ps1` + RUN_ID |
| Exit Waiter | 18608 | — | **停止前已不在运行** | PID 文件有记录；现场无进程 |

证据：`R9_STOP_SNAPSHOT\PROCESS_SNAPSHOT_20261011_080002.json`、`R8_STOP_CANDIDATES_*.json`、`STOP_ACTIONS_*.json`

### 2.2 本次复核（09:01）现场扫描

对全部 `Win32_Process` 按上述规则扫描：

| 检查 | 结果 |
|------|------|
| 存活 R8 ln / wrapper / watchdog / observer / exit_waiter | **0** |
| 任意 `ln.exe` | **无** |
| 历史 PID 文件中的 40756/33076/14732/39044/18608 | **均 process_alive=False**（仅作对照，**未**据此杀进程） |

→ **旧任务已退出；本轮不重复停止。**

---

## 3. 停止动作与结果

| 时间 | 动作 | 结果 |
|------|------|------|
| 08:00:28 | 身份核对后 `Stop-Process`：40756→33076→14732→39044 | wrapper/watchdog/observer：立即退出；ln 在动作瞬间 `still_alive` 曾为 true，同秒后 `POST_STOP_VERIFY` 已 `remain_ln` 空 |
| 08:00:28+ | 标记 `SUPERSEDED_BY_R9` | 已写 JSON/MD；**不伪造成功** |
| 09:01:37 | 复核 | 无残留 R8 复制/监控进程；无新 ln |

受控停止机制：无 ln 官方 cancel API；采用「命令行身份匹配后方可 Stop-Process」。脚本文件仍保留在 RUN 目录（供审计），**当前无进程在执行它们**。

### 自动重启入口

| 检查 | 结果 |
|------|------|
| 同命令行 ln / R8 E_COPY 脚本进程 | 无 |
| 计划任务名含 BLACKBOX/R8/E_COPY 且指向本 RUN | **未发现** |
| 命中任务 `BlackboxCheckTemp` | `C:\DEV\check_blackbox.ps1` → 会话检查，**非**本 R8 复制重启入口；上次运行 2026-06-27 |

---

## 4. 残留检查

```text
OLD_LN_STOPPED=TRUE
OLD_WRAPPER_STOPPED=TRUE
OLD_MONITORS_INACTIVE=TRUE
```

依据：09:01 全进程命令行扫描无匹配；历史 PID 均不存活；`Get-Process ln` 为空。

源端旧冻结 / READY：**不得直接沿用**（`SOURCE_OLD_FREEZE_READY_REUSE=FALSE`）。本轮**未**设置新的全量复制许可。

---

## 5. 目标目录现状

| 路径 | 状态 |
|------|------|
| `E:\BLACKBOX` | **不存在** |
| 落盘文件 | **无**（未做全盘递归；仅查 E:\ 顶层与 `Test-Path E:\BLACKBOX`） |
| 相对 R8 开拷基线占用增量 | **0 GiB**（SizeRemaining 仍为 4000538427392） |

若曾有半成品：本策略为保留不删——当前无半成品。

---

## 6. 日志与证据位置

| 类别 | 路径 |
|------|------|
| 本报告 | `C:\LAN_SHARE_REPORT\BLACKBOX_R9_OLD_JOB_STOP_REPORT.md` |
| 停止快照目录 | `...\BLACKBOX_MIGRATION_RUN_20261010_173201_R8_3B85D677\R9_STOP_SNAPSHOT\`（20 个保存文件） |
| 复核 JSON | `...\R9_STOP_REVERIFY.json` |
| 进度/看门狗/容量日志副本 | `R9_STOP_SNAPSHOT\E_COPY_*.saved_20261011_080002` |
| 原进度日志 | `...\E_COPY_LN_PROGRESS.log` |
| SUPERSEDED 标记 | `...\R8_SUPERSEDED_BY_R9.json` / `.md`；`C:\LAN_SHARE_REPORT\R8_SUPERSEDED_BY_R9.json` |
| 原 T0/READY/STOP/StageA | 仍在 `C:\LAN_SHARE_REPORT\` 与 RUN 目录（未伪造成功） |

---

## 7. 已有 R9 / 实验相关材料（只收集，不重跑）

| 路径 | 说明 |
|------|------|
| `C:\LAN_SHARE_REPORT\INDEX_LOCAL_R2\filesystem_inventory.sqlite` | 只读索引副本，≈8.73 GiB，mtime 2026-10-10 |
| `C:\LAN_SHARE_REPORT\ln_content_pilot_107b_RESULT.md` | 既有小规模 content pilot 结果（10-10） |
| `...\ln_content_pilot_step1_full.json` / `step2_junction.json` | 同上配套 JSON |
| `...\BLACKBOX_R9_OLD_JOB_STOP_REPORT.md` | 本停止/核验报告 |
| `...\R9_STOP_SNAPSHOT\` | 旧任务停止证据包 |

**未发现**已创建的 R9 1GiB 实验目标目录（探测：`F:\BLACKBOX_R9`、`F:\R9_PILOT`、`E:\BLACKBOX_R9`、`E:\R9_PILOT`、`C:\LAN_SHARE_REPORT\R9_PILOT`、`C:\LAN_SHARE_REPORT\BLACKBOX_R9_PILOT` 均不存在）。  
未覆盖、未清理任何已有材料。本轮**不**启动 1GiB 实验。

---

## 8. 必填结论（仅实际核验成立项）

```text
OLD_LN_STOPPED=TRUE
OLD_WRAPPER_STOPPED=TRUE
OLD_MONITORS_INACTIVE=TRUE
E_TARGET_CURRENT_STATUS=E:\BLACKBOX_ABSENT; MarketData; Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}; free_GiB=3725.792; used_delta_GiB=0
SOURCE_INDEX_AVAILABLE=TRUE
READY_FOR_R9_INVENTORY=TRUE
SAFE_TO_SHUTDOWN_OLD_JOB=TRUE
STOP_ACTION_THIS_PASS=NONE_ALREADY_EXITED
```

等待 ChatGPT 审核。不启动 1GiB 实验或全量迁移。
