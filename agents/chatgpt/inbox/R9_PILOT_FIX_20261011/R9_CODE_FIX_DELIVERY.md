# R9 1GiB 脚本定点补修交付（R9FIX2）

Generated: 2026-10-11T11:20+0800  
**未执行 1GiB 复制；未全量迁移；未重扫 D/E；未清理实验目录。**

## 硬状态（给 GPT）

- **D 完整性仍未证实**（历史 `stack[-5000:]` 截断风险保留）。
- **历史 R8 READY / DESKTOP_READY / WRITERS_STOPPED 不可复用**为停止证据；必须三字段精确 TRUE 且无冲突。
- 台式机 **UniqueId / UNC 稳定只读** 仍为现场核验项。
- 笔记本合成测：**passed=16 failed=0**（见 `R9FIX2_LEAN_TEST_FULL.json`，含逐项结果，非仅摘要）。

## 本轮缺口修复

1. **源身份与修改时间**  
   清单 vs 实时源比较 `volume_serial + file_id + size`；硬链接兄弟比较 `volume_serial + file_id`。  
   `source_last_write_time` 按 ISO UTC 解析，与句柄 FILETIME 按清单精度比较；无法解析则停止。  
   保留同一句柄复制前后状态检查。

2. **验收记录完整性**  
   `entity_id` 无重复且与待验实体集合完全一致；每实体强制 64 位 hex SHA-256 比较（删除 `if expected_sha` 放行）。  
   `run_id` 非空；复制前后空间证据必须完整。缺证据则分项与 `overall_pass` 均不能为 TRUE。

3. **验收目录与读错误**  
   `os.walk(onerror=…)` 枚举失败计入缺项；验收前检查目标根及祖先非重解析点。  
   `read_exact_hash` / `copy_bounded` 末尾 1 字节探测：`ReadFile` 失败报错，不得当 EOF 成功。

4. **R8 真实检查**  
   三字段完整、无冲突、精确 TRUE；FALSE/UNKNOWN/缺字段/重复冲突均拒绝。  
   现场按 **命令行 + 启动时间 + 父子 PID** 识别旧 RUN_ID `20261010_173201_R8_3B85D677`（覆盖 monitor/wrapper/ln 上下文）。  
   **实际复制不得**通过 `R9_SKIP_PROC_CHECK` 跳过。

## 文件

| 文件 | 说明 |
|------|------|
| `r9_pilot_common_r9fix.py` | 共用：身份/mtime/EOF/R8/进程/记录完整性 |
| `copy_executor_r9_1g.py` | 复制器 |
| `acceptance_script_r9_1g.py` | 验收器 |
| `R9_SYNTH_TESTS/run_r9fix_lean_tests.py` | 合成测源码 |
| `R9_SYNTH_TESTS/R9FIX2_LEAN_TEST_FULL.json` | 完整逐项结果 |
| `R9_SYNTH_TESTS/R9FIX_LEAN_TEST_RESULTS.json` | 同上（兼容旧名） |

## 仍须台式机现场

1. 主机名 ZHANGWEI  
2. E: serial `806508DF` + UniqueId 现场比对  
3. UNC `\\192.168.100.2\E_DRIVE\BLACKBOX` 稳定只读  
4. 真实停止报告三字段 TRUE + 无旧 RUN_ID 进程  
5. 新建 `E:\BLACKBOX_MANIFEST_PILOT_R9_1G` 后全量 662 复制与验收（**本轮不执行**）
