# -*- coding: utf-8 -*-
import sys
import unittest
from pathlib import Path

sys.path.insert(0, r"C:\LAN_SHARE_REPORT\R9_DESKTOP_EXECUTOR_DEV_20261013")
import r9_formal_chain as chain


def _full(**extra):
    payload = {
        "phase": "FORMAL_COPY",
        "scope": "FULL",
        "copy_authorized": False,
        "full_migration": False,
        "version_choice": "PENDING_USER",
        "dest_roots": [chain.FORMAL_E, chain.FORMAL_D],
        "expected_volume_serial": chain.EXPECTED_VOLUME,
        "expected_unique_id": chain.EXPECTED_DISK,
        "source_plan_sha": chain.CANDIDATE_PLAN_SHA,
        "plan_sha": chain.CANDIDATE_PLAN_SHA,
        "max_unique_bytes": 1,
        "subset_unique_bytes": 1,
        "state_path": r"C:\LAN_SHARE_REPORT\R9_DESKTOP_BUILD_FINAL_PLAN_PENDING_VERSION_CHOICE_20261015\state\candidate.sqlite",
        "dest_probe": {"ok": True, "volume_serial": chain.EXPECTED_VOLUME, "unique_id": chain.EXPECTED_DISK, "filesystem": "NTFS"},
        "plan_audit": {"ok": True},
        "run": {
            "plan_digest": chain.CANDIDATE_PLAN_SHA,
            "inputs_digest": chain.CANDIDATE_PLAN_SHA,
            "code_digest": "present",
            "dest_volume": chain.EXPECTED_VOLUME,
            "dest_root": chain.FORMAL_E,
        },
    }
    payload.update(extra)
    return payload


class Binding(unittest.TestCase):
    def test_pending_version_and_closed_copy_do_not_open_the_gate(self):
        self.assertFalse(chain.formal_write_gate(_full(), None))

    def test_marked_choice_without_copy_authorization_stays_closed(self):
        self.assertFalse(chain.formal_write_gate(_full(version_choice="AS_IS_MIGRATE_MARKED", full_migration=True), None))

    def test_other_plan_file_is_not_accepted(self):
        self.assertIsNone(chain.bound_plan_sha(Path(r"C:\Windows\notepad.exe")))
        self.assertEqual(chain.bound_plan_sha(chain.CANDIDATE_PLAN), chain.CANDIDATE_PLAN_SHA)
        self.assertEqual(chain.bound_plan_sha(chain.FULL_PLAN), chain.FULL_PLAN_SHA)


if __name__ == "__main__":
    unittest.main(verbosity=1)
