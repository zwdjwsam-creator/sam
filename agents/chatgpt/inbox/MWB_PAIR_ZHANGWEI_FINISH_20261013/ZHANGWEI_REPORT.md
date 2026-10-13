# ZHANGWEI_REPORT — MWB_PAIR_ZHANGWEI_FINISH_20261013

host: ZHANGWEI  
task_id: MWB_PAIR_ZHANGWEI_FINISH_20261013  
status: USER_TEST_PENDING / WAITING_PEER_15100  
r9_hold: true  
copy_authorized: false  
SECRET_EXPOSED: false  
NETWORK_UNCHANGED: true  

## Evidence checklist

| Field | Result | Notes |
|-------|--------|-------|
| MWB_PROCESS | PASS | PowerToys.MouseWithoutBorders running (e.g. PID 27716) |
| 15100/15101 | PASS | listening locally on :: |
| PEER_PING | PASS | 192.168.100.2 reachable |
| PEER_15100 | FAIL | TCP 15100/15101 to .2 not succeeding from desktop probe |
| HOSTNAME | PASS | local ZHANGWEI; pool contains `sam` |
| POWERTOYS_VER | PASS | 0.100.2.0 (peer version NOT_VERIFIED) |
| PAIR_HANDSHAKE | PARTIAL | see below |
| MOUSE_CROSS_SCREEN | NOT_TESTED | needs live user proof |
| KEYBOARD_CROSS_SCREEN | NOT_TESTED | needs live user proof |
| SECRET_EXPOSED | false | key not written to HUB/report body |
| NETWORK_UNCHANGED | true | no IP/SMB/route edits |
| R9_HOLD | true | |

## What was wrong (logs, timestamps)

Pre-fix (still true for outbound path):

- `12:26:55` Cannot resolve IPv4 Addresses of machine: sam (intermittent)
- `12:27:54` `invalid package from sam: 0` (×6)
- `12:28:25` / `12:37:04` tcpClient.Connect timeout to **sam:fe80::…** and **sam:192.168.0.62:15101** (WLAN/mDNS — wrong path)

DNS on desktop for `sam.local` → `192.168.0.62` + link-local AAAA (NOT 192.168.100.2).

MachinePool already had hostname `sam` (lowercase). Name2IP had been set to uppercase `SAM`, mismatching pool name.

## Single fix applied

- **Only** corrected Name2IP to:
  - `ZHANGWEI 192.168.100.1`
  - `sam 192.168.100.2`
- Key not regenerated; UseService/ShareClipboard/TransferFile remain false; ValidateRemoteMachineIP false; SameSubnetOnly true.
- No firewall disable; no hosts/DNS/IP/SMB changes; no R9.

## After fix

- `12:36:21` MWB restarted; listening 15100/15101
- `12:36:27` `New connection from client: [sam].` — **no new `invalid package` after this**
- `12:37:04` outbound still attempted via fe80 / 192.168.0.62 (Name2IP not observed to override DNS on this build/path)
- Desktop→`.2:15100` still FAIL → cannot claim full pair

## User actions needed (this PC)

1. Open **PowerToys → Mouse Without Borders** (already launched if available).
2. Confirm device row shows **sam** (no extra spaces) and Security Key matches notebook (**type in UI if Connect still fails**; do not paste into chat/HUB).
3. On **notebook**: ensure MWB process is up and **listening on 15100** bound such that `192.168.100.2:15100` accepts from `.1` (desktop currently cannot open that port).
4. Live test: mouse SAM↔ZHANGWEI twice; Notepad `MWB-SAM-TEST` / `MWB-ZHANGWEI-TEST` on focused window only.

Until step 4 is witnessed: **do not treat pairing as PASS**.

## Local artifacts

`C:\LAN_SHARE_REPORT\MWB_PAIR_ZHANGWEI_FINISH_20261013\`