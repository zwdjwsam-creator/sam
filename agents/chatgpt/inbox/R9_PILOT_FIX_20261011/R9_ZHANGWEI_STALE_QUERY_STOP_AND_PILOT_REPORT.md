# R9 ZHANGWEI — 挂起查询定点停止 + 普通预检 + 1GiB 实测报告

任务ID：`R9_DESKTOP_FINISH_STALE_QUERY_20261011_1227`  
执行主机：`ZHANGWEI`  
报告时间：2026-10-11T12:50+08:00  
FULL_MIGRATION：`FALSE`

---

## 0. 结论摘要

| 字段 | 值 |
|------|-----|
| STOP_DONE | **TRUE**（findstr 34324 → Stop-Process；cmd 20440 → NATURAL_EXIT） |
| PREFLIGHT_PASS（普通上下文） | **TRUE** |
| COPY_STARTED | **TRUE** |
| COPY_OK | **TRUE**（executor：`entities=662 unique=1064950668`） |
| ACCEPTANCE_PASS | **FALSE**（脚本 verdict：`FAIL_DEFICITS_PRESENT`） |
| FULL_MIGRATION | **FALSE** |

说明：官方验收脚本因 `Path.exists()` 对超长路径的假阴性报 `MISSING_DEST_PATHS`。只读长路径复核（`GetFileAttributesW(\\?\...)`）显示 **0 路径真正缺失**。未改门禁/验收代码，未自动重试复制。

---

## 1. 定点停止

脚本：`C:\LAN_SHARE_REPORT\R9_FINISH_STALE_QUERY.ps1`  
启动命令行**不含**旧 RUN_ID（仅 `-File` 脚本路径）。

| 步骤 | 结果 |
|------|------|
| 普通会话停止 | `STOP_FAIL` / `FINDSTR_IDENTITY_MISMATCH`（cmdline 空，无法核验） |
| UAC RunAs（用户批准） | `STOP_DONE` ExitCode=0 |
| UAC 用途 | 结束已确认挂起的旧 findstr 日志查询及其 cmd 外壳；不停止 SSH 服务；不删除文件 |

### 停止前身份（与 `R9_ZHANGWEI_ADMIN_PROCESS_DETAIL.json` 一致）

| PID | 名 | Owner | 父PID | StartTime | 命令行要点 |
|-----|----|-------|-------|-----------|------------|
| 34324 | findstr.exe | ZHANGWEI\Admin | 20440 | 2026-10-10T17:33:54.8014005+08:00 | `findstr /i " DESKTOP_READY RUN_ID\ ...\20261010_173201_R8_3B85D677\DESKTOP_PREFLIGHT.json` |
| 20440 | cmd.exe | ZHANGWEI\Admin | 3348 | 2026-10-10T17:33:54.7809759+08:00 | `cmd.exe /c "findstr ... DESKTOP_PREFLIGHT.json"` |
| 3348 | sshd.exe | ZHANGWEI\Admin | 28700 | 2026-10-10T17:33:54.7071876+08:00 | 会话 sshd（**未**对其 Stop-Process） |

### 动作与停止后

| 目标 | 动作 | 结果 |
|------|------|------|
| findstr 34324 | `Stop-Process`（无 `/T`） | ok，进程消失 |
| cmd 20440 | 短暂等待自然退出 | `NATURAL_EXIT`，进程消失 |
| sshd 3348 | **未主动终止** | 随子外壳退出后会话进程消失；**OpenSSH 服务 `sshd` 仍 Running**（复核时服务 PID≈5892） |

证据：
- `R9_STALE_QUERY_STOP_DONE.json`
- `R9_STALE_QUERY_STOP_SNAPSHOT.json`
- `R9_STALE_QUERY_STOP.log`
- `R9_FINISH_STALE_QUERY.ps1`

---

## 2. 普通上下文预检

```text
python copy_executor_r9_1g.py --preflight-only
  --confirm-dest E:\BLACKBOX_MANIFEST_PILOT_R9_1G
  --r8-stopped-evidence C:\LAN_SHARE_REPORT\BLACKBOX_R9_OLD_JOB_STOP_REPORT.md
  --log C:\LAN_SHARE_REPORT\COPY_EXECUTOR_R9_PREFLIGHT_ZHANGWEI_AFTER_STALE_STOP.json
```

| 门禁 | 结果 |
|------|------|
| hostname ZHANGWEI | PASS |
| E 卷 serial `806508DF` / UniqueId `Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}` | PASS |
| 目标不存在 / confirm-dest / R8 停止报告 | PASS |
| live_r8_process_check（旧 RUN_ID / ln / 监控） | PASS（suspicious=[]） |
| manifest SHA | `cfb831ecc0a85fec0137b74a12162e169828d708ff57961df906deffb185c041` |
| **PREFLIGHT_PASS** | **TRUE** |

未设 `R9_SKIP_PROC_CHECK`，未改门禁代码。

---

## 3. 复制前简短核对

| 项 | 值 |
|----|-----|
| 主机 | ZHANGWEI |
| E NTFS serial | 806508DF |
| Volume GUID | b8545ee8-e403-48c6-9d3f-09afd3e0349f |
| 目标 `E:\BLACKBOX_MANIFEST_PILOT_R9_1G` | 复制前不存在 |
| 清单 | 662 / 22998 / 1064950668；SHA 同上 |
| PY SHA256 | copy_executor `41E64620…4884`；acceptance `99A6F0D5…83A3D`；common `D5B61E02…D1CE` |
| 源 | `\\192.168.100.2\E_DRIVE\BLACKBOX` |
| 662 UNC 全文探测 | 不重复（沿用既有证据） |

---

## 4. 1GiB 实测复制

```text
python copy_executor_r9_1g.py
  --enable-copy --i-accept-pilot-copy
  --confirm-dest E:\BLACKBOX_MANIFEST_PILOT_R9_1G
  --r8-stopped-evidence C:\LAN_SHARE_REPORT\BLACKBOX_R9_OLD_JOB_STOP_REPORT.md
  --log C:\LAN_SHARE_REPORT\COPY_EXECUTOR_R9_PILOT_COPY_ZHANGWEI.json
```

| 字段 | 值 |
|------|-----|
| COPY_STARTED | **TRUE** |
| COPY_OK | **TRUE** |
| detail | `entities=662 unique=1064950668` |
| copy-record | `C:\LAN_SHARE_REPORT\PILOT_COPY_RECORD_2026-10-11T1230430800.json` |
| 复制日志 | `C:\LAN_SHARE_REPORT\COPY_EXECUTOR_R9_PILOT_COPY_ZHANGWEI.json` |
| volume_free_before | 4000538427392 |
| volume_free_after | 3999439306752 |
| volume_free_delta | **1099120640** |
| 耗时（墙钟） | ≈953 s（约 15.9 min） |
| finished_at | 2026-10-11T12:46:35+0800 |

---

## 5. 完整验收（官方脚本）

```text
python acceptance_script_r9_1g.py
  --copy-record C:\LAN_SHARE_REPORT\PILOT_COPY_RECORD_2026-10-11T1230430800.json
  --dest E:\BLACKBOX_MANIFEST_PILOT_R9_1G
  --log C:\LAN_SHARE_REPORT\ACCEPTANCE_R9_PILOT_ZHANGWEI.json
```

| 字段 | 值 |
|------|-----|
| ACCEPTANCE_PASS | **FALSE** |
| verdict | `FAIL_DEFICITS_PRESENT` |
| deficits | `HASH_COVERAGE=650`；`PATH_IDENTITY_COVERAGE=22082`；`MISSING_DEST_PATHS` |
| entities_hashed / expected | 650 / 662 |
| paths_identity_checked / expected | 22082 / 22998 |
| manifest_unique_content_bytes | 1064950668 |
| dest_unique_content_bytes（脚本所见） | 1064153681 |
| dest_unique_allocated_bytes | 1065459712 |
| logical_path_bytes | 19786558967 |
| occupancy_pass | true |
| content_link_pass | false |

JSON：`ACCEPTANCE_R9_PILOT_ZHANGWEI.json`

### 5b. 只读补充：长路径存在性复核（非验收改判）

未修改验收脚本。用 `GetFileAttributesW` + `\\?\` 长路径对清单全部 22998 路径复核：

| 指标 | Path.exists() | GetFileAttributesW(long) |
|------|---------------|---------------------------|
| 缺失路径数 | 916 | **0** |
| 实体主键缺失 | 12 | **0** |

缺失样本均落在 `数据\...` 下超长路径；父目录存在，短路径 API 假阴性。  
**本报告仍按官方脚本将 ACCEPTANCE_PASS 记为 FALSE**；是否认定 MAX_PATH 假阴性、是否授权验收修复后重跑，由 ChatGPT/用户决定。未自动重试复制，未清理目标。

---

## 6. 禁止项遵守

- 未写 E/D 源；未重开 P7；未格式化/VSS/删除源
- 未全量迁移；失败后未自动重试
- 未主动杀 sshd 服务 / Cursor；停止无 `/T`
- 停止脚本启动命令行未嵌入 RUN_ID

---

## 7. 本地证据清单

- `R9_FINISH_STALE_QUERY.ps1`
- `R9_STALE_QUERY_STOP_DONE.json` / `R9_STALE_QUERY_STOP_SNAPSHOT.json` / `R9_STALE_QUERY_STOP.log`
- `COPY_EXECUTOR_R9_PREFLIGHT_ZHANGWEI_AFTER_STALE_STOP.json`
- `COPY_EXECUTOR_R9_PILOT_COPY_ZHANGWEI.json`
- `PILOT_COPY_RECORD_2026-10-11T1230430800.json`
- `ACCEPTANCE_R9_PILOT_ZHANGWEI.json`
- 既有管理员诊断：`R9_ZHANGWEI_ADMIN_PROCESS_DETAIL.json` 等（保留，不删）
