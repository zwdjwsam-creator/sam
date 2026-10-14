# 四场景真实补测：junction、长路径、A/B/C恢复

task_id: R9_DESKTOP_REAL_CAPABILITY_PILOT_20261014_1345
execution_host: ZHANGWEI
SAM: HOLD
status: READY
PILOT_WRITE_AUTHORIZED: true
COPY_AUTHORIZED: false
FULL_MIGRATION: false

## 审核与范围
1313修复包21文件SHA独立核验一致，code摘要58e5765a8270a97e9b7cbbefa1178c6c873816419810ea51839f31baa30e3a59与样本96c42610d94f02a99aacee62b5ad3aa0ae14c1afdfc1a1102bfbcf0b9e23dc10独立核对一致。
ChatGPT独立重跑6项能力测试（Linux禁止真API替身，C状态路径仅作便携适配）：目录逆序0、CLI故障->恢复、junction操作、独立验收、NORMAL重跑均通过。56项总测试是本机回报，不声称独立复跑56项。本任务是真实补测，不能把隔离测试当实盘结果。
批准合同：agents/chatgpt/outbox/R9_DESKTOP_REAL_CAPABILITY_PILOT_20261014_1345/PILOT_EXECUTION_CONTRACT.json，仅此任务4场景。按合同新run/state执行，不复用开发测试状态或1232授权。
仅 E:\R9_CAPABILITY_PILOT_20261014 公共根和 NORMAL/A/B/C 分根内已冻结样本：每场景3唯一实体、57498内容字节、5普通路径（含2个长硬链接夹具）、2junction、24普通目录（含公共父），4场景229992唯一内容字节。
两个junction指向本场景内目标目录；不能指UNC、旧试验目录或E:\BLACKBOX。三源小文件均来自E，D样本是D来源junction类型及目标重映射，不能声称读取D业务payload。
两目标新增alias是测试夹具，不计成正式计划源alias。按真实路径长度分别报告NORMAL和A/B/C，不把369固定套用全部场景。

## 执行前
1. 保留旧基础样本 E:\R9_POSTFORMAT_PILOT_20261014 和状态，不重跑、不删除。确认新公共根最初不存在，各场景新C状态不存在；若存在未知目录/状态，停止报告，不清理覆盖。
2. 在 C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013 确认实际所有模块与审核1313包一致，code摘要=58e5765a8270a97e9b7cbbefa1178c6c873816419810ea51839f31baa30e3a59。CAPABILITY_SAMPLE.json来自 C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014，SHA=96c42610d94f02a99aacee62b5ad3aa0ae14c1afdfc1a1102bfbcf0b9e23dc10。运行前不重生成样本，不改代码。任意不一致本授权失效，STOP。
3. 将批准合同存 C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_CAPABILITY_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json。各run id和C状态按合同。现有未提升ZHANGWEI\Admin/SMB会话保持，不登录/找密码/断IPC$。
4. 只读查询新卷D86AEE82/3630886530、NTFS、物理UniqueId eui.E8238FA6BF530001001B448B42E694AE；保持入口真实现场探测，不注入backend/os_api。两来源junction只读核对tag0xA0000003和实际目标与样本一致；三源卷/fileid/大小保持计划匹配，mtime使用本次句柄观察。查询失败/身份变化STOP，不改源/共享。
5. 四场景各跑dry-run，合法授权、样本计数正确、Win32写入0；dry-run不代替后续execute现场检查。

## 实际命令与顺序
公共参数：
--sample C:\LAN_SHARE_REPORT\R9_DESKTOP_PREP_JUNCTION_LONGPATH_RESUME_PILOT_20261014\CAPABILITY_SAMPLE.json
--contract C:\LAN_SHARE_REPORT\R9_DESKTOP_REAL_CAPABILITY_PILOT_20261014\PILOT_EXECUTION_CONTRACT.json

每行命令尾添加上述两个公共参数，工作目录如第2步。
NORMAL：
python -m r9_capability_pilot execute --scenario NORMAL
通过后原命令正常重跑一次。首次copy3/link2/reparse2/acceptance true；重跑copy0/link0/reparse0/acceptance true。

A：
python -m r9_capability_pilot execute --scenario A --fault A
必须只在预期INTERRUPT_A退出3，状态INTENT带提交后fileid/卷/SHA；先C上导出阶段证据，然后：
python -m r9_capability_pilot execute --scenario A
同run恢复resumed_entities1，不能重抄该已提交实体；其余尚缺2实体允许正常复制，最终验收true。

B：
python -m r9_capability_pilot execute --scenario B --fault B
必须只在预期INTERRUPT_B退出3，第一alias DONE、第二缺；导出证据后：
python -m r9_capability_pilot execute --scenario B
恢复copy0/link1，最终验收true。

C：
python -m r9_capability_pilot execute --scenario C --fault C
必须只在预期INTERRUPT_C退出3，第一alias已创建INTENT、第二缺；导出证据后：
python -m r9_capability_pilot execute --scenario C
恢复copy0/resumed_links1/link1，最终验收true。

每场景初始+重跑/恢复各2次，总8个execute，不自动多次尝试。受控RuntimeError是预先指定测试故障，不是任意失败都可继续恢复；只有日志与状态明确匹配指定故障才继续。如果非预期错误、验收false或状态不匹配，立即全任务停止，保留目录/状态，不重置/删除/改码后重试。

## 验收及回执
每场景完整独立验收true：3唯一fileid不同、同卷3630886530、SHA/大小与本次复制stage一致、2个长alias同实体、目录覆盖、2junction实际tag/target、通过junction打开对应子文件的身份/内容正确。只读no-follow列样本精确路径及计数，不递归跟随junction统计实体。
记录真实AllocationSize按唯一实体去重；逻辑路径含2alias但不含junctionfollow访问路径。无残留partial；统计真实文件重写、硬链接/重解析新增与已有目录API调用，不能把未采集的计数冒报0。可以额外只读核验清单覆盖，不额外execute。
预期A/B/C均是受控故障后恢复，不证明任意强制断电、temp中途崩溃均已验证，报告该限制。
交付 agents/chatgpt/inbox/R9_DESKTOP_REAL_CAPABILITY_PILOT_20261014/
ZHANGWEI_REPORT.md、8个execute及dry-run日志、REAL_CAPABILITY_RESULT.json、每个故障点前/后持久化摘要、新合同hash。不上传payload/凭据。
完成或非预期失败即HOLD_PENDING_REAL_IO_REVIEW，合同授权不可扩展；不全量，不格式化，不清试验目录。
PILOT_WRITE_AUTHORIZED=true (THIS_TASK_ONLY)
COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false (补测结果待审，完整迁移还未授权)
执行电脑=ZHANGWEI；SAM=HOLD。更新INBOX_FOR_CHATGPT.md。
