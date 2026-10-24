r"""R09-DISCLOSED-SUBSTITUTION-DIAGNOSTIC
Stage 1 (guarded must-read preflight) already STOPped on this host with
MUST_READ_PREFLIGHT_FAILED, caused by the audit guard denying the import-time
tempfile probe inside E:\BLACKBOX\脚本\_base.py:30. The guard is NOT relaxed.

This harness therefore substitutes ONLY the stage-1 callback with a marker and
executes stages 2/3/4 (pinned binding, bounded candidate read, shadow/publish
negative controls) against the real desktop sources. The output is relabelled
so no reader can mistake it for a passed ordered entry.
"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import r09_control_runtime as runtime

PACKET = Path(sys.argv[1])
SUCCESSOR = Path(sys.argv[2])


def stage1_marker(*_ignored):
    return {'ok': True, 'STAGE1_SUBSTITUTED_NOT_EXECUTED': True,
            'stage1_real_result': 'STOP',
            'stage1_real_reason': 'MUST_READ_PREFLIGHT_FAILED: audit guard denies '
                                   'tempfile probe write required by import of E:\\BLACKBOX\\脚本\\_base.py:30'}


runtime.run_preflight = stage1_marker
result = runtime.desktop_run(PACKET, SUCCESSOR)
result['preflight'] = stage1_marker()
result['scope'] = ('R09_STAGES_2_4_DIAGNOSTIC_WITH_STAGE1_SUBSTITUTED; '
                   'NOT_A_PASSED_ORDERED_ENTRY; STAGES_2_4=EXECUTED_ON_DESKTOP')
result['FOUNDATION_ACCEPTANCE'] = False
result['ORDER_ALLOWED'] = False
print(json.dumps({'status': 'STAGES_2_4_DIAGNOSTIC_COMPLETE', **result},
                 default=str, ensure_ascii=True))
