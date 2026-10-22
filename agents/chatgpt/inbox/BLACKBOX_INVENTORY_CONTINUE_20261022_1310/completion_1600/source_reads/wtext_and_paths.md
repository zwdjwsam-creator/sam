# wtext + paths

`
20|import pandas as pd
21|
22|sys.stdout.reconfigure(encoding="utf-8")
23|
24|ROOT = Path(r"E:\BLACKBOX")
25|TASK = ROOT / "任务" / "BLACKBOX_BACKTEST_CACHE_COMPILER_R1"
26|ARCHIVE = Path(r"D:\CURSOR_TASK_ARCHIVE\BLACKBOX_BACKTEST_CACHE_COMPILER_R1")
27|CACHE_ROOT = ROOT / "数据" / "回测缓存"
28|RELEASES = CACHE_ROOT / "releases"
29|CANARY_ROOT = CACHE_ROOT / "_canary"
30|REGISTRY = CACHE_ROOT / "registry"
31|POINTER = CACHE_ROOT / "CURRENT_CACHE_RELEASE.json"
32|# HARD: canary is a smoke artifact only — never authority / never CURRENT.
33|CANARY_CURRENT_PUBLISH = "STRUCTURALLY_FORBIDDEN"
34|CURRENT = ROOT / "数据" / "清洗成品" / "CURRENT_CLEANING_RELEASE.json"
35|PLANE = ROOT / "数据" / "原始只读" / "strategy_data_plane_additions"

56|def wjson(path: Path, obj: Any) -> None:
57|    path.parent.mkdir(parents=True, exist_ok=True)
58|    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
59|    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
60|    os.replace(tmp, path)
61|
62|
63|def wtext(path: Path, text: str) -> None:
64|    path.parent.mkdir(parents=True, exist_ok=True)
65|    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
66|    tmp.write_text(text, encoding="utf-8")
67|    os.replace(tmp, path)
68|
69|
70|def log(msg: str) -> None:
71|    line = f"[{now_iso()}] {msg}"
72|    print(line, flush=True)
`
