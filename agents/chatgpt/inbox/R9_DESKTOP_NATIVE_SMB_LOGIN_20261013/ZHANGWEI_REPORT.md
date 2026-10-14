# ZHANGWEI_REPORT — R9_DESKTOP_NATIVE_SMB_LOGIN_20261013_2137

host: ZHANGWEI
SAM: HOLD
state: AUTH_NOT_COMPLETE
authenticated: false
winerror: 1219
SOURCE_ACCESS_VALID: false
SOURCE_ROOT_METADATA_OK: false
SOURCE_LIVE_STABLE_FILE_READ_VALID: NOT_RUN
COPY_AUTHORIZED: false
FORMAT_DONE: false
FULL_MIGRATION: false
WRITE_TESTS_NOT_RUN: true

用户授权后，用 SAM\ThinkPad 对 \\192.168.100.2\E_DRIVE 做了一次连接。没有保存凭据，没有映射盘符，没有读取业务内容。

Windows 返回 1219：同一服务器已有另一套会话身份。现有会话是 \\192.168.100.2\IPC$，状态 OK。没有断开该会话，也没有删除已保存凭据。源目录 metadata 没有读取。

密码没有写入本报告、STATUS 或 HUB。
