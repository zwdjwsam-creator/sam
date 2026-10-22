# BLACKBOX script base — B7 UTF-8 subprocess + U2 guarded_run + P2 delete whitelist + W1 write guard
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

SCHEMA_VERSION = "1.1.0"

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
OK, WARN, FAIL = 0, 1, 2

ALLOWED_DELETE_PATHS = [
    ("ALLOW_STAGING_DELETE", ROOT / "参考资料/.staging", None),
    (
        "ALLOW_CORRUPTED_THIRD_PARTY_REDOWNLOAD",
        ROOT / "参考资料/third_party_skills_reference/mattpocock_skills",
        "REQUIRE_DOWNLOAD_COMPLETE_MISSING",
    ),
    ("ALLOW_TEMPFILE_DELETE", Path(tempfile.gettempdir()), None),
]


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _allowed_delete_reason(p: Path):
    p = Path(p).resolve()
    for reason, root, guard in ALLOWED_DELETE_PATHS:
        root = Path(root).resolve()
        if not _is_relative_to(p, root):
            continue
        if guard == "REQUIRE_DOWNLOAD_COMPLETE_MISSING" and (root / ".download_complete").exists():
            return None
        return reason
    return None


class ForbiddenCommandError(RuntimeError):
    pass


def guarded_delete_path(p: Path) -> None:
    """仅删除白名单范围内路径；禁止删除用户数据、桌面文件、业务文件。"""
    p = Path(p)
    reason = _allowed_delete_reason(p)
    if reason is None:
        raise ForbiddenCommandError(f"DELETE BLOCKED outside whitelist: {p}")
    if p.is_dir():
        shutil.rmtree(p)
    elif p.exists():
        p.unlink()


def read_text(p: Path) -> str:
    return Path(p).read_text(encoding="utf-8")


def write_text(p: Path, s: str) -> None:
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(cmd, **kw):
    """统一 UTF-8 + 不抛异常，返回 CompletedProcess。"""
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("errors", "replace")
    kw.setdefault("text", True)
    return subprocess.run(cmd, **kw)


FORBIDDEN_PATTERNS = [
    r"\bgit\s+push\b",
    r"\bgit\s+merge\b",
    r"\bgit\s+branch\s+-D\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-fdx\b",
    r"\brm\s+-rf\b",
    r"\bRemove-Item\b.*-Recurse.*-Force",
    r"qmt\..*trade",
    r"\bpip\s+install\b",
    r"\bnpm\s+install\b",
    r"\bcursor\s+--install-extension\b",
    r"\bnpx\s+skills",
    r"/setup-matt-pocock-skills",
]


def guarded_run(cmd, **kw):
    """对潜在破坏性命令做正则黑名单拦截。"""
    flat = cmd if isinstance(cmd, str) else " ".join(map(str, cmd))
    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, flat, flags=re.IGNORECASE):
            raise ForbiddenCommandError(f"BLOCKED by guarded_run: {pat} matched in: {flat}")
    return run(cmd, **kw)


_SLUG_BAD = re.compile(r"[^\w\u4e00-\u9fff-]+", flags=re.UNICODE)


def make_slug(title: str, max_chars: int = 24) -> str:
    import secrets

    safe = _SLUG_BAD.sub("_", title).strip("_")
    safe = safe[:max_chars]
    safe.encode("utf-8").decode("utf-8")
    return f"{safe}_{secrets.token_hex(3)}"


# ════════════════════════════════════════════════════════════════
#  W1 写入层守卫
# ════════════════════════════════════════════════════════════════

_RUNTIME_CONTEXT: dict = {
    "current_task_dir": None,
    "current_task_slug": None,
    "task_type": None,
    "write_exemption_paths": [],
}

DEFAULT_WRITE_WHITELIST_PATTERNS = [
    "<CURRENT_TASK_DIR>/**",
    "记忆盘/04_任务报告归档/<CURRENT_TASK_SLUG>/**",
    "记忆盘/00_入口/experience_index.sqlite",
    "记忆盘/00_入口/installed_tools_scan.json",
    "记忆盘/00_入口/工具清单变更日志.md",
    "记忆盘/00_入口/tool_diff_ack_state.json",
    ".cursor/rules/installed_tools_snapshot.mdc",
    "AGENTS.md",
    ".cursor/rules/blackbox_master_contract.mdc",
    "smoke_test_report.json",
]

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


def get_current_task_dir() -> Path:
    if _RUNTIME_CONTEXT["current_task_dir"] is None:
        raise RuntimeError("RUNTIME_CONTEXT_NOT_SET")
    return _RUNTIME_CONTEXT["current_task_dir"]


class WriteGuardError(RuntimeError):
    pass


def set_runtime_context(
    task_dir: Path | str | None = None,
    task_slug: str | None = None,
    task_type: str | None = None,
    exemption_paths: list[str] | None = None,
) -> None:
    """由 bootstrap / finish_gate 在启动时注入运行时上下文。"""
    if task_dir is not None:
        _RUNTIME_CONTEXT["current_task_dir"] = Path(task_dir).resolve()
    if task_slug is not None:
        _RUNTIME_CONTEXT["current_task_slug"] = task_slug
    if task_type is not None:
        _RUNTIME_CONTEXT["task_type"] = task_type
    if exemption_paths is not None:
        _RUNTIME_CONTEXT["write_exemption_paths"] = [
            Path(p).resolve() for p in exemption_paths
        ]


def reset_runtime_context() -> None:
    """清空运行时上下文（smoke test 隔离用）。"""
    _RUNTIME_CONTEXT["current_task_dir"] = None
    _RUNTIME_CONTEXT["current_task_slug"] = None
    _RUNTIME_CONTEXT["task_type"] = None
    _RUNTIME_CONTEXT["write_exemption_paths"] = []


def get_runtime_context() -> dict:
    """返回运行时上下文的只读快照。"""
    return dict(_RUNTIME_CONTEXT)


def _path_matches_pattern(p: Path, pattern: str) -> bool:
    p = p.resolve()
    task_dir = _RUNTIME_CONTEXT["current_task_dir"]
    task_slug = _RUNTIME_CONTEXT["current_task_slug"]
    pat = pattern
    if task_dir is not None:
        pat = pat.replace("<CURRENT_TASK_DIR>", str(task_dir))
    if task_slug is not None:
        pat = pat.replace("<CURRENT_TASK_SLUG>", str(task_slug))
    if "<CURRENT_TASK_DIR>" in pat or "<CURRENT_TASK_SLUG>" in pat:
        return False
    if not pat.startswith(str(ROOT)):
        pat = str((ROOT / pat).resolve())
    return fnmatch.fnmatch(str(p), pat)


def _is_write_allowed(p: Path) -> tuple[bool, str]:
    p = Path(p).resolve()

    # 永久禁止优先级最高
    for pat in PERMANENT_WRITE_FORBIDDEN:
        if _path_matches_pattern(p, pat):
            return False, f"PERMANENT_FORBIDDEN: {pat}"

    # 受保护经验包
    for pat in PROTECTED_MEMORY_WRITE_PATTERNS:
        if _path_matches_pattern(p, pat):
            task_type = _RUNTIME_CONTEXT.get("task_type")
            if task_type not in MEMORY_WRITE_ALLOWED_TASK_TYPES:
                return False, f"PROTECTED_MEMORY_BLOCKED_FOR_TASK_TYPE={task_type}"
            for allowed in _RUNTIME_CONTEXT["write_exemption_paths"]:
                try:
                    allowed_p = Path(allowed).resolve()
                    p.relative_to(allowed_p.parent if allowed_p.is_file() else allowed_p)
                    return True, f"PROTECTED_MEMORY_EXEMPTION_GRANTED: {allowed}"
                except (ValueError, TypeError):
                    continue
            return False, "PROTECTED_MEMORY_REQUIRES_EXPLICIT_EXEMPTION"

    # 默认白名单
    for pat in DEFAULT_WRITE_WHITELIST_PATTERNS:
        if _path_matches_pattern(p, pat):
            return True, f"DEFAULT_WHITELIST: {pat}"

    # 豁免名单
    for allowed in _RUNTIME_CONTEXT["write_exemption_paths"]:
        try:
            allowed_p = Path(allowed).resolve()
            p.relative_to(allowed_p.parent if allowed_p.is_file() else allowed_p)
            return True, f"EXEMPTION_GRANTED: {allowed}"
        except (ValueError, TypeError):
            continue

    return False, "NOT_IN_ANY_WHITELIST"


_SECRET_LABEL_PATTERNS = [
    re.compile(r"(?i)\bpassword\s*[:=]\s*[^\s<>{}]{6,}"),
    re.compile(r"(?i)\bpasswd\s*[:=]\s*[^\s<>{}]{6,}"),
    re.compile(r"(?i)\bpwd\s*[:=]\s*[^\s<>{}]{6,}"),
    re.compile(r"(?i)\btoken\s*[:=]\s*[^\s<>{}]{12,}"),
    re.compile(r"(?i)\bapi_key\s*[:=]\s*[^\s<>{}]{12,}"),
    re.compile(r"(?i)\bapikey\s*[:=]\s*[^\s<>{}]{12,}"),
    re.compile(r"(?i)\bsecret\s*[:=]\s*[^\s<>{}]{12,}"),
    re.compile(r"账号：\s*[^\s<>{}]{4,}"),
    re.compile(r"密码：\s*[^\s<>{}]{6,}"),
    re.compile(r"token：\s*[^\s<>{}]{12,}"),
    re.compile(r"api_key：\s*[^\s<>{}]{12,}"),
]


def _looks_like_secret_plaintext(content: str) -> bool:
    if not isinstance(content, str):
        return False
    scan = content
    for marker in [
        "<REDACTED>",
        "secret_ref=",
        "secret_file_path=",
        "secret_value_printed=False",
        "secret_value_logged=False",
        "secret_value_written_to_report=False",
        "secret_value_written_to_memory=False",
        "secret_value_written_to_sqlite=False",
    ]:
        scan = scan.replace(marker, "")
    # 去掉行内代码反引号，防止文档示例误触发
    scan = scan.replace("`", "")
    for pat in _SECRET_LABEL_PATTERNS:
        if pat.search(scan):
            return True
    return False


def guarded_write_path(p: Path, content, mode: str = "text") -> None:
    """所有写入必须经过此函数。mode='binary' 用 bytes。"""
    p = Path(p)
    allowed, reason = _is_write_allowed(p)
    if not allowed:
        raise WriteGuardError(
            f"WRITE BLOCKED: {p}\n"
            f"  reason: {reason}\n"
            f"  runtime_context: {get_runtime_context()}\n"
            f"  hint: 基础设施任务需在 preflight.infrastructure_write_exemption 显式声明"
        )
    if mode != "binary" and isinstance(content, str):
        if _looks_like_secret_plaintext(content):
            raise WriteGuardError(
                f"WRITE BLOCKED: {p}\n"
                f"  reason: SECRET_PLAINTEXT_WRITE_BLOCKED\n"
                f"  hint: 密钥/账号密码允许受控读取，但明文不得写入报告、经验卡等"
            )
    p.parent.mkdir(parents=True, exist_ok=True)
    if mode == "binary":
        p.write_bytes(content)
    else:
        p.write_text(content, encoding="utf-8", newline="\n")


def write_text(p: Path, s: str) -> None:
    """guarded_write_path 的轻量包装，向后兼容。"""
    guarded_write_path(p, s, mode="text")
