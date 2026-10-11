# R9 1GiB 脚本修复交付（ChatGPT 审核）

Generated: 2026-10-11T10:40+0800  
**未执行 1GiB 复制；未全量迁移；未重扫 D/E。**

## 文件

| 文件 | 说明 |
|------|------|
| `C:\LAN_SHARE_REPORT\copy_executor_r9_1g.py` | 修复后复制器 |
| `C:\LAN_SHARE_REPORT\acceptance_script_r9_1g.py` | 修复后验收器 |
| `C:\LAN_SHARE_REPORT\r9_pilot_common_r9fix.py` | 共用 WinAPI/路径/R8/清单绑定（两脚本依赖） |
| `*_PRE_REVIEW_FIX.py` | 审核前旧版保留 |

## 关键修复点（含本轮补充）

1. 源路径：台式机只用 `\\192.168.100.2\E_DRIVE\BLACKBOX` + 校验后的相对路径；不回退本地 E:。
2. UNC → `\\?\UNC\...`；API argtypes/restype；句柄异常路径关闭。
3. R8：必须三字段 `OLD_LN_STOPPED/OLD_WRAPPER_STOPPED/OLD_MONITORS_INACTIVE` 均为 TRUE；`R8_STOPPED=FALSE` 等旧令牌不足以通过。
4. 复制仅 ZHANGWEI + E 卷 serial `806508DF`；目标必须原先不存在。
5. **同一只读源句柄**：身份 → seek → 有界读/写/哈希 → 再读身份；禁止关闭后再 `shutil.copy2`。SMB 稳定读失败 → `SMB_STABLE_READ_UNAVAILABLE` 停。
6. 分配空间：`FileStandardInfo.AllocationSize`，按 `(volume_serial,file_id)` 去重；与文件长度分列。
7. 复制记录绑定 manifest SHA / dest / dest_volume / run_id；完整验收 662/22998；`--limit-entities` → `PARTIAL`，不得 overall PASS。

## 笔记本合成测试（C:）

`R9_SYNTH_TESTS\R9FIX_LEAN_TEST_RESULTS.json`：**passed=10 failed=0**

覆盖：UNC、相对路径拒绝、R8 TRUE/FALSE/缺字段、错主机拒复制、同句柄复制+哈希、硬链接同组/不同实体、空清单、PARTIAL 验收、清单 SHA 绑定、dry-run 映射。

## 仍须台式机现场验证

1. 主机名 ZHANGWEI  
2. E: 卷 serial `806508DF` 与 UniqueId 现场比对  
3. UNC `\\192.168.100.2\E_DRIVE\BLACKBOX` 稳定只读打开  
4. 真实 R8 停止报告三字段 TRUE + 进程抽查  
5. 新建 `E:\BLACKBOX_MANIFEST_PILOT_R9_1G` 后全量 662 复制与验收（**本轮不执行**）

## D 覆盖

完整性未证实（历史 stack 截断风险）；缺口留正式迁移前对账补扫；本轮不重扫。
