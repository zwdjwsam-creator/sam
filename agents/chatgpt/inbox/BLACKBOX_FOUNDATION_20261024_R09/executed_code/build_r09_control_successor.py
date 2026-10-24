"""Build source-pinned R09 control successors in the existing _OPS candidate tree.

No production import, source edit, network, registry refresh or live publication.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

WORK=Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
PINS={
 'PREFLIGHT':'3bb85023387ce976aaf03694073936b0da5b5ef710f80f6284e8347f067fe217',
 'REQ_CAPABILITY':'c22fc461db2049c0d3a9ca8988b08c6f9ee0fee95c0d2bdbb8ea8bd00114710e',
 'PRE_INGESTION_GATE':'9385131008d24b82b616bc1f175be4e8ce237d81556711ed6781270322ad0637',
 'PUBLISH_GATE':'6a55ec57ef4740105ec4023563bdebac6038ffe0ca458136b70ee2055a2bd654'}
TARGETS={'PREFLIGHT':'blackbox_must_read_preflight_r1.py',
         'REQ_CAPABILITY':'blackbox_request_window_data_capability_resolver_r1.py',
         'PRE_INGESTION_GATE':'pre_ingestion_gate.py',
         'PUBLISH_GATE':'blackbox_daily_increment_publish_gate_r1.py'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(ok,reason):
    if not ok:
        raise ValueError(reason)


def replace_once(text,old,new):
    require(text.count(old)==1,'PATCH_ANCHOR_NOT_UNIQUE:'+old[:70])
    return text.replace(old,new,1)


def patch_preflight(text):
    text=replace_once(text,'    if args.acceptance:\n        return _acceptance()',
        '''    if args.acceptance or args.write_manifest:
        print("R09_SUCCESSOR_READONLY_PREFLIGHT_ONLY")
        return FAIL''')
    text=replace_once(text,"        elif m[\"lines\"] > budgets[\"LINE_CAP\"]:",
        '''        elif not isinstance(expected, str) or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            problems.append(f"SHA_AUTHORITY_MISSING_{k}")
            status = "SHA_AUTHORITY_MISSING"
        elif m["lines"] > budgets["LINE_CAP"]:''')
    return replace_once(text,'    if k_expected and kernel_meta.get("sha256") != k_expected:',
        '''    if not isinstance(k_expected, str) or len(k_expected) != 64 or any(c not in "0123456789abcdef" for c in k_expected):
        problems.append("SHA_AUTHORITY_MISSING_KERNEL")
        kernel_status = "SHA_AUTHORITY_MISSING"
    elif kernel_meta.get("sha256") != k_expected:''')


def patch_capability(text):
    text=replace_once(text,'    signal = _parse_iso(req.get("SIGNAL_TIME"))\n    known_at = _parse_iso(facts.get("KNOWN_AT"))\n    earliest = _parse_iso(facts.get("EARLIEST_USABLE_TIME"))',
        '''    try:
        signal = _parse_iso(req.get("SIGNAL_TIME"))
        known_at = _parse_iso(facts.get("KNOWN_AT"))
        earliest = _parse_iso(facts.get("EARLIEST_USABLE_TIME"))
    except (ValueError, TypeError, AttributeError):
        return {"CAUSAL_READINESS": "FAIL", "reason": "INVALID_CAUSAL_TIMESTAMP"}''')
    text=replace_once(text,'    fields_ok = bool(facts.get("REQUIRED_FIELDS_OK", True))\n    if not fields_ok and readiness == "AVAILABLE_FORMAL":',
        '''    fields_ok = facts.get("REQUIRED_FIELDS_OK") is True
    if not fields_ok and readiness in ("AVAILABLE_FORMAL", "AVAILABLE_FORMAL_WITH_DECLARED_GAP", "NO_CACHE_REQUIRED_FORMAL_ROUTE"):''')
    text=replace_once(text,'    if signal is None:\n        return {',
        '''    if signal is None and str(req.get("USAGE_MODE", "")).startswith("BACKTEST"):
        return {"CAUSAL_READINESS": "FAIL", "reason": "SIGNAL_TIME_REQUIRED_FOR_BACKTEST"}
    if signal is None:
        return {''')
    text=replace_once(text,'    # If facts provide explicit known_at / earliest, use them.',
        '''    if signal.tzinfo is None or (known_at is not None and known_at.tzinfo is None) or (earliest is not None and earliest.tzinfo is None):
        return {"CAUSAL_READINESS": "FAIL", "reason": "EXPLICIT_TIMEZONE_REQUIRED"}
    if known_at is None:
        return {"CAUSAL_READINESS": "FAIL", "reason": "KNOWN_AT_EVIDENCE_REQUIRED"}
    # If facts provide explicit known_at / earliest, use them.''')
    return text


def patch_admission(text):
    text=replace_once(text,'from dataclasses import dataclass, asdict, field',
        'import hashlib\nimport json\nfrom dataclasses import dataclass, asdict, field')
    text=replace_once(text,'        self.last_gate_before_parse = False',
        '''        self.last_gate_before_parse = False
        self._issued_admission = None
        self._issued_payload_sha256 = None''')
    text=replace_once(text,'        checked = []\n        for key in REQUIRED_FIELDS:',
        '''        self.last_gate_before_parse = False
        self._issued_admission = None
        self._issued_payload_sha256 = None
        checked = []
        for key in REQUIRED_FIELDS:''')
    text=replace_once(text,'        self.last_gate_before_parse = True\n        return AdmissionResult(True, None, checked_fields=checked, details={"role": role})',
        '''        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        self._issued_payload_sha256 = hashlib.sha256(encoded).hexdigest()
        result = AdmissionResult(True, None, checked_fields=checked, details={"role": role})
        self._issued_admission = result
        self.last_gate_before_parse = True
        return result''')
    text=replace_once(text,'        if not admission.allowed:\n            raise RuntimeError(f"PARSE_BLOCKED:{admission.block_reason_code}")',
        '''        if not admission.allowed:
            raise RuntimeError(f"PARSE_BLOCKED:{admission.block_reason_code}")
        if admission is not self._issued_admission or self._issued_payload_sha256 is None:
            raise RuntimeError("PARSE_WITHOUT_CURRENT_ADMISSION")
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        if hashlib.sha256(encoded).hexdigest() != self._issued_payload_sha256:
            raise RuntimeError("PAYLOAD_CHANGED_AFTER_ADMISSION")''')
    return replace_once(text,'        self._parse_calls += 1',
        '''        self._issued_admission = None
        self._issued_payload_sha256 = None
        self.last_gate_before_parse = False
        self._parse_calls += 1''')


def patch_publisher(text):
    # Scope is deliberately a candidate-only dry-run successor. Legacy multi-head
    # writes below are unreachable; do not mistake per-file replace for bundle atomicity.
    text=replace_once(text,'    if dry_run:\n        return {**matrix, "published": False, "dry_run": True}',
        '''    if dry_run:
        return {**matrix, "CANDIDATE_MATRIX_RESULT": matrix["CURRENT_PUBLISH"],
                "CURRENT_PUBLISH": "FORBIDDEN", "published": False, "dry_run": True,
                "reason": "R09_SUCCESSOR_DRY_RUN_ONLY"}''')
    return replace_once(text,'    gen = facts.get("SYSTEM_GENERATION_ID")\n    if gen != cache_pointer.get("cache_release_id"):',
        '''    if not dry_run:
        return {"OPERATIONAL_READINESS": "FAIL_CLOSED", "CURRENT_PUBLISH": "FORBIDDEN",
                "published": False, "reason": "R09_SUCCESSOR_DRY_RUN_ONLY"}
    if not cache_pointer.get("release_root") or Path(cache_pointer["release_root"]).resolve() != Path(cache_root).resolve():
        return {"OPERATIONAL_READINESS": "FAIL_CLOSED", "CURRENT_PUBLISH": "FORBIDDEN",
                "published": False, "reason": "CACHE_ROOT_IDENTITY_MISMATCH"}
    active_clean = cleaning_pointer
    if active_clean is None:
        active_clean = json.loads(CLEAN_PTR.read_text(encoding="utf-8-sig"))
    if not cache_pointer.get("source_cleaning_release") or cache_pointer["source_cleaning_release"] != active_clean.get("release_id"):
        return {"OPERATIONAL_READINESS": "FAIL_CLOSED", "CURRENT_PUBLISH": "FORBIDDEN",
                "published": False, "reason": "CLEANING_CACHE_PAIR_MISMATCH"}
    gen = facts.get("SYSTEM_GENERATION_ID")
    if not gen or gen != cache_pointer.get("cache_release_id"):''')


PATCHERS={'PREFLIGHT':patch_preflight,'REQ_CAPABILITY':patch_capability,
          'PRE_INGESTION_GATE':patch_admission,'PUBLISH_GATE':patch_publisher}


def read_packet(packet,key):
    item=json.loads((Path(packet)/(key+'.body.json')).read_text(encoding='ascii'))
    raw=base64.b64decode(item['payload_base64'],validate=True)
    require(digest(raw)==PINS[key]==item['original_sha256'],'SOURCE_PIN_CHANGED:'+key)
    return raw


def build(packet,dest):
    packet,dest=Path(packet),Path(dest)
    sources={k:read_packet(packet,k) for k in PINS}
    outputs={TARGETS[k]:PATCHERS[k](b.decode('utf-8-sig').replace('\r\n','\n')).encode('utf-8') for k,b in sources.items()}
    for name,data in outputs.items():
        compile(data,str(dest/name),'exec')
    marker=dest/'SUCCESSOR_BUILD_MANIFEST.json'
    if marker.exists():
        old=json.loads(marker.read_text(encoding='utf-8'))
        require(old['source_pins']==PINS,'REPLAY_SOURCE_SET_CHANGED')
        for name,data in outputs.items():
            require(digest((dest/name).read_bytes())==digest(data)==old['outputs'][name],'REPLAY_PATCH_CHANGED')
        return {'status':'ALREADY_BUILT_VERIFIED','manifest':str(marker)}
    require(not dest.exists(),'PARTIAL_SUCCESSOR_REQUIRES_REVIEW')
    dest.mkdir(parents=True)
    def guarded_write_path(path):
        p=Path(path).resolve()
        require(p.parent==dest.resolve(),'OUTSIDE_AUTHORIZED_SUCCESSOR')
        require(not p.exists(),'SUCCESSOR_FILE_EXISTS')
        return p
    for name,data in outputs.items():
        with guarded_write_path(dest/name).open('xb') as f:
            f.write(data)
    body={'generation':'R09_CONTROL_SUCCESSOR','source_pins':PINS,
          'outputs':{n:digest(d) for n,d in outputs.items()},'production_modified':False,
          'formal_backtest_active':False,'live_publication_authorized':False,'FOUNDATION_ACCEPTANCE':False}
    with guarded_write_path(marker).open('xb') as f:
        f.write((json.dumps(body,indent=2)+'\n').encode('utf-8'))
    return {'status':'CONTROL_SUCCESSOR_BUILT','manifest':str(marker),'outputs':body['outputs']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--packet',required=True);args=ap.parse_args()
    print(json.dumps(build(args.packet,WORK/'candidate'/'r09'/'control_successor')))
