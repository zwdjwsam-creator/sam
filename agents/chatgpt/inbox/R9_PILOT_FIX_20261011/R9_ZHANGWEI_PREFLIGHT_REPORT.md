# R9 台式机 ZHANGWEI — 预检 / UNC 探测报告

时间：2026-10-11 ≈11:34–11:53 +08  
主机：`ZHANGWEI`（已确认，非 SAM）  
脚本来源：HUB `R9_PILOT_FIX_20261011` + 笔记本 C 盘同步至 `C:\LAN_SHARE_REPORT\`  
清单：`C:\LAN_SHARE_REPORT\BLACKBOX_R9_MANIFEST\PILOT_1G_MANIFEST.sqlite`  
SHA-256：`cfb831ecc0a85fec0137b74a12162e169828d708ff57961df906deffb185c041`（与 pin 一致）

```text
HOSTNAME_OK=TRUE
DEST_VOLUME_OK=TRUE
R8_STOP_EVIDENCE_OK=TRUE
R8_LIVE_PROC_OK=FALSE
PREFLIGHT_PASS=FALSE
UNC_PROBE_OK=TRUE
PILOT_1G_COPY_STARTED=FALSE
FULL_MIGRATION=FALSE
```

---

## 1. 材料就位

| 项 | 状态 |
|----|------|
| `copy_executor_r9_1g.py` / `acceptance_script_r9_1g.py` / `r9_pilot_common_r9fix.py` | 已同步到 `C:\LAN_SHARE_REPORT\` |
| HUB 副本目录 | `C:\LAN_SHARE_REPORT\R9_PILOT_FIX_20261011\` |
| PILOT_1G_MANIFEST.sqlite | 已从笔记本 `\\192.168.100.2\C_DRIVE\...\BLACKBOX_R9_MANIFEST\` 复制 |
| R8 停止报告 | `BLACKBOX_R9_OLD_JOB_STOP_REPORT.md`（三字段 TRUE） |

---

## 2. 第三节预检（`--preflight-only`）

命令：

```text
python copy_executor_r9_1g.py --preflight-only --probe-sources
  --confirm-dest E:\BLACKBOX_MANIFEST_PILOT_R9_1G
  --r8-stopped-evidence C:\LAN_SHARE_REPORT\BLACKBOX_R9_OLD_JOB_STOP_REPORT.md
  --log C:\LAN_SHARE_REPORT\COPY_EXECUTOR_R9_PREFLIGHT_ZHANGWEI.json
```

| 门禁 | 结果 | 说明 |
|------|------|------|
| hostname == ZHANGWEI | **PASS** | |
| E: MarketData serial `806508DF` / NTFS | **PASS** | live 与 EXPECTED 一致 |
| R8 停止报告三字段 | **PASS** | OLD_LN/WRAPPER/MONITORS 均为 TRUE |
| `E:\BLACKBOX_MANIFEST_PILOT_R9_1G` 不存在 | **PASS** | |
| confirm-dest 匹配 | **PASS** | |
| live_r8_process_check | **FAIL** | `PROC_CMDLINE_UNREADABLE` |

**预检总结果：`PREFLIGHT_FAIL`**  
日志：`C:\LAN_SHARE_REPORT\COPY_EXECUTOR_R9_PREFLIGHT_ZHANGWEI.json`

### 进程门禁失败详情（未放宽）

- 可疑行：`cmd.exe` PID **20440**，PPID **3348**（`sshd.exe`），`CommandLine=null`
- FIX2b 规则：`ln|powershell|pwsh|cmd` 命令行不可读 → `ok=false` / `UNKNOWN`（不得当作“无旧任务”）
- 另查：系统中 **无** `ln.exe`；**无** 含 `20261010_173201_R8` / `BLACKBOX_R8_E_COPY` 的可读命令行
- **未**设置 `R9_SKIP_PROC_CHECK`；**未**终止 sshd/cmd（可能为远程会话相关，避免误伤 Agent）

→ 第四节 1GiB **实测未执行**（条件未全满足）。

---

## 3. UNC 探测（独立 dry-run，未开复制）

因 `--preflight-only` 在门禁失败时提前返回，另跑：

```text
python copy_executor_r9_1g.py --probe-sources
  --confirm-dest E:\BLACKBOX_MANIFEST_PILOT_R9_1G
  --log C:\LAN_SHARE_REPORT\COPY_EXECUTOR_R9_UNC_PROBE_ZHANGWEI.json
```

（此模式按脚本设计会经稳定句柄做源身份核对 + 全文 SHA 探测，约读完 1.06GiB 唯一字节。）

| 项 | 结果 |
|----|------|
| status | **DRY_RUN_OK** |
| probed_entities | **662** |
| planned_bytes | **1,064,950,668** |
| 耗时 | ≈17.5 min（11:35–11:52） |
| 目标目录写入 | **无**（dry_run） |
| 日志 | `COPY_EXECUTOR_R9_UNC_PROBE_ZHANGWEI.json` |

---

## 4. 未做

- 未 `--enable-copy` / 未创建 `E:\BLACKBOX_MANIFEST_PILOT_R9_1G`
- 未跑完整 acceptance（无复制产物）
- 未全量迁移；未改网络；未恢复 P7；未清理任何目录

---

## 5. 建议（供 ChatGPT 审核）

1. 处理/豁免策略需评审：sshd 子进程 `cmd.exe` 空命令行是否应排除在 `_R8_CMDLINE_REQUIRED_NAMES` 之外，或仅对“可证明非 R8”的 PPID 树放宽——**台式机未擅自改脚本**。  
2. 门禁通过后，再执行：

```text
python copy_executor_r9_1g.py --enable-copy --i-accept-pilot-copy
  --confirm-dest E:\BLACKBOX_MANIFEST_PILOT_R9_1G
  --r8-stopped-evidence C:\LAN_SHARE_REPORT\BLACKBOX_R9_OLD_JOB_STOP_REPORT.md
```

然后跑 `acceptance_script_r9_1g.py`。

---

*ZHANGWEI Cursor；预检阻塞于进程命令行不可读；UNC 探测 PASS；1GiB 复制未启动。*
