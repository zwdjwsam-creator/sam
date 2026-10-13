# UGREEN 2.5G SAM REPORT — 2026-10-13T09:47:47+08:00

task_id: SAM_UGREEN_2P5G_DRIVER_INSTALL_VERIFY_20261013
host: sam
scope: NOTEBOOK_USB_2P5G_DRIVER_ONLY
r9_hold: true
copy_authorized: false

## Checklist
- HARDWARE_PRESENT: true
- USB_VID_PID: VID_0BDA&PID_8156 (Realtek RTL8156)
- PRODUCT_ID_CONFIRMED: chip matches UGREEN 25051/25052 family; physical package label not visually confirmed this run
- DRIVER_ALREADY_WORKED: true (no reinstall)
- DRIVER_INSTALL_ATTEMPTED: false
- DRIVER_SOURCE_AND_SIGNATURE: Windows/Microsoft published inbox driver; INF=rtucx21x64.inf; Provider=Microsoft
- DRIVER_VERSION: 11.4.211.2022
- DEVICE_MANAGER_OK: True (ProblemCode=0)
- OLD_ETHERNET_PRESERVED: true (Realtek PCIe GbE still present; currently Disconnected/0 bps; IP on old NIC=192.168.100.2)
- NEW_ADAPTER_NAME: 以太网 / Realtek Gaming USB 2.5GbE Family Controller
- LINK_SPEED_NEGOTIATED: 2.5 Gbps
- LINK_2P5G_PASS: True
- NEW_USB_NIC_IP: 169.254.64.211 (APIPA — no production static IP moved this run)
- DIRECT_PEER_AVAILABLE: false (ping 192.168.100.1 failed)
- NETWORK_PATH_ON_NEW_NIC: NOT_PASS (no L3 path on new NIC to 192.168.100.1; IP not cut over)
- SMB_OVER_NEW_NIC: NOT_TESTED
- INSTALLER_RESTART_REQUIRED: false
- SAFE_TO_REBOOT: false (not needed)
- REBOOT_PERFORMED: false
- AFTER_REBOOT_TEST: N/A
- USER_ACTION_REQUIRED: Optional: assign static IP on USB NIC only after user-approved cutover window (do not dual-bind 192.168.100.2). Peer ZHANGWEI must respond on direct link; confirm package label 25051 vs 25052. Then retest NETWORK_PATH/SMB.
- SOURCE_E_D_WRITE_COUNT: 0
- BLACKBOX_R9_HOLD: true
- COPY_AUTHORIZED: false

## Verdict
DRIVER_PASS + LINK_2P5G_PASS. Did not install third-party driver (inbox driver already healthy at 2.5 Gbps). Did not reboot. Did not change IP/routing/SMB. NETWORK_PATH/SMB pending peer L3 + optional user-approved IP cutover.

## Local artifacts
C:\LAN_SHARE_REPORT\UGREEN_2P5G_DRIVER_20261013\REPORT.md
C:\LAN_SHARE_REPORT\UGREEN_2P5G_DRIVER_20261013\STATUS.json
