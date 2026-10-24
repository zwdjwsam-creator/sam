"""Fixed metadata evidence capture; never import or execute an updater."""
import hashlib
import json
from pathlib import Path

BASE = Path(r'E:\BLACKBOX')
OUT = BASE / '_OPS/FOUNDATION_RECOVERY_20261024/r10_readiness_metadata_delivery'
INPUTS = {
    'legacy_checkpoint': BASE / '数据/原始只读/JQData_9999_official_raw/_checkpoint/latest_checkpoint.json',
    'pipeline_matrix': BASE / '运行/BLACKBOX_FULL_DATA_PIPELINE_MATRIX_CURRENT.json',
    'increment_rule': BASE / '运行/BLACKBOX_JQ_INCREMENTAL_DOWNLOAD_RULE_CURRENT.json',
    'raw_coverage_ledger': BASE / '运行/BLACKBOX_RAW_COVERAGE_LEDGER_CURRENT.json',
}
LIMIT = 4 * 1024 * 1024
SENSITIVE = {'password', 'passwd', 'pwd', 'token', 'api_key', 'apikey', 'secret', 'cookie', 'authorization', '密码', '密钥'}

def pairs(items):
    out = {}
    for k, v in items:
        if k in out:
            raise ValueError('DUPLICATE_JSON_KEY')
        out[k] = v
    return out

def safe(value):
    if isinstance(value, dict):
        for k, v in value.items():
            if str(k).lower() in SENSITIVE and v not in (None, '', False):
                return False
            if not safe(v):
                return False
    elif isinstance(value, list):
        return all(safe(v) for v in value)
    elif isinstance(value, str):
        # Refuse obvious embedded credential assignments, bearer headers and key formats.
        import re
        if re.search(r'(?i)(?:bearer\s+[a-z0-9._-]{8,}|(?:password|passwd|api[_-]?key|token)\s*[:=]\s*[\w+/.-]{6,}|gh[pousr]_[a-z0-9]{12,}|github_pat_[a-z0-9_]{12,}|sk-[a-z0-9_-]{12,})', value):
            return False
    return True

def capture_one(path, destination):
    # No linked path resolution, enumeration, SDK call or file referenced inside JSON.
    if path.is_symlink():
        return {'status': 'LINK_REFUSED'}
    if not path.exists():
        return {'status': 'EXACT_METADATA_PATH_NOT_FOUND', 'source_absence_claim_allowed': False}
    if not path.is_file() or path.stat().st_size > LIMIT:
        return {'status': 'FILE_TYPE_OR_SIZE_REFUSED'}
    raw = path.read_bytes()
    if len(raw) > LIMIT:
        return {'status': 'FILE_TYPE_OR_SIZE_REFUSED'}
    try:
        obj = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs)
    except (ValueError, UnicodeError):
        return {'status': 'INVALID_OR_DUPLICATE_JSON_NOT_EXPORTED'}
    if not isinstance(obj, (dict, list)):
        return {'status': 'JSON_CONTAINER_REQUIRED'}
    if not safe(obj):
        # Do not export values, raw bytes or secret-derived hashes.
        return {'status': 'POTENTIAL_SECRET_NOT_EXPORTED'}
    if path.read_bytes() != raw:
        return {'status': 'INPUT_CHANGED_NOT_EXPORTED'}
    destination.write_bytes(raw)
    return {'status': 'ORIGINAL_METADATA_BYTES_CAPTURED', 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(),
            'export': destination.name, 'authority': 'OBSERVED_METADATA_ONLY_NOT_ADMITTED'}

def main():
    OUT.mkdir(exist_ok=False)
    records = {name: capture_one(path, OUT / (name + '.original.json'))
               for name, path in INPUTS.items()}
    receipt = {'schema': 'R10_FIXED_READINESS_METADATA_1', 'records': records,
               'interpretation': 'No checkpoint selected as authoritative; no target range or missing-data verdict computed.',
               'supplier_calls': 0, 'business_data_written': False,
               'FOUNDATION_ACCEPTANCE': False, 'NEW_DATA_ACQUISITION_AUTHORIZED': False,
               'CURRENT_SWITCH_ALLOWED': False, 'ORDER_ALLOWED': False}
    (OUT / 'CAPTURE_RECEIPT.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))
    return 0 if all(r['status'] == 'ORIGINAL_METADATA_BYTES_CAPTURED' for r in records.values()) else 3

if __name__ == '__main__':
    raise SystemExit(main())
