# ZHANGWEI REPORT — MWB_INSTALL_ZHANGWEI_DESKTOP_C_20261013

host: ZHANGWEI
task_id: MWB_INSTALL_ZHANGWEI_DESKTOP_C_20261013
reported_utc: 2026-10-13T01:32:39.7955095Z

## Status fields
- INSTALLED_OR_REUSED: REUSED
- OFFICIAL_PACKAGE: Microsoft.PowerToys (winget id) already present; not reinstalled
- ACTUAL_INSTALL_PATH: C:\Users\Admin\AppData\Local\PowerToys (drive C:)
- POWERTOYS_VERSION: 0.100.2.0
- MWB_ENABLED: true (PowerToys settings + process running: PowerToys.MouseWithoutBorders / Helper)
- PEER_SAM_HOSTNAME_RESOLVED: PARTIAL (sam.local resolves; IPv4 192.168.100.2 ping FAIL at report time)
- PAIRING_STATUS: WAITING_FOR_PRIVATE_KEY (no SAM New Key received via private channel; MachinePool empty / not paired to SAM)
- CROSS_SCREEN_MOUSE: NOT_RUN (blocked on pairing)
- CROSS_SCREEN_KEYBOARD: NOT_RUN (blocked on pairing)
- NETWORK_UNCHANGED: true (no WiFi/SMB/migration route changes; Ethernet I226-V has 192.168.100.1/24)
- SECRET_EXPOSED: false (no security key written to PUBLIC HUB)
- R9_HOLD_UNCHANGED: true
- COPY_AUTHORIZED: false
- USER_STEP_IF_BLOCKED: On notebook SAM, open PowerToys → Mouse Without Borders → New Key, send hostname+key to ZHANGWEI via private channel only; on ZHANGWEI paste key, set peer machine name to SAM real hostname, Connect. Keep Same subnet / direct Ethernet. Do not paste keys into GitHub.

## Local actions done
1. Reused existing PowerToys Preview x64 on C: (winget showed 0.100.2 installed; did not force upgrade/reinstall).
2. Restored accidentally truncated settings.json from pre-change backup; set MouseWithoutBorders enabled=true.
3. MWB settings: TransferFile=false; SameSubnetOnly=true; WrapMouse=false; did not invent peer matrix.
4. Restarted PowerToys; confirmed MWB processes running.
5. Attempted minimal firewall allow for MWB TCP/15100 on Private/Domain (program-scoped). Firewall service itself left enabled.
6. AUTOHUB PROD remains STOP; this task did not create AUTOHUB PRs.

## Network snapshot (non-secret)
- hostname: ZHANGWEI
- Ethernet: 192.168.100.1/24 (Intel I226-V, 2.5 Gbps)
- WLAN present (unchanged): 192.168.0.136
- Tailscale present (unchanged)
- 192.168.100.2: no reply at report time

## Note
settings.json was briefly emptied during a locked-file write attempt; restored from `settings.json.bak_20261013092933` before enabling MWB. PowerToys UI/settings functional after restore.