# 台式机 E 盘只读共享（给 SAM 笔记本）

- 主机：`ZHANGWEI`（台式机）
- 地址：**`192.168.100.1`**（以太网，直连）
- 共享名：**`E_DRIVE`** → `E:\`
- UNC：**`\\192.168.100.1\E_DRIVE`**
- 账号：`ZHANGWEI\sam_ro`（本机**普通用户**，非管理员）
- 权限：**只读**（共享层 `sam_ro=Read`；NTFS 经 `Users` 组继承 `ReadAndExecute`）
- 开通时间：2026-10-25 16:46 +08:00

---

## 1. 凭据在哪

```
\\192.168.100.2\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024\desktop_structure_audit_20261025\desktop_reply_Q1_Q9\secrets\sam_smb_readonly.TXT
```

台机本地同一份：`C:\LAN_SHARE_REPORT\配置\secrets\sam_smb_readonly.TXT`（ACL 已收紧为 SYSTEM / Administrators / Admin 可读写）。

> 为避免二次传输，密码只写在上面这个文件里，不写进本文档、不进 GitHub。
> 本机每次重新配置会**轮换密码**，届时以该文件为准。

## 2. 挂载（SAM 上执行，Windows）

```powershell
# 方式 A：临时映射盘符
net use Z: \\192.168.100.1\E_DRIVE /user:ZHANGWEI\sam_ro <PASSWORD> /persistent:yes

# 方式 B：先存凭据，再直接走 UNC（脚本/程序更方便）
cmdkey /add:192.168.100.1 /user:ZHANGWEI\sam_ro /pass:<PASSWORD>
```

## 3. 验证

```powershell
dir Z:\BLACKBOX\研究系统            # 应能列出
dir \\192.168.100.1\E_DRIVE\BLACKBOX
echo x > Z:\_probe.txt              # 必须失败（拒绝访问）
```

Python（SAM 侧跑研究脚本时可直接用 UNC）：

```python
from pathlib import Path
root = Path(r"\\192.168.100.1\E_DRIVE\BLACKBOX")
print(len(list((root / "研究系统").iterdir())))
```

## 4. 台机侧已做的配置（可核）

| 项 | 状态 |
|---|---|
| 本地账号 `sam_ro` | 已启用、密码已设、`PasswordNeverExpires` |
| 组成员 | `Users`（**不在** `Administrators`） |
| 共享 `E_DRIVE`（`E:\`） | `BUILTIN\Administrators=Full`、`Everyone=Read`、`ZHANGWEI\sam_ro=Read` |
| NTFS | `E:\` 继承 `BUILTIN\Users=ReadAndExecute` → `sam_ro` 可读；**未改写根 ACL** |
| 防火墙 | 新增 `BLACKBOX SMB 445 from SAM 192.168.100.0/24`（Inbound TCP 445，仅 192.168.100.0/24） |
| 服务 | `LanmanServer=Running`，`445` 在监听 |
| 连通性 | 台机 → `192.168.100.2:445` = True；本机 `192.168.100.1:445` = True |
| `sam_ro` 身份实测 | 读 `E:\BLACKBOX\HAND.txt` = **OK**；写探针 = **DENIED** |

台账（机器可读）：`E:\BLACKBOX\任务\BLACKBOX_DESKTOP_STRUCTURE_REMAP_AND_REPAIR_R1\输出\SAM_SMB_READONLY_PROVISION.json`
配置脚本：`...\脚本\provision_sam_smb_readonly_v4.ps1`
执行日志：`C:\LAN_SHARE_REPORT\配置\logs\sam_smb_provision_v4_*.log`

## 5. 边界（重要）

1. **只读**：`E_DRIVE` 共享对 `sam_ro` 是 `Read`。你在 SAM 侧不要试图写 `Z:`；要回传请走台机既有的 `\\192.168.100.1\BLACKBOX_DEST`（= `E:\BLACKBOX`，`Everyone=Change`）或 HUB。
2. **不碰业务数据的约定不变**：读写 `E:\BLACKBOX` 视为改台机生产树。当前台机处于
   `运行\BLACKBOX_DESKTOP_REPAIR_DELEGATION_CURRENT.json` 的**写冻结**状态
   （`manifest_and_plane` / `data_plane_current` / `business_code` / `data_artifacts` 全 true）。
   你若要写，请按 `HANDOFF_TO_SAM_CURSOR.md` 第 6 节留账，并只动你裁决过的项。
3. **不暴露到公网**：本共享只对 `192.168.100.0/24` 放行 445；Tailscale/WLAN 侧未额外开放。
4. **不给 `sam_ro` 任何管理权**：它不在 Administrators，故 `E$` 等管理共享不可用。

## 6. 撤销 / 轮换

```powershell
# 撤销共享授权
Revoke-SmbShareAccess -Name E_DRIVE -AccountName ZHANGWEI\sam_ro -Force
# 停用账号
Disable-LocalUser -Name sam_ro
# 删除定向防火墙规则
Remove-NetFirewallRule -DisplayName 'BLACKBOX SMB 445 from SAM 192.168.100.0/24'
```

撤销后台机侧 `E:\` 的 NTFS / 继承均未被改动，无需回滚。
