"""Exact reviewed spawn equivalence across POSIX/Windows audit representations."""
import ntpath,os,subprocess,threading


class Rejected(ValueError):pass


class SpawnPolicy:
    def __init__(self,processes=(),inherited_cwd=None):
        self.cwd=os.path.normcase(os.path.abspath(os.fspath(inherited_cwd or os.getcwd())))
        self.vectors=set();self.commands={};self.local=threading.local()
        for argv in processes:
            a=tuple(argv)
            if not a or not all(isinstance(x,str) and '\0' not in x for x in a):raise Rejected('INVALID_REVIEWED_VECTOR')
            if not(os.path.isabs(a[0]) or (ntpath.isabs(a[0]) and ntpath.splitdrive(a[0])[0])):raise Rejected('EXECUTABLE_MUST_BE_ABSOLUTE')
            cmd=subprocess.list2cmdline(a)
            if cmd in self.commands and self.commands[cmd]!=a:raise Rejected('AMBIGUOUS_REVIEWED_COMMAND')
            self.vectors.add(a);self.commands[cmd]=a

    def working_dir(self,cwd):
        try:return os.path.normcase(os.path.abspath(os.fspath(os.getcwd() if cwd is None else cwd)))
        except TypeError:raise Rejected('CWD_TYPE')

    def candidate(self,executable,args,cwd):
        if isinstance(args,(list,tuple)):
            if not all(isinstance(x,str) and '\0' not in x for x in args):raise Rejected('ARGV_TYPE')
            a=tuple(args)
            if a not in self.vectors:raise Rejected('ARGV_NOT_REVIEWED')
            cmd=subprocess.list2cmdline(a)
        elif isinstance(args,str):
            a=self.commands.get(args);cmd=args
            if a is None:raise Rejected('COMMAND_LINE_NOT_REVIEWED')
        else:raise Rejected('ARGV_TYPE')
        if executable is not None and executable!=a[0]:raise Rejected('EXECUTABLE_OVERRIDE')
        effective=self.working_dir(cwd)
        if effective!=self.cwd:raise Rejected('CWD_NOT_REVIEWED')
        return cmd,effective

    def check(self,event,args):
        if event=='subprocess.Popen':
            self.local.pending=None
            if len(args)!=4:raise Rejected('POPEN_SHAPE')
            executable,argv,cwd,env=args
            if env is not None:raise Rejected('EXPLICIT_ENV_NOT_REVIEWED')
            self.local.pending=self.candidate(executable,argv,cwd)
        elif event=='_winapi.CreateProcess':
            pending=getattr(self.local,'pending',None);self.local.pending=None
            if len(args)!=3 or not isinstance(args[1],str):raise Rejected('CREATEPROCESS_SHAPE')
            if self.candidate(args[0],args[1],args[2])!=pending:raise Rejected('CREATEPROCESS_WITHOUT_MATCHING_POPEN')
