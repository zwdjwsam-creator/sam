"""Exact E: originals; no ZIP construction, discovery, alternate roots or price fetch."""
from pathlib import Path,PureWindowsPath
import ast,csv,io,json,os,socket
import candidate_adapter as c

TASK='BLACKBOX_R5_NATIVE_CANDIDATE_P3_20261101'
ROOT=Path(r'E:\BLACKBOX')
ADMISSION=ROOT/'STAGING/BLACKBOX_RAW_NONE_INCREMENT_20261027_R5/ADMISSION_R5.json'
REUSE=ROOT/'STAGING/BLACKBOX_RAW_NONE_INCREMENT_20261027_R5/REUSE_MANIFEST_R5.json'
DICT=ROOT/'数据/原始只读/JQData_reference_dictionary/20_unified_data_schema_contract_freeze_full_R1'
DOMAIN=DICT/'02_domain_schema/domain_schema_contract.csv'
PIT=DICT/'04_pit_schema/pit_schema_contract.csv'

def safe(p):
    p=Path(p)
    for part in [p,*p.parents]:
        if part.exists() or part.is_symlink():
            s=part.lstat()
            c.require(not part.is_symlink() and not getattr(s,'st_file_attributes',0)&0x400
                      and not (hasattr(part,'is_junction') and part.is_junction()),'NATIVE_REPARSE_PATH')
    return p

def exact(p,pin):
    safe(p);b=p.read_bytes()
    c.require(len(b)==pin['bytes'] and c.sha(b)==pin['sha256'],'NATIVE_SOURCE_IDENTITY:'+str(p))
    return b

def semantic_bind(domain,pit):
    domains=list(csv.DictReader(io.StringIO(domain.decode('utf-8-sig'))))
    pits=list(csv.DictReader(io.StringIO(pit.decode('utf-8-sig'))))
    price=[r for r in domains if r['domain']=='price_fq_factor']
    c.require(len(price)==1,'PRICE_DOMAIN_ROW')
    r=price[0];required=ast.literal_eval(r['required_fields'])
    expected=['symbol','trade_date','open','high','low','close','volume','money','factor','high_limit','low_limit','paused']
    c.require(required==expected and r['target_table_name']=='stock_daily'
              and r['primary_keys']=='symbol+trade_date' and r['time_key']=='trade_date'
              and r['can_enter_clean']=='True' and not ast.literal_eval(r['forbidden_fields']), 'DICTIONARY_SEMANTICS_CHANGED')
    pitrow=next(r for r in pits if r['domain']=='price_fq_factor')
    mappings=[]
    for name in c.FIELDS:
        target={'time':'trade_date','code':'symbol'}.get(name,name)
        mappings.append({'source':name,'target_stock_view':target,'required_by_domain':target in required,
          'physical_source_type':str(c.EXPECTED.field(name).type),'transform':'EXACT_COPY_NO_SCALE_OR_FILL',
          'role':'SOURCE_SUPPLEMENT' if name in ['avg','pre_close'] else 'DOMAIN_REQUIRED',
          'null_rule':'NO_ADMITTED_NULL; exact quarantined OHL nulls retained separately',
          'unit':'SOURCE_NATIVE_UNCONVERTED; no numeric unit asserted by CSV',
          'formal_type_unit_definition':'UNBOUND_IN_NORMATIVE_CSV',
          'P1_activation_in_this_task':False,'factor_excluded_from_P1_policy':name=='factor'})
    return {'domain_row':r,'pit_row':pitrow,'field_mapping':mappings,
      'unbound':['Normative target physical types and numeric unit definitions are not in these CSVs.',
                 'ETF/index normative product rows not bound; native values only, no P1 eligibility.',
                 'Historical actual availability not established; P1 approved presumption separate.',
                 'Original eight-field consumer does not enforce observation/tradability restrictions.'],
      'stock_required_fields_checked':12,'source_supplements':['avg','pre_close'],
      'dictionary_formal_admission':False,'candidate_scope':'VALUE_PRESERVATION_QA_ONLY'}

class NativeBodyReader:
    def __init__(self,package,gate_verified=False):
        c.require(os.name=='nt' and socket.gethostname().upper()=='ZHANGWEI','NATIVE_HOST')
        self.root=ROOT;self.bindings=json.loads((Path(package)/'bindings.json').read_bytes())
        self.native_gate_verified=gate_verified
        admission_bytes=exact(ADMISSION,self.bindings['admission'])
        reuse_bytes=exact(REUSE,self.bindings['reuse_manifest'])
        self.admission=json.loads(admission_bytes)
        reuse=json.loads(reuse_bytes)
        self.source_roots=[Path(p) for p in self.bindings['source_prefixes'].values()]
        self.plan=c.load_pinned(Path(package)/'RAW_TRANSFER_PLAN.json',self.bindings['plan'])
        self.rows={(r['root'],r['relative_path']):r for r in self.plan['rows']}
        self.entry_keys=[c.source_key(e,self.bindings) for e in self.admission['entries']]
        c.require(len(self.rows)==len(self.entry_keys)==len(set(self.entry_keys))==1504
                  and set(self.rows)==set(self.entry_keys),'NATIVE_SOURCE_SET')
        c.require(self.admission['row_position_base']==0 and self.admission['source_values_changed'] is False,'ADMISSION_HEADER')
        cells=[[p,d] for p,ds in reuse['r1']['plan']['increment_days'].items() for d in ds]
        c.require(cells==self.bindings['expected_cells'],'EXPECTED_CELLS')
        domain_bytes=exact(DOMAIN,self.bindings['domain_contract'])
        pit_bytes=exact(PIT,self.bindings['pit_contract'])
        self.semantic=semantic_bind(domain_bytes,pit_bytes)
        self.control_originals={ADMISSION:admission_bytes,REUSE:reuse_bytes,DOMAIN:domain_bytes,PIT:pit_bytes}

    def read(self,e,key):
        expected=PureWindowsPath(self.bindings['source_prefixes'][key[0]])/key[1]
        p=Path(e['source']['path'])
        c.require(PureWindowsPath(str(p))==expected and e['product']==key[1].split('/')[1],'EXACT_ORIGINAL_PATH')
        row=self.rows[key]
        c.require(e['source']['bytes']==row['bytes'] and e['source']['sha256']==row['sha256'],'PLAN_IDENTITY')
        return exact(p,e['source'])

    def verify_storage_again(self):
        for e,k in zip(self.admission['entries'],self.entry_keys):self.read(e,k)
        for p,b in self.control_originals.items():c.require(safe(p).read_bytes()==b,'CONTROL_SOURCE_CHANGED')
