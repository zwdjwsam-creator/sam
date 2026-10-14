# ZHANGWEI_REPORT — R9_DESKTOP_FIX_ACTUAL_PILOT_EXECUTE_CHAIN_20261014_1124

host: ZHANGWEI
SAM: HOLD
state: HOLD_PENDING_CODE_REVIEW
COPY_AUTHORIZED: false
PILOT_WRITE_AUTHORIZED: false
FULL_MIGRATION: false
IMPLEMENTATION_READY: false
WRITE_TESTS_NOT_RUN: true

公开 `execute` 在授权通过后会调用 `production_run`。未授权仍是 `PILOT_WRITE_REFUSED`，不会进入生产链。合法授权如果现场目标检查失败，在第一次写入前返回具体原因，例如 `REPARSE_ANCESTOR`。真实 Win32 后端在 `PILOT_REAL_IO` 下仍然拒绝，本轮没有向 E 写入，也没有创建试验目录。

测试从 `execute` 进入：隔离后端复制 2 个实体、创建 38 个硬链接，验收通过；第二次写入次数不变。错误卷、错误磁盘、过期代码摘要、样本摘要变化、祖先重解析都在写入前拒绝。dry-run 和未授权 execute 的 Win32 写入次数是 0。全量 `copy` 仍然拒绝。

`r9_bounded_pilot.py` 已计入代码 digest `56c75ad07c3216d2fafa79086c024a197fd4a118e00ceccf1c7d1e19487db11a`。样本 SHA256 `a0330b0115e2cd603c792807266633cdf7206a82d98d53d1afb0d7a52ce361c3`。mtime 用的是上次只读句柄读到的值，不是测试占位字符串。
