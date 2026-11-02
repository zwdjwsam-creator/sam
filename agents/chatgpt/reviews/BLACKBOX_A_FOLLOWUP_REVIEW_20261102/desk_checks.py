import json, hashlib
from pathlib import Path
from decimal import Decimal as D, ROUND_CEILING

root=Path(__file__).resolve().parent
checks=[]
def check(name, ok):
    if not ok: raise AssertionError(name)
    checks.append(name)
account=json.loads((root/'PRIOR_18_FILES.json').read_text())
paths=[x['path'] for x in account['files']]
check('18 unique prior paths',len(paths)==len(set(paths))==18)
check('16 review paths',sum('/reviews/' in p for p in paths)==16)
check('one outbox and one state',sum('/outbox/' in p for p in paths)==sum('/state/' in p for p in paths)==1)
check('all prior blob identities present',all(len(x['git_blob_sha'])==40 for x in account['files']))
record=json.loads((root/'OFFICIAL_SCREENSHOT_RECORD_DRAFT.json').read_text())
check('unreceived screenshot identity is null',all(v is None for v in record['original_artifact'].values()))
check('unit gate remains closed',record['absolute_units_established'] is False)
regime=json.loads((root/'REGIME_BINDING_DESK_PLAN.json').read_text())
check('no native command',regime['local_command'] is None and record['local_command'] is None)
check('no regime coverage invented',regime['bound_current_window_security_day_regime_records'] is None)
check('no orders or backtest',regime['orders_allowed'] is False and regime['backtest_admission'] is False)
b=(root.parent/'a_inputs_review/DATASET_STATE.json').read_bytes()
check('registered source literal Git blob',hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==regime['evidence_blob_sha'])
proxy=D(14076869)/D(896225431)*100
check('turnover proxy share versus hands',D('1.57')<proxy<D('1.58') and D('157')<proxy*100<D('158'))
check('relative price check only',D('17.64')<D('254286654.36')/D(14076869)<D('18.38'))
check('exact slippage precursor',D('17.87')*D('1.0005')==D('17.878935'))
check('outward rounding reaches equality case',(D('19.81')*D('1.0005')/D('.01')).to_integral_value(rounding=ROUND_CEILING)*D('.01')==D('19.82'))
check('quantity cap is not commission',D(14076869)*D('.005')==D('70384.345'))
print(json.dumps({'assertions':len(checks),'checks':checks,'status':'DESK_DOCUMENT_AND_ARITHMETIC_ONLY','turnover_proxy_if_shares_percent':str(proxy),'turnover_proxy_if_hands_percent':str(proxy*100),'native_execution':False,'units_established':False,'regime_admitted':False},indent=2))
