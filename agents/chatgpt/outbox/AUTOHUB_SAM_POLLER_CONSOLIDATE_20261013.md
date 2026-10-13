# SAM — 收件器并发争用根因修复与回执可靠性（在网卡网络修复后执行）

task_id: AUTOHUB_SAM_POLLER_CONSOLIDATE_20261013
target: SAM
priority: 2_OF_3
status: READY_AFTER_NET_DIAG
scope: CONSOLIDATE_KNOWN_RECEIVERS_C_ONLY
R9: HOLD
COPY_AUTHORIZED: false

## ChatGPT核对报告
当前SAM有两个**每分钟**调度：
- `AUTOHUB_SAM_NOTEBOOK_POLLER` → `C:\LAN_SHARE_REPORT\AUTOHUB_SAM_ONE_SHOT\scripts\sam_notebook_poller.ps1`
- `AUTOHUB_R2_COMM_TEST_RECEIVER_SAM` → `C:\LAN_SHARE_REPORT\AUTOHUB_R2_NOTEBOOK\scripts\autohub_r2_comm_test_receiver.ps1`
两者已被加`-WindowStyle Hidden`，实证两个周期无弹窗，**不需要再次修改窗口显示**；本机额外报告反复`gh api` / PowerShell shell长时间无输出，可能是轮询器重叠、git锁、网络等待或Windows资源争用。并发是**待验证假说**，不能仅凭报告说100%已证实。

## 执行顺序（必须先取证、再减载）
1. 在C盘 `C:\LAN_SHARE_REPORT\AUTOHUB_SAM_POLLER_CONSOLIDATE_20261013\` 记录两个任务的XML备份、Action、Trigger、LastTaskResult、真实最长运行时间、近10次开始/结束时间及已写回任务ID；不要读取笔记本E/D业务数据。
2. 限定检查两个C盘轮询脚本的**实际订阅/触发消息、任务ID去重策略、可能执行的命令、Hub写入行为**；区别R2旧“通信测试”与SAM正式HUB轮询。若当前仍有消费者依赖R2，报告其准确任务ID/必要性；不得直接禁用。
3. 只要证明R2是已验收结束的历史通信测试接收器、且SAM正式poller已经能消费需要的现有READY消息（例如UGREEN/NET/MWB相关），则**停止并禁用旧`AUTOHUB_R2_COMM_TEST_RECEIVER_SAM`计划任务**，保留原XML、脚本、日志、恢复操作；不得删除。若不能证明则只引入非并发锁与安全错峰，不能随意停任一消费者。
4. 正式`AUTOHUB_SAM_NOTEBOOK_POLLER`保留；采用Windows原生单实例机制，原则：
   - Scheduled Task `MultipleInstances=IgnoreNew`；
   - 如果已有同一脚本的其他启动入口，`Global\AutoHubSAMReceiver` Mutex 或者安全C盘锁文件（用finally释放）；
   - 设置合法的只读GitHub调用超时(例如20~30秒)、有限重试上限1、每条消息幂等；
   - 明确`LastTaskResult=0x41301`仅代表正在运行，不等于失败；
   - 避免每分钟启动真实Cursor Agent/新GitHub PR/付费模型；仅在严格白名单且原有用户授权范围内处理READY消息。
5. 不向对端共享GitHub认证明文，不更新Windows用户密码、凭据、代理。网络调试正在进行时只取证，不修改任务调度；避免两个Cursor Agent同时改同一个脚本。
6. 针对`gh api`上传超时，建议分离耗时的网络访问和响应：C盘队列落地、唯一请求ID、30秒超时后检查同名HUB目标文件是否已提交、存在则核对内容不重复PUT；失败需指数退避，最多有限2次且不会阻塞当前Cursor交互。**不能凭命令行无stdout判为上传失败，先通过GitHub远端GET核对**（此前SAM popup报告实际已上传多次）。
7. 代码建议（PowerShell单实例互斥+最小流程示意；仅在确认现有脚本兼容后整合，不可原样覆盖）：

```powershell
$created = $false
$mutex = [System.Threading.Mutex]::new($false, 'Global\AutoHubSAMReceiver')
try {
  if (-not $mutex.WaitOne(0)) { exit 0 }
  # Only call audited, C-disk pre-existing SAFE inbox handler here.
  # Never turn a GitHub Markdown body into PowerShell code.
} finally {
  if ($mutex) {
    try { $mutex.ReleaseMutex() } catch {}
    $mutex.Dispose()
  }
}
```
注意：首次Mutex由当前账号权限创建可能受多用户影响；如异常不要绕开安全锁，改为TaskScheduler IgnoreNew并报告。

8. 验收：连续至少两个周期无黑窗；正式SAM poller每次运行不重叠；定点HUB只读收件成功；一次真实**无模型、无新PR、C-only**的已授权任务去重测试，HUB上传仅一次；监控Shell/gh调用是否仍卡，若变差立即按XML/脚本备份**准确回滚**。
9. 不要为了减少黑窗口停掉正式轮询器；不改变绿联2.5G网络IP/驱动、MWB或双方IP配置。

## 状态上报
`agents/chatgpt/inbox/AUTOHUB_SAM_POLLER_CONSOLIDATE_20261013/SAM_REPORT.md`，
本机 `C:\LAN_SHARE_REPORT\AUTOHUB_SAM_POLLER_CONSOLIDATE_20261013\REPORT.md`；
字段：R2_RECEIVER_REQUIRED/LEGACY_R2_DISABLED_IF_SAFE/
FORMAL_POLLER_RETAINED/MUTEX_OR_IGNORNEW/UPLOAD_RETRY_IDEMPOTENT/
POWERSHELL_PROCESS_COUNT_BEFORE_AFTER/REPORT_REMOTE_CONFIRMED/
NO_VISIBLE_POPUP_TWO_CYCLES/ROLLBACK_READY/R9_HOLD=true。
