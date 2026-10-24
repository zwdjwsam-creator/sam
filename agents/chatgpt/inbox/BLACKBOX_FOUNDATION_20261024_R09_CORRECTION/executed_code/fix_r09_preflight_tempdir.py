"""GPT-owned R09 compatibility repair; originals and the guard stay unchanged.

Seed the stdlib tempfile directory cache with the existing successor directory.
This avoids tempfile's import-time write probe. It grants no write exception.
"""
import argparse
import hashlib
from pathlib import Path

SOURCE_SHA='87ff01f31d4a77736f1a2eb3eb031c81a627923eb73c61e29c0035f93e128e60'
OLD="    child='''import sys,os,runpy\nsys.dont_write_bytecode=True\n"
NEW="""    child='''import sys,os,runpy,tempfile
sys.dont_write_bytecode=True
# _base calls gettempdir() at import. Seed the documented stdlib cache without
# probing, creating or deleting a file. All write/network denials below remain.
temp_root=os.path.realpath(os.path.dirname(sys.argv[1]))
if not os.path.isabs(temp_root) or not os.path.isdir(temp_root):
 raise RuntimeError('R09_EXISTING_SUCCESSOR_DIRECTORY_REQUIRED')
tempfile.tempdir=temp_root
"""


def repair(source):
    source=Path(source)
    raw=source.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
        raise ValueError('R09_RUNTIME_SOURCE_PIN_CHANGED')
    text=raw.decode('utf-8')
    if text.count(OLD)!=1:
        raise ValueError('R09_PREFLIGHT_PATCH_ANCHOR_CHANGED')
    result=text.replace(OLD,NEW,1).encode('utf-8')
    compile(result,'<r09-preflight-fixed>','exec')
    return result


def build(source):
    source=Path(source);data=repair(source)
    target=source.with_name('r09_control_runtime_preflight_fixed.py')
    if target.exists():
        if target.read_bytes()!=data:
            raise ValueError('R09_FIXED_ENTRY_ALREADY_EXISTS_WITH_DIFFERENT_BYTES')
        status='ALREADY_FIXED_VERIFIED'
    else:
        with target.open('xb') as out:
            out.write(data)
        status='FIXED_ENTRY_CREATED'
    return {'status':status,'path':str(target),'sha256':hashlib.sha256(data).hexdigest(),
            'original_sha256':SOURCE_SHA,'production_modified':False,'write_exceptions_added':0}


if __name__=='__main__':
    import json
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);args=ap.parse_args()
    print(json.dumps(build(args.source),ensure_ascii=True))
