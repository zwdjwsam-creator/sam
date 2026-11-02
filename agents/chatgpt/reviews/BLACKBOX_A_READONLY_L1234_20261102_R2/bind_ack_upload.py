"""Bind actual connector ACK upload/readback identifiers; no network itself.

Arguments are the immutable Git commit and ACK blob returned by the HUB tool,
not invented identifiers. GPT audits the real Git history after the return.
"""
import hashlib,json,re,sys
from datetime import datetime,timezone
import guard as g
import observe as o

def main():
    spec,digest=g.validate(False)
    o.need(len(sys.argv)==3 and all(re.fullmatch('[0-9a-f]{40}',x) for x in sys.argv[1:]),'EXACT_COMMIT_AND_BLOB_REQUIRED')
    o.need(not g.OUTER.exists() and not g.CONTROL.exists(),'PRIOR_RUN_NO_RETRY')
    raw=o.safe(g.ACK_ROOT/'ACK.json').read_bytes();a=json.loads(raw)
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    o.need(a['task_id']==o.TASK and a['package_sha256']==digest and a['rules']==g.rules() and blob==sys.argv[2],'ACK_ACTUAL_BLOB_IDENTITY')
    g.audit([g.ACK_ROOT])
    g.write(g.ACK_ROOT/'ACK_UPLOAD.json',dict(task_id=o.TASK,git_commit=sys.argv[1],ack_blob_sha=blob,
              ack_bytes=len(raw),ack_sha256=o.sha(raw),bound_utc=datetime.now(timezone.utc).isoformat(),
              evidence_kind='LOCAL_BINDING_OF_CONNECTOR_IDENTIFIERS_PENDING_INDEPENDENT_GIT_HISTORY_REVIEW'))
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:print(type(e).__name__+':'+str(e),file=sys.stderr);sys.exit(4)
