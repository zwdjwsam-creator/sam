# SAM_REPORT — R9_NOTEBOOK_SOURCE_LINK_AND_SHARE_FACTS_20261013_1957

generated_at: 2026-10-13T12:15:12.459551+00:00
hostname: sam
phase: SOURCE_METADATA_READONLY
desktop_ZHANGWEI: HOLD

COPY_AUTHORIZED: false
FORMAT_DONE: false
FULL_MIGRATION: false
DESKTOP_SMB_ACCESS_VERIFIED: false
WRITE_TESTS_NOT_RUN: true

## Map
- file: R9_SAM_DEPENDENCY_MAP_R3.json
- sha256: `1c00ece5db519bf39de33473b5cbb81728cbdd65d8d38d6e00532f4a136084fe` (match expected)
- selected: D_TO_E id 25–40 = 16

## Link types
- LINK_TYPES_VERIFIED: True
- ok/errors: 16/0
- kind counts: {"junction_or_mount_point": 16}
- numeric tags from FileAttributeTagInfo and/or FSCTL_GET_REPARSE_POINT
- D snapshot / E delta SHAs retained unchanged (4c094df43ca348ac… / aa58ed8bd7b22e01…)

## Share facts
- E_SHARE_EXISTS: True
- E_share_covers_E_BLACKBOX: True
- D_SHARE_EXISTS: True
- D_SOURCE_UNC_RESOLVED: True
- has_ip_192_168_100_2: True
- ips: ['192.168.0.62', '100.119.199.3', '192.168.100.2']
- DESKTOP_SMB_ACCESS_VERIFIED: false (not tested)

## Artifacts
- D_REPARSE_TYPE_OVERLAY.json
- SOURCE_SHARE_FACTS.json
- query script + FILE_SHA256.json

## Notes
- No business copy/hash, no SMB/network changes, no desktop E write tests.
- 37 desktop unit tests PASS ≠ IMPLEMENTATION_READY / real IO.
