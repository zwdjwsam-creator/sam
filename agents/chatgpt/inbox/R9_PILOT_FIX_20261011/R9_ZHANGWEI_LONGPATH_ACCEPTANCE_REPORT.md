# R9 ZHANGWEI — 长路径验收修复与现有 1GiB 复验

任务ID：`R9_DESKTOP_LONGPATH_ACCEPTANCE_20261011_1301`  
执行主机：`ZHANGWEI`  
报告时间：2026-10-11T13:10+08:00  
FULL_MIGRATION：`FALSE`（未开始；等待审核）

---

## 0. 结论

| 字段 | 值 |
|------|-----|
| 小型回归 `all_ok` | **TRUE** |
| ACCEPTANCE_PASS（修订验收器 / 现有副本） | **TRUE** |
| verdict | `PASS` |
| entities_hashed / expected | **662 / 662** |
| paths_identity_checked / expected | **22998 / 22998** |
| dest_unique_content_bytes | **1064950668**（= 清单唯一字节） |
| dest_unique_allocated_bytes | **1066270720** |
| content_link_pass / occupancy_pass | TRUE / TRUE |
| deficits | `[]` |
| 复制器重跑 | **未执行**（禁止倒退） |
| 原失败 JSON | 保留：`ACCEPTANCE_R9_PILOT_ZHANGWEI.json` |

---

## 1. 代码变更

备份目录：`C:\LAN_SHARE_REPORT\R9_LONGPATH_ACCEPTANCE_BACKUP_20261011_130508\`

| 文件 | SHA256 before | SHA256 after |
|------|---------------|--------------|
| `acceptance_script_r9_1g.py` | `99a6f0d5f6e594f40a43dd4c95c292c0d84e716e2919d9a4f00b9b99caf83a3d` | `4924e17e35ae9a5d12929b427aadce5616830e0aacf9caaed75413d8f0a4fac0` |
| `r9_pilot_common_r9fix.py` | `d5b61e02c60d7eff5e2fb31746385e5e41b69f04fc8ecad9cf38e95c2368d1ce` | `bc969b160ca161b682637e839f283370ff1e41b4cf4f94ae1d8c208334259a87` |

diff 文件：`R9_LONGPATH_DIFF_acceptance_script_r9_1g_py.diff`、`R9_LONGPATH_DIFF_r9_pilot_common_r9fix_py.diff`

### 要点

**common（新增辅助，复制逻辑未改）：**
- `classify_path_presence` / `path_exists_win`：`GetFileAttributesW` + `to_win_long_path`；仅 Win32 2/3 记 missing；其它错误上抛（读取 `errno`/`winerror`）
- `strip_win_long_prefix` / `relative_under_root`：规范化后做根边界检查，避免 `\\?\` 导致 EXTRA 误判

**acceptance：**
- 目标存在性与路径检查改用上述 API，不再用裸 `Path.exists()`
- `walk_dest_extra` 从 `\\?\` 扩展根遍历；相对路径用 `relative_under_root`
- 权限/属性错误独立 deficit：`PATH_ATTR_OR_ACCESS_FAIL`
- 未改系统 `LongPathsEnabled`；未降覆盖门槛；未改清单/copy-record

---

## 2. 小型回归（仅 C:）

源码：`R9_LONGPATH_ACCEPTANCE_REGRESSION.py`  
结果：`R9_LONGPATH_ACCEPTANCE_REGRESSION_RESULT.json`  
数据根：`C:\LAN_SHARE_REPORT\R9_LONGPATH_REGRESSION_20261011_1301\`（中文长路径，len≈417/493）

| 用例 | 期望 | 结果 |
|------|------|------|
| LONGPATH_PRESENT_CONTENT_LINK_PASS | PASS | ok |
| DELETE_ONE_PATH_FAIL | FAIL | ok（MISSING） |
| CORRUPT_CONTENT_FAIL | FAIL | ok（SHA） |
| INJECT_WALK_ENUM_ERROR_FAIL | FAIL | ok（WALK） |
| EXTRA_LONGPATH_FILE_FAIL | FAIL | ok（EXTRA） |
| HARDLINK_SPLIT_FAIL | FAIL | ok（LINK） |
| CROSS_GROUP_MERGE_FAIL | FAIL | ok（MERGE） |
| PATH_EXISTS_VS_LONGPATH_HELPER | helper 可见 | ok |

`all_ok=true`。未触碰 `E:\BLACKBOX_MANIFEST_PILOT_R9_1G`。

---

## 3. 现有 1GiB 只读复验

```text
python acceptance_script_r9_1g.py
  --copy-record C:\LAN_SHARE_REPORT\PILOT_COPY_RECORD_2026-10-11T1230430800.json
  --dest E:\BLACKBOX_MANIFEST_PILOT_R9_1G
  --log C:\LAN_SHARE_REPORT\ACCEPTANCE_R9_PILOT_ZHANGWEI_LONGPATH.json
```

核对：主机 ZHANGWEI；E serial `806508DF`；GUID `Volume{b8545ee8-e403-48c6-9d3f-09afd3e0349f}`；清单 SHA `cfb831ecc0a85fec0137b74a12162e169828d708ff57961df906deffb185c041`；run_id `2026-10-11T1230430800`。

| 指标 | 值 |
|------|-----|
| ACCEPTANCE_PASS | **TRUE** |
| 662 实体哈希 | 完成 |
| 22998 路径身份 | 完成 |
| 唯一内容字节 | 1064950668 |
| 分配空间（去重 AllocationSize） | 1066270720 |
| volume_free_before（copy-record） | 4000538427392 |
| volume_free_after（copy-record / 当前） | 3999439306752 |
| volume_free_delta | 1099120640 |
| 复验墙钟 | ≈2 s（本地 NVMe 读唯一内容；见 JSON 时间戳） |
| 组内链接 / 跨组合并 | 通过 / 无误合并 |
| 缺失 / 额外 / 重解析 / 枚举错误 | 无 |

日志：`ACCEPTANCE_R9_PILOT_ZHANGWEI_LONGPATH.json`

---

## 4. 上一轮「22998 长路径 0 缺失」材料

上一轮报告层结论来自会话内脚本 `_r9_longpath_check.py`（当时未单独入库 JSON）。  
本轮补跑并固化：

- 脚本：`_r9_longpath_check.py`
- 文本：`R9_PRIOR_LONGPATH_0_MISSING_PROBE.txt`
- JSON：`R9_PRIOR_LONGPATH_0_MISSING_PROBE.json`  
  → `missing_plain_Path_exists=916`，`missing_long_GetFileAttributesW=0`，`exist_long_only=916`

非伪造；与修订验收 PASS 一致解释为 MAX_PATH / `Path.exists` 假阴性。

---

## 5. 禁止项

- 未重跑复制器；未改/清实验目录；未改清单与 copy-record  
- 未写源 E/D；未全量迁移；未改注册表 LongPathsEnabled  
- 原 `ACCEPTANCE_R9_PILOT_ZHANGWEI.json` 保留  

D 完整性仍未证实。本次 PASS 仅证明该 1GiB 样本的复制与链接方法及修订验收器正确性。
