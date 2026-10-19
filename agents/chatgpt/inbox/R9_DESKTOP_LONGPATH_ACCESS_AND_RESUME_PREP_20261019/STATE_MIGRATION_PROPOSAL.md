# 状态迁移说明（未对原库执行）

task_id: R9_DESKTOP_LONGPATH_ACCESS_AND_RESUME_PREP_20261019_1840

原 `full_1400.sqlite` 和其中的 run_bind 没有修改。
没有做 8GB 状态库的备份，因为还有 1 个 816 字节的源文件没有读到，不能把恢复链标成可执行。

已保留的进度仍然是：
- run R9_FULL_RESUME_AFTER_ROOT_FIX_ZHANGWEI_20261015_1400
- code_digest 62aff763e4c12d782039e067ea12985e36d2164af41564453249774c89d84ae3
- plan 53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d
- dest volume 2694002743
- entity DONE 1083975，logical bytes 348928107919
- alias DONE 6689430
- dir DONE 233668

以后如果相对打开把那 1 个文件也读通，恢复时要用 SQLite backup API 复制 state，在副本上绑定新摘要。不能改原 run_bind，也不能建空库重抄。旧 runner 恢复 DONE 实体时仍会按原规则读内容做校验，不能把它说成零读取。
