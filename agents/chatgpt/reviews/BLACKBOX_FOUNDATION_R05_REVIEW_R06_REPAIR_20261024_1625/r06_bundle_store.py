"""Candidate-only single-generation visibility; does not publish legacy CURRENT files."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import uuid


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    data = (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)+'\n').encode('utf-8')
    with tmp.open('xb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def publish_candidate(store, manifest, expected_pointer_digest, fault=None):
    """A process-crash boundary, not a power-loss or legacy-consumer atomicity claim."""
    store, manifest = Path(store), Path(manifest)
    if store.resolve() not in manifest.resolve().parents:
        raise ValueError('MANIFEST_OUTSIDE_CANDIDATE_STORE')
    body = json.loads(manifest.read_text(encoding='utf-8'))
    if body.get('candidate_only') is not True or body.get('build_validated') is not True:
        raise ValueError('CANDIDATE_NOT_VALIDATED')
    for item in body['artifacts']:
        if digest(item['path']) != item['sha256']:
            raise ValueError('CANDIDATE_ARTIFACT_CHANGED')
    pointer = store/'CANDIDATE_CURRENT.json'
    desired = {'generation':body['generation'], 'manifest_path':str(manifest.resolve()), 'manifest_sha256':digest(manifest)}
    lock = store/'CANDIDATE_WRITER.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        actual = digest(pointer) if pointer.exists() else None
        if pointer.exists() and json.loads(pointer.read_text()) == desired:
            return 'ALREADY_CURRENT'
        if actual != expected_pointer_digest:
            raise ValueError('STALE_CANDIDATE_PARENT')
        for source, expected in body.get('source_pins', {}).items():
            if digest(source) != expected:
                raise ValueError('SOURCE_CHANGED_BEFORE_CANDIDATE_COMMIT')
        if fault == 'before_commit':
            raise RuntimeError('INJECTED_BEFORE_COMMIT')
        write_json(pointer, desired)
        if fault == 'after_commit':
            raise RuntimeError('INJECTED_AFTER_COMMIT')
        return 'COMMITTED_CANDIDATE_ONLY'
    finally:
        os.close(fd)
        lock.unlink()


def read_generation(store):
    pointer = json.loads((Path(store)/'CANDIDATE_CURRENT.json').read_text(encoding='utf-8'))
    path = Path(pointer['manifest_path'])
    if digest(path) != pointer['manifest_sha256']:
        raise ValueError('MANIFEST_CHANGED')
    body = json.loads(path.read_text(encoding='utf-8'))
    if body['generation'] != pointer['generation']:
        raise ValueError('MIXED_GENERATION')
    return body


def relative_key(value):
    if '\\' in value or ':' in value:
        raise ValueError('INVALID_RELATIVE_KEY')
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('INVALID_RELATIVE_KEY')
    return p


def resolve_clean(body, relative):
    key = str(relative_key(relative))
    prefix = 'price/stock_ohlcv_daily/'
    if key.startswith(prefix):
        return Path(body['cleaning_daily_root'])/key[len(prefix):]
    return Path(body['parent_cleaning_standard_root'])/key


def resolve_cache(body, product, relative):
    relative_key(product)
    key = str(relative_key(relative))
    override = body['cache_overrides'].get(product, {}).get(key)
    if override:
        return Path(override)
    if product not in body['inherited_cache_products']:
        raise ValueError('UNKNOWN_PRODUCT')
    return Path(body['parent_cache_root'])/product/key
