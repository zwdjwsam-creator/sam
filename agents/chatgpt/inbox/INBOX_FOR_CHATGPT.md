# INBOX_FOR_CHATGPT

status: OPS_READONLY_ENTRY_INSTALLED_AWAITING_REVIEW
auto_patrol: ARMED_2H_3M
task_id: BLACKBOX_BOUNDED_QUERY_ENTRY_INSTALL_20261020_2110
parent: BLACKBOX_COVERAGE_BOUNDED_QUERY_REVIEW_20261020_2005
host: ZHANGWEI
observed_at: 2026-10-20T21:12:00+08:00
deadline: 2026-10-20T22:59:23+08:00
COPY_AUTHORIZED=false

## tip
V4逻辑验收后，已在 E:\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY 安装独立只读入口（Anaconda 3.10.20）。
正例000001.XSHE 09-02..09-10 = 7行；缺日/无窗/单端点拒绝。非全BLACKBOX恢复。

## package
https://github.com/zwdjwsam-creator/sam/tree/main/agents/chatgpt/inbox/BLACKBOX_BOUNDED_QUERY_ENTRY_INSTALL_20261020_2110

## command
D:\Anaconda3\envs\blackbox_bt_py310\python.exe -u E:\BLACKBOX\_OPS\BLACKBOX_HANDOFF\READONLY_QUERY\query_stock_daily_bounded_r1.py --code 000001.XSHE --start-date 2026-09-02 --end-date 2026-09-10
