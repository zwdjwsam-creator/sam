# ZHANGWEI STOP note 2026-10-19

Host: ZHANGWEI
Run: R9_FULL_RESUME_AFTER_ROOT_FIX_ZHANGWEI_20261015_1400
PID: 32636, now exited
Status: STOPPED
This is not a completed migration.

exit_class: PHASE_STOP
exit_code: 4
phase_stop: true
refused_before_write: false
full_plan_acceptance: false
stderr: empty

Failure: open_source_fail, WinError 206 (ERROR_FILENAME_EXCED_RANGE).
The source path is 33770 characters and repeats `manifest_backup` 336 times. That is past the Windows extended-path limit. The copy stopped before opening that source file.

Prefix: `\\192.168.100.2\E_DRIVE\BLACKBOX\数据\原始只读\JQData_reference_dictionary\31_jq_pre_download_experiment_cleanup_dryrun\`
The repeated segment is `manifest_backup\数据\原始只读\JQData_reference_dictionary\31_jq_pre_download_experiment_cleanup_dryrun\`.
Final file name: `jq_pre_download_experiment_cleanup_r0_manifest.json`

Counts at stop:
- entity DONE 1083975 of 1223767
- alias DONE 6689430
- dir DONE 233668
- stream_write_bytes 348928107919
- unique-byte budget 365004696055
- write_calls 10410956
- source_open_calls 1083976
- plan SHA 53551d39338d0f45e1cde111391bc9d296d62bd09b08703ecfce177183a24e0d

No second copy was started. Dest roots E:\BLACKBOX and E:\BLACKBOX_ENGINES were left in place. Source was not deleted. E: was not formatted.
Waiting for the next published GPT command.
