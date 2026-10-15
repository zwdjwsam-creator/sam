import json, sqlite3, tempfile
from pathlib import Path
import r9_formal_chain as chain
import test_full_closure as fixtures

with tempfile.TemporaryDirectory() as folder:
    root=Path(folder)
    p=root/'d.sqlite'
    fixtures._write(p,[(r'D:\data\one.txt',4)],[r'D:\data'],[])
    entity=next(chain._entities(p,p.stat()))
    print(json.dumps({'case':'FORMAL_D_SOURCE','source_path':entity['source_path'],'source_share':entity['source_share'],'dest_path':entity['dest_path']}))
    assert entity['source_path']==r'D:\data\one.txt'
    for name,dirs,links in [
        ('EMPTY_DIRECTORY_MISSING_PARENT',[r'E:\BLACKBOX\missing\empty'],[]),
        ('LINK_MISSING_PARENT',[r'E:\BLACKBOX\real'],[(r'E:\BLACKBOX\missing\link',r'E:\BLACKBOX\real')]),
        ('ORDINARY_DIRECTORY_LINK_COLLISION',[r'E:\BLACKBOX\a'],[(r'E:\BLACKBOX\a',r'E:\BLACKBOX\a')])
    ]:
        p=root/(name+'.sqlite')
        fixtures._write(p,[(r'E:\BLACKBOX\one.txt',4)],dirs,links)
        result=chain.inspect_plan(p,fixtures._contract(p))
        print(json.dumps({'case':name,'ok':result['ok'],'closure':result['closure']}))
        assert result['ok'] is True
