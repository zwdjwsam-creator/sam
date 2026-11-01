"""Stock-only presumed availability. No acquisition, native cleaning or execution engine."""
import hashlib
import json
from datetime import datetime, date, time, timedelta, timezone
from pathlib import Path

CN=timezone(timedelta(hours=8))
POLICY_SHA='31dee3a67f7674db25b0ba4d56c169c941e28f857b8656454b6006401938f884'
CAL_SHA='ab00fa8c597c9b01977cc060a202371d2de73a6a32b8a4fe6cc533a705d056d9'
SOURCE_FIELDS=['time','code','open','high','low','close','volume','money','paused',
               'high_limit','low_limit','avg','pre_close','factor']
FIELDS=[x for x in SOURCE_FIELDS if x!='factor']
USES={'BACKTEST_DAILY_T1','FACTOR_RESEARCH_T1'}

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(b):return hashlib.sha256(b).hexdigest()

def load_contract(root):
    root=Path(root);body=(root/'POLICY_BODY.txt').read_bytes();cal=(root/'CALENDAR.json').read_bytes()
    approval=json.loads((root/'APPROVAL.json').read_bytes())
    require(sha(body)==POLICY_SHA==approval['policy_body_sha256'],'POLICY_IDENTITY')
    require(sha(cal)==CAL_SHA==approval['calendar_sha256'],'CALENDAR_IDENTITY')
    require(approval['status']=='OWNER_APPROVED_POLICY_ONLY' and approval['order_allowed'] is False,'APPROVAL')
    days=json.loads(cal)['returned']
    require(days==sorted(set(days)),'CALENDAR_ORDER')
    for d in days:require(date.fromisoformat(d).isoformat()==d,'CALENDAR_DATE')
    return {'days':days,'policy_body_sha256':POLICY_SHA,'calendar_sha256':CAL_SHA}

def available_at(day,contract):
    days=contract['days']
    if day not in days:return None
    i=days.index(day)
    if i+1==len(days):return None
    return datetime.combine(date.fromisoformat(days[i+1]),time(9),CN).isoformat()

def make_layer(rows,contract,product,generation,manifest_sha):
    require(product=='stock','PRODUCT_NOT_ADMITTED')
    require(bool(generation) and len(manifest_sha)==64 and all(c in '0123456789abcdef' for c in manifest_sha),'GENERATION_BINDING')
    require(contract['policy_body_sha256']==POLICY_SHA and contract['calendar_sha256']==CAL_SHA,'CONTRACT_BINDING')
    output=[];seen=set()
    for row in rows:
        require(set(row)==set(SOURCE_FIELDS),'SOURCE_FIELD_SET')
        require(isinstance(row['time'],str) and len(row['time'])==10,'DAILY_DATE_REQUIRED')
        day=row['time'];require(date.fromisoformat(day).isoformat()==day,'DATE')
        code=row['code'];require(isinstance(code,str) and len(code)==11 and code[:6].isdigit()
                and code[6:] in {'.XSHG','.XSHE'},'SOURCE_NAMESPACE')
        key=(day,code);require(key not in seen,'DUPLICATE_KEY');seen.add(key)
        require(code!='600621.XSHG' or day!='2026-10-27','QUARANTINED_KEY')
        require(row['paused'] in [0,1],'PAUSED_STATE')
        at=available_at(day,contract)
        # Original source values are copied; excluded factor is never exposed by this view.
        values={k:row[k] for k in FIELDS}
        output.append({'values':values,'availability':{
            'availability_basis':'PRESUMED_T1_PREOPEN',
            'status':'PRESUMED' if at else 'UNRESOLVED',
            'presumed_available_at':at,
            'unresolved_reason':None if at else 'DATA_DAY_OR_SUCCESSOR_NOT_IN_FROZEN_CALENDAR',
            'revision_assumption':'PRESUMED_UNCHANGED',
            'policy_id':'BLACKBOX_DAILY_AVAILABILITY_PRESUMPTION_P1',
            'policy_body_sha256':POLICY_SHA,'calendar_sha256':CAL_SHA,
            'source_generation':generation,'source_manifest_sha256':manifest_sha,
            'historical_pit':'NOT_ESTABLISHED','factor':'UNRESOLVED_NOT_EXPOSED'}})
    return output

def select(layer,contract,purpose,decision_time,fields,generation,manifest_sha):
    require(purpose in USES,'PURPOSE_NOT_ADMITTED')
    require(fields and set(fields)<=set(FIELDS) and len(fields)==len(set(fields)),'FIELD_NOT_ADMITTED')
    decision=datetime.fromisoformat(decision_time)
    require(decision.tzinfo is not None and decision.utcoffset() is not None,'NAIVE_DECISION_TIME')
    answer=[];seen=set()
    for row in layer:
        a=row['availability'];v=row['values'];key=(v['time'],v['code'])
        require(key not in seen,'DUPLICATE_KEY');seen.add(key)
        require(set(v)==set(FIELDS),'LAYER_FIELD_SET')
        require(a['source_generation']==generation and a['source_manifest_sha256']==manifest_sha,'SOURCE_BINDING')
        expected=available_at(v['time'],contract)
        require(a['presumed_available_at']==expected and a['status']==('PRESUMED' if expected else 'UNRESOLVED'),'AVAILABILITY_TAMPER')
        require(a['policy_body_sha256']==POLICY_SHA and a['calendar_sha256']==CAL_SHA
                and a['historical_pit']=='NOT_ESTABLISHED' and a['revision_assumption']=='PRESUMED_UNCHANGED','POLICY_BINDING')
        if expected is not None and datetime.fromisoformat(expected)<=decision:
            answer.append({k:v[k] for k in fields})
    return answer
