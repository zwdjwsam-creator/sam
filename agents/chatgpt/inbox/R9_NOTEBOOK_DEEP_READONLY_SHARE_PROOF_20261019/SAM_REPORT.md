# SAM_REPORT

task_id: R9_NOTEBOOK_DEEP_READONLY_SHARE_PROOF_20261019_1906
host: SAM
start_time: 2026-10-19T19:27:27+08:00
status: FACTS_READY
COPY_AUTHORIZED=false
FULL_MIGRATION=false
IMPLEMENTATION_READY=false

## 已完成

1. 领取时 R9LP_RO 不存在，已写 ACK，没有创建第二个共享。
2. 指定 anchor 现存，205 字符，普通目录，reparse=false，卷序列号 2387166462（8E49-44FE）与要求一致。自 E:\ 到该 anchor 的祖先目录均为普通目录且同一卷。
3. 用 \\.\E: 提示句柄 OpenFileById 打开 file_id 844424930324643。同一句柄读到 816 字节。读前读后 file_id、卷序列号、size=816、mtime 不变。SHA-256 = 62141a61f0f729dd563160b0835fe4af86cba703a470e181fb0b4c9892e8b007。文件属性 0x20，不是目录，不是 reparse。atime 因本次读取更新。
4. 一次正常 UAC 后创建共享：Name=R9LP_RO，Path 与 anchor 逐字符一致，Temporary=true，CachingMode=None，唯一权限 SAM\ThinkPad Read Allow。
5. 固定 UNC 根为 \\192.168.100.2\R9LP_RO（23 字符）。相对本地 anchor，客户端前缀少 182 字符。服务端 NTFS 路径未改。

## 路径观察

GetFinalPathNameByHandle 给出的 DOS 路径为 32742 字符，完整落在该 anchor 之下，叶子名为 missing_file_targeted_download_audit_manifest.json。同一 97 字符目录段重复 336 次。路径字符串的 UTF-8 SHA-256 在 LOCAL_FILE JSON，路径正文未上传。

## 未做

未扫全盘，未改名，未写源数据，未改 NTFS ACL / 账号 / 密码 / 安全策略，未扩大共享权限，未上传业务字节。