from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parent;P=R.parent/'p1_dispatch';b=(R/'POLICY_BODY.source.txt').read_bytes();SHA='31dee3a67f7674db25b0ba4d56c169c941e28f857b8656454b6006401938f884';checks=[]
def digest(x):return hashlib.sha256(x).hexdigest()
def ok(v,name):
 if not v:raise AssertionError(name)
 checks.append(name)
ok(len(b)==6982 and digest(b)==SHA,'whole_file_bytes_and_hash')
ok(b.count(b'\r')==0 and b.count(b'\n')==71 and b.endswith(b'\n') and not b.endswith(b'\n\n') and not b.startswith(b'\xef\xbb\xbf'),'LF_only_no_BOM_exact_final_LF')
source=(P/'p1_layer.py').read_bytes();approval=(P/'APPROVAL.json').read_bytes();calendar=(P/'CALENDAR.json').read_bytes()
ok(hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest()=='caa7cca0a4f5f4dac0b62c5cfca5b8a45ce97972','original_loader_git_identity')
sp=importlib.util.spec_from_file_location('original_p1',P/'p1_layer.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
variants={'valid':b,'CRLF':b.replace(b'\n',b'\r\n'),'no_final_LF':b[:-1],'BOM':b'\xef\xbb\xbf'+b,'extra_space':b+b' ','wrapped':b'POLICY_BODY_BEGIN\n'+b+b'POLICY_BODY_END\n'}
for name,v in variants.items():
 d=R/'fixtures'/name;d.mkdir(parents=True,exist_ok=False)
 (d/'POLICY_BODY.txt').write_bytes(v);(d/'CALENDAR.json').write_bytes(calendar);(d/'APPROVAL.json').write_bytes(approval)
 if name=='valid':ok(m.load_contract(d)['policy_body_sha256']==SHA,'actual_original_loader_accepts_whole_file')
 else:
  try:m.load_contract(d)
  except ValueError as e:ok(str(e)=='POLICY_IDENTITY','actual_original_loader_stops:'+name)
  else:raise AssertionError('unexpected acceptance:'+name)
 ok((d/'POLICY_BODY.txt').read_bytes()==v and (d/'APPROVAL.json').read_bytes()==approval,'no_repin_or_rewrite:'+name)
ok(m.POLICY_SHA==SHA and (P/'p1_layer.py').read_bytes()==source,'original_loader_unchanged')
path='agents/chatgpt/reviews/BLACKBOX_P1_NATIVE_TEST_20261101/POLICY_BODY.txt'
attrs='# Preserve only the approved P1 policy file as LF on checkout.\n'+path+' text eol=lf\n'
(R/'proposed.gitattributes').write_text(attrs,encoding='utf-8')
repo=R/'git_fixture';repo.mkdir(exist_ok=False)
def git(*args):return subprocess.run(['git','-C',str(repo),*args],capture_output=True,check=True).stdout
cmds=[]
git('init','--quiet');git('config','core.autocrlf','true');(repo/'.gitattributes').write_text(attrs)
f=repo/path;f.parent.mkdir(parents=True);f.write_bytes(b)
git('add','--','.gitattributes',path);actual=git('check-attr','text','eol','--',path).decode();ok('text: set' in actual and 'eol: lf' in actual,'scoped_attributes_effective')
ok(git('show',':'+path)==b,'index_blob_preserved')
f.write_bytes(b'fixture overwrite before forced checkout')
git('checkout-index','-f','--',path)
ok(f.read_bytes()==b and digest(f.read_bytes())==SHA,'autocrlf_true_checkout_retains_exact_LF_bytes')
ok(git('check-attr','eol','--','unrelated.txt').decode().strip().endswith('unspecified'),'unrelated_paths_unaffected')
result={'actual_original_loader_and_git_fixture_checks':len(checks),'checks':checks,'source_blob_sha':'2b2249af770a40bbeb6027da870c78f8631e1c4c','bytes':len(b),'sha256':SHA,'encoding':'UTF-8','BOM':False,'line_ending':'LF','LF_count':71,'trailing_LF_count':1,'byte_range_half_open':[0,len(b)],'last_byte_offset':len(b)-1,'last_byte_hex':'0a','Git_autocrlf_true_checkout_byte_equal':True,'native_execution':False,'policy_changed':False,'local_task_issued':False}
(R/'CHECK_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
