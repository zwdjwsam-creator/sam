# BLACKBOX CURRENT Dictionary Rule Library (R1)

## 概述

本目录是 D 盘回测引擎 (`D:\backtest_lab`) 正式规则库的一部分。

- **rule_library_id**: `BLACKBOX_CURRENT_DICTIONARY_R1`
- **来源**: BLACKBOX 主规则库 CURRENT 快照（只读复制）
- **生成任务**: `D_BACKTEST_ENGINE_BLACKBOX_CURRENT_DICTIONARY_RULE_IMPORT_R1`
- **生成时间**: 2026-06-19T07:56:12+08:00

## 来源路径（BLACKBOX 只读，未修改）

- `E:\BLACKBOX\规则库\data_dictionary\jqdata_rule_library_current`
- `E:\BLACKBOX\规则库\data_dictionary\jqdata_factor_dictionary_current`

## 运行约束

1. D 盘引擎运行时**只允许读取本目录副本**，不得依赖 `E:\BLACKBOX` 活路径。
2. JQData 官方字典 CURRENT 已作为 D 盘规则库输入。
3. 260 因子字典 CURRENT 已作为 D 盘规则库输入。
4. **因子值不得下载**（`factor_value_download_allowed=false`）。
5. **因子清洗未启动**（`factor_cleaning_active=false`）。
6. **正式回测未启动**（`formal_backtest_active=false`）。
7. **engine core 未修改**（`engine_core_modified=false`）。
8. `E:\BLACKBOX` 在本次导入中保持只读，未被修改。

## 后续步骤

真实数据就绪后，先在 **shadow engine** 使用这些规则做：

- 字段覆盖验证
- PIT 规则验证
- 清洗规则验证
- 因子映射验证

## 源快照

完整源树备份位于：

`D:\backtest_lab\10_reference_inputs\blackbox_current_dictionary_R1\source_snapshot`
