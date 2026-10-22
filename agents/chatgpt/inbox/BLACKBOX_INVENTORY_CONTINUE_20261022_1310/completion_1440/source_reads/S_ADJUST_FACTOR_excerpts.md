## main @12
```
12|def main() -> int:
13|    if not TASK_SCRIPT.is_file():
14|        print("HARD_BLOCK: incremental engine missing", TASK_SCRIPT)
15|        return FAIL
16|    cmd = [str(PY), "-u", str(TASK_SCRIPT), *sys.argv[1:]]
17|    r = guarded_run(cmd, cwd=str(ROOT))
18|    return int(r.returncode)
19|
20|
21|if __name__ == "__main__":
22|    raise SystemExit(main())
```