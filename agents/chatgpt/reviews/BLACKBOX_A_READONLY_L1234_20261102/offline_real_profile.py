"""Exercise new processor on already held immutable HUB RAW; no native replay."""
import json,sys
from pathlib import Path
import observe as o
sys.path.insert(0,str(Path('p3_dispatch').resolve()))
import candidate_adapter as old

def main():
 cat=json.loads(Path('l1234_dispatch/INPUTS.json').read_bytes())
 bind=json.loads(Path('p3_dispatch/bindings.json').read_bytes())
 reader=old.BodyReader(Path('evidence'),bind)
 u={}
 for ref in cat['universes']:
  b=Path('l1234_offline_universes',Path(ref['hub_path']).name).read_bytes()
  assert len(b)==ref['expected_bytes'] and o.sha(b)==ref['expected_sha256']
  u[ref['indexed_session']]=o.universe(b,ref['indexed_session'])
 root=Path('l1234_offline_observations_final');root.mkdir(exist_ok=False)
 output=o.Output(root);p=o.Profile(output,cat['review_sessions'],{tuple(x) for x in cat['no_limit_exceptions']},cat['preregistration'],u)
 refs={r['original_serialized_path']:r for r in cat['stock']}
 for e,key in zip(reader.admission['entries'],reader.entry_keys):
  if e['product']!='stock':continue
  p.add(refs[e['source']['path']],reader.read(e,key))
 result=p.finish(cat['data_sessions'],cat['official_reference'])
 for arc in reader.archive_identities:
  b=Path('evidence',arc['name']).read_bytes()
  assert len(b)==arc['bytes'] and o.sha(b)==arc['sha256']
 assert result==dict(rows=88812,quarantined=1,decode_errors=0)
 counts=json.loads((root/'L2_L3_COUNTS.json').read_bytes())
 assert len(counts['rows_per_indexed_day'])==17
 assert json.loads((root/'SAMPLE_002270.json').read_bytes())['observation']['physical_row']==68
 assert json.loads((root/'L4_TOTALS.json').read_bytes())['scale_result']['status']=='UNRESOLVED'
 summary=dict(status='PASS_NEW_PROCESSOR_AGAINST_RETAINED_HUB_BODIES_ONLY',**result,
              sample_row=68,data_days=17,source_files=1122,universe_files=17,
              native_source_presence_proved=False,regime_admitted=False,unit_admitted=False,
              l4_preregistered_dates=cat['preregistration']['dates'],
              output_files=len(output.sizes),output_bytes=output.total,
              real_anomaly_counts=counts['anomaly_flags'],actual_native_execution=False)
 Path('l1234_dispatch/OFFLINE_REAL_PROFILE.json').write_bytes(o.packed(summary)+b'\n')
 print(json.dumps(summary))
if __name__=='__main__':main()
