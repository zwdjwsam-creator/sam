import io,json
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import candidate_adapter as c

def value_hash(table):
    table=table.combine_chunks().replace_schema_metadata(None)
    sink=pa.BufferOutputStream()
    with pa.ipc.new_stream(sink,table.schema) as writer:writer.write_table(table)
    return c.sha(sink.getvalue().to_pybytes())

def verify_values(candidate,expected):
    root=Path(candidate);r=json.loads((root/'RESULT.json').read_bytes());observed=[]
    for row in r['outputs']:
        table=pq.ParquetFile(root/row['path']).read()
        observed.append({'product':row['product'],'date':row['date'],'rows':len(table),'value_sha256':value_hash(table)})
    c.require(observed==expected,'PORTABLE_VALUE_HASH_MISMATCH')
    return observed

def expected_files(cells):
    s={'quarantine/original_row.parquet','SOURCES.json','EXCLUSIONS.json','RESULT.json','MANIFEST.json','BUILD_COMPLETE.json'}
    for product,date in cells:
        s|={'native/'+c.FAMILIES[product]+'/'+date+'.parquet','lineage/'+product+'/'+date+'.json'}
        if product=='stock':s.add('dictionary/stock_daily/'+date+'.parquet')
    return s
