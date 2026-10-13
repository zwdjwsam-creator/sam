# ZHANGWEI台式机｜原生Windows认证与只读来源核验

task_id: R9_DESKTOP_NATIVE_SMB_LOGIN_20261013_2137
target: ZHANGWEI
status: READY
phase: SOURCE_AUTH_INTERACTIVE_READONLY
instruction: agents/chatgpt/outbox/R9_DESKTOP_NATIVE_SMB_LOGIN_20261013_2137.md
SAM: HOLD

有后续任务，执行电脑回台式机。
SAM回执无匹配4625，SMBServer元数据Unauthorized，具体1326根因未证实；已确认SAM\ThinkPad为存在且启用的本地来源账号。
用HUB现成r9_native_smb_login.py只启动一次Windows原生凭据流程，密码由用户在本机原生窗口输入，不进脚本参数/日志/HUB。
脚本有语法和假API成功/取消/1326/错卷测试；实际认证只由本轮执行。
窗口待输入先回传USER_LOCAL_INPUT_PENDING；取消/失败不循环重试、不改密码/Guest/共享/网络。
成功后E/D来源根及各一个计划文件仅metadata核验，不读业务payload。
COPY_AUTHORIZED=false
FORMAT_DONE=false
FULL_MIGRATION=false
WRITE_TESTS_NOT_RUN=true
仍准备期，不格式化、不复制、不实盘链接试验、不在E写入。
回执：agents/chatgpt/inbox/R9_DESKTOP_NATIVE_SMB_LOGIN_20261013/ZHANGWEI_REPORT.md
