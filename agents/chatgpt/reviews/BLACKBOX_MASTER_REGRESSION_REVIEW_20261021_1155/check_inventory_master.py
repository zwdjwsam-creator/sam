"""Check isolated inventory CSV consistency; never opens business paths.

This checks report assertions, not data completeness or runtime readiness.
"""
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

PLACEHOLDERS = {'SEE_PRIOR_CONTRACT_OR_UNKNOWN', 'NOT_RECHECKED_THIS_PASS',
                'RETAIN_PRIOR_EVIDENCE', 'SEE_PRIOR_MAPPING', 'REUSE_PRIOR_LEDGER_FIELDS'}

def inspect(rows):
    issues = []
    for row in rows:
        pid = row.get('product_id', '')
        path = row.get('authority_path', '')
        frequency = {'ETF_MINUTE_1M_R1': '1m', 'ETF_MINUTE_5M_R1': '5m'}.get(pid)
        if frequency and re.search(r'(?i)(A股_stock_|(?:^|[\\/])stock_)', path):
            issues.append({'product_id': pid, 'code': 'ETF_AUTHORITY_POINTS_TO_STOCK',
                           'authority_path': path, 'prior_verified_etf_path': row.get('content_0836_path')})
        if str(row.get('inventory_scope_cleared', '')).lower() == 'true':
            unresolved = [key for key in ('required_range_source', 'update_entry_upstream',
                                          'gap_or_unproven', 'consumer_admission')
                          if not row.get(key) or row[key] in PLACEHOLDERS]
            if unresolved:
                issues.append({'product_id': pid, 'code': 'SCOPE_CLEARED_WITH_PLACEHOLDERS',
                               'fields': unresolved})
    ids = [row.get('product_id') for row in rows]
    duplicates = [pid for pid, count in Counter(ids).items() if count > 1]
    if duplicates or None in ids or '' in ids:
        issues.append({'code': 'MISSING_OR_DUPLICATE_OBJECT_ID', 'duplicates': duplicates})
    return {'rows': len(rows), 'unique_ids': len(set(ids)),
            'issue_counts': dict(Counter(i['code'] for i in issues)), 'issues': issues,
            'report_consistency_pass': not issues,
            'data_completeness': 'NOT_TESTED', 'system_inventory_acceptance': False,
            'limits': 'CSV-only consistency check. No input modifications or business-file reads. Unknown with evidence is allowed; no rule that all business gaps must be fixed.'}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv_path', type=Path)
    args = ap.parse_args()
    with args.csv_path.open(encoding='utf-8-sig', newline='') as file:
        report = inspect(list(csv.DictReader(file)))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['report_consistency_pass'] else 2

if __name__ == '__main__':
    raise SystemExit(main())
