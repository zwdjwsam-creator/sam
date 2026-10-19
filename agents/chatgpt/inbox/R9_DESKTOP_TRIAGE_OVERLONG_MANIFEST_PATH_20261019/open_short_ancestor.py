# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
from r9_pilot_common_r9fix import open_source_stable, handle_identity, CloseHandle
from r9_plan_reader import map_inventory_path

inv = r"E:\BLACKBOX\数据\原始只读\JQData_reference_dictionary\31_jq_pre_download_experiment_cleanup_dryrun\manifest_backup"
src = map_inventory_path(inv)["source_path"]
handle = open_source_stable(src)
try:
    ident = handle_identity(handle)
finally:
    CloseHandle(handle)
print("api", len(__import__("r9_pilot_common_r9fix").to_win_long_path(src)))
print("volume", ident["volume_serial"])
print("file_id", ident["file_id"])
print("size", ident["size"])
print("nlinks", ident["nlinks"])
print("reparse_rejected", False)
