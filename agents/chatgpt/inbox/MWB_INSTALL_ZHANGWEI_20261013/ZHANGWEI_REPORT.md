# ZHANGWEI REPORT — MWB_INSTALL_ZHANGWEI_DESKTOP_C_20261013 (HUB re-poll)

host: ZHANGWEI
task_id: MWB_INSTALL_ZHANGWEI_DESKTOP_C_20261013
reported_utc: 2026-10-13T01:54:08.2010808Z
poll: HUB re-poll; inbox unique pointer unchanged (desk blob 6b40365f…)

## Status fields
- INSTALLED_OR_REUSED: REUSED
- OFFICIAL_PACKAGE: Microsoft.PowerToys Preview x64 already on C:
- ACTUAL_INSTALL_PATH: C:\Users\Admin\AppData\Local\PowerToys
- POWERTOYS_VERSION: 0.100.2.0
- MWB_ENABLED: True
- MWB_PROCESS_RUNNING: True (pid=14276; helper=6924)
- PEER_SAM_HOSTNAME_RESOLVED: sam.local ping=True ; IPv4 192.168.100.2 ping=False
- PAIRING_STATUS: WAITING_FOR_PRIVATE_KEY
- CROSS_SCREEN_MOUSE: NOT_RUN
- CROSS_SCREEN_KEYBOARD: NOT_RUN
- NETWORK_UNCHANGED: true
- SECRET_EXPOSED: false
- R9_HOLD_UNCHANGED: true
- COPY_AUTHORIZED: false
- USER_STEP_IF_BLOCKED: 1) Confirm Ethernet link SAM↔ZHANGWEI so 192.168.100.1↔192.168.100.2 ping works. 2) On SAM: PowerToys MWB → New Key; send hostname+key via private channel only. 3) On ZHANGWEI: enter key + peer name SAM, Connect. Do not paste keys to GitHub.

## Live checks this poll
- Ethernet adapter: 以太网 / Intel(R) Ethernet Controller I226-V / LinkSpeed=2.5 Gbps Status=Up
- Local IPv4 on that NIC: 192.168.100.1
- ARP 192.168.100.2: State=Unreachable LinkLayer=00-00-00-00-00-00
- Route to 192.168.100.2: via WLAN local=192.168.0.136 nexthop=
- MachinePool: :,:,:,:
- SameSubnetOnly=True TransferFile=False TCPPort=15100
- Private key drop files present: False
- Firewall MWB allow rules present: True

## Inbox scope note
INBOX_FOR_DESKTOP unique current remains MWB_INSTALL_ZHANGWEI_DESKTOP_C_20261013; AUTOHUB PROD stays STOP. Outbox also contains AUTOHUB_CONSOLE_POPUP_FIX_ZHANGWEI_20261013 READY but not pointed as unique current — not executed this poll.