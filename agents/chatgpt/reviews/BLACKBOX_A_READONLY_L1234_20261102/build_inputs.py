"""GPT assembly from exact retained HUB bodies; never a native entry point."""
from pathlib import Path, PureWindowsPath
import hashlib,json

ROOT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,o):(ROOT/n).write_text(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n',encoding='utf-8')
draft=read('l123_contract_draft/INPUT_CATALOGUE_DRAFT.json')
bindings=read('p3_dispatch/bindings.json')
for name,key in [('evidence/ADMISSION_R5.json','admission'),('evidence/REUSE_MANIFEST_R5.json','reuse_manifest')]:
 b=Path(name).read_bytes();assert len(b)==bindings[key]['bytes'] and sha(b)==bindings[key]['sha256']
admission=read('evidence/ADMISSION_R5.json');by_path={e['source']['path']:e for e in admission['entries']}
hist=[dict(source_id=r['source_id'],kind='HISTORICAL',path=str(PureWindowsPath(r['original_path'])),
           original_serialized_path=r['original_path'],expected_bytes=None,expected_sha256=r['expected_sha256']) for r in draft['historical_refs']]
stock=[]
for r in draft['stock_refs']:
 e=by_path[r['original_path']];assert e['source']['sha256']==r['expected_sha256']
 stock.append(dict(source_id=r['source_id'],kind='STOCK',path=str(PureWindowsPath(r['original_path'])),original_serialized_path=r['original_path'],
             expected_bytes=r['expected_bytes'],expected_sha256=r['expected_sha256'],indexed_session=e['date'],
             expected_physical_rows=len(e['admitted_positions'])+len(e['quarantined_positions']),quarantined_positions=e['quarantined_positions'],
             sample=r['root']=='R4' and r['relative_path']=='raw/stock/2026-10-15_00720_R4.parquet'))
reuse=read('evidence/REUSE_MANIFEST_R5.json')
refs={str(PureWindowsPath(r['path']).name):r for part in reuse.values() for r in part['references'] if 'universes' in r['path'] and 'stock_' in r['path']}
universes=[]
for i,r in enumerate(read(ROOT/'UNIVERSE_HUB_IDENTITIES.json')['files']):
 name=r['path'].split('/')[-1];ref=refs[name];b=Path('l1234_offline_universes',name).read_bytes()
 assert len(b)==ref['bytes']==r['bytes'] and sha(b)==ref['sha256']
 assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['git_blob_sha']
 u=json.loads(b)
 universes.append(dict(source_id='UNIVERSE_%02d'%i,kind='UNIVERSE',path=str(PureWindowsPath(ref['path'])),original_serialized_path=ref['path'],
             indexed_session=u['date'],expected_bytes=ref['bytes'],expected_sha256=ref['sha256'],hub_path=r['path'],hub_blob_sha=r['git_blob_sha']))
b=read('calendar_acceptance/return/capture/result_001/TRADE_DAY_SEQUENCE.json')
p1=read('p1_dispatch/CALENDAR.json');sessions=sorted(set(b['trade_days'])|set(p1['returned']))
assert len(sessions)==3114 and sessions[-1]=='2026-10-27'
data_sessions=sorted({r['indexed_session'] for r in stock})
assert len(hist)==17 and len(stock)==1122 and len(universes)==17 and len(set(r['path'] for r in hist+universes+stock))==1156
assert sum(r['expected_physical_rows'] for r in stock)==88812
assert sum(len(r['quarantined_positions']) for r in stock)==1
save('INPUTS.json',dict(task_id='BLACKBOX_A_READONLY_L1234_20261102',historical=hist,universes=universes,stock=stock,
     data_sessions=data_sessions,review_sessions=sessions,calendar_is_policy_extension=False,
     no_limit_exceptions=[['002731.XSHE','2026-10-23'],['301139.XSHE','2026-09-30']],
     exception_census_complete=False,preregistration=read(ROOT/'L4_PREREGISTRATION.json'),
     official_reference=dict(scope_compatible_and_complete=False,cells={},status='OFFICIAL_DATED_TOTALS_AND_SCOPE_NOT_BOUND')))
save('RULE_PINS.json',read('calendar_dispatch/RULE_PINS.json'))
manifest=read('evidence/MUST_READ_MANIFEST_CURRENT.json')
save('PREFLIGHT_AUX_RULES.json',dict(files=[dict(path=str(PureWindowsPath('E:/BLACKBOX')/r['path']),text_sha256=r['sha256'],
            role='UNSELECTED_RULE_TEXT_READ_BY_ORIGINAL_PREFLIGHT_METADATA_PASS') for k,r in manifest['files'].items() if k not in ('BOOTSTRAP','DATA_ACCESS')]))
save('CONTRACT.json',dict(task_id='BLACKBOX_A_READONLY_L1234_20261102',status='APPROVED_READ_ONLY_DISPATCH',execution_host='ZHANGWEI',
     ACK_REQUESTED=True,ORDER_ALLOWED=False,native_fixture_tests=51,source_refs=1156,stock_physical_rows=88812,
     source_discovery=False,source_writes=False,supplier_calls=False,backtest_admitted=False,research_admitted=False,
     current_switch_allowed=False,release_allowed=False,policy_calendar_extended=False,
     return_path='agents/chatgpt/inbox/BLACKBOX_A_READONLY_L1234_20261102/ZHANGWEI/',
     runtime=dict(python='3.12.10',pyarrow='24.0.0'),source_max_file_bytes=67108864,total_source_bytes_cap=536870912,
     output_max_file_bytes=8388608,output_total_bytes_cap=268435456,total_row_cap=150000,
     package_path=r'C:\LAN_SHARE_REPORT\BLACKBOX_A_READONLY_L1234_20261102_PACKAGE\package',
     capture_path=r'C:\LAN_SHARE_REPORT\BLACKBOX_A_READONLY_L1234_20261102_CAPTURE',outer_path=r'C:\LAN_SHARE_REPORT\BLACKBOX_A_READONLY_L1234_20261102_OUTER',
     runtime_network=False,transport='Only local AI HUB upload and immutable readback after capture; no supplier/general networking'))
save('INPUT_ASSEMBLY_CHECK.json',dict(status='PASS_PINNED_INPUT_ASSEMBLY_ONLY',historical_refs=17,stock_refs=1122,universe_refs=17,
     distinct_paths=1156,stock_physical_rows=88812,review_only_dates=3114,raw_source_reads_on_ZHANGWEI=0,
     source_identity_basis='Prior exact RAW plan/admission/reuse manifests plus independent immutable HUB universe blob verification',
     native_execution_observed=False))
print('Pinned1156 sources;17 exact daily lifecycle files replace the unbound legacy master-root dependency for candidate classification only.')
