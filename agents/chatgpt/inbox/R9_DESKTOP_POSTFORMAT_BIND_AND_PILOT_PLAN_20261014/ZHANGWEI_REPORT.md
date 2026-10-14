# ZHANGWEI_REPORT — R9_DESKTOP_POSTFORMAT_BIND_AND_PILOT_PLAN_20261014_1109

host: ZHANGWEI
SAM: HOLD
state: HOLD_PENDING_REVIEW
FORMAT_DONE: USER_REPORTED_TRUE
TARGET_POSTFORMAT_VERIFIED: true
COPY_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false
WRITE_TESTS_NOT_RUN: true

E: 对应物理盘 0，UniqueId `eui.E8238FA6BF530001001B448B42E694AE`，与预期一致，不是 BLOCKED。整盘大小 4000787030016 字节。E 卷大小 4000769372160 字节，等于任务给出的容量数字；分区大小 4000769376256。三者分开记录。

新 NTFS serial 是 `D86AEE82`，不是历史 `806508DF`。分区 GUID 仍是 `{b8545ee8-e403-48c6-9d3f-09afd3e0349f}`，只作为观测，不作为新授权。文件系统 NTFS，簇 4096，空闲 4000538427392。根目录只有 `System Volume Information`，没有业务目录。没有删除任何东西，也没有创建 `E:\R9_POSTFORMAT_PILOT_20261014`。

同一未提升上下文重查来源：E 根卷 2387166462，D 根卷 3187598165。没有登录，没有断开 IPC$。磁盘查询不需要另开提升上下文。

冻结计划仍是 6025072640 字节、无 WAL。SHA256 沿用 2026-10-13 的 `94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba`，这次没有重算。`r9_formal_executor.py copy` 仍会拒绝写入，本轮没有运行。

小规模方案见 `PILOT_PLAN.md`：2 个实体、40 条普通路径、3 个目录。E 实体的 39 条路径可做同卷硬链接。junction 不能在这组样本里闭合，所以不纳入。
