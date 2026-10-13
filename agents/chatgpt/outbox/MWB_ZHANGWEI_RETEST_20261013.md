# 台式机 ZHANGWEI：MWB 双机连接复测

task_id: MWB_ZHANGWEI_RETEST_20261013
target: ZHANGWEI 台式机 Cursor
status: READY
R9: HOLD
COPY_AUTHORIZED: false

## 背景
笔记本 SAM 已完成 Mouse Without Borders 入站连接问题的本机修复，报告在 `agents/chatgpt/inbox/MWB_SAM_INBOUND_15100_FIX_20261013/SAM_REPORT.md`。但是否能从台式机访问笔记本仍未验证。

## 本次唯一任务
1. **只读**复测台式机到笔记本有线地址 `192.168.100.2` 的 TCP 端口 15100 和 15101，记录每个端口能否连接及测试时间。分别记录 ping 与 TCP，不要混同。
2. 任何端口不通：记录事实、关键错误及实际使用的网络接口，报告 `WAITING_SAM_FOLLOWUP`，停止，不要自行修改现有网络配置。
3. 两个端口均可达：核对官方 PowerToys Mouse Without Borders 是否真正显示两台设备成功连接；关注之前尝试连接错误 Wi-Fi 地址 `192.168.0.62` 的问题是否依然存在。网络端口可达不等于应用已连接。
4. 若官方设置仍未完成配对，给用户显示所需的最少界面操作；不生成新密钥，不将密钥写入报告或公开仓库。不根据版本差异自行升级软件。
5. 如果用户已完成配对，再请用户亲自尝试两次鼠标跨屏，并在两台电脑空白记事本测试键盘输入。未做实测的一律标记 `USER_TEST_PENDING`，不可宣称通过。
6. 禁止更改现有有线网络、SMB 或业务文件，不能触发 R9 数据迁移，保持 `COPY_AUTHORIZED=false`。不要安装额外软件或改变安全设置。

## 报告
上传到 `agents/chatgpt/inbox/MWB_ZHANGWEI_RETEST_20261013/ZHANGWEI_REPORT.md`。
须列出两端口结果、应用连接状态、是否有错误路线、跨屏验收状态及是否需要用户操作。
