# MWB_INSTALL_SAM_20261013 — SAM REPORT

task_id: MWB_INSTALL_SAM_NOTEBOOK_C_20261013
routing_fix: MWB_SAM_ROUTING_FIX_20261013
host: sam
reported_at: 2026-10-13T09:32:50+08:00
scope: INPUT_DEVICE_SHARING_ONLY
r9_hold: true
copy_authorized: false

## Status fields
INSTALLED_OR_REUSED: REUSED
OFFICIAL_PACKAGE: Microsoft.PowerToys winget/local v0.100.0.0 (Preview x64)
ACTUAL_INSTALL_PATH: C:\Users\ThinkPad\AppData\Local\PowerToys
MWB_ENABLED: True
MWB_PROCESS_RUNNING: True
MASTER_HOST: SAM (sam)
LOCAL_WIRED_IP: 192.168.100.2
PEER_EXPECTED_IP: 192.168.100.1
PEER_CONNECTIVITY: FAIL
PAIRING_STATUS: WAITING_FOR_DESKTOP
INPUT_SWITCH_TEST: NOT_RUN
USER_STEP_IF_BLOCKED: Desktop ZHANGWEI must be online on 192.168.100.1 with PowerToys MWB installed; enter the security key shown only on SAM PowerToys MWB UI (do not paste key into GitHub/chat). Then set layout notebook-left / desktop-right and retest cross-screen mouse+keyboard in blank Notepad.
FIREWALL_CHANGE_SCOPE: NONE (no firewall rules added/changed this run)
SECRET_EXPOSED: false
SOURCE_ED_UNTOUCHED: true
R9_HOLD_UNCHANGED: true
OLD_BLACKBOX_OUTBOX_GATE: NOT_INVOKED (per MWB_SAM_ROUTING_FIX_20261013)
STAGING_E_BLACKBOX: NOT_WRITTEN_THIS_RUN

## Config applied (non-secret)
UseService: False
ShareClipboard: False
TransferFile: False
SameSubnetOnly: True
ValidateRemoteMachineIP: True
TCPPort: 15100
SecurityKey: PRESENT_ON_DEVICE_ONLY (not exported)

## Notes
- Reused existing PowerToys at C:\Users\ThinkPad\AppData\Local\PowerToys; no reinstall.
- Enabled MouseWithoutBorders module; process PowerToys.MouseWithoutBorders is running.
- Peer 192.168.100.1 did not respond to ping; ARP empty for peer. Cannot complete pairing or input switch test.
- Did not run 外部大脑信箱_fetch_outbox.py; did not modify its HARD_BLOCK logic.
- Did not upload security key / screenshots of key to public HUB.
