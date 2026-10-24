"""Offline proof that exact body bytes survive transport and pins fail closed."""
import base64
import json
from pathlib import Path
import tempfile
from export_r08_exact_bodies import export,sha,json_bytes


def reject(fn,prefix):
    try:
        fn()
    except ValueError as exc:
        assert str(exc).startswith(prefix),str(exc)
    else:
        raise AssertionError('UNEXPECTED_PASS:'+prefix)


def main():
    with tempfile.TemporaryDirectory(prefix='r08_export_test_') as tmp:
        root=Path(tmp)
        raw=[b'line1\r\nline2\r\n','original text\r\n'.encode('utf-16')]
        files=[]
        for key,data in zip(['RULE','LESSON'],raw):
            p=root/(key+'.txt');p.write_bytes(data)
            files.append({'key':key,'locator':str(p),'sha256':sha(data),'bytes':len(data)})
        spec=root/'spec.json'
        spec.write_bytes(json_bytes({'schema_version':'R08_EXACT_SOURCE_EXPORT_1','count':2,'files':files}))
        dest=root/'packet'
        assert export(spec,dest,live=False)['status']=='COMPLETE_FIXED_BODY_EXPORT'
        for item,wanted in zip(files,raw):
            body=json.loads((dest/(item['key']+'.body.json')).read_text(encoding='ascii'))
            assert base64.b64decode(body['payload_base64'])==wanted
            assert Path(item['locator']).read_bytes()==wanted
        assert export(spec,dest,live=False)['status']=='ALREADY_EXPORTED_VERIFIED'
        carrier=dest/'RULE.body.json';saved=carrier.read_bytes();carrier.write_bytes(saved+b' ')
        reject(lambda:export(spec,dest,live=False),'REPLAY_CARRIER_CHANGED')
        carrier.write_bytes(saved)
        partial=root/'partial';partial.mkdir()
        reject(lambda:export(spec,partial,live=False),'PARTIAL_PACKET_REQUIRES_REVIEW')
        p=Path(files[0]['locator']);p.write_bytes(b'changed')
        reject(lambda:export(spec,root/'new',live=False),'SOURCE_PIN_MISMATCH')
        assert not (root/'new').exists()
    print(json.dumps({'status':'PASS','controls':['byte-exact CRLF and UTF16 carriers','source bytes unchanged',
          'complete marker','unchanged replay','tampered carrier rejected','partial packet preserved',
          'source change rejected before output'],'scope':'OFFLINE_SYNTHETIC','network_calls':0}))


if __name__=='__main__':
    main()
