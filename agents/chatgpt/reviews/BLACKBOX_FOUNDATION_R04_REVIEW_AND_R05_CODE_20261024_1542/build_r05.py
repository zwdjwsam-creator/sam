"""GPT-only exact safety changes. Preserve R04 and production engine files."""
import ast
import hashlib
import json
from pathlib import Path
import sys

EXPECTED = {
 'provider.py': 'dc1e35bd58027507d20e1972b78c04d4bbeadad5bfe70b244778c05f4395788a',
 'engine_adapter.py': 'c8536166045e62624a54fbba19a3d64ef365da56e80faf4af8d19efbb7aed9e6',
 'file_index.py': '1c74bebab1a39aacc56c303e8fab51a7401fac39546e5ab31b7bc2f776083803',
 'securities.py': 'eebfa2ae3fb356b81966086dae91427e4a0d72474fe91f939fd8196a9b3ed499',
 'errors.py': '7eb7ac69f42931842b2bb279cee39a9c247be816325c0c247d127c2cd00cb281'}


def norm(s):
    return s.replace('\r\n', '\n').rstrip('\n') + '\n'


def sha(s):
    return hashlib.sha256(norm(s).encode()).hexdigest()


def edit(s, old, new):
    if s.count(old) != 1:
        raise ValueError('PATCH_ANCHOR_MISMATCH')
    return s.replace(old, new, 1)


def build(src, dst):
    if dst.exists():
        raise ValueError('DESTINATION_EXISTS')
    texts = {n: norm((src/n).read_text(encoding='utf-8-sig')) for n in EXPECTED}
    for n, s in texts.items():
        if sha(s) != EXPECTED[n]:
            raise ValueError('SOURCE_HASH_MISMATCH:' + n)
    texts['errors.py'] = edit(texts['errors.py'], 'class ProviderReject(Exception):\n',
        'class ProviderReject(Exception):\n    bb_admission_error = True\n')
    s = texts['provider.py']
    s = edit(s, 'is_top = [rank_map.get((c, t)) == v for c, t, v in zip(df2["code"], df2["ts"], df2["_rk"])]',
        'is_top = [True] * len(df2)  # compare every overlapping revision; do not infer authority')
    s = edit(s, '[sdt["date"], per.get("listing_start"), obs_start]',
        '[sdt["date"], per.get("listing_start")]')
    s = edit(s, '[cutoff.date().isoformat(), per.get("listing_end"), obs_end]',
        '[cutoff.date().isoformat(), per.get("listing_end")]')
    texts['provider.py'] = s
    s = texts['file_index.py']
    s = edit(s, '        if not lo or not hi:\n            continue\n',
        '        if not lo or not hi:\n'
        '            hits.append((e, start, end, "UNKNOWN_REQUIRES_REVIEW"))\n'
        '            continue\n')
    s = edit(s, 'key = (e.family, lo, hi)', 'key = (e.path, lo, hi)  # no unproved version suppression')
    texts['file_index.py'] = s
    # Clean is a diagnostic source. Neither these edits nor status=OK implement MASTER gates.
    for s in texts.values():
        ast.parse(s)
    dst.mkdir(parents=True)
    for n, s in texts.items():
        (dst/n).write_text(s, encoding='utf-8')
    (dst/'__init__.py').write_text('"""R05 diagnostic candidate; full MASTER admission pending."""\n', encoding='utf-8')
    return {n: sha(s) for n, s in texts.items()}


if __name__ == '__main__':
    print(json.dumps({'status': 'CREATED', 'normalized_sha256': build(Path(sys.argv[1]), Path(sys.argv[2]))}))
