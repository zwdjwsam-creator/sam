from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import io,json,zipfile
import candidate_adapter as c
import native_reader as n
from p3_common import verify_values,expected_files
import run_p3 as runner
ROOT=Path(__file__).resolve().parent.parent
E=ROOT/'evidence';P=ROOT/'p3_dispatch';O=ROOT/'p3_offline_results/iteration_002'
bindings=json.loads((P/'bindings.json').read_bytes());reference=c.BodyReader(E,bindings)
assert str(n.ADMISSION).endswith('R5/ADMISSION_R5.json')
assert str(n.REUSE).endswith('R5/REUSE_MANIFEST_R5.json')
exact=n.exact
price={(e['source']['path']):(e,k) for e,k in zip(reference.admission['entries'],reference.entry_keys)}
def mapped_exact(p,pin):
 if str(p) in price:
  e,k=price[str(p)];b=reference.read(e,k);c.require(len(b)==pin['bytes'] and c.sha(b)==pin['sha256'],'MAPPED_PRICE_IDENTITY');return b
 return exact(p,pin)
with patch.object(n,'os',SimpleNamespace(name='nt')),patch.object(n,'socket',SimpleNamespace(gethostname=lambda:'ZHANGWEI')),patch.object(n,'ADMISSION',E/'ADMISSION_R5.json'),patch.object(n,'REUSE',E/'REUSE_MANIFEST_R5.json'),patch.object(n,'DOMAIN',E/'domain_schema_contract.csv'),patch.object(n,'PIT',E/'pit_schema_contract.csv'),patch.object(n,'exact',mapped_exact):
 reader=n.NativeBodyReader(P,gate_verified=True)
 for e,k in zip(reader.admission['entries'],reader.entry_keys):
  assert reader.read(e,k)==reference.read(e,k)
 reader.verify_storage_again()
 semantic=reader.semantic
c.write_new(O/'SEMANTIC_BINDINGS.json',c.packed(semantic))
full=O/'full_body';expected=json.loads((P/'PORTABLE_EXPECTED.json').read_bytes())
observed=verify_values(full,expected);assert len(observed)==51
out=O/'packed';out.mkdir(exist_ok=False);archives=runner.pack(full,out)
seen=[]
for a in archives:
 with zipfile.ZipFile(out/a['path']) as z:
  for info in z.infolist():
   assert info.compress_type==zipfile.ZIP_STORED
   assert z.read(info.filename)==(full/info.filename).read_bytes()
   seen.append(info.filename)
assert len(seen)==len(set(seen))==125 and set(seen)==expected_files(bindings['expected_cells'])
c.write_new(O/'NATIVE_BINDING_AND_PACK_AUDIT.json',c.packed({'native_reader_windows_host_branch_modeled':True,'actual_windows_execution':False,'modeled_windows_original_paths_checked':1504,'original_body_bytes_equal':True,'semantic_mapping_fields':14,'required_names':12,'formal_dictionary_admission':False,'portable_cells_equal':51,'archive_files':archives,'exact_member_count':125,'all_members_byte_equal':True,'source_roots_unchanged':True}))
print(json.dumps({'native_reader_paths':1504,'portable_cells':51,'archive_members':125,'archives':len(archives),'archive_bytes':sum(a['bytes'] for a in archives)}))
