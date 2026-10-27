"""Reviewer-only temporary Linux fixtures; no BLACKBOX/supplier paths are accessed.

PyArrow is unavailable here. The metadata-only stand-in is deliberate and reported;
it supplies num_rows=1, while the submitted byte hashing and control flow execute.
Windows reparse detection is replaced by an explicit fixture path predicate.
"""
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

pq = types.ModuleType('pyarrow.parquet')
pq.ParquetFile = lambda p: types.SimpleNamespace(metadata=types.SimpleNamespace(num_rows=1))
pa = types.ModuleType('pyarrow'); pa.parquet = pq
sys.modules['pyarrow'] = pa; sys.modules['pyarrow.parquet'] = pq
spec = importlib.util.spec_from_file_location('submitted_v3', Path('review_20261027_1339/desktop/capture_003/bodies/0015.py'))
cc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cc)
results = []
def record(name, **details):
    results.append({'case': name, **details})
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp); rel = root/'release'; rel.mkdir()
    cc.COMMIT_ROOT=root/'cc'; cc.COMMIT_ROOT.mkdir()
    cc.COMMIT_FILE=cc.COMMIT_ROOT/'COMMIT.json'; cc.VERSIONS=cc.COMMIT_ROOT/'versions'
    cc.RCID_CONTRACT_FILE=cc.COMMIT_ROOT/'contract.json'; cc.RCID_SIDE_DIR=cc.COMMIT_ROOT/'rcid'
    def contract(names, formal=None):
        cc.RCID_CONTRACT_FILE.write_text(json.dumps({'declared_products':names,'formal_required_products':formal or [],'contract_id':'C','contract_sha256':'arbitrary-unvalidated','junction_content_proven':False}))
    cc._is_reparse=lambda p: Path(p).name=='LINK'
    target=root/'target'; target.mkdir(); (target/'x.parquet').write_bytes(b'A')
    (rel/'LINK').mkdir(); cc._reparse_target=lambda p:str(target)
    contract(['LINK']); a=cc.release_content_digest(rel)
    (target/'x.parquet').write_bytes(b'B'); b=cc.release_content_digest(rel)
    record('linked_byte_mutation_not_detected',same_rcid=a['release_content_id']==b['release_content_id'],complete=b['complete'],proven=b['junction_content_proven'])
    (rel/'REAL').mkdir(); (rel/'REAL'/'x.parquet').write_bytes(b'A'); contract(['REAL'])
    with patch.object(cc,'product_digest_sha',side_effect=PermissionError('fixture unreadable')):
        a=cc.release_content_digest(rel); (rel/'REAL'/'x.parquet').write_bytes(b'B'); b=cc.release_content_digest(rel)
    record('unreadable_bytes_still_complete',same_rcid=a['release_content_id']==b['release_content_id'],complete=b['complete'])
    contract(['REAL','ABSENT']); a=cc.release_content_digest(rel)
    ident={'commit_id':'a'*64,'release_content_id':a['release_content_id'],'rcid_complete':False,'release_id':'R','release_root':str(rel),'asof':'2026-09-24','products':{},'junction_content_proven':False}
    with patch.object(cc,'build_identity',return_value=ident): out=cc.commit(rel)
    record('fresh_commit_accepts_incomplete',status=out['status'],written=cc.COMMIT_FILE.exists())
    cj=json.loads(cc.COMMIT_FILE.read_text()); cj['release_id']='OLD'; cj['release_content_id']='different'; cc.COMMIT_FILE.write_text(json.dumps(cj))
    cp=Path(cj['checkpoint_path']); cp_before=cp.read_bytes(); commit_before=cc.COMMIT_FILE.read_bytes()
    original_replace=cc.os.replace
    def fail_swap(src,dst):
        if Path(dst)==cc.COMMIT_FILE: raise OSError('fixture swap failure')
        return original_replace(src,dst)
    with patch.object(cc,'build_identity',return_value=ident), patch.object(cc.os,'replace',side_effect=fail_swap):
        try: cc.commit(rel)
        except OSError: pass
    record('repair_rewrites_checkpoint_before_failed_swap',checkpoint_changed=cp_before!=cp.read_bytes(),commit_unchanged=commit_before==cc.COMMIT_FILE.read_bytes())
    with patch.object(cc,'build_identity',return_value=ident): out=cc.commit(rel)
    record('same_root_label_repair_bypasses_rcid_difference',status=out['status'],candidate_rcid=ident['release_content_id'],stored_rcid='different')
    cj=json.loads(cc.COMMIT_FILE.read_text()); cj['release_content_id']='wrong'; cc.COMMIT_FILE.write_text(json.dumps(cj))
    contract(['REAL'])
    out=cc.verify(deep=False)
    record('mismatch_flag_claims_verified',check=out['release_content_id_check']['status'],consistent=out['consistent'],content_identity_verified=out['content_identity_verified'])
    contract(['REAL']); out=cc.load_product_contract()
    record('unvalidated_contract_hash_accepted',accepted_sha=out['contract_sha256'])
print(json.dumps({'scope':'ISOLATED_LINUX_CONTROL_FLOW_WITH_METADATA_STAND_IN_NOT_NTFS_OR_PARQUET_QA','findings':results},indent=2))
