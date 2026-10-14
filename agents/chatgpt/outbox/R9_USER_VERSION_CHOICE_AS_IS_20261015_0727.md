# 用户已选择方案1：140个异常文件按现状迁移并标记

decision_id: R9_USER_VERSION_CHOICE_AS_IS_20261015_0727
user_choice: 1
VERSION_CHOICE: AS_IS_MIGRATE_MARKED
VERSION_CHOICE_CONFIRMED: true
execution_host: ZHANGWEI
active_task: R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015_0725
SAM: HOLD
status: READY_SUPPLEMENT
COPY_AUTHORIZED=false
FULL_COPY_AUTHORIZED=false
PILOT_WRITE_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false
CANDIDATE_EXECUTABLE=false
full_plan_acceptance=false

用户明确选择上一轮选项1：“按当前来源原样迁移并标记异常，旧版本后续单独处理。”
此决定接受140个文件的当前观察版本进入最终候选，不表示这些版本内容正确，也不授权恢复、跳过或改写来源。

## 台式机ZHANGWEI立即继续同一个0725任务
本文件覆盖0725任务中所有 VERSION_CHOICE=PENDING_USER / 等待用户版本选择的条款；其余技术范围与复制授权限制保持原任务规定。
- 140个不同实体全部纳入迁移候选，保留127 CRLF、13 EMPTY及证据中的size/SHA/身份/观察时间，保留SUSPECT_VERSION标记和具体清单。不得自动填回旧内容、过滤空文件或宣称已恢复。
- 将新候选侧表、准备合同与报告的版本选择更新为 AS_IS_MIGRATE_MARKED，注明用户选择及本决定路径；若修改已冻结候选，重算确切SHA并同步合同绑定，不沿用过期摘要。
- 继续原任务的52条有限metadata补齐、42逻辑视图处理、既有目标修复重放、统计/冻结/统一入口绑定和零目标写入验证；不重新全源扫描、不新增实盘试验、不另起复制主体。
- 不再以“等待140文件版本选择”作为阻塞。一次回报其余真实技术阻塞；收到此补充后ACK中注明 decision_id。若已在执行，接入现有工作，不重复启动。
- 完成后上传原任务报告目录并停止待审。正式迁移须待最终包审核和对应明确复制授权；本次选择本身不是全量复制授权。

## 笔记本SAM
保持HOLD，保持来源及既有证据可用；本轮无需继续找旧备份、恢复内容或重扫。

本决定只解除版本处理方式的待定项。原因及旧版本恢复另案处理。
