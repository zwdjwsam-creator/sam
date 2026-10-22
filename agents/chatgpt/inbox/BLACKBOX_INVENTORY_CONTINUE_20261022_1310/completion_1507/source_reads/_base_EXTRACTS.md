# 脚本/_base.py
sha256=b8cc60746f92dc63049e8e6b6b6f39c6553dd98b69374b9f797d49b2654f2258
size=11800

## imports
```
import sys
import io
import re
import json
import hashlib
import subprocess
import tempfile
import shutil
import fnmatch
from pathlib import Path
from datetime import datetime, timezone
```

## consts
```
SCHEMA_VERSION = "1.1.0"
ROOT = Path(__file__).resolve().parents[1]
OK, WARN, FAIL = 0, 1, 2
_SLUG_BAD = re.compile(r"[^\w\u4e00-\u9fff-]+", flags=re.UNICODE)
_RUNTIME_CONTEXT: dict = {
    "current_task_dir": None,
    "current_task_slug": None,
    "task_type": None,
    "write_exemption_paths": [],
}
PROTECTED_MEMORY_WRITE_PATTERNS = [
    "记忆盘/01_黑盒任务经验包/**",
    "记忆盘/02_策略经验包/**",
    "记忆盘/03_操作流程经验包/**",
]
PERMANENT_WRITE_FORBIDDEN = [
    "**/.env",
    "**/*.token",
    "**/*.key",
    "**/credentials*",
    "**/secrets*",
    "**/*password*",
    "**/*passwd*",
    "**/*pwd*",
    "**/*交易密码*",
    "**/*券商*交易*",
    "**/*qmt*trade*",
    "**/*order_bridge*",
]
MEMORY_WRITE_ALLOWED_TASK_TYPES = {
    "MEMORY_PATCH",
    "EXPERIENCE_UPDATE",
    "SETUP_INFRASTRUCTURE_BOOTSTRAP",
    "LESSON_HARVEST",
}
```

## run L92-L97 (6 lines)
```python
def run(cmd, **kw):
    """统一 UTF-8 + 不抛异常，返回 CompletedProcess。"""
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    kw.setdefault("text", True)
    return subprocess.run(cmd, **kw)
```

## guarded_run L117-L123 (7 lines)
```python
def guarded_run(cmd, **kw):
    """对潜在破坏性命令做正则黑名单拦截。"""
    flat = cmd if isinstance(cmd, str) else " ".join(map(str, cmd))
    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, flat, flags=re.IGNORECASE):
            raise ForbiddenCommandError(f"BLOCKED by guarded_run: {pat} matched in: {flat}")
    return run(cmd, **kw)
```
