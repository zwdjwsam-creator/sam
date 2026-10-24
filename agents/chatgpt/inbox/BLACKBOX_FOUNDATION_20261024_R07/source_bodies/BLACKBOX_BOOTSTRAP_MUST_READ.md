# BLACKBOX BOOTSTRAP MUST_READ

rule_id: `BLACKBOX_BOOTSTRAP_MUST_READ_R1`  
audience: 任何任务

## 权威

1. 磁盘 HAND / CURRENT / Resolver 高于聊天记忆
2. 先读 Manifest `契约/必读/MUST_READ_MANIFEST_CURRENT.json`，再读本包路由文件
3. sealed / CURRENT 禁止原地改；successor 另发
4. 禁止猜路径、禁止 superseded 当 CURRENT、禁止伪造 `HAND_DECISION.json`

## 数据存在性（一句）

`EMPTY ≠ NO_DATA`。未查询 L1/L2/L3 全层 + `DATA_ABSENCE_GATE` 前，禁止说缺少数据 / NO_DATA。

## 回测时钟（一句）

`KNOWN_AT <= SIGNAL_TIME < FILL_TIME`

## 硬边界（一句）

无 `LIVE_EXECUTION_SESSION` 不得 QMT 下单。禁止打印密钥明文。禁止为回测 `download_history`。

## 增量后研究（一句）

日增后的研究/映射/总结：先读 `DAILY_RESEARCH/CONFIG/POST_INCREMENT_RESEARCH_RULES_R1.md`（会话选择、消费绑定、Focus 资格）。下载 PASS ≠ 研究已消费。

## 写入

非黑盒任务产物不得写入 `E:\BLACKBOX` 业务树。脚本写入走 `guarded_write_path()`。

## 预检（操作前必须输出）

```
BLACKBOX_BOOTSTRAP_PREFLIGHT
TASK_CLASS = ...
MUST_READ_BOOTSTRAP = YES
MUST_READ_BOOTSTRAP_SHA256 = <from preflight script>
MUST_READ_DATA_ACCESS = YES | NOT_APPLICABLE
MUST_READ_ACQUISITION = YES | NOT_APPLICABLE
MUST_READ_FACTOR = YES | NOT_APPLICABLE
MUST_READ_BACKTEST = YES | NOT_APPLICABLE
HAND_READ = YES/NO
AUTHORITY_READY = YES/NO
```

`HAND_READ=YES` 不能替代任何 `MUST_READ_*`。  
`AUTHORITY_READY != YES` → STOP。
