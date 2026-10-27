"""Exact legacy TIP watcher control only. No business/supplier module imports."""
import argparse
import base64
import datetime
import json
import ntpath
import os
from pathlib import Path
import platform
import re
import subprocess

ARCH = r'D:\CURSOR_TASK_ARCHIVE\JQ_TIP_CATCHUP_UNATTENDED_R1'
WATCHERS = {ntpath.normcase(ntpath.join(ARCH,n)) for n in
            ['watchdog_after_resume.ps1','catchup_progress_loop.ps1','monitor_loop.ps1']}
DRIVER = ntpath.normcase(ntpath.join(ARCH,'run_unattended_catchup_r1.py'))
PS_NAMES = {'powershell.exe','pwsh.exe','powershell','pwsh'}
QUERY = r'''$ErrorActionPreference='Stop'
$p=@(Get-CimInstance Win32_Process | Select-Object ProcessId,CreationDate,Name,ExecutablePath,CommandLine)
$t=@(Get-ScheduledTask | ForEach-Object { [pscustomobject]@{TaskName=$_.TaskName;TaskPath=$_.TaskPath;State=[string]$_.State;Enabled=$_.Settings.Enabled;Actions=@($_.Actions | Select-Object Execute,Arguments)} })
@{Processes=$p;Tasks=$t} | ConvertTo-Json -Depth 7 -Compress'''

def quoted(s):
    return "'"+str(s).replace("'","''")+"'"

def ps(script):
    r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive',
                     '-EncodedCommand',base64.b64encode(('[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false); '+script).encode('utf-16le')).decode('ascii')],
                     capture_output=True,timeout=30)
    if r.returncode:
        # Do not print raw command/arguments; native task arguments may contain secrets.
        raise RuntimeError('NATIVE_OPERATION_FAILED_EXIT_'+str(r.returncode))
    return r.stdout.decode('utf-8-sig')

def snapshot():
    d=json.loads(ps(QUERY))
    if len(d.get('Processes',[]))>5000 or len(d.get('Tasks',[]))>5000:
        raise RuntimeError('METADATA_CAP_NO_MUTATION')
    return d

def ps_file(arguments):
    if re.search(r'(?i)(?:^|\s)-(?:command|c|encodedcommand|enc)\b',arguments or ''):
        return None
    m=re.search(r'(?i)(?:^|\s)-file\s+(?:"([^"]+)"|(\S+))',arguments or '')
    return ntpath.normcase(ntpath.normpath(m.group(1) or m.group(2))) if m else None

def action_kind(a):
    exe=ntpath.basename(a.get('Execute') or '').lower()
    args=a.get('Arguments') or ''
    if exe in PS_NAMES:
        path=ps_file(args)
        if path in WATCHERS:return 'WATCHER'
        if path==DRIVER:return 'DRIVER'
    if exe in {'python.exe','pythonw.exe','python','pythonw'}:
        # A quoted/unquoted exact source token is required, not a keyword/name match.
        tokens=re.findall(r'"([^"]+)"|(\S+)',args)
        values=[ntpath.normcase(ntpath.normpath(x or y)) for x,y in tokens]
        if DRIVER in values and '-c' not in values:return 'DRIVER'
    return None

def task_kind(t):
    kinds=[action_kind(a) for a in t.get('Actions',[])]
    return ('WATCHER' if all(k=='WATCHER' for k in kinds) else 'DRIVER') if kinds and all(kinds) else None

def process_watcher(p):
    return (str(p.get('Name','')).lower() in PS_NAMES and
            ps_file(p.get('CommandLine') or '') in WATCHERS)

def task_identity(t):
    return (t.get('TaskPath'),t.get('TaskName'),t.get('Actions'),t.get('Enabled'))

def process_identity(p):
    return (p.get('ProcessId'),p.get('CreationDate'),p.get('ExecutablePath'),p.get('CommandLine'))

def candidates(d):
    tasks=[];processes=[]
    for t in d.get('Tasks',[]):
        kind=task_kind(t)
        if kind or re.search(r'(?i)JQ_TIP_CATCHUP|catchup|watchdog',str(t.get('TaskName',''))):
            tasks.append({'TaskPath':t.get('TaskPath'),'TaskName':t.get('TaskName'),
                          'Enabled':t.get('Enabled'),'State':t.get('State'),'proven_kind':kind})
    for p in d.get('Processes',[]):
        cmd=p.get('CommandLine') or ''
        if process_watcher(p) or re.search(r'(?i)run_unattended_catchup|watchdog_after_resume|catchup_progress_loop|monitor_loop',cmd):
            processes.append({'ProcessId':p.get('ProcessId'),'CreationDate':p.get('CreationDate'),
                              'Name':p.get('Name'),'proven_watcher':process_watcher(p)})
    return {'tasks':tasks,'processes':processes,'raw_command_lines_exported':False}

def require_role(role,apply,actual):
    if actual.upper()!=role or (apply and role!='SAM'):
        raise RuntimeError('HOST_OR_AUTHORITY_MISMATCH')

def write_new(path,obj):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,ensure_ascii=True,indent=2);f.write('\n')

def small_controls():
    result=[]
    for name in ['TARGET_END.txt','FINAL_STATUS.json']:
        p=Path(ARCH)/name
        try:
            if p.is_symlink() or os.path.isjunction(p.parent):raise ValueError('REPARSE_BLOCKED')
            if p.stat().st_size>65536:raise ValueError('SIZE_CAP')
            b=p.read_bytes();text=b.decode('utf-8-sig')
            if re.search(r'(?i)password|passwd|api_key|access_token|private key',text):
                raise ValueError('POTENTIAL_CREDENTIAL_LITERAL_WITHHELD')
            result.append({'path':str(p),'status':'READ','content':text})
        except (OSError,ValueError,UnicodeError) as e:
            result.append({'path':str(p),'status':'UNRESOLVED','reason':type(e).__name__})
    return result

def raw_name_listing():
    root=Path(r'E:\BLACKBOX\数据\原始只读\JQData_9999_official_raw')
    result=[]
    for rel in ['P2_stock_daily','P3_index',r'P4_fund_etf_raw_none\fund_etf_price_daily']:
        p=root/rel;record={'directory':str(p),'files':[],'contents_read':False,'source_absence_claim_allowed':False}
        try:
            if p.is_symlink() or os.path.isjunction(p):raise ValueError('REPARSE_BLOCKED')
            with os.scandir(p) as entries:
                for i,e in enumerate(entries):
                    if i>=10000:record['limit']='ENTRY_CAP';break
                    if '20260924' in e.name and e.name.lower().endswith('.parquet') and e.is_file(follow_symlinks=False):
                        s=e.stat(follow_symlinks=False)
                        record['files'].append({'name':e.name,'bytes':s.st_size,'mtime_ns':s.st_mtime_ns})
                        if len(record['files'])>=1000:record['limit']='MATCH_CAP';break
        except (OSError,ValueError):record['status']='UNRESOLVED_EXACT_DIRECTORY'
        result.append(record)
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--role',choices=['SAM','ZHANGWEI'],required=True)
    ap.add_argument('--allow-sam-stop',action='store_true');ap.add_argument('--out',required=True)
    a=ap.parse_args();require_role(a.role,a.allow_sam_stop,platform.node())
    if os.name!='nt':raise RuntimeError('WINDOWS_REQUIRED')
    out=Path(a.out);base=Path(r'C:\LAN_SHARE_REPORT\BLACKBOX_UPDATE_PREREQUISITES_20261027')/a.role
    if out.parent.resolve()!=base.resolve() or out.name!='watchdog_control_001':raise RuntimeError('OUTPUT_BOUNDARY')
    out.mkdir(exist_ok=False)
    report={'host':platform.node(),'role':a.role,'authorized_sam_stop':a.allow_sam_stop,
            'order_allowed':False,'actions':[],'supplier_calls':0,'business_modules_imported':False}
    try:
        before=snapshot();report['before']=candidates(before)
        report['control_files']=small_controls()
        if a.role=='ZHANGWEI':report['raw_filename_metadata']=raw_name_listing()
        selected=[t for t in before['Tasks'] if task_kind(t) and t.get('Enabled')]
        watchers=[p for p in before['Processes'] if process_watcher(p)]
        if len(selected)+len(watchers)>50:raise RuntimeError('ACTION_CAP_NO_MUTATION')
        if a.allow_sam_stop:
            for t in selected:
                current=snapshot();live=next((x for x in current['Tasks'] if x.get('TaskName')==t.get('TaskName') and x.get('TaskPath')==t.get('TaskPath')),None)
                if live is None or task_identity(live)!=task_identity(t):
                    report['actions'].append({'action':'SKIPPED_TASK_DRIFT','name':t.get('TaskName')});continue
                row={'action':'DISABLE_SAM_TASK','TaskName':t['TaskName'],'TaskPath':t['TaskPath'],'enabled_before':True,'delete':False}
                report['actions'].append(row);write_new(out/f'INTENT_{len(report["actions"]):03}.json',row)
                ps('Disable-ScheduledTask -TaskName '+quoted(t['TaskName'])+' -TaskPath '+quoted(t['TaskPath'])+' -ErrorAction Stop | Out-Null')
                row['native_exit']=0
            for p in watchers:
                live=next((x for x in snapshot()['Processes'] if x.get('ProcessId')==p.get('ProcessId')),None)
                if live is None or process_identity(live)!=process_identity(p) or not process_watcher(live):
                    report['actions'].append({'action':'SKIPPED_PROCESS_DRIFT','pid':p.get('ProcessId')});continue
                pid=int(p['ProcessId']);assert pid>0
                row={'action':'STOP_EXACT_SAM_WATCHER_PROCESS','pid':pid,'creation':p.get('CreationDate'),'children_stopped':False}
                report['actions'].append(row);write_new(out/f'INTENT_{len(report["actions"]):03}.json',row)
                ps('Stop-Process -Id '+str(pid)+' -ErrorAction Stop');row['native_exit']=0
        after=snapshot();report['after']=candidates(after)
        if a.allow_sam_stop and (any(task_kind(t) and t.get('Enabled') for t in after['Tasks']) or any(process_watcher(p) for p in after['Processes'])):
            report['status']='PARTIAL_MATCHED_REMAIN_NO_AUTOMATIC_RETRY';return 2
        report['status']='COMPLETED_BOUNDED'
        return 0
    except Exception as e:
        report['status']='PARTIAL_PRESERVE_FAILURE';report['error_type']=type(e).__name__
        if str(e).startswith('NATIVE_OPERATION_FAILED_EXIT_'):
            report['native_failure_exit']=int(str(e).rsplit('_',1)[-1])
        return 2
    finally:
        report['at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        write_new(out/'RESULT.json',report)
        for p in out.iterdir():
            if p.is_file():assert p.read_bytes()

if __name__=='__main__':raise SystemExit(main())
