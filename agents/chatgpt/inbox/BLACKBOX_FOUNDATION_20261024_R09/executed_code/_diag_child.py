import sys,os,runpy,traceback
sys.dont_write_bytecode=True
def guard(event,args):
 if event in ('socket.connect','socket.connect_ex','socket.getaddrinfo','subprocess.Popen','os.system','os.remove','os.rename','os.mkdir','os.rmdir','os.truncate','os.link','os.symlink'):
  raise PermissionError('R09_PREFLIGHT_SIDE_EFFECT_BLOCKED:'+event)
 if event=='open':
  mode=args[1];flags=args[2] or 0
  if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
   raise PermissionError('R09_PREFLIGHT_WRITE_BLOCKED')
sys.addaudithook(guard)
sys.path.insert(0,sys.argv[2])
script=sys.argv[1];sys.argv=[script,'--task-class','CACHE','--json']
try:
 runpy.run_path(script,run_name='__main__')
except SystemExit as e:
 print('SYSTEMEXIT',e.code)
except BaseException:
 traceback.print_exc()
