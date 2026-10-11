# R9 ZHANGWEI — 授权可见性诊断报告

任务ID：`R9_DESKTOP_AUTHORIZED_VISIBILITY_20261011_1220`  
取代：`R9_DESKTOP_PROCESS_RESOLVE_20261011`（已消费）  
执行：台式机 ZHANGWEI Cursor  
时间：2026-10-11 ≈12:24+08:00

```text
STATUS=DIAGNOSIS_DONE
WAITING_FOR_LOCAL_UAC=FALSE
COPY_STARTED=NOT_RUN
COPY_OK=NOT_RUN
ACCEPTANCE_PASS=NOT_RUN
PREFLIGHT_PASS_NORMAL=FALSE
PREFLIGHT_PASS_ADMIN=FALSE
FULL_MIGRATION=FORBIDDEN
```

---

## 1. 普通会话权限（诊断前）

| 项 | 值 |
|----|-----|
| whoami | `zhangwei\admin` |
| Administrators 组成员 | **false**（未提升令牌视角） |
| Integrity | **Medium** |
| process_elevated | **false** |

证据：`R9_ZHANGWEI_PRIVILEGE_STATE.json`  
在此权限下此前只能得到 `CommandLine=null` → 不再重复同权限 FAIL 查询。

---

## 2. UAC 只读诊断（已获用户批准）

- 脚本：`C:\LAN_SHARE_REPORT\R9_ADMIN_READONLY_DIAG.ps1`
- 启动：`Start-Process -Verb RunAs`（正常 UAC，非静默）
- 提升后：`integrity=High`，`adminGroup=true`，`elevated=true`
- 完成标记：`R9_ADMIN_DIAG_DONE.json` → `DIAGNOSIS_DONE`

用途限定：只读进程身份 + `--preflight-only`。**未**杀进程、**未**复制、**未**改 ACL。

---

## 3. 提升后 PID 20440 真实身份

| 项 | 值 |
|----|-----|
| PID | 20440 |
| 进程 | `c:\windows\system32\cmd.exe` |
| 创建 | 2026-10-10T17:33:54+08:00（与先前一致，非 PID 复用空号） |
| Owner | `ZHANGWEI\Admin` |
| 父链 | sshd(3348 `-z`) ← sshd(28700 `-R`) ← sshd 服务 |
| **CommandLine（现可读）** | `cmd.exe /c "findstr /i " DESKTOP_READY RUN_ID\ C:\LAN_SHARE_REPORT\BLACKBOX_MIGRATION_RUN_20261010_173201_R8_3B85D677\DESKTOP_PREFLIGHT.json"` |
| 子进程 | `conhost` 8488；`findstr` 34324（同一路径/RUN_ID） |

判定（据实，不豁免）：

- 这是挂起的 **findstr 读 R8 运行目录 `DESKTOP_PREFLIGHT.json`** 的 ssh 会话残余，**不是**正在跑的 `ln` / wrapper / watchdog / observer / exit_waiter。
- 命令行含旧 **RUN_ID** `20261010_173201_R8_3B85D677` → 现有门禁命中 `R8_LEGACY_TASK_STILL_RUNNING`（合理 fail-closed）。
- **本任务不扩大授权去停止该进程**（按 inbox）。

证据：`R9_ZHANGWEI_ADMIN_PROCESS_DETAIL.json`（含完整命令行；无 token）

---

## 4. 预检结果

| 上下文 | 结果 | 原因 |
|--------|------|------|
| 普通 Medium（历史） | FAIL | `PROC_CMDLINE_UNREADABLE` |
| **管理员 High（本轮）** | **FAIL** | `R8_LIVE_PROC:R8_LEGACY_TASK_STILL_RUNNING`（cmd/findstr 命中 RUN_ID） |

管理员预检日志：`COPY_EXECUTOR_R9_PREFLIGHT_ZHANGWEI_ADMIN.json`  
卷 serial/NTFS 在管理员预检中仍 PASS；目标目录不存在。

---

## 5. 复制边界（本轮）

- 普通上下文原预检 **未** PASS → **不**启动 1GiB 复制。
- 管理员上下文亦 **未** PASS → 无“仅管理员可过预检再请写授权”分支。
- `COPY_STARTED` / `COPY_OK` / `ACCEPTANCE_PASS` = **NOT_RUN**
- 全量迁移 / 重扫 E/D / 改网络：**不做**

若 ChatGPT/用户后续授权**终止**该挂起 findstr/cmd（或会话退出后进程消失），再在**普通**上下文重跑 `--preflight-only`；仅当原门槛 PASS 且用户明确授权复制上下文时，才可双开关实测。

---

## 6. 交付文件

- `R9_ZHANGWEI_VISIBILITY_AUTH_REPORT.md`（本文件）
- `R9_ZHANGWEI_PRIVILEGE_STATE.json`
- `R9_ZHANGWEI_PRIVILEGE_STATE_ADMIN.json`
- `R9_ZHANGWEI_ADMIN_PROCESS_DETAIL.json`
- `COPY_EXECUTOR_R9_PREFLIGHT_ZHANGWEI_ADMIN.json`
- `R9_ADMIN_READONLY_DIAG.ps1` / `R9_LAUNCH_ADMIN_READONLY_DIAG.ps1`
- `R9_ADMIN_DIAG_DONE.json` / `R9_ADMIN_DIAG_RUN.log`
