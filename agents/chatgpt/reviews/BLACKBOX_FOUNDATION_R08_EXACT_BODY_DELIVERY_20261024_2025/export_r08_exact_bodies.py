"""Export fixed hash-pinned text bodies into ASCII JSON/base64 carriers.

Only stdlib; no original module imports or execution, no scans and no network.
The exporter creates an evidence packet in _OPS, never edits a source file.
"""
import base64
import hashlib
import json
from pathlib import Path

WORK=Path(r'E:\BLACKBOX\_OPS\FOUNDATION_RECOVERY_20261024')
DEFAULT_DEST=WORK/'reviews'/'R08'/'BODY_EXPORT_20261024_2025'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok,reason):
    if not ok:
        raise ValueError(reason)


def json_bytes(body):
    return (json.dumps(body,ensure_ascii=True,indent=2,sort_keys=True)+'\n').encode('ascii')


def export(spec_path,dest,*,live=True):
    spec_path,dest=Path(spec_path),Path(dest)
    spec_bytes=spec_path.read_bytes()
    spec=json.loads(spec_bytes.decode('utf-8-sig'))
    require(spec['schema_version']=='R08_EXACT_SOURCE_EXPORT_1','WRONG_EXPORT_SPEC')
    files=spec['files']
    require(len(files)==spec['count'] and bool(files),'SPEC_COUNT_MISMATCH')
    require(len({f['key'] for f in files})==len(files),'DUPLICATE_BODY_KEY')
    if live:
        require(len(files)==23,'LIVE_EXPECTS_23_BODIES')
        require(dest.resolve()==DEFAULT_DEST.resolve(),'UNAUTHORIZED_EXPORT_DESTINATION')
    payloads=[]
    for item in files:
        key=item['key']
        require(key and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789' for c in key),'INVALID_BODY_KEY')
        source=Path(item['locator'])
        if live:
            require(source.suffix.lower() in {'.py','.json','.md','.csv'},'UNAUTHORIZED_SOURCE_KIND')
            parts=[p.lower() for p in source.parts]
            require(not any('secret' in p or p=='.env' or p=='密钥' for p in parts),'SECRET_SOURCE_FORBIDDEN')
        raw=source.read_bytes()
        require(0<len(raw)<=1024*1024,'INVALID_BODY_SIZE:'+key)
        require(len(raw)==item['bytes'] and sha(raw)==item['sha256'],'SOURCE_PIN_MISMATCH:'+key)
        carrier={'body_key':key,'original_path':str(source),'original_sha256':sha(raw),
                 'original_bytes':len(raw),'payload_encoding':'BASE64_ORIGINAL_BYTES',
                 'original_not_executed':True,'payload_base64':base64.b64encode(raw).decode('ascii')}
        payloads.append((item,key+'.body.json',json_bytes(carrier)))
    marker=dest/'EXPORT_MANIFEST.json'
    if marker.exists():
        old=json.loads(marker.read_text(encoding='ascii'))
        require(old['spec_sha256']==sha(spec_bytes),'REPLAY_SPEC_CHANGED')
        require(len(old['bodies'])==len(payloads),'REPLAY_BODY_COUNT_CHANGED')
        expected={name:sha(data) for _,name,data in payloads}
        require(set(expected)=={b['file'] for b in old['bodies']},'REPLAY_BODY_SET_CHANGED')
        for b in old['bodies']:
            require(sha((dest/b['file']).read_bytes())==b['carrier_sha256']==expected[b['file']],'REPLAY_CARRIER_CHANGED')
        return {'status':'ALREADY_EXPORTED_VERIFIED','bodies':len(payloads),'manifest':str(marker)}
    require(not dest.exists(),'PARTIAL_PACKET_REQUIRES_REVIEW')
    # All source pins are checked before creating any output directory.
    dest.mkdir(parents=True)
    records=[]
    for item,name,data in payloads:
        p=dest/name
        with p.open('xb') as out:
            out.write(data)
        back=json.loads(p.read_text(encoding='ascii'))
        decoded=base64.b64decode(back['payload_base64'],validate=True)
        require(sha(decoded)==item['sha256'] and len(decoded)==item['bytes'],'LOCAL_BODY_READBACK_FAILED')
        records.append({'body_key':item['key'],'file':name,'original_path':item['locator'],
                        'original_sha256':item['sha256'],'original_bytes':item['bytes'],'carrier_sha256':sha(data)})
    for item,_,_ in payloads:
        require(sha(Path(item['locator']).read_bytes())==item['sha256'],'SOURCE_CHANGED_DURING_EXPORT')
    result={'schema_version':'R08_EXACT_SOURCE_EXPORT_MANIFEST_1','spec_sha256':sha(spec_bytes),
            'status':'COMPLETE_FIXED_BODY_EXPORT','body_count':len(records),'bodies':records,
            'round':'R08/10','future_execution_deliveries_remaining':2,
            'source_files_executed':0,'source_files_modified':0,'source_absence_claims':0,
            'network_calls':0,'FOUNDATION_ACCEPTANCE':False,'ORDER_ALLOWED':False}
    with marker.open('xb') as out:
        out.write(json_bytes(result))
    return {'status':'COMPLETE_FIXED_BODY_EXPORT','bodies':len(records),'manifest':str(marker)}


if __name__=='__main__':
    here=Path(__file__).resolve().parent
    print(json.dumps(export(here/'EXACT_SOURCE_EXPORT_SPEC.json',DEFAULT_DEST),ensure_ascii=True))
