"""
JQData 下载工具基座 - 可复用模块
供所有 JQData 下载任务使用。

使用方法：
    from 脚本.jq_download_base import (
        auth, quota_left, subproc_get_price,
        save_parquet, load_skip_stocks, save_skip_stock
    )

线程安全 + 子进程超时 kill + 额度缓存 + 断点续传
"""
import sys, os, time, json, subprocess, tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# ─── 全局配置 ───────────────────────────────────────────
CRED_FILE = Path("E:/BLACKBOX/配置/secrets/已验证/聚宽账号.txt")
DEFAULT_SCHEMA_VERSION = "1.0.0"
DOWNLOAD_BATCH_PY = Path(__file__).parent / "_download_batch.py"
SKIP_STOCKS_FILE = Path("E:/BLACKBOX/数据/原始只读/JQData_9999_official_raw/_quota_log/skip_stocks.json")

# ─── 认证 ───────────────────────────────────────────────
_CRED_U = None
_CRED_P = None

def auth(username=None, password=None):
    """JQData 认证（轻量，不查额度）"""
    global _CRED_U, _CRED_P
    if username and password:
        _CRED_U, _CRED_P = username, password
    elif _CRED_U and _CRED_P:
        pass  # 使用缓存
    else:
        # 从文件读取：支持「账号：/密码：」或两行明文（user\\npass）
        plain_lines = []
        for line in CRED_FILE.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if "：" in line or ":" in line:
                k, v = (line.split("：", 1) if "：" in line else line.split(":", 1))
                k, v = k.strip(), v.strip()
                if "账号" in k or "user" in k.lower():
                    _CRED_U = v
                if "密码" in k or "pass" in k.lower():
                    _CRED_P = v
            else:
                plain_lines.append(line)
        if (not _CRED_U or not _CRED_P) and len(plain_lines) >= 2:
            _CRED_U, _CRED_P = plain_lines[0], plain_lines[1]
    import jqdatasdk as jq
    if not _CRED_U or not _CRED_P:
        raise ValueError("JQ credentials missing in %s" % CRED_FILE)
    jq.auth(_CRED_U, _CRED_P)

def auth_and_show_quota():
    """认证并显示剩余额度"""
    auth()
    import jqdatasdk as jq
    q = jq.get_query_count()
    print(f"[auth] 总量={q['total']}, 剩余={q['spare']}", flush=True)
    return q

# ─── 额度检查 ───────────────────────────────────────────
_QUOTA_CACHE: dict = {"spare": None, "ts": 0}

def quota_left(force=False) -> Optional[int]:
    """
    返回剩余额度。
    - 5 秒内缓存
    - 连接失败时返回缓存值
    - 无缓存时返回 None（不限制）
    """
    now = time.time()
    if not force and _QUOTA_CACHE["spare"] is not None and now - _QUOTA_CACHE["ts"] < 5:
        return _QUOTA_CACHE["spare"]
    try:
        import jqdatasdk as jq
        q = jq.get_query_count()
        spare = q.get("spare", 0)
        _QUOTA_CACHE["spare"] = spare
        _QUOTA_CACHE["ts"] = now
        return spare
    except Exception:
        return _QUOTA_CACHE.get("spare")  # None = unknown, 不限制

def quota_ok() -> bool:
    """剩余额度是否足够（>0 或未知）"""
    q = quota_left()
    return q is None or q > 0

# ─── 子进程下载引擎 ─────────────────────────────────────
def subproc_get_price(stocks: List[str], start_date: str, end_date: str,
                      frequency: str, timeout: int = 60,
                      extra_kwargs: Optional[dict] = None) -> Optional["pd.DataFrame"]:
    """
    带超时的 JQData get_price。
    启动独立子进程，超时后强制 kill（Windows 安全）。
    返回 DataFrame 或 None（超时/失败/空）。
    """
    import pandas as pd
    batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp = Path(tempfile.gettempdir()) / f"_jq_batch_{os.getpid()}_{int(time.time())}.parquet"
    cmd = [
        sys.executable, "-u", str(DOWNLOAD_BATCH_PY),
        json.dumps(stocks), start_date, end_date, frequency,
        str(tmp), batch_id, DEFAULT_SCHEMA_VERSION,
    ]
    if extra_kwargs:
        cmd.append(json.dumps(extra_kwargs))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        tmp.unlink(missing_ok=True)
        return None
    if proc.returncode != 0:
        tmp.unlink(missing_ok=True)
        return None
    if tmp.exists() and tmp.stat().st_size > 200:
        try:
            df = pd.read_parquet(tmp)
            tmp.unlink(missing_ok=True)
            return df
        except Exception:
            tmp.unlink(missing_ok=True)
            return None
    tmp.unlink(missing_ok=True)
    return None

def subproc_exec_python(script: str, timeout: int = 120) -> Optional[str]:
    """
    执行任意 Python 代码片段（子进程），返回 stdout。
    适用于 run_query、get_mtss 等非 get_price 调用。
    """
    try:
        r = subprocess.check_output([sys.executable, "-c", script], timeout=timeout)
        return r.decode('utf-8', errors='replace')
    except subprocess.TimeoutExpired:
        return None
    except subprocess.CalledProcessError:
        return None

# ─── 文件保存 ───────────────────────────────────────────
def save_parquet(df: "pd.DataFrame", out_path: Path, domain: str = "",
                 source_api: str = "", batch_id: str = "",
                 schema_version: str = DEFAULT_SCHEMA_VERSION):
    """保存 DataFrame 为 parquet，附带 JSON 元数据"""
    df.to_parquet(out_path, index=False)
    meta = {
        "file": out_path.name,
        "domain": domain,
        "source_api": source_api,
        "batch_id": batch_id or datetime.now().strftime("%Y%m%d_%H%M%S"),
        "schema_version": schema_version,
        "rows": len(df),
        "columns": list(df.columns),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    out_path.with_suffix(".json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

# ─── 股票列表加载 ───────────────────────────────────────
def load_securities(meta_root: Path = None) -> List[str]:
    """加载全部 A 股代码列表"""
    if meta_root is None:
        meta_root = Path("E:/BLACKBOX/数据/原始只读/JQData_9999_official_raw/P0_meta")
    import pandas as pd
    codes = []
    for sf in sorted(meta_root.glob("securities_stock__*.parquet")):
        codes.extend(pd.read_parquet(sf)["code"].dropna().unique().tolist())
    stocks = sorted(set(c.strip() for c in codes if c and isinstance(c, str)))
    return [s for s in stocks if s.endswith(("XSHE", "XSHG"))]

# ─── 跳过股票管理 ───────────────────────────────────────
def load_skip_stocks() -> set:
    if SKIP_STOCKS_FILE.exists():
        return set(json.loads(SKIP_STOCKS_FILE.read_text(encoding="utf-8")))
    return set()

def save_skip_stock(stock: str):
    skipped = load_skip_stocks()
    skipped.add(stock)
    SKIP_STOCKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SKIP_STOCKS_FILE.write_text(
        json.dumps(sorted(skipped), ensure_ascii=False, indent=2), encoding="utf-8")

# ─── 文件跳过（断点续传）──────────────────────────────────
def files_exist(out_dir: Path, pattern: str) -> bool:
    """检查目录下是否有匹配 glob pattern 的文件"""
    return len(list(out_dir.glob(pattern))) > 0

# ─── 当前时间戳 ─────────────────────────────────────────
def now_cn() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
