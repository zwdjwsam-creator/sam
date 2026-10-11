# R9 ZHANGWEI — 进程阻塞核实与条件式实测（本轮）

任务ID：`R9_DESKTOP_PROCESS_RESOLVE_20261011`  
执行主机：`ZHANGWEI`  
核验时间：2026-10-11T12:18:09+08:00  
HUB 指令：`INBOX_FOR_DESKTOP.md`

```text
COPY_STARTED=NOT_RUN
COPY_OK=NOT_RUN
ACCEPTANCE_PASS=NOT_RUN
PREFLIGHT_PASS=FALSE
PROCESS_GATE=UNKNOWN (PROC_CMDLINE_UNREADABLE)
FULL_MIGRATION=FORBIDDEN
```

---

## 1. 现场卷身份（简短核对）

| 项 | 结果 |
|----|------|
| hostname | ZHANGWEI |
| E FileSystem / serial | NTFS / `806508DF` |
| UniqueId | `\\?\Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}\` **MATCH** |
| `E:\BLACKBOX_MANIFEST_PILOT_R9_1G` | **不存在** |

证据：`R9_ZHANGWEI_VOLUME_IDENTITY_LIVE.json`

---

## 2. PID 20440 核实（不终止）

| 项 | 值 |
|----|-----|
| 仍存在 | **TRUE**（非“已退出后 PID 复用为空”） |
| Name | `cmd.exe` |
| PPID | **3348** `sshd.exe` |
| 祖父 | 28700 `sshd.exe` → 5892 |
| CommandLine | **null**（仍不可读） |
| ExecutablePath / Path | null（当前会话可见性受限） |
| Owner（GetOwner） | 空 `\` |
| CreationDate（WMI） | **2026-10-10 17:33:54**（早于今日预检；与预检可疑行同 PID/PPID） |
| 子进程 | `conhost.exe` 8488；`findstr.exe` 34324（命令行亦不可读） |

结论边界（据实）：

- **不能**写成“R8 仍在运行”（无任何可读命令行命中 `20261010_173201_R8_3B85D677` / `BLACKBOX_R8_E_COPY_*` / `PROGRESS_WRAPPER` / `WATCHDOG` / `CAPACITY_OBSERVER` / `EXIT_WAITER`；`ln.exe` 计数=0）。
- **不能**仅因父进程名 `sshd` 就自行判定与 R8 无关并豁免门禁。
- 在命令行仍不可读的情况下，按 FIX2b：**保持 `PROC_CMDLINE_UNREADABLE` / UNKNOWN**。
- 未杀 sshd/cmd，未设 `R9_SKIP_PROC_CHECK`，未伪造快照，未改复制/验收代码。

证据：`R9_ZHANGWEI_PROCESS_DETAIL.json`、`R9_ZHANGWEI_UNREADABLE_CMDLINE_PROCS.json`、`R9_ZHANGWEI_UNREADABLE_PARENT_CHAINS.json`、`R9_ZHANGWEI_R8_MARKER_SCAN.json`

---

## 3. 本轮预检重跑

```text
python copy_executor_r9_1g.py --preflight-only
  --confirm-dest E:\BLACKBOX_MANIFEST_PILOT_R9_1G
  --r8-stopped-evidence C:\LAN_SHARE_REPORT\BLACKBOX_R9_OLD_JOB_STOP_REPORT.md
  --log C:\LAN_SHARE_REPORT\COPY_EXECUTOR_R9_PREFLIGHT_ZHANGWEI_ROUND2.json
```

| 门禁 | 结果 |
|------|------|
| 主机 / 卷 serial+UniqueId / 目标不存在 / confirm-dest / R8 停止报告 | PASS |
| `live_r8_process_check` | **FAIL** `PROC_CMDLINE_UNREADABLE`（仍指向 PID 20440） |
| **PREFLIGHT_PASS** | **FALSE** |

---

## 4. 1GiB 实测

按任务第 2 节：**原门槛未 PASS → 停止，不启动复制**。

| 字段 | 值 |
|------|-----|
| COPY_STARTED | **NOT_RUN** |
| COPY_OK | **NOT_RUN** |
| ACCEPTANCE_PASS | **NOT_RUN** |

既有 662 实体 UNC 探测证据保留，本轮**未**重跑全量 `--probe-sources`。

D 完整性未证实结论保留；全量迁移仍禁止。

---

## 5. 供 ChatGPT 窄范围判断的事实（非自行豁免）

1. 阻塞进程自 **2026-10-10 17:33:54** 起由 **sshd→cmd→(conhost,findstr)** 组成，命令行对本会话不可读。  
2. 全进程可读命令行扫描：**0** 条命中旧 R8 RUN_ID / E_COPY 监控脚本；无 `ln.exe`。  
3. 若策略上要对“仅 sshd 会话且无 R8 标记”做窄豁免，需 ChatGPT 改门禁定义后再执行；台式机本轮不改代码。

---

## 6. 本轮交付文件（本地）

- `R9_ZHANGWEI_PROCESS_RESOLUTION_REPORT.md`（本文件）
- `COPY_EXECUTOR_R9_PREFLIGHT_ZHANGWEI_ROUND2.json`
- `R9_ZHANGWEI_VOLUME_IDENTITY_LIVE.json`
- `R9_ZHANGWEI_PROCESS_DETAIL.json`
- 及相关进程扫描 JSON
