# ZHANGWEI 只读定位报告

task_id: R9_DESKTOP_TRIAGE_OVERLONG_MANIFEST_PATH_20261019_1826
host: ZHANGWEI
status: TRIAGE_REPORT_READY
queried_at: 2026-10-19T18:30:48+08:00
COPY_AUTHORIZED=false
full_plan_acceptance=false

本轮没有启动复制，没有改代码、计划、契约、run_bind 或 state。code_digest 仍是 62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3。

## 停机点

失败发生在 `open_source_stable(source_path)`，也就是 `CreateFileW(to_win_long_path(source_path))`。不是创建硬链接、不是回读临时文件、也不是哈希调用。

结果日志是 GBK。按 GBK 解析后，传给打开函数的源路径是 32759 个 Python 字符，UTF-16 也是 32759。`to_win_long_path` 之后的 API 字符串是 32765。组件 1688 个，最长组件 51，没有超过 255。`manifest_backup` 出现 336 次。路径 SHA256 是 `1d1e7115a47ca9098e19b5855464a32ffa2f8d97cb080cd357c0eb6791983c81`。

先前写成 33770，是把这份 GBK 日志按 UTF-8 替换解码后的字符数，不是源路径长度。日志文件本身 75321 字节，因为同一条路径在 reason 和 error 里各出现一次，也不能当成路径长度。

再次打开这条唯一源路径，得到同一个 WinError 206。`\\?\\` 前缀不能避开这个失败。

## 实体

- entity_key: `2387166462|844424930324628`
- logical_size: 1166
- nlinks: 1
- is_reparse: 0
- 计划里只有 1 条路径，所以没有更短的来源别名
- `ORDER BY path` 的代表路径就是这条失败路径
- state 里没有这个 file_id 的行，实体没有被标成 DONE
- links 表没有这一行

代表路径的目标 API 长度是 32742，源 API 长度是 32765。源是 UNC，目标是 `E:\`。打开失败的是源。

## 目录为什么能全部 DONE

计划里的目录行没有一条 API 长度超过 32767，也没有组件超过 255。失败文件的直接父目录 API 长度是 32690，仍在本地 `\\?\` 路径可创建的范围内。目录阶段写的是目标路径，不是这条 UNC 源路径。因此 dir DONE 233668 和这个文件打不开可以同时成立。

第一层 `manifest_backup` 目录在计划里是普通目录，不是重解析点。现场只读打开它的短 UNC（API 长度 135）成功，卷 2387166462，不是重解析点。没有顺着 336 层往下枚举。计划没有把这些前缀标成重解析，所以不能把这次失败说成重解析循环，也不能说文件损坏。

## 范围

对本地候选 `paths` 做了一次流式统计，用时 42.534 秒。阈值是 API 字符串 UTF-16 长度超过 32767。

- 文件实体 1223767
- 超过 32767 的文件实体：1 个，唯一字节 816。它的源 API 长度 32769，目标 API 长度 32746。文件名落在 `missing_file_targeted_download_audit_manifest.json`
- 没有任何实体同时拥有一条不超限的短来源路径
- 超限目录行：0

刚停住的 1166 字节文件源 API 是 32765，按 32767 这个字面阈值不会被算进上面那 1 个。它实际打开仍然是 206。因此当前 API 打不开的至少是这两个小文件：1166 字节和 816 字节。没有把整条路径上传。

## 已保留的进度

run_id 仍是 R9_FULL_RESUME_AFTER_ROOT_FIX_ZHANGWEI_20261015_1400。
entity DONE 1083975，logical_size 合计 348928107919。
alias DONE 6689430。
dir DONE 233668。
非 DONE 行 0。
剩余计划实体 139792。
结果 JSON 里的 stream_write_bytes 也是 348928107919。这两个数这次相等，但它们不是同一个定义，不能把它写成完整验收百分比。
