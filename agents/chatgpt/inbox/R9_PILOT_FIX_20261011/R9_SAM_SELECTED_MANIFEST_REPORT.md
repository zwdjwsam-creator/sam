# R9_SAM_SELECTED_MANIFEST_REPORT

任务：`R9_NOTEBOOK_SELECTED_MANIFEST_20261011_1354`  
主机：笔记本 **SAM**  
时间：2026-10-11 ≈14:15 +08  
**FULL_MIGRATION=false**

HUB：https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/R9_PILOT_FIX_20261011

---

## 0. 结论

| 字段 | 值 |
|------|-----|
| `enumeration_complete`（选定根） | **true**（QUEUE_EMPTY，~198s） |
| `SELECTED_SCOPE_COVERAGE_PROVEN` | **false**（未知依赖边界未闭合：全 MIN_sandbox / 全 ARCHIVE / QMT） |
| `D_GLOBAL_COVERAGE_PROVEN` | **false** |
| 选定清单唯一字节 | **8,186,614,545**（vol+file_id 去重） |
| 唯一实体 | **45,381** |
| 节点 | 45,398；目录 ENUM_DONE **10,637**；身份未解决文件 **0** |
| 与旧 DB 差异 | 3370 条均为目录 `SIZE_DRIFT`（live 非零 vs old=0）→ **归因为目录尺寸无语义，非内容漂移**；文件尺寸漂移 **0** |

未复制业务数据；未改 r9_1g；未全 E 重扫；P7 禁用；历史 R8 READY 不复用。

---

## 1. 依赖表（逐条）

`R9_SAM_DEPENDENCY_MAP.json` + 补交 `ED_LINKS_RECHECK.json`（本机存在，已附）。

| 方向 | 条数 | 现场存活（本轮只读核验） |
|------|-----:|--------------------------|
| E→D | 24 | 见 JSON `live.alive` |
| D→E | 16 | 见 JSON |

- **链接存活 ≠ 内容纳入**。E→D 目标均为 `D:\CURSOR_TASK_ARCHIVE\...\pit_products\...` 下精确子树；本轮将 **4 个不重叠 pit 根** 加入枚举（非 `**/pit_products/**` 通配，非整棵 ARCHIVE）。
- 跨卷记为 Junction；**不跟随**展开；拟迁移后映射标 **PROPOSED**，目标布局建议在台式机 **E: MarketData / 806508DF**，**不用旧 F: 映射**。
- 未授权扩展：`D:\MIN_sandbox`、整棵 `D:\CURSOR_TASK_ARCHIVE`、`D:\国金证券QMT交易端`。

配置：`R9_SAM_SELECTED_SCOPE_CONFIG.json`  
`config_sha256=b9dd8c323e68bab7dc032f1efbb8a0d1574a4c699c57391639d7b79a4dc312cd`

枚举根（12）：
1–8：`backtest_lab` 族 + `blackbox_data` + `JQ` + 两个 BLACKBOX_*  
9–12：四条显式 pit_products 根（见 config）

---

## 2. 可续接元数据对账

程序：`selected_manifest_enumerator.py`  
清单 DB（本机，不上传大文件）：`SELECTED_D_MANIFEST.sqlite`  
SHA-256：`787b14d267b3b167b37695adbdffaba96c719ed50bf64659ba4ba3828f630d39`

能力：全量子项/递归；长路径；`REPARSE_POINT` 只记不跟；精确 path 对账；目录 ENUM_DONE 仅完整 scandir 后；队列不截断；配置 SHA + 卷 serial 绑定；30min 预算 / 5min checkpoint。

本轮：`stop_reason=QUEUE_EMPTY`，pending=0，dir_enum_error=0，files_identity_unresolved=0。  
旧 8,161,681,208 仅历史基线；新唯一字节 **8,186,614,545**（含显式 pit 依赖）。

合成测：`R9_SELECTED_MANIFEST_SYNTH_TEST_RESULTS.json` → **4/4 PASS**（>40 子项、深度>2、中途恢复、junction 不展开、旧子项缺失可检出）。

续核状态：`R9_SAM_SELECTED_RESUME_STATE.json`（queue_len=0，完整队列，未截断）。

---

## 3. 两套范围建议（非复制授权）

台式机目标事实（历史证据，正式仍须 ZHANGWEI 预检）：E: NTFS MarketData serial **806508DF**，GUID `{b8545ee8-e403-48c6-9d3f-09afd3e0349f}`。

### A. 独立运行最小范围（PROPOSED）

- E:\BLACKBOX 基线（本轮未重扫 E；沿用既有索引/样本）  
- 本轮已枚举 D 选定根（lab 族 + blackbox_data + JQ + BLACKBOX_* + 显式 pit 目标）  
- 唯一内容字节（D 选定）：**≈8.19 GB**  
- 分配：正式复制时用 AllocationSize；另加元数据余量  
- `backtest_lab_shadow_experiments`：已枚举元数据；**不宣称运行必需**  

### B. 保留研究资料（PROPOSED）

- A + 将 RELATED/UNKNOWN（MIN_sandbox、其余 ARCHIVE、QMT 安装树等）作**独立存档**候选  
- QMT 树「保存 ≠ 可运行安装」  
- 未查清默认 **UNRESOLVED**，不因名字陌生建议丢弃  
- 旧全 D 59.48GB **不是**已证明总量（PARTIAL）  

---

## 4. 交付清单

| 文件 | 说明 |
|------|------|
| `R9_SAM_SELECTED_MANIFEST_REPORT.md` | 本报告 |
| `R9_SAM_SELECTED_MANIFEST_SUMMARY.json` | 统计/SHA/proven 字段 |
| `R9_SAM_DEPENDENCY_MAP.json` | 逐条链接 |
| `R9_SAM_SELECTED_SCOPE_CONFIG.json` | 枚举配置 |
| `ED_LINKS_RECHECK.json` | 本机补交 |
| `selected_manifest_enumerator.py` | 程序 |
| `export_dependency_map.py` | 依赖导出 |
| `run_selected_manifest_synth_tests.py` + 结果 JSON | 测试 |
| `R9_SAM_SELECTED_RESUME_STATE.json` | 续核状态 |
| `SELECTED_D_MANIFEST.sqlite` | **本机**大 DB（仅路径/SHA） |

等待下一调度。正式复制器开发须在清单可用且范围授权之后；不改 r9_1g 硬上限。
