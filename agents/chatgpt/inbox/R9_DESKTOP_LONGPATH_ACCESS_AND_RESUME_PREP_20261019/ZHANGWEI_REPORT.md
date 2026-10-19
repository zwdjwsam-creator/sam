# ZHANGWEI 1840 报告

task_id: R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019_1840
host: ZHANGWEI
status: CAPABILITY_PARTIAL_NOT_IMPLEMENTATION_READY
COPY_AUTHORIZED=false
IMPLEMENTATION_READY=false
full_plan_acceptance=false

## 现成短共享

`\\192.168.100.2\BLACKBOX` 和 `\\192.168.100.2\E_DRIVE\BLACKBOX` 是同一个目录。卷 2387166462，文件号 1125899907016167，大小 0。没有新建共享。

这条短共享只少 8 个字符。用它打开计划里库存路径不少于 32000 字符的 133 个文件时，129 个能打开并且卷、文件号、大小与计划一致。剩下 4 个仍然是 WinError 206。所以短共享不能作为这批文件的访问入口。

## 相对目录句柄

从批准的 `E_DRIVE\BLACKBOX` 短句柄开始，逐层 `NtCreateFile`，只读，`FILE_SHARE_READ`，打开重解析点但不跟随。3 个先前打不开的源文件读完了，读前读后的身份一致：

- 844424930324628，1166 字节，SHA256 f1b5e3bfcf220ff36e9b1518ee2208a4e189b6b91d85ba66cb4ea3f79553b575
- 844424930324634，9095 字节，SHA256 3fde2b052b555a4e4d2d3a0b86ba004c6fe222fa5d109abed20f3f99c1607883
- 844424930324640，558 字节，SHA256 a65ee5d885a1c300a901d3e6cf1c7ea0df96bb2498644a92a2a06b0d07b9c3d5

第 4 个没有读到。文件号 844424930324643，816 字节。目录层已经走完，最后一次打开文件分量失败。NTSTATUS `0xC0000039`（STATUS_OBJECT_PATH_INVALID），WinError 161。失败阶段是 file。最后的文件名是 50 个普通字符，没有冒号、结尾空格或控制字符。

因此相对句柄在这条 SMB 上对多数近限文件可用，但不能把整条恢复链标成可执行。没有改生产代码，没有新 digest，没有恢复复制。

## 没有改动的东西

源目录、真实目标 E、原 full_1400.sqlite 和 run_bind 都保持原样。已完成的 1083975 个实体、348928107919 逻辑字节、6689430 个别名和 233668 个目录仍在。
