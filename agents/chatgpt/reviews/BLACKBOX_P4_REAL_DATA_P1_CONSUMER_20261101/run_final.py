import os,sys,subprocess,json,time
from pathlib import Path
r=Path(__file__).resolve().parent;start=time.time()
with (r/'FINAL_TEST.stdout.txt').open('xb') as a,(r/'FINAL_TEST.stderr.txt').open('xb') as b:
 p=subprocess.run([sys.executable,'-B','-X','utf8','-m','unittest','-v','test_p4'],env=dict(os.environ,PYTHONPATH='testdeps:p4_offline'),stdout=a,stderr=b)
(r/'FINAL_PROCESS.json').write_text(json.dumps({'argv':[sys.executable,'-B','-X','utf8','-m','unittest','-v','test_p4'],'actual_exit':p.returncode,'start_epoch':start,'end_epoch':time.time(),'scope':'GPT_OFFLINE_ONLY_NO_NATIVE_TASK'},indent=2)+'\n')
print('actual_exit',p.returncode);print((r/'FINAL_TEST.stderr.txt').read_text()[-1400:]);sys.exit(p.returncode)
