"""Actual selection and extracted calculation-block tests; synthetic inputs only."""
from datetime import datetime
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import pandas as pd


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def block(source, start, end, ns):
    import textwrap
    lines = source.splitlines()
    a = next(i for i, line in enumerate(lines) if start in line)
    b = next(i for i, line in enumerate(lines[a+1:], a+1) if end in line)
    exec(textwrap.dedent('\n'.join(lines[a:b])), ns)
    return ns


def coverage(source):
    ns = dict(out=pd.DataFrame({'code': ['A','A'], 'ts': pd.to_datetime(['2026-06-01','2026-06-02'])}),
              codes=['A'], routed={'per_code': {'A': {'listing_start': '2020-01-01', 'listing_end': '2030-01-01'}}},
              sdt={'date':'2026-06-01'}, cutoff=datetime(2026,6,3),
              idx={'observed_start':'2026-06-01', 'observed_end':'2026-06-02'},
              self=SimpleNamespace(trade_days=lambda a,b: [d for d in ['2026-06-01','2026-06-02','2026-06-03'] if a<=d<=b]),
              pd=pd, Dict=dict, List=list)
    return block(source, 'expected: Dict[str, List[str]]', 'truncated = 0', ns)['coverage']


def revisions(source):
    data = pd.DataFrame({'code':['A','A'], 'ts': pd.to_datetime(['2026-06-01']*2),
        '_rank':[1,3], '_ver':['20260101','20260102'], '_src':['year','day'], 'close':[1.,2.]})
    ns = dict(df=data, pd=pd, want_src=['close'], Dict=dict, List=list, Any=object)
    return block(source, 'df = df.sort_values(["code", "ts", "_rank"', 'dup_resolved =', ns)['conflicts']


def main():
    before, after = map(Path, sys.argv[1:])
    old = load(before/'file_index.py', 'r05_old_file_index')
    new = load(after/'file_index.py', 'r05_new_file_index')
    def entry(p, ver, unreadable=False):
        return old.FileEntry(path=p, name=p, family='same-family', version=ver,
            size=1, mtime_ns=0, rows=1, time_col='time',
            data_start=None if unreadable else '2026-06-01',
            data_end=None if unreadable else '2026-06-02',
            read_error='BAD_FOOTER' if unreadable else None).as_dict()
    idx = {'files':[entry('old.parquet','20260101'),entry('new.parquet','20260102')]}
    assert old.select(idx,'2026-06-01','2026-06-02')['selected']==1
    assert new.select(idx,'2026-06-01','2026-06-02')['selected']==2
    unknown = {'files':[entry('broken.parquet','',True)]}
    assert old.select(unknown,'2026-06-01','2026-06-02')['selected']==0
    assert new.select(unknown,'2026-06-01','2026-06-02')['selected']==1
    osrc=(before/'provider.py').read_text(encoding='utf-8')
    nsrc=(after/'provider.py').read_text(encoding='utf-8')
    assert not coverage(osrc)['missing_dates_per_code']
    assert coverage(nsrc)['missing_dates_per_code']=={'A':['2026-06-03']}
    assert not revisions(osrc) and revisions(nsrc)
    print(json.dumps({'status':'PASS','scope':'synthetic file-index and actual provider calculation blocks',
        'checks':['all overlapping builds retained','unknown footer not silently dropped',
                  'unserved tail counted','different-rank revision conflict exposed']}))


if __name__=='__main__':
    main()
