"""Run the unchanged pinned DATA preflight under no-E-write/no-network guard."""
import runpy,sys
import guard as g
g.validate(True)
g.audit([g.CONTROL])
sys.path.insert(0,str(g.ROOT/'脚本'))
sys.argv=[str(g.ROOT/'脚本/blackbox_must_read_preflight_r1.py'),'--task-class','DATA']
runpy.run_path(sys.argv[0],run_name='__main__')
