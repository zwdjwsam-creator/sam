# P7 HARD GUARD — inserted by JQ_P7_MINUTE_RELEASE_BLOCKER_REPAIR_R1
# Date: 2026-06-14T18:59:36+00:00
# This script is BLOCKED as a P7 minute download entry.
# Use: guard/jq_p7_minute_guarded_download_entry_r1.py ONLY
#
if __name__ != "__main__":
    raise SystemExit(0)
print("=" * 60)
print("BLOCKED: P7 MINUTE DIRECT ENTRY FORBIDDEN")
print("Use guarded entry: jq_p7_minute_guarded_download_entry_r1.py")
print("This old entrypoint has been blocked.")
print("=" * 60)
raise SystemExit(1)
# END P7 HARD GUARD

# P7 HARD GUARD — inserted by JQ_P7_MINUTE_RELEASE_BLOCKER_REPAIR_R1
# Date: 2026-06-14T18:59:14+00:00
# This script is BLOCKED as a P7 minute download entry.
# Use: guard/jq_p7_minute_guarded_download_entry_r1.py ONLY
#
if __name__ != "__main__":
    raise SystemExit(0)
print("=" * 60)
print("BLOCKED: P7 MINUTE DIRECT ENTRY FORBIDDEN")
print("Use guarded entry: jq_p7_minute_guarded_download_entry_r1.py")
print("This old entrypoint has been blocked.")
print("=" * 60)
raise SystemExit(1)
# END P7 HARD GUARD

"""
JQData 正式下载编排器 R1
===========================
完整的多阶段 JQData 下载编排器，带 checkpoint/resume/quota/manifest/quality gate 系统。

任务类型: DATA_INGESTION
Python: E:/BLACKBOX/.venv/Scripts/python.exe
JDK: jqdatasdk 1.9.8
"""

import sys
import os
import json
import hashlib
import re
import gzip
import time
import uuid
import traceback
from pathlib import Path
from datetime import datetime, timezone, date, timedelta
from typing import Any, Optional, Union

import pandas as pd
import numpy as np

# ─── 版本 ────────────────────────────────────────────────
SCRIPT_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"

# ─── 路径常量 ────────────────────────────────────────────
ROOT = Path(r"E:/BLACKBOX/数据/原始只读/JQData_9999_official_raw")
CRED_FILE = Path(r"E:/BLACKBOX/配置/secrets/已验证/聚宽账号.txt")

# ─── 日期范围 ────────────────────────────────────────────
START_DATE = "2014-01-01"
END_DATE = "2026-06-12"

# ─── 任务元数据 ──────────────────────────────────────────
TASK_NAME = "JQ_DATA_DOWNLOAD_EXECUTION_R1"
BATCH_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

# ─── 阶段目录定义 ────────────────────────────────────────
STAGE_DIRS = {
    "T0": "P0_meta",
    "T1": "P1_adjust_factor",
    "T2": "P2_stock_daily",
    "T3": "P3_finance_pit",
    "T4": "P4_index",
    "T5": "P5_attributes_events",
    "T6": "P6_factor_reference",
    "T7": "P7_stock_minute",
    "T8": "P8_etf_fund",
    "T9": "P9_derivative_aux",
}

# ─── 基础设施子目录 ──────────────────────────────────────
INFRA_DIRS = {
    "_probe": ROOT / "_probe",
    "_manifest": ROOT / "_manifest",
    "_checksum": ROOT / "_checksum",
    "_quota_log": ROOT / "_quota_log",
    "_checkpoint": ROOT / "_checkpoint",
    "_failed_fragment": ROOT / "_failed_fragment",
    "_quarantine": ROOT / "_quarantine",
}

# ─── 阶段执行顺序 ────────────────────────────────────────
T_STAGES = ["T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9"]

# ─── JQData 每日额度上限 ─────────────────────────────────
JQDATA_DAILY_QUOTA_LIMIT = 200_000_000  # JQ_P7_QUOTA_UNIT_FIX_R1: corrected from 150M  # 接近 JQData 9999 套餐上限

# ─── 重试配置 ────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY_BASE = 5  # seconds

# ─── 安全写入 - guarded_write_path() 等价实现 ────────────
# 不使用 _base.py 的 guarded_write_path 以避免跨模块依赖
# 自己实现轻量级写入守卫

DEFAULT_WRITE_WHITELIST_PATTERNS = [
    str(ROOT) + os.sep,
]

PERMANENT_WRITE_FORBIDDEN_PATTERNS = [
    ".env", ".token", ".key", "credentials", "secrets",
    "*password*", "*passwd*", "*pwd*", "*交易密码*",
    "*券商*交易*", "*qmt*trade*", "*order_bridge*",
]

SECRET_PLAINTEXT_PATTERNS = re.compile(
    r"(password\s*[=：:]\s*|账号\s*[：:]\s*|token\s*[=：:]\s*|"
    r"secret\s*[=：:]\s*|api[_-]?key\s*[=：:]\s*|"
    r"api_key\s*[=：:]\s*)",
    re.IGNORECASE,
)


def _path_is_allowed(file_path: Union[str, Path]) -> bool:
    """检查路径是否在白名单内"""
    p = str(Path(file_path).resolve())
    for pattern in PERMANENT_WRITE_FORBIDDEN_PATTERNS:
        if pattern in p:
            return False
    for allowed in DEFAULT_WRITE_WHITELIST_PATTERNS:
        if p.startswith(allowed):
            return True
    return False


def _looks_like_secret_plaintext(text: str) -> bool:
    """检测内容是否包含疑似密钥明文"""
    if SECRET_PLAINTEXT_PATTERNS.search(text):
        # 豁免含有安全标记的行
        exempt_markers = ["REDACTED", "secret_value_printed=False",
                          "***", "xxxx"]
        for marker in exempt_markers:
            if marker in text:
                return False
        return True
    return False


def write_json(path: Union[str, Path], data: Any, **kwargs) -> None:
    """安全写入 JSON 文件"""
    file_path = Path(path)
    if not _path_is_allowed(file_path):
        raise PermissionError(
            f"写入路径不在白名单内: {file_path}"
        )
    content = json.dumps(data, ensure_ascii=False, **kwargs)
    if _looks_like_secret_plaintext(content):
        raise PermissionError(
            f"检测到疑似密钥明文，禁止写入: {file_path}"
        )
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = file_path.with_suffix(file_path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(file_path)


def read_json(path: Union[str, Path]) -> Any:
    """安全读取 JSON 文件"""
    file_path = Path(path)
    if not file_path.exists():
        return None
    return json.loads(file_path.read_text(encoding="utf-8"))


# ─── 时间戳工具 ──────────────────────────────────────────


def now_iso() -> str:
    """返回 UTC ISO 时间戳"""
    return datetime.now(timezone.utc).isoformat()


def now_cn() -> str:
    """返回北京时间字符串"""
    return (datetime.now(timezone.utc) + timedelta(hours=8)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ─── 文件校验工具 ────────────────────────────────────────


def sha256_file(file_path: Union[str, Path]) -> str:
    """计算文件的 SHA256 校验值"""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ─── 数据保存工具 ────────────────────────────────────────


def save_parquet(df: pd.DataFrame, path: Union[str, Path]) -> int:
    """保存 DataFrame 到 parquet，返回行数"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(file_path, index=False, compression="snappy")
    return len(df)


def save_csv_gz(df: pd.DataFrame, path: Union[str, Path]) -> int:
    """保存 DataFrame 到 gzip csv（备用格式），返回行数"""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False, compression="gzip")
    return len(df)


# ─── 凭据解析 ────────────────────────────────────────────


def parse_cred() -> tuple[str, str]:
    """读取并解析聚宽账号凭据文件"""
    if not CRED_FILE.exists():
        raise FileNotFoundError(f"凭据文件不存在: {CRED_FILE}")
    lines = CRED_FILE.read_text(encoding="utf-8").strip().split("\n")
    username = None
    password = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("账号：") or line.startswith("账号:"):
            username = line.split("：")[-1].split(":")[-1].strip()
        elif line.startswith("密码：") or line.startswith("密码:"):
            password = line.split("：")[-1].split(":")[-1].strip()
    if not username or not password:
        raise ValueError(f"凭据文件格式错误，无法解析账号或密码: {CRED_FILE}")
    return username, password


def jq_auth() -> None:
    """认证 JQData，返回 auth 对象"""
    import jqdatasdk

    username, password = parse_cred()
    print(f"[{now_cn()}] 正在认证 JQData...")
    jqdatasdk.auth(username, password)
    # 验证认证是否成功
    try:
        info = jqdatasdk.get_query_count()
        print(f"[{now_cn()}] JQData 认证成功。今日已用额度: {info}")
    except Exception:
        print(f"[{now_cn()}] JQData 认证成功（额度查询不可用）")


# ─── Checkpoint 系统 ────────────────────────────────────

CHECKPOINT_FILE = INFRA_DIRS["_checkpoint"] / "latest_checkpoint.json"


def load_checkpoint() -> Optional[dict]:
    """读取最新 checkpoint"""
    data = read_json(CHECKPOINT_FILE)
    if data and data.get("task") == TASK_NAME:
        return data
    return None


def save_checkpoint(
    stage: str,
    domain: str,
    status: str,
    detail: Optional[dict] = None,
    completed_stages: Optional[list] = None,
    completed_partitions: Optional[list] = None,
    quota_used: int = 0,
    total_rows: int = 0,
    total_bytes: int = 0,
    stop_reason: Optional[str] = None,
    frequency: Optional[str] = None,
) -> dict:
    """保存 checkpoint"""
    cp = {
        "task": TASK_NAME,
        "batch_id": BATCH_ID,
        "current_T_stage": stage,
        "current_domain": domain,
        "current_frequency": frequency,
        "status": status,
        "completed_stages": completed_stages or [],
        "completed_partitions": completed_partitions or [],
        "quota_used_estimated": quota_used,
        "total_rows": total_rows,
        "total_bytes": total_bytes,
        "stop_reason": stop_reason,
        "updated_at": now_iso(),
    }
    if detail:
        cp["detail"] = detail

    INFRA_DIRS["_checkpoint"].mkdir(parents=True, exist_ok=True)
    write_json(CHECKPOINT_FILE, cp, indent=2)
    return cp


def get_resume_point() -> Optional[dict]:
    """获取断点续传位置"""
    cp = load_checkpoint()
    if cp is None:
        return None
    stage = cp.get("current_T_stage")
    domain = cp.get("current_domain")
    completed = cp.get("completed_stages", [])
    partitions = cp.get("completed_partitions", [])
    return {
        "stage": stage,
        "domain": domain,
        "completed_stages": completed,
        "completed_partitions": partitions,
        "quota_used": cp.get("quota_used_estimated", 0),
        "total_rows": cp.get("total_rows", 0),
        "total_bytes": cp.get("total_bytes", 0),
    }


# ─── Quota 跟踪系统 ─────────────────────────────────────


def log_quota(
    stage: str,
    domain: str,
    api: str,
    rows: int,
    byte_size: int,
    estimated_cost: int,
) -> None:
    """记录单次 API 调用的额度消耗"""
    record = {
        "batch_id": BATCH_ID,
        "timestamp": now_iso(),
        "T_stage": stage,
        "domain": domain,
        "jq_api": api,
        "rows": rows,
        "byte_size": byte_size,
        "estimated_quota_cost": estimated_cost,
    }
    daily_dir = INFRA_DIRS["_quota_log"] / datetime.now().strftime("%Y%m%d")
    daily_dir.mkdir(parents=True, exist_ok=True)
    log_file = daily_dir / f"quota_log_{BATCH_ID}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def daily_quota_summary() -> dict:
    """生成当日额度汇总"""
    daily_dir = INFRA_DIRS["_quota_log"] / datetime.now().strftime("%Y%m%d")
    if not daily_dir.exists():
        return {
            "date": datetime.now().strftime("%Y%m%d"),
            "total_requests": 0,
            "total_rows": 0,
            "total_bytes": 0,
            "estimated_quota_used": 0,
        }
    total_rows = 0
    total_bytes = 0
    total_quota = 0
    total_req = 0
    for log_file in daily_dir.glob("quota_log_*.jsonl"):
        for line in log_file.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            rec = json.loads(line)
            total_req += 1
            total_rows += rec.get("rows", 0)
            total_bytes += rec.get("byte_size", 0)
            total_quota += rec.get("estimated_quota_cost", 0)
    return {
        "date": datetime.now().strftime("%Y%m%d"),
        "total_requests": total_req,
        "total_rows": total_rows,
        "total_bytes": total_bytes,
        "estimated_quota_used": total_quota,
    }


def get_quota_remaining() -> int:
    """获取今日剩余额度"""
    summary = daily_quota_summary()
    used = summary["estimated_quota_used"]
    remaining = JQDATA_DAILY_QUOTA_LIMIT - used
    return max(0, remaining)


# ─── Manifest 系统 ──────────────────────────────────────


def write_sidecar(data_file: Union[str, Path], meta: dict) -> None:
    """为数据文件写入 sidecar JSON"""
    file_path = Path(data_file)
    sidecar_path = file_path.with_suffix(file_path.suffix + ".sidecar.json")
    write_json(sidecar_path, meta, indent=2)


def write_manifest_row(
    stage: str,
    domain: str,
    symbol: Optional[str],
    date_range: Optional[str],
    api: str,
    rows: int,
    byte_size: int,
    checksum: str,
    quota: int,
    frequency: Optional[str] = None,
    adj: str = "none_adj",
    extra: Optional[dict] = None,
) -> dict:
    """写入一条 manifest 记录并返回 manifest 字典"""
    key = f"{stage}/{domain}"
    manifest = {
        "task": TASK_NAME,
        "schema_version": SCHEMA_VERSION,
        "T_stage": stage,
        "domain": domain,
        "date_range": date_range,
        "symbol": symbol,
        "frequency": frequency,
        "adj": adj,
        "row_count": rows,
        "byte_size": byte_size,
        "download_ts": now_iso(),
        "jq_api": api,
        "quota_consumed_estimated": quota,
        "batch_id": BATCH_ID,
        "checksum_sha256": checksum,
        "checkpoint_key": key,
    }
    if extra:
        manifest.update(extra)

    INFRA_DIRS["_manifest"].mkdir(parents=True, exist_ok=True)
    manifest_file = (
        INFRA_DIRS["_manifest"]
        / f"manifest_{stage}_{domain}_{BATCH_ID}.json"
    )
    write_json(manifest_file, manifest, indent=2)
    return manifest


# ─── Probe 系统 ─────────────────────────────────────────


def probe_api(api_name: str, test_params: Optional[dict] = None) -> dict:
    """安全探测单个 API 的可用性"""
    import jqdatasdk

    result = {
        "api_name": api_name,
        "api_supported": False,
        "permission_ok": False,
        "sample_ok": False,
        "fields_available": [],
        "estimated_rows": 0,
        "download_allowed": False,
        "notes": [],
    }
    try:
        # 检查 API 是否存在
        api_func = getattr(jqdatasdk, api_name, None)
        if api_func is None:
            result["notes"].append(f"API {api_name} 不存在")
            return result
        result["api_supported"] = True

        # 尝试调用
        if test_params:
            df = api_func(**test_params)
        else:
            df = api_func()

        if df is None:
            result["notes"].append("API 返回 None")
            return result

        if isinstance(df, pd.DataFrame):
            result["sample_ok"] = True
            result["fields_available"] = list(df.columns)
            result["estimated_rows"] = len(df)
            result["permission_ok"] = True
            result["download_allowed"] = True
        elif hasattr(df, '__len__') and len(df) > 0:
            # 支持 list/ndarray 返回值（如 get_trade_days）
            result["sample_ok"] = True
            result["fields_available"] = [f"col_{i}" for i in range(min(5, len(df)))]
            result["estimated_rows"] = len(df)
            result["permission_ok"] = True
            result["download_allowed"] = True
        else:
            result["notes"].append(f"API 返回类型非 DataFrame: {type(df)}")

    except Exception as e:
        err = str(e)
        if "权限" in err or "permission" in err.lower() or "not allowed" in err.lower():
            result["notes"].append(f"权限不足: {err}")
        elif "额度" in err or "quota" in err.lower():
            result["notes"].append(f"额度受限: {err}")
        else:
            result["notes"].append(f"调用异常: {err}")

    return result


def record_probe_result(
    stage: str,
    domain: str,
    api: str,
    supported: bool,
    permission_ok: bool,
    fields: list,
    notes: list,
) -> dict:
    """记录 probe 结果到文件"""
    probe_dir = INFRA_DIRS["_probe"] / stage
    probe_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "T_stage": stage,
        "domain": domain,
        "api": api,
        "api_supported": supported,
        "permission_ok": permission_ok,
        "sample_ok": supported and permission_ok,
        "fields_available": fields,
        "estimated_rows": 0 if not fields else 1,
        "download_allowed": supported and permission_ok,
        "notes": "; ".join(notes) if notes else "",
        "probe_ts": now_iso(),
    }
    probe_file = probe_dir / f"probe_{stage}_{domain}_{api}_{BATCH_ID}.json"
    write_json(probe_file, record, indent=2)
    return record


def save_probe_matrix(stage: str) -> None:
    """汇总当前阶段的 probe 结果到 CSV matrix"""
    probe_dir = INFRA_DIRS["_probe"] / stage
    if not probe_dir.exists():
        return
    records = []
    for f in sorted(probe_dir.glob("probe_*.json")):
        rec = read_json(f)
        if rec:
            records.append(rec)
    if not records:
        return

    df = pd.DataFrame(records)
    matrix_file = (
        INFRA_DIRS["_probe"] / f"probe_matrix_{stage}_{BATCH_ID}.csv"
    )
    df.to_csv(matrix_file, index=False, encoding="utf-8-sig")
    print(f"[{now_cn()}] Probe matrix 已保存: {matrix_file}")


# ─── 质量闸 ─────────────────────────────────────────────


def check_checksum(file_path: Union[str, Path], expected_sha256: str) -> bool:
    """校验文件 SHA256"""
    actual = sha256_file(file_path)
    ok = actual == expected_sha256
    if not ok:
        print(
            f"[{now_cn()}] [质量闸] SHA256 不匹配: {file_path.name}\n"
            f"  期望: {expected_sha256}\n"
            f"  实际: {actual}"
        )
    return ok


def check_row_count(df: pd.DataFrame, expected_min: int) -> bool:
    """检查 DataFrame 行数是否达到最低预期"""
    ok = len(df) >= expected_min
    if not ok:
        print(
            f"[{now_cn()}] [质量闸] 行数不足: 期望 >= {expected_min}, "
            f"实际 {len(df)}"
        )
    return ok


def check_schema(df: pd.DataFrame, expected_columns: list) -> tuple[bool, list]:
    """检查 DataFrame 是否包含所需字段，返回 (ok, missing_columns)"""
    missing = [c for c in expected_columns if c not in df.columns]
    ok = len(missing) == 0
    if not ok:
        print(
            f"[{now_cn()}] [质量闸] 缺少字段: {missing}"
        )
    return ok, missing


def check_pit_visibility(df: pd.DataFrame, pub_date_col: str) -> int:
    """检查 PIT 数据的可见性（有多少行 pub_date < 当前日期）"""
    if pub_date_col not in df.columns:
        return 0
    now = pd.Timestamp.now(tz="Asia/Shanghai")
    visible = df[df[pub_date_col] <= now].shape[0]
    total = df.shape[0]
    print(
        f"[{now_cn()}] [质量闸] PIT 可见性: {visible}/{total} 行可见 "
        f"({visible / max(total, 1) * 100:.1f}%)"
    )
    return visible


def check_duplicate_partition(file_path: Union[str, Path], domain_key: str) -> bool:
    """检查是否已存在相同 partition 的数据文件"""
    # 检查 manifest 中是否已有相同 domain_key 的记录
    manifest_dir = INFRA_DIRS["_manifest"]
    if not manifest_dir.exists():
        return False
    for mf in manifest_dir.glob(f"manifest_*_{domain_key}_*.json"):
        return True
    return False


# ─── 失败记录 ──────────────────────────────────────────


def record_failure(
    stage: str,
    domain: str,
    api: str,
    error: str,
    detail: Optional[dict] = None,
) -> None:
    """记录失败信息到 _failed_fragment"""
    failed_dir = INFRA_DIRS["_failed_fragment"] / stage
    failed_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "batch_id": BATCH_ID,
        "timestamp": now_iso(),
        "T_stage": stage,
        "domain": domain,
        "jq_api": api,
        "error": error,
        "detail": detail or {},
    }
    failed_file = (
        failed_dir
        / f"failed_{stage}_{domain}_{api}_{BATCH_ID}_{uuid.uuid4().hex[:8]}.json"
    )
    write_json(failed_file, record, indent=2)
    print(f"[{now_cn()}] [失败] 已记录到: {failed_file.name}")


# ─── 重试装饰器 ─────────────────────────────────────────


def with_retry(func, *args, max_retries=MAX_RETRIES, **kwargs):
    """带重试的函数调用封装"""
    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = RETRY_DELAY_BASE * (2 ** (attempt - 1))
                print(
                    f"[{now_cn()}] 重试 {attempt}/{max_retries} "
                    f"({func.__name__}): {e}，{delay}s 后重试..."
                )
                time.sleep(delay)
            else:
                print(
                    f"[{now_cn()}] 重试 {attempt}/{max_retries} 失败: {e}"
                )
    raise last_exception


# ─── 文件名生成器 ───────────────────────────────────────


def make_filename(
    stage: str,
    domain: str,
    date_range: Optional[str] = None,
    symbol: Optional[str] = None,
    adj: str = "none_adj",
    version: str = "v1",
    ext: str = "parquet",
) -> str:
    """生成标准化的数据文件名"""
    parts = [domain]
    if symbol:
        parts.append(str(symbol))
    if date_range:
        parts.append(str(date_range))
    parts.append(adj)
    parts.append(version)
    parts.append(BATCH_ID)
    return "__".join(parts) + f".{ext}"


def stage_dir(stage: str) -> Path:
    """获取阶段的物理目录"""
    dirname = STAGE_DIRS.get(stage)
    if not dirname:
        raise ValueError(f"未知阶段: {stage}")
    return ROOT / dirname


# ══════════════════════════════════════════════════════════
# T1 下载：复权因子
# ══════════════════════════════════════════════════════════


def download_adjust_factor(
    stage: str,
    sec_type: str,
    domain: str,
    resume_partitions: list,
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """T1: 下载复权因子 (get_price fields=['factor'])"""
    import jqdatasdk

    print(f"[{now_cn()}] [T1] 下载复权因子: {sec_type}")

    # ─── Probe ────────────────────────────────────────────
    probe_domain = f"{domain}_probe"
    probe_cp_key = f"{stage}/{probe_domain}"
    if probe_cp_key not in resume_partitions:
        meta_dir = stage_dir("T0")
        sec_files = list(meta_dir.glob(f"securities_{sec_type}__*.parquet"))
        probe_codes = []
        for sf in sec_files:
            df_meta = pd.read_parquet(sf)
            codes = df_meta["code"].dropna().unique().tolist()
            if len(codes) >= 5:
                probe_codes = codes[:5]
                break
        if not probe_codes:
            record_failure(stage, domain, "get_price",
                           f"无法从 P0_meta 读取 {sec_type} 列表用于 probe")
            return domain, quota_used, total_rows, total_bytes

        import datetime as dt
        probe_end = dt.date(2014, 1, 15)
        probe_start = dt.date(2014, 1, 6)
        try:
            probe_df = with_retry(
                jqdatasdk.get_price,
                security=probe_codes,
                start_date=probe_start,
                end_date=probe_end,
                fields=["factor"],
            )
        except Exception as e:
            record_failure(stage, domain, "get_price", str(e),
                           {"sec_type": sec_type, "codes_sample": probe_codes[:3]})
            return domain, quota_used, total_rows, total_bytes

        if probe_df is None or probe_df.empty:
            record_failure(stage, domain, "get_price",
                           "Probe 返回空数据", {"sec_type": sec_type})
            return domain, quota_used, total_rows, total_bytes

        probe_ok = "factor" in probe_df.columns if hasattr(probe_df, "columns") else False
        if not probe_ok:
            record_failure(stage, domain, "get_price",
                           "Probe 未返回 factor 字段",
                           {"columns": list(probe_df.columns) if hasattr(probe_df, "columns") else None})
            return domain, quota_used, total_rows, total_bytes

        record_probe_result(stage, probe_domain, "get_price",
                            True, True, ["factor"], [])
        resume_partitions.append(probe_cp_key)

    # ─── 读取 securities 列表 ─────────────────────────────
    meta_dir = stage_dir("T0")
    sec_files = sorted(meta_dir.glob(f"securities_{sec_type}__*.parquet"))
    all_codes = []
    for sf in sec_files:
        df_meta = pd.read_parquet(sf)
        codes = df_meta["code"].dropna().unique().tolist()
        all_codes.extend(codes)
    all_codes = sorted(set(all_codes))
    print(f"[{now_cn()}] [T1] {sec_type} 总数: {len(all_codes)}")

    if not all_codes:
        record_failure(stage, domain, "get_price",
                       f"P0_meta 中未找到 {sec_type} 代码")
        return domain, quota_used, total_rows, total_bytes

    # ─── 分批（500） + 按年分片 ────────────────────────────
    batch_size = 500
    batches = [all_codes[i:i + batch_size] for i in range(0, len(all_codes), batch_size)]
    print(f"[{now_cn()}] [T1] {sec_type} 共 {len(batches)} 批")

    years = list(range(2014, 2027))

    for batch_idx, codes_batch in enumerate(batches):
        for year in years:
            cp_key = f"{stage}/{domain}/{year}/batch_{batch_idx}"
            if cp_key in resume_partitions:
                print(f"[{now_cn()}] [SKIP] {cp_key} 已完成，跳过")
                continue

            if get_quota_remaining() <= 0:
                print(f"[{now_cn()}] [额度耗尽] 停止 T1 {sec_type} 下载")
                save_checkpoint(stage, domain, "STOPPED",
                                stop_reason="QUOTA_EXHAUSTED",
                                completed_partitions=resume_partitions,
                                quota_used=quota_used,
                                total_rows=total_rows,
                                total_bytes=total_bytes)
                return domain, quota_used, total_rows, total_bytes

            start_d = f"{year}-01-01"
            end_d = f"{year}-12-31"

            print(f"[{now_cn()}] [T1] {sec_type} 批次 {batch_idx}/{len(batches)}, "
                  f"年份 {year}: {len(codes_batch)} 只, {start_d} ~ {end_d}")

            try:
                df_raw = with_retry(
                    jqdatasdk.get_price,
                    security=codes_batch,
                    start_date=start_d,
                    end_date=end_d,
                    fields=["factor"],
                )
            except Exception as e:
                record_failure(stage, domain, "get_price", str(e),
                               {"sec_type": sec_type, "batch": batch_idx,
                                "year": year, "codes_sample": codes_batch[:3]})
                continue

            if df_raw is None or df_raw.empty:
                print(f"[{now_cn()}] [T1] {sec_type} 批次 {batch_idx} 年份 {year} 返回空")
                resume_partitions.append(cp_key)
                continue

            # 扁平 DataFrame (time, code, factor 列)
            # get_price 返回长格式：time/code 是列不是索引
            df_flat = df_raw.copy()
            if "time" in df_flat.columns:
                df_flat = df_flat.rename(columns={"time": "date"})
            if "code" not in df_flat.columns:
                # 如果是多级索引格式兜底
                df_flat = df_raw.reset_index()
                if "security" in df_flat.columns:
                    df_flat = df_flat.rename(columns={"security": "code"})
            df_flat["sec_type"] = sec_type
            if "factor" in df_flat.columns:
                df_flat = df_flat.dropna(subset=["factor"])

            if df_flat.empty:
                print(f"[{now_cn()}] [T1] {sec_type} 批次 {batch_idx} 年份 {year} 全空")
                resume_partitions.append(cp_key)
                continue

            # ─── 质量闸 ────────────────────────────────────
            if not check_row_count(df_flat, 1):
                print(f"[{now_cn()}] [质量闸警告] {sec_type} 批次 {batch_idx} "
                      f"年份 {year} 行数异常: {len(df_flat)}")

            date_range_str = f"{year}"
            fname = make_filename(stage, domain, date_range=date_range_str,
                                  symbol=f"batch_{batch_idx}")
            out_path = stage_dir(stage) / fname

            rows = save_parquet(df_flat, out_path)
            byte_size = out_path.stat().st_size
            checksum = sha256_file(out_path)

            sidecar = {
                "task": TASK_NAME,
                "T_stage": stage,
                "domain": domain,
                "date_range": date_range_str,
                "frequency": "daily",
                "adj": "none_adj",
                "sec_type": sec_type,
                "batch_idx": batch_idx,
                "codes_in_batch": len(codes_batch),
                "schema_version": SCHEMA_VERSION,
                "row_count": rows,
                "byte_size": byte_size,
                "download_ts": now_iso(),
                "jq_api": "get_price(fields=['factor'])",
                "quota_consumed_estimated": 1,
                "batch_id": BATCH_ID,
                "checksum_sha256": checksum,
                "checkpoint_key": cp_key,
            }
            write_sidecar(out_path, sidecar)

            write_manifest_row(
                stage=stage, domain=domain,
                symbol=f"batch_{batch_idx}",
                date_range=date_range_str,
                api="get_price(fields=['factor'])",
                rows=rows, byte_size=byte_size,
                checksum=checksum, quota=1,
                extra={"sec_type": sec_type, "year": year,
                       "batch_idx": batch_idx,
                       "codes_in_batch": len(codes_batch)},
            )

            log_quota(stage, domain, "get_price(fields=['factor'])",
                      rows, byte_size, estimated_cost=1)

            quota_used += 1
            total_rows += rows
            total_bytes += byte_size

            print(f"[{now_cn()}] [T1] {sec_type} 批次 {batch_idx} 年份 {year}: "
                  f"{rows} 行, {byte_size / 1024:.1f} KB")

            resume_partitions.append(cp_key)
            save_checkpoint(stage, domain, "RUNNING",
                            completed_partitions=resume_partitions,
                            quota_used=quota_used, total_rows=total_rows,
                            total_bytes=total_bytes)

    return domain, quota_used, total_rows, total_bytes


def download_stock_daily(
    stage: str,
    year: int,
    resume_partitions: list,
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """T2: 下载股票日线（不复权）"""
    import jqdatasdk

    domain = "stock_daily"
    print(f"[{now_cn()}] [T2] 下载股票日线: {year}")

    # ─── Probe ────────────────────────────────────────────
    probe_domain = f"{domain}_probe_{year}"
    probe_cp_key = f"{stage}/{probe_domain}"
    if probe_cp_key not in resume_partitions:
        meta_dir = stage_dir("T0")
        sec_files = list(meta_dir.glob("securities_stock__*.parquet"))
        probe_codes = []
        for sf in sec_files:
            df_meta = pd.read_parquet(sf)
            codes = df_meta["code"].dropna().unique().tolist()
            if len(codes) >= 5:
                probe_codes = codes[:5]
                break
        if not probe_codes:
            record_failure(stage, domain, "get_price",
                           "无法从 P0_meta 读取 stock 列表用于 probe")
            return domain, quota_used, total_rows, total_bytes

        probe_start = f"{year}-01-01"
        probe_end = f"{year}-01-15"
        try:
            probe_df = with_retry(
                jqdatasdk.get_price,
                security=probe_codes,
                start_date=probe_start,
                end_date=probe_end,
                frequency="daily",
                fields=["open", "close", "high", "low", "volume", "money",
                        "avg", "pre_close", "high_limit", "low_limit",
                        "paused", "factor"],
                skip_paused=False,
            )
        except Exception as e:
            record_failure(stage, domain, "get_price", str(e),
                           {"year": year, "codes_sample": probe_codes[:3]})
            return domain, quota_used, total_rows, total_bytes

        if probe_df is None or probe_df.empty:
            record_failure(stage, domain, "get_price",
                           "Probe 返回空数据", {"year": year})
            return domain, quota_used, total_rows, total_bytes

        record_probe_result(stage, probe_domain, "get_price",
                            True, True,
                            list(probe_df.columns) if hasattr(probe_df, "columns") else [],
                            [])
        resume_partitions.append(probe_cp_key)

    # ─── 读取全 stocks 列表 ───────────────────────────────
    meta_dir = stage_dir("T0")
    sec_files = sorted(meta_dir.glob("securities_stock__*.parquet"))
    all_codes = []
    for sf in sec_files:
        df_meta = pd.read_parquet(sf)
        codes = df_meta["code"].dropna().unique().tolist()
        all_codes.extend(codes)
    all_codes = sorted(set(all_codes))
    print(f"[{now_cn()}] [T2] 股票总数: {len(all_codes)}")

    if not all_codes:
        record_failure(stage, domain, "get_price",
                       "P0_meta 中未找到股票代码")
        return domain, quota_used, total_rows, total_bytes

    # ─── 分批（500） ──────────────────────────────────────
    batch_size = 500
    batches = [all_codes[i:i + batch_size] for i in range(0, len(all_codes), batch_size)]

    start_d = f"{year}-01-01"
    end_d = f"{year}-12-31"

    for batch_idx, codes_batch in enumerate(batches):
        cp_key = f"{stage}/{domain}/{year}/batch_{batch_idx}"
        if cp_key in resume_partitions:
            print(f"[{now_cn()}] [SKIP] {cp_key} 已完成，跳过")
            continue

        if get_quota_remaining() <= 0:
            print(f"[{now_cn()}] [额度耗尽] 停止 T2 日线下载")
            save_checkpoint(stage, domain, "STOPPED",
                            stop_reason="QUOTA_EXHAUSTED",
                            completed_partitions=resume_partitions,
                            quota_used=quota_used,
                            total_rows=total_rows,
                            total_bytes=total_bytes)
            return domain, quota_used, total_rows, total_bytes

        print(f"[{now_cn()}] [T2] 批次 {batch_idx}/{len(batches)}, "
              f"年份 {year}: {len(codes_batch)} 只")

        try:
            df_raw = with_retry(
                jqdatasdk.get_price,
                security=codes_batch,
                start_date=start_d,
                end_date=end_d,
                frequency="daily",
                fields=["open", "close", "high", "low", "volume", "money",
                        "avg", "pre_close", "high_limit", "low_limit",
                        "paused", "factor"],
                skip_paused=False,
            )
        except Exception as e:
            record_failure(stage, domain, "get_price", str(e),
                           {"year": year, "batch": batch_idx,
                            "codes_sample": codes_batch[:3]})
            continue

        if df_raw is None or df_raw.empty:
            print(f"[{now_cn()}] [T2] 批次 {batch_idx} 年份 {year} 返回空")
            resume_partitions.append(cp_key)
            continue

        # 扁平 DataFrame (time, code, ... 列)
        # get_price 返回长格式：time/code 是列不是索引
        df_flat = df_raw.copy()
        if "time" in df_flat.columns:
            df_flat = df_flat.rename(columns={"time": "date"})
        if "code" not in df_flat.columns:
            # 如果是多级索引格式兜底
            df_flat = df_raw.reset_index()
            if "security" in df_flat.columns:
                df_flat = df_flat.rename(columns={"security": "code"})

        # ─── 质量闸 ────────────────────────────────────────
        if not check_row_count(df_flat, 1):
            print(f"[{now_cn()}] [质量闸警告] T2 批次 {batch_idx} 年份 {year} "
                  f"行数异常: {len(df_flat)}")

        date_range_str = f"{year}"
        fname = make_filename(stage, domain, date_range=date_range_str,
                              symbol=f"batch_{batch_idx}")
        out_path = stage_dir(stage) / fname

        rows = save_parquet(df_flat, out_path)
        byte_size = out_path.stat().st_size
        checksum = sha256_file(out_path)

        sidecar = {
            "task": TASK_NAME,
            "T_stage": stage,
            "domain": domain,
            "date_range": date_range_str,
            "frequency": "daily",
            "adj": "none_adj",
            "batch_idx": batch_idx,
            "codes_in_batch": len(codes_batch),
            "schema_version": SCHEMA_VERSION,
            "row_count": rows,
            "byte_size": byte_size,
            "download_ts": now_iso(),
            "quota_consumed_estimated": 1,
            "jq_api": "get_price(frequency='daily')",
            "batch_id": BATCH_ID,
            "checksum_sha256": checksum,
            "checkpoint_key": cp_key,
        }
        write_sidecar(out_path, sidecar)

        write_manifest_row(
            stage=stage, domain=domain,
            symbol=f"batch_{batch_idx}",
            date_range=date_range_str,
            api="get_price(frequency='daily')",
            rows=rows, byte_size=byte_size,
            checksum=checksum, quota=1,
            extra={"year": year, "batch_idx": batch_idx,
                   "codes_in_batch": len(codes_batch)},
        )

        log_quota(stage, domain, "get_price(frequency='daily')",
                  rows, byte_size, estimated_cost=1)

        quota_used += 1
        total_rows += rows
        total_bytes += byte_size

        print(f"[{now_cn()}] [T2] 批次 {batch_idx} 年份 {year}: "
              f"{rows} 行, {byte_size / 1024:.1f} KB")

        resume_partitions.append(cp_key)
        save_checkpoint(stage, domain, "RUNNING",
                        completed_partitions=resume_partitions,
                        quota_used=quota_used, total_rows=total_rows,
                        total_bytes=total_bytes)

    return domain, quota_used, total_rows, total_bytes


# ══════════════════════════════════════════════════════════
# T0 下载：元数据骨架
# ══════════════════════════════════════════════════════════


def download_trade_calendar(
    stage: str, resume_partitions: list, quota_used: int, total_rows: int, total_bytes: int
) -> tuple[str, int, int, int]:
    """T0: 下载交易日历"""
    import jqdatasdk

    domain = "trade_calendar"
    cp_key = f"{stage}/{domain}"
    if cp_key in resume_partitions:
        print(f"[{now_cn()}] [SKIP] {cp_key} 已完成，跳过")
        return domain, quota_used, total_rows, total_bytes

    print(f"[{now_cn()}] [T0] 下载交易日历...")

    probe = probe_api("get_trade_days", {"start_date": START_DATE, "end_date": END_DATE})
    record_probe_result(stage, domain, "get_trade_days",
                        probe["api_supported"], probe["permission_ok"],
                        probe["fields_available"], probe["notes"])
    if not probe["download_allowed"]:
        record_failure(stage, domain, "get_trade_days",
                       "Probe 失败，不允许下载", probe)
        return domain, quota_used, total_rows, total_bytes

    try:
        trade_days = with_retry(
            jqdatasdk.get_trade_days,
            start_date=START_DATE,
            end_date=END_DATE,
        )
    except Exception as e:
        record_failure(stage, domain, "get_trade_days", str(e),
                       {"start": START_DATE, "end": END_DATE})
        save_checkpoint(stage, domain, "STOPPED",
                        stop_reason=f"get_trade_days 失败: {e}",
                        quota_used=quota_used, total_rows=total_rows,
                        total_bytes=total_bytes)
        return domain, quota_used, total_rows, total_bytes

    if trade_days is None or len(trade_days) == 0:
        record_failure(stage, domain, "get_trade_days",
                       "返回空数据")
        return domain, quota_used, total_rows, total_bytes

    # 构造 DataFrame
    dates = pd.Series(trade_days, name="calendar_date")
    df = pd.DataFrame({"calendar_date": dates})
    df["is_trading_day"] = True
    df["session_label"] = "CN_A"
    df = df.sort_values("calendar_date").reset_index(drop=True)

    # 质量闸
    if not check_row_count(df, 1):
        print(f"[{now_cn()}] [质量闸警告] 交易日历行数异常: {len(df)}")

    date_range_str = f"{START_DATE}_{END_DATE}"
    fname = make_filename(stage, domain, date_range=date_range_str)
    out_path = stage_dir(stage) / fname

    rows = save_parquet(df, out_path)
    byte_size = out_path.stat().st_size
    checksum = sha256_file(out_path)

    # Sidecar
    sidecar = {
        "task": TASK_NAME,
        "T_stage": stage,
        "domain": domain,
        "date_range": date_range_str,
        "frequency": None,
        "adj": "none_adj",
        "schema_version": SCHEMA_VERSION,
        "row_count": rows,
        "byte_size": byte_size,
        "download_ts": now_iso(),
        "jq_api": "get_trade_days",
        "quota_consumed_estimated": rows,
        "batch_id": BATCH_ID,
        "checksum_sha256": checksum,
        "checkpoint_key": cp_key,
    }
    write_sidecar(out_path, sidecar)

    # Manifest
    write_manifest_row(
        stage=stage, domain=domain,
        symbol=None, date_range=date_range_str,
        api="get_trade_days", rows=rows,
        byte_size=byte_size, checksum=checksum, quota=rows,
    )

    # Quota
    log_quota(stage, domain, "get_trade_days", rows, byte_size, rows)

    quota_used += rows
    total_rows += rows
    total_bytes += byte_size

    print(
        f"[{now_cn()}] [T0] 交易日历完成: {rows} 行, "
        f"{byte_size / 1024:.1f} KB"
    )

    save_checkpoint(stage, domain, "RUNNING",
                    completed_partitions=resume_partitions + [cp_key],
                    quota_used=quota_used, total_rows=total_rows,
                    total_bytes=total_bytes)
    return domain, quota_used, total_rows, total_bytes


def download_securities(
    stage: str,
    sec_type: str,
    domain: str,
    resume_partitions: list,
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """T0: 下载股票/ETF/指数/基金/期货基本信息"""
    import jqdatasdk

    cp_key = f"{stage}/{domain}"
    if cp_key in resume_partitions:
        print(f"[{now_cn()}] [SKIP] {cp_key} 已完成，跳过")
        return domain, quota_used, total_rows, total_bytes

    print(f"[{now_cn()}] [T0] 下载证券基本信息: {sec_type}")

    probe = probe_api("get_all_securities", {"types": [sec_type]})
    record_probe_result(stage, domain, "get_all_securities",
                        probe["api_supported"], probe["permission_ok"],
                        probe["fields_available"], probe["notes"])
    if not probe["download_allowed"]:
        record_failure(stage, domain, "get_all_securities",
                       "Probe 失败", probe)
        return domain, quota_used, total_rows, total_bytes

    try:
        df = with_retry(
            jqdatasdk.get_all_securities,
            types=[sec_type],
        )
    except Exception as e:
        record_failure(stage, domain, "get_all_securities", str(e),
                       {"sec_type": sec_type})
        save_checkpoint(stage, domain, "STOPPED",
                        stop_reason=f"get_all_securities({sec_type}) 失败: {e}",
                        quota_used=quota_used, total_rows=total_rows,
                        total_bytes=total_bytes)
        return domain, quota_used, total_rows, total_bytes

    if df is None or df.empty:
        record_failure(stage, domain, "get_all_securities",
                       f"返回空数据 (type={sec_type})")
        return domain, quota_used, total_rows, total_bytes

    # 质量闸
    ok, missing = check_schema(df, ["display_name", "name", "start_date",
                                    "end_date", "type"])
    if not ok:
        print(f"[{now_cn()}] [质量闸警告] {sec_type} 字段不完整: {missing}")

    df = df.reset_index().rename(columns={"index": "code"}).copy()

    date_range_str = f"{START_DATE}_{END_DATE}"
    fname = make_filename(stage, domain, date_range=date_range_str, symbol="ALL")
    out_path = stage_dir(stage) / fname

    rows = save_parquet(df, out_path)
    byte_size = out_path.stat().st_size
    checksum = sha256_file(out_path)

    sidecar = {
        "task": TASK_NAME,
        "T_stage": stage,
        "domain": domain,
        "date_range": date_range_str,
        "frequency": None,
        "adj": "none_adj",
        "schema_version": SCHEMA_VERSION,
        "row_count": rows,
        "byte_size": byte_size,
        "download_ts": now_iso(),
        "jq_api": "get_all_securities",
        "quota_consumed_estimated": rows,
        "batch_id": BATCH_ID,
        "checksum_sha256": checksum,
        "checkpoint_key": cp_key,
    }
    write_sidecar(out_path, sidecar)

    write_manifest_row(
        stage=stage, domain=domain,
        symbol="ALL", date_range=date_range_str,
        api="get_all_securities", rows=rows,
        byte_size=byte_size, checksum=checksum, quota=rows,
        extra={"sec_type": sec_type},
    )

    log_quota(stage, domain, "get_all_securities", rows, byte_size, rows)

    quota_used += rows
    total_rows += rows
    total_bytes += byte_size

    print(
        f"[{now_cn()}] [T0] {sec_type} 完成: {rows} 行, "
        f"{byte_size / 1024:.1f} KB"
    )

    save_checkpoint(stage, domain, "RUNNING",
                    completed_partitions=resume_partitions + [cp_key],
                    quota_used=quota_used, total_rows=total_rows,
                    total_bytes=total_bytes)
    return domain, quota_used, total_rows, total_bytes


def download_industries(
    stage: str, resume_partitions: list, quota_used: int,
    total_rows: int, total_bytes: int
) -> tuple[str, int, int, int]:
    """T0: 下载行业分类"""
    import jqdatasdk

    domain = "industry_sw"
    sw_levels = [
        ("sw_l1", "申万一级行业"),
        ("sw_l2", "申万二级行业"),
        ("sw_l3", "申万三级行业"),
    ]

    for sw_name, sw_label in sw_levels:
        cp_key = f"{stage}/{domain}_{sw_name}"
        if cp_key in resume_partitions:
            print(f"[{now_cn()}] [SKIP] {cp_key} 已完成，跳过")
            continue

        print(f"[{now_cn()}] [T0] 下载行业分类: {sw_name} ({sw_label})")

        probe = probe_api("get_industries", {"name": sw_name})
        record_probe_result(stage, f"{domain}_{sw_name}", "get_industries",
                            probe["api_supported"], probe["permission_ok"],
                            probe["fields_available"], probe["notes"])
        if not probe["download_allowed"]:
            record_failure(stage, f"{domain}_{sw_name}", "get_industries",
                           "Probe 失败", probe)
            continue

        try:
            df = with_retry(jqdatasdk.get_industries, name=sw_name)
        except Exception as e:
            record_failure(stage, f"{domain}_{sw_name}", "get_industries",
                           str(e), {"sw_name": sw_name})
            save_checkpoint(stage, f"{domain}_{sw_name}", "STOPPED",
                            stop_reason=f"get_industries({sw_name}) 失败: {e}",
                            quota_used=quota_used, total_rows=total_rows,
                            total_bytes=total_bytes)
            continue

        if df is None or df.empty:
            record_failure(stage, f"{domain}_{sw_name}", "get_industries",
                           f"返回空数据 ({sw_name})")
            continue

        df = df.reset_index().rename(columns={"index": "industry_code"}).copy()

        fname = make_filename(stage, f"industry_{sw_name}",
                              date_range="ALL", symbol="ALL")
        out_path = stage_dir(stage) / fname

        rows = save_parquet(df, out_path)
        byte_size = out_path.stat().st_size
        checksum = sha256_file(out_path)

        sidecar = {
            "task": TASK_NAME,
            "T_stage": stage,
            "domain": f"industry_{sw_name}",
            "date_range": "ALL",
            "frequency": None,
            "adj": "none_adj",
            "schema_version": SCHEMA_VERSION,
            "row_count": rows,
            "byte_size": byte_size,
            "download_ts": now_iso(),
            "jq_api": "get_industries",
            "quota_consumed_estimated": rows,
            "batch_id": BATCH_ID,
            "checksum_sha256": checksum,
            "checkpoint_key": cp_key,
        }
        write_sidecar(out_path, sidecar)

        write_manifest_row(
            stage=stage, domain=f"industry_{sw_name}",
            symbol="ALL", date_range="ALL",
            api="get_industries", rows=rows,
            byte_size=byte_size, checksum=checksum, quota=rows,
            extra={"sw_name": sw_name, "sw_label": sw_label},
        )

        log_quota(stage, f"industry_{sw_name}", "get_industries",
                  rows, byte_size, rows)

        quota_used += rows
        total_rows += rows
        total_bytes += byte_size

        print(
            f"[{now_cn()}] [T0] 行业 {sw_name} 完成: {rows} 行, "
            f"{byte_size / 1024:.1f} KB"
        )

        save_checkpoint(stage, f"industry_{sw_name}", "RUNNING",
                        completed_partitions=resume_partitions + [cp_key],
                        quota_used=quota_used, total_rows=total_rows,
                        total_bytes=total_bytes)

    return domain, quota_used, total_rows, total_bytes


def download_concepts(
    stage: str, resume_partitions: list, quota_used: int,
    total_rows: int, total_bytes: int
) -> tuple[str, int, int, int]:
    """T0: 下载概念分类"""
    import jqdatasdk

    domain = "concepts"
    cp_key = f"{stage}/{domain}"
    if cp_key in resume_partitions:
        print(f"[{now_cn()}] [SKIP] {cp_key} 已完成，跳过")
        return domain, quota_used, total_rows, total_bytes

    print(f"[{now_cn()}] [T0] 下载概念分类...")

    probe = probe_api("get_concepts")
    record_probe_result(stage, domain, "get_concepts",
                        probe["api_supported"], probe["permission_ok"],
                        probe["fields_available"], probe["notes"])
    if not probe["download_allowed"]:
        record_failure(stage, domain, "get_concepts",
                       "Probe 失败", probe)
        return domain, quota_used, total_rows, total_bytes

    try:
        df = with_retry(jqdatasdk.get_concepts)
    except Exception as e:
        record_failure(stage, domain, "get_concepts", str(e))
        save_checkpoint(stage, domain, "STOPPED",
                        stop_reason=f"get_concepts 失败: {e}",
                        quota_used=quota_used, total_rows=total_rows,
                        total_bytes=total_bytes)
        return domain, quota_used, total_rows, total_bytes

    if df is None or df.empty:
        record_failure(stage, domain, "get_concepts", "返回空数据")
        return domain, quota_used, total_rows, total_bytes

    df = df.reset_index().rename(columns={"index": "concept_code"}).copy()

    fname = make_filename(stage, domain, date_range="ALL", symbol="ALL")
    out_path = stage_dir(stage) / fname

    rows = save_parquet(df, out_path)
    byte_size = out_path.stat().st_size
    checksum = sha256_file(out_path)

    sidecar = {
        "task": TASK_NAME,
        "T_stage": stage,
        "domain": domain,
        "date_range": "ALL",
        "frequency": None,
        "adj": "none_adj",
        "schema_version": SCHEMA_VERSION,
        "row_count": rows,
        "byte_size": byte_size,
        "download_ts": now_iso(),
        "jq_api": "get_concepts",
        "quota_consumed_estimated": rows,
        "batch_id": BATCH_ID,
        "checksum_sha256": checksum,
        "checkpoint_key": cp_key,
    }
    write_sidecar(out_path, sidecar)

    write_manifest_row(
        stage=stage, domain=domain,
        symbol="ALL", date_range="ALL",
        api="get_concepts", rows=rows,
        byte_size=byte_size, checksum=checksum, quota=rows,
    )

    log_quota(stage, domain, "get_concepts", rows, byte_size, rows)

    quota_used += rows
    total_rows += rows
    total_bytes += byte_size

    print(
        f"[{now_cn()}] [T0] 概念分类完成: {rows} 行, "
        f"{byte_size / 1024:.1f} KB"
    )

    save_checkpoint(stage, domain, "RUNNING",
                    completed_partitions=resume_partitions + [cp_key],
                    quota_used=quota_used, total_rows=total_rows,
                    total_bytes=total_bytes)
    return domain, quota_used, total_rows, total_bytes


def download_all_factors(
    stage: str, resume_partitions: list, quota_used: int,
    total_rows: int, total_bytes: int
) -> tuple[str, int, int, int]:
    """T0: 下载所有因子列表"""
    import jqdatasdk

    domain = "all_factors"
    cp_key = f"{stage}/{domain}"
    if cp_key in resume_partitions:
        print(f"[{now_cn()}] [SKIP] {cp_key} 已完成，跳过")
        return domain, quota_used, total_rows, total_bytes

    print(f"[{now_cn()}] [T0] 下载所有因子列表...")

    probe = probe_api("get_all_factors")
    record_probe_result(stage, domain, "get_all_factors",
                        probe["api_supported"], probe["permission_ok"],
                        probe["fields_available"], probe["notes"])
    if not probe["download_allowed"]:
        record_failure(stage, domain, "get_all_factors",
                       "Probe 失败", probe)
        return domain, quota_used, total_rows, total_bytes

    try:
        df = with_retry(jqdatasdk.get_all_factors)
    except Exception as e:
        record_failure(stage, domain, "get_all_factors", str(e))
        save_checkpoint(stage, domain, "STOPPED",
                        stop_reason=f"get_all_factors 失败: {e}",
                        quota_used=quota_used, total_rows=total_rows,
                        total_bytes=total_bytes)
        return domain, quota_used, total_rows, total_bytes

    if df is None or df.empty:
        record_failure(stage, domain, "get_all_factors", "返回空数据")
        return domain, quota_used, total_rows, total_bytes

    fname = make_filename(stage, domain, date_range="ALL", symbol="ALL")
    out_path = stage_dir(stage) / fname

    rows = save_parquet(df, out_path)
    byte_size = out_path.stat().st_size
    checksum = sha256_file(out_path)

    sidecar = {
        "task": TASK_NAME,
        "T_stage": stage,
        "domain": domain,
        "date_range": "ALL",
        "frequency": None,
        "adj": "none_adj",
        "schema_version": SCHEMA_VERSION,
        "row_count": rows,
        "byte_size": byte_size,
        "download_ts": now_iso(),
        "jq_api": "get_all_factors",
        "quota_consumed_estimated": rows,
        "batch_id": BATCH_ID,
        "checksum_sha256": checksum,
        "checkpoint_key": cp_key,
    }
    write_sidecar(out_path, sidecar)

    write_manifest_row(
        stage=stage, domain=domain,
        symbol="ALL", date_range="ALL",
        api="get_all_factors", rows=rows,
        byte_size=byte_size, checksum=checksum, quota=rows,
    )

    log_quota(stage, domain, "get_all_factors", rows, byte_size, rows)

    quota_used += rows
    total_rows += rows
    total_bytes += byte_size

    print(
        f"[{now_cn()}] [T0] 所有因子列表完成: {rows} 行, "
        f"{byte_size / 1024:.1f} KB"
    )

    save_checkpoint(stage, domain, "RUNNING",
                    completed_partitions=resume_partitions + [cp_key],
                    quota_used=quota_used, total_rows=total_rows,
                    total_bytes=total_bytes)
    return domain, quota_used, total_rows, total_bytes


def run_t0(
    resume_point: Optional[dict],
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """执行 T0 阶段所有下载任务"""
    stage = "T0"
    print(f"\n{'='*60}")
    print(f"[{now_cn()}] 开始 T0 阶段：元数据骨架")
    print(f"{'='*60}")

    # Probe 阶段：先 probe 再下载
    save_probe_matrix(stage)

    completed_partitions = (resume_point or {}).get("completed_partitions", [])

    # 7.1 交易日历
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_trade_calendar(
            stage, completed_partitions, quota_used, total_rows, total_bytes
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过交易日历")

    # 7.2 股票基本信息
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_securities(
            stage, "stock", "securities_stock",
            completed_partitions, quota_used, total_rows, total_bytes
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过股票基本信息")

    # 7.3 ETF 主表
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_securities(
            stage, "etf", "securities_etf",
            completed_partitions, quota_used, total_rows, total_bytes
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过 ETF 主表")

    # 7.4 指数主表
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_securities(
            stage, "index", "securities_index",
            completed_partitions, quota_used, total_rows, total_bytes
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过指数主表")

    # 7.5 行业分类
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_industries(
            stage, completed_partitions, quota_used, total_rows, total_bytes
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过行业分类")

    # 7.6 概念分类
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_concepts(
            stage, completed_partitions, quota_used, total_rows, total_bytes
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过概念分类")

    # 7.7 基金基本信息
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_securities(
            stage, "fund", "securities_fund",
            completed_partitions, quota_used, total_rows, total_bytes
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过基金基本信息")

    # 7.8 期货基本信息
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_securities(
            stage, "futures", "securities_futures",
            completed_partitions, quota_used, total_rows, total_bytes
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过期货基本信息")

    # 7.9 所有因子列表
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_all_factors(
            stage, completed_partitions, quota_used, total_rows, total_bytes
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过因子列表")

    # 保存 probe matrix
    save_probe_matrix(stage)

    # 标记 T0 完成
    completed_stages = (resume_point or {}).get("completed_stages", [])
    if stage not in completed_stages:
        completed_stages.append(stage)

    save_checkpoint(stage, "ALL_DONE", "RUNNING",
                    completed_stages=completed_stages,
                    completed_partitions=completed_partitions,
                    quota_used=quota_used, total_rows=total_rows,
                    total_bytes=total_bytes)

    print(f"\n[{now_cn()}] T0 阶段完成。累计: {total_rows} 行, "
          f"{total_bytes / 1024 / 1024:.2f} MB, "
          f"额度已用: {quota_used}")

    return stage, quota_used, total_rows, total_bytes


# ══════════════════════════════════════════════════════════
# T1/T2 编排器
# ══════════════════════════════════════════════════════════


def run_t1(
    resume_point: Optional[dict],
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """执行 T1 阶段：复权因子下载（股票 + ETF）"""
    stage = "T1"
    print(f"\n{'='*60}")
    print(f"[{now_cn()}] 开始 T1 阶段：复权因子")
    print(f"{'='*60}")

    completed_partitions = (resume_point or {}).get("completed_partitions", [])

    # 股票复权因子
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_adjust_factor(
            stage, "stock", "adjust_factor_stock",
            completed_partitions, quota_used, total_rows, total_bytes,
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过股票复权因子")

    # ETF 复权因子
    if get_quota_remaining() > 0:
        _, quota_used, total_rows, total_bytes = download_adjust_factor(
            stage, "etf", "adjust_factor_etf",
            completed_partitions, quota_used, total_rows, total_bytes,
        )
    else:
        print(f"[{now_cn()}] [额度耗尽] 跳过 ETF 复权因子")

    save_probe_matrix(stage)

    completed_stages = (resume_point or {}).get("completed_stages", [])
    if stage not in completed_stages:
        completed_stages.append(stage)

    save_checkpoint(stage, "ALL_DONE", "RUNNING",
                    completed_stages=completed_stages,
                    completed_partitions=completed_partitions,
                    quota_used=quota_used, total_rows=total_rows,
                    total_bytes=total_bytes)

    print(f"\n[{now_cn()}] T1 阶段完成。累计: {total_rows} 行, "
          f"{total_bytes / 1024 / 1024:.2f} MB, "
          f"额度已用: {quota_used}")

    return stage, quota_used, total_rows, total_bytes


def run_t2(
    resume_point: Optional[dict],
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """执行 T2 阶段：股票日线下载（不复权）"""
    stage = "T2"
    print(f"\n{'='*60}")
    print(f"[{now_cn()}] 开始 T2 阶段：股票日线（不复权）")
    print(f"{'='*60}")

    completed_partitions = (resume_point or {}).get("completed_partitions", [])

    years = list(range(2014, 2027))
    for year in years:
        if get_quota_remaining() <= 0:
            print(f"[{now_cn()}] [额度耗尽] 停止 T2 日线下载")
            break

        _, quota_used, total_rows, total_bytes = download_stock_daily(
            stage, year, completed_partitions,
            quota_used, total_rows, total_bytes,
        )

    save_probe_matrix(stage)

    completed_stages = (resume_point or {}).get("completed_stages", [])
    if stage not in completed_stages:
        completed_stages.append(stage)

    save_checkpoint(stage, "ALL_DONE", "RUNNING",
                    completed_stages=completed_stages,
                    completed_partitions=completed_partitions,
                    quota_used=quota_used, total_rows=total_rows,
                    total_bytes=total_bytes)

    print(f"\n[{now_cn()}] T2 阶段完成。累计: {total_rows} 行, "
          f"{total_bytes / 1024 / 1024:.2f} MB, "
          f"额度已用: {quota_used}")

    return stage, quota_used, total_rows, total_bytes


# ══════════════════════════════════════════════════════════
# T3: PIT 财务五表
# ══════════════════════════════════════════════════════════


# T3 关键财务表：使用 jq.finance.run_query 或 get_fundamentals
# 注意：jq.finance 中的表需要通过 getattr 惰性加载
T3_FINANCE_TABLES = [
    # (table_name_in_finance, output_subdir, key_cols)
    ("STK_BALANCE_SHEET", "balance_sheet", ["code", "day"]),
    ("STK_BALANCE_SHEET_PARENT", "balance_sheet_parent", ["code", "day"]),
    ("STK_INCOME_STATEMENT", "income_statement", ["code", "day"]),
    ("STK_INCOME_STATEMENT_PARENT", "income_statement_parent", ["code", "day"]),
    ("STK_CASHFLOW_STATEMENT", "cashflow_statement", ["code", "day"]),
    ("STK_CASHFLOW_STATEMENT_PARENT", "cashflow_statement_parent", ["code", "day"]),
    ("STK_FINANCIAL_INDICATOR", "financial_indicator", ["code", "day"]),
    ("STK_FINANCIAL_INDICATOR_CALCULATE", "fin_indicator_calc", ["code", "day"]),
    ("STK_COMPANY_INFO", "company_info", ["code", "day"]),
]


# ─── T3-T9 辅助函数 ──────────────────────────────────


def _get_stock_list() -> list:
    """从 P0_meta 读取全市场股票代码列表"""
    meta_dir = stage_dir("T0")
    sec_files = sorted(meta_dir.glob("securities_stock__*.parquet"))
    if not sec_files:
        sec_files = sorted(meta_dir.glob("securities_*__*.parquet"))
    all_codes = []
    for sf in sec_files:
        try:
            df_meta = pd.read_parquet(sf)
            codes = df_meta["code"].dropna().unique().tolist()
            all_codes.extend(codes)
        except Exception:
            continue
    return sorted(set(all_codes))


def _get_trade_days_between(start_date: str, end_date: str) -> list:
    """从 P0_meta 加载交易日历"""
    meta_dir = stage_dir("T0")
    cal_files = sorted(meta_dir.glob("trade_calendar__*.parquet"))
    if not cal_files:
        return []
    try:
        df = pd.read_parquet(cal_files[-1])
        # Look for actual column names: calendar_date, day, or date
        date_col = None
        for candidate in ["calendar_date", "day", "date"]:
            if candidate in df.columns:
                date_col = candidate
                break
        if date_col is None:
            print(f"[_get_trade_days_between] 无法识别日期列, 可用列: {list(df.columns)}")
            return []

        df["_dt"] = pd.to_datetime(df[date_col])
        # Filter only trading days if column exists
        if "is_trading_day" in df.columns:
            df = df[df["is_trading_day"] == True]

        mask = (df["_dt"] >= pd.Timestamp(start_date)) & (df["_dt"] <= pd.Timestamp(end_date))
        result = sorted(df.loc[mask, "_dt"].dt.strftime("%Y-%m-%d").tolist())
        print(f"[_get_trade_days_between] {start_date}~{end_date}: {len(result)} 个交易日")
        return result
    except Exception as e:
        print(f"[_get_trade_days_between] 异常: {e}")
    return []


def _quick_row_count(file_path: Union[str, Path]) -> int:
    """快速读取 parquet 的行数"""
    try:
        return len(pd.read_parquet(file_path))
    except Exception:
        return 0


def _save_parquet_with_sidecar(
    df: pd.DataFrame,
    out_path: Union[str, Path],
    sidecar_path: Union[str, Path],
    stage: str,
    domain: str,
    api: str,
    partition_key: str,
    batch_id: str,
) -> int:
    """保存 parquet + sidecar + manifest 的一站式函数"""
    out_path = Path(out_path)
    rows = save_parquet(df, out_path)
    byte_size = out_path.stat().st_size
    checksum = sha256_file(out_path)

    sidecar = {
        "task": TASK_NAME,
        "T_stage": stage,
        "domain": domain,
        "partition_key": partition_key,
        "date_range": f"{START_DATE}_{END_DATE}",
        "row_count": rows,
        "byte_size": byte_size,
        "download_ts": now_iso(),
        "jq_api": api,
        "quota_consumed_estimated": 1,
        "batch_id": batch_id,
        "checksum_sha256": checksum,
        "schema_version": SCHEMA_VERSION,
    }
    write_sidecar(out_path, sidecar)

    write_manifest_row(
        stage=stage, domain=domain,
        symbol=partition_key,
        date_range=f"{START_DATE}_{END_DATE}",
        api=api,
        rows=rows, byte_size=byte_size,
        checksum=checksum, quota=1,
        extra={"partition_key": partition_key, "batch_id": batch_id},
    )

    log_quota(stage, domain, api, rows, byte_size, estimated_cost=1)
    return rows


def _write_checksum_row(stage: str, domain: str, file_path: Union[str, Path]) -> str:
    """写入 checksum 记录"""
    file_path = Path(file_path)
    checksum = sha256_file(file_path)
    checksum_dir = INFRA_DIRS["_checksum"]
    checksum_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "batch_id": BATCH_ID,
        "timestamp": now_iso(),
        "T_stage": stage,
        "domain": domain,
        "file": file_path.name,
        "size": file_path.stat().st_size,
        "sha256": checksum,
    }
    checksum_file = checksum_dir / f"checksum_{stage}_{domain}_{BATCH_ID}_{uuid.uuid4().hex[:8]}.json"
    write_json(checksum_file, record, indent=2)
    return checksum


def _record_failure(stage: str, domain: str, error: str, detail: Optional[dict] = None) -> None:
    """记录失败（别名调用 record_failure）"""
    record_failure(stage, domain, "api", error, detail)


# ══════════════════════════════════════════════════════════
# T3: PIT 财务五表
# ══════════════════════════════════════════════════════════


def _download_finance_table(
    stage: str,
    table_name: str,
    out_subdir: str,
    key_cols: list,
    trade_days: list,
    resume_partitions: set,
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """下载单个 finance 表 (按 day 分片)"""
    import jqdatasdk as jq

    domain = f"P3.{out_subdir}"
    stage_dir = ROOT / STAGE_DIRS[stage] / out_subdir
    stage_dir.mkdir(parents=True, exist_ok=True)

    local_q = 0
    local_rows = 0
    local_bytes = 0
    fragment_count = 0

    try:
        tbl = getattr(jq.finance, table_name)
    except Exception as e:
        print(f"  [{now_cn()}] 无法加载 finance 表 {table_name}: {e}")
        _record_failure("T3", f"finance.{table_name}", f"LOAD_ERROR: {e}")
        # Mark done for this whole table
        save_checkpoint("T3", f"T3.{table_name}", "DONE",
                        completed_stages=[], quota_used=quota_used,
                        total_rows=total_rows, total_bytes=total_bytes)
        return stage, quota_used, total_rows, total_bytes

    # Determine if table has 'day' column
    has_day_col = hasattr(tbl, 'day')
    if not has_day_col:
        # Non-daily table, download all at once
        partition_key = f"{table_name}__full"
        out_path = stage_dir / f"{table_name.lower()}__full__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
        sidecar_path = out_path.with_suffix(".json")
        if out_path.exists():
            print(f"  [{now_cn()}] 跳过已存在: {out_path.name}")
            existing_rows = _quick_row_count(out_path)
            local_rows += existing_rows
            return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes

        try:
            q = jq.query(tbl).limit(50000)
            df = jq.finance.run_query(q)
            if df is not None and len(df) > 0:
                rows = _save_parquet_with_sidecar(
                    df, out_path, sidecar_path, stage, domain,
                    f"finance.{table_name}", partition_key, BATCH_ID
                )
                local_rows += rows
                local_bytes += out_path.stat().st_size
                local_q += 1
                fragment_count += 1
                _write_checksum_row(stage, domain, out_path)
            else:
                print(f"  [{now_cn()}] {table_name} 无数据")
        except Exception as e:
            print(f"  [{now_cn()}] {table_name} 查询异常: {e}")
            _record_failure("T3", f"finance.{table_name}", str(e)[:200])

        save_checkpoint("T3", f"T3.{table_name}", "DONE",
                        completed_stages=[], quota_used=quota_used + local_q,
                        total_rows=total_rows + local_rows,
                        total_bytes=total_bytes + local_bytes)
        return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes

    # Daily table: partition by day batches
    days_to_process = [d for d in trade_days if d not in resume_partitions]
    # Group days into batches of 20 to reduce queries
    batch_size = 20
    for i in range(0, len(days_to_process), batch_size):
        day_batch = days_to_process[i:i + batch_size]
        day_str = f"{day_batch[0]}_{day_batch[-1]}"
        partition_key = f"{table_name}__{day_str}"
        out_path = stage_dir / f"{table_name.lower()}__{day_str}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
        sidecar_path = out_path.with_suffix(".json")

        if out_path.exists():
            continue

        try:
            rows_before = local_rows
            for day_str_single in day_batch:
                q = jq.query(tbl).filter(tbl.day == day_str_single).limit(30000)
                df = jq.finance.run_query(q)
                if df is not None and len(df) > 0:
                    # Accumulate to temp list
                    temp_path = out_path.with_suffix(".tmp.parquet")
                    if not temp_path.exists():
                        df.to_parquet(temp_path, index=False)
                    else:
                        existing = pd.read_parquet(temp_path)
                        combined = pd.concat([existing, df], ignore_index=True)
                        combined.to_parquet(temp_path, index=False)
                    local_q += 1

            # Save combined
            temp_path = out_path.with_suffix(".tmp.parquet")
            if temp_path.exists():
                final_df = pd.read_parquet(temp_path)
                rows = _save_parquet_with_sidecar(
                    final_df, out_path, sidecar_path, stage, domain,
                    f"finance.{table_name}", partition_key, BATCH_ID
                )
                local_rows += rows
                local_bytes += out_path.stat().st_size
                temp_path.unlink(missing_ok=True)
                _write_checksum_row(stage, domain, out_path)
                fragment_count += 1

            # Check quota
            remaining = get_quota_remaining()
            if remaining <= 0:
                print(f"  [{now_cn()}] 额度耗尽，停止 T3.{table_name}")
                save_checkpoint("T3", f"T3.{table_name}", "STOPPED_QUOTA",
                                completed_stages=[], quota_used=quota_used + local_q,
                                total_rows=total_rows + local_rows,
                                total_bytes=total_bytes + local_bytes)
                return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes
        except Exception as e:
            print(f"  [{now_cn()}] {table_name} 批次错误 {day_str}: {e}")
            _record_failure("T3", f"finance.{table_name}.{day_str}", str(e)[:200])

    print(f"  [{now_cn()}] T3.{table_name} 完成: {local_rows} 行, {fragment_count} 分片")
    save_checkpoint("T3", f"T3.{table_name}", "DONE",
                    completed_stages=[], quota_used=quota_used + local_q,
                    total_rows=total_rows + local_rows,
                    total_bytes=total_bytes + local_bytes)
    return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes


def run_t3(
    resume_point: Optional[dict],
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """T3: PIT 财务五表下载"""
    import jqdatasdk as jq

    stage = "T3"
    print(f"\n[{now_cn()}] {'='*50}")
    print(f"[{now_cn()}] T3: 开始下载 PIT 财务五表")
    print(f"[{now_cn()}] {'='*50}")

    jq_auth()
    remaining = get_quota_remaining()
    print(f"[{now_cn()}] 当前额度剩余: {remaining:,}")
    if remaining <= 0:
        print(f"[{now_cn()}] 额度已耗尽，暂缓 T3")
        return stage, quota_used, total_rows, total_bytes

    # Get trade days from calendar
    trade_days = _get_trade_days_between(START_DATE, END_DATE)
    if not trade_days:
        print(f"[{now_cn()}] 无可用的交易日历数据")
        return stage, quota_used, total_rows, total_bytes

    resume_partitions = set()
    if resume_point:
        resume_partitions = set(resume_point.get("completed_partitions", []))

    local_q = 0
    local_rows = 0
    local_bytes = 0

    for table_name, out_subdir, key_cols in T3_FINANCE_TABLES:
        remaining = get_quota_remaining()
        if remaining <= 0:
            print(f"[{now_cn()}] 额度已耗尽，停止 T3")
            save_checkpoint("T3", "ALL", "STOPPED_QUOTA",
                            completed_stages=[], quota_used=quota_used + local_q,
                            total_rows=total_rows + local_rows,
                            total_bytes=total_bytes + local_bytes)
            return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes

        stage, q_used, rows_added, bytes_added = _download_finance_table(
            stage, table_name, out_subdir, key_cols,
            trade_days, resume_partitions,
            quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes
        )
        local_q += q_used - quota_used
        local_rows += rows_added - total_rows
        local_bytes += bytes_added - total_bytes

    print(f"\n[{now_cn()}] T3 完成. 新增 {local_rows} 行 / {local_bytes/1024/1024:.2f} MB")
    return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes


# ══════════════════════════════════════════════════════════
# T4: 指数体系
# ══════════════════════════════════════════════════════════


def run_t4(
    resume_point: Optional[dict],
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """T4: 指数体系（日线、成分、权重）"""
    import jqdatasdk as jq

    stage = "T4"
    print(f"\n[{now_cn()}] {'='*50}")
    print(f"[{now_cn()}] T4: 开始下载指数体系")
    print(f"[{now_cn()}] {'='*50}")

    jq_auth()
    remaining = get_quota_remaining()
    if remaining <= 0:
        return stage, quota_used, total_rows, total_bytes

    stage_dir = ROOT / STAGE_DIRS[stage]
    stage_dir.mkdir(parents=True, exist_ok=True)
    domain = "P4.index"
    local_q = 0
    local_rows = 0
    local_bytes = 0

    # 确定主要指数列表
    major_indices = [
        "000001.XSHG",  # 上证综指
        "000300.XSHG",  # 沪深300
        "000016.XSHG",  # 上证50
        "000905.XSHG",  # 中证500
        "000688.XSHG",  # 科创50
        "399001.XSHE",  # 深证成指
        "399006.XSHE",  # 创业板指
        "000852.XSHG",  # 中证1000
    ]

    # 4a. 指数日线
    print(f"\n[{now_cn()}] T4a: 指数日线")
    trade_days = _get_trade_days_between(START_DATE, END_DATE)
    if trade_days:
        # Year batches for index daily
        years = sorted(set(d[:4] for d in trade_days))
        for year in years:
            remaining = get_quota_remaining()
            if remaining <= 0:
                save_checkpoint("T4", "T4.index_daily", "STOPPED_QUOTA", [])
                return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes

            year_start = f"{year}-01-01"
            year_end = f"{year}-12-31" if year != "2026" else "2026-06-12"
            out_path = stage_dir / f"index_daily__{year}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
            sidecar_path = out_path.with_suffix(".json")

            if out_path.exists():
                print(f"  [{now_cn()}] 跳过已存在: {out_path.name}")
                local_rows += _quick_row_count(out_path)
                continue

            try:
                df = jq.get_price(major_indices, start_date=year_start, end_date=year_end, frequency='daily')
                if df is not None and len(df) > 0:
                    rows = _save_parquet_with_sidecar(
                        df, out_path, sidecar_path, stage, domain,
                        "get_price.index.daily", f"index_daily_{year}", BATCH_ID
                    )
                    local_rows += rows
                    local_bytes += out_path.stat().st_size
                    local_q += 1
                    _write_checksum_row(stage, domain, out_path)
                    print(f"  [{now_cn()}] 指数日线 {year}: {rows} 行")
                else:
                    print(f"  [{now_cn()}] 指数日线 {year}: 无数据")
            except Exception as e:
                print(f"  [{now_cn()}] 指数日线 {year} 异常: {e}")
                _record_failure("T4", f"index_daily_{year}", str(e)[:200])

    # 4b. 指数成分股（年度快照）
    print(f"\n[{now_cn()}] T4b: 指数成分股快照")
    snapshot_years = ["2014", "2015", "2016", "2017", "2018", "2019",
                       "2020", "2021", "2022", "2023", "2024", "2025", "2026"]
    for idx_code in major_indices[:5]:  # Top 5 indices
        for snap_year in snapshot_years:
            remaining = get_quota_remaining()
            if remaining <= 0:
                return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes

            snap_date = f"{snap_year}-06-30"
            out_path = stage_dir / f"index_constituents__{idx_code.replace('.','_')}__{snap_year}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
            sidecar_path = out_path.with_suffix(".json")

            if out_path.exists():
                continue

            try:
                members = jq.get_index_stocks(idx_code, date=snap_date)
                if members:
                    df = pd.DataFrame({"code": members, "index_code": idx_code, "snapshot_date": snap_date})
                    rows = _save_parquet_with_sidecar(
                        df, out_path, sidecar_path, stage, domain,
                        "get_index_stocks", f"index_constituents_{idx_code}_{snap_year}", BATCH_ID
                    )
                    local_rows += rows
                    local_bytes += out_path.stat().st_size
                    local_q += 1
                    print(f"  [{now_cn()}] 成分 {idx_code} {snap_year}: {rows} 行")
            except Exception as e:
                print(f"  [{now_cn()}] 成分 {idx_code} {snap_year} 异常: {e}")

    # 4c. 指数权重
    print(f"\n[{now_cn()}] T4c: 指数权重")
    try:
        out_path = stage_dir / f"index_weights__reference__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
        sidecar_path = out_path.with_suffix(".json")
        if not out_path.exists():
            # get_index_weights 返回 DataFrame
            df_weights = jq.get_index_weights("000300.XSHG", date="2026-01-01")
            if df_weights is not None and len(df_weights) > 0:
                rows = _save_parquet_with_sidecar(
                    df_weights, out_path, sidecar_path, stage, domain,
                    "get_index_weights", "index_weights_300_ref", BATCH_ID
                )
                local_rows += rows
                local_bytes += out_path.stat().st_size
                local_q += 1
                print(f"  [{now_cn()}] 指数权重: {rows} 行")
    except Exception as e:
        print(f"  [{now_cn()}] 指数权重异常: {e}")

    print(f"\n[{now_cn()}] T4 完成. 新增 {local_rows} 行 / {local_bytes/1024/1024:.2f} MB")
    return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes


# ══════════════════════════════════════════════════════════
# T5: 状态 / 事件属性表
# ══════════════════════════════════════════════════════════


def run_t5(
    resume_point: Optional[dict],
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """T5: 状态 / 事件属性表"""
    import jqdatasdk as jq

    stage = "T5"
    print(f"\n[{now_cn()}] {'='*50}")
    print(f"[{now_cn()}] T5: 开始下载状态/事件属性表")
    print(f"[{now_cn()}] {'='*50}")

    jq_auth()
    remaining = get_quota_remaining()
    if remaining <= 0:
        return stage, quota_used, total_rows, total_bytes

    stage_dir = ROOT / STAGE_DIRS[stage]
    stage_dir.mkdir(parents=True, exist_ok=True)
    domain = "P5.attributes_events"
    local_q = 0
    local_rows = 0
    local_bytes = 0

    # Get all-stock list
    all_stocks = _get_stock_list()
    if not all_stocks:
        print(f"[{now_cn()}] 无法获取股票列表")
        return stage, quota_used, total_rows, total_bytes

    trade_days = _get_trade_days_between(START_DATE, END_DATE)
    if not trade_days:
        return stage, quota_used, total_rows, total_bytes

    # 5a. ST 标记 (get_extras)
    print(f"\n[{now_cn()}] T5a: ST 标记")
    out_path = stage_dir / f"st_mark__{START_DATE}_{END_DATE}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
    sidecar_path = out_path.with_suffix(".json")
    if not out_path.exists():
        try:
            # Process in smaller batches of 500 stocks per year chunk
            stock_batches = [all_stocks[i:i+500] for i in range(0, len(all_stocks), 500)]
            all_st_dfs = []
            for batch_stocks in stock_batches:
                remaining = get_quota_remaining()
                if remaining <= 0:
                    break
                for year in range(2014, 2027):
                    ys = f"{year}-01-01"
                    ye = f"{year}-12-31" if year < 2026 else "2026-06-12"
                    try:
                        df_st = jq.get_extras('is_st', batch_stocks, start_date=ys, end_date=ye)
                        if df_st is not None and len(df_st) > 0:
                            df_st = df_st.stack().reset_index()
                            df_st.columns = ['date', 'code', 'is_st']
                            all_st_dfs.append(df_st)
                            local_q += 1
                    except Exception as e:
                        print(f"  [{now_cn()}] ST {year} 异常: {e}")
                        continue
            
            if all_st_dfs:
                combined_st = pd.concat(all_st_dfs, ignore_index=True)
                rows = _save_parquet_with_sidecar(
                    combined_st, out_path, sidecar_path, stage, domain,
                    "get_extras.is_st", "st_mark_full", BATCH_ID
                )
                local_rows += rows
                local_bytes += out_path.stat().st_size
                print(f"  [{now_cn()}] ST 标记: {rows} 行")
        except Exception as e:
            print(f"  [{now_cn()}] ST 整体异常: {e}")

    # 5b. 停牌标记 (get_extras)
    print(f"\n[{now_cn()}] T5b: 停牌标记")
    out_path = stage_dir / f"suspended__{START_DATE}_{END_DATE}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
    sidecar_path = out_path.with_suffix(".json")
    if not out_path.exists():
        try:
            stock_batches = [all_stocks[i:i+500] for i in range(0, len(all_stocks), 500)]
            all_pause_dfs = []
            for batch_stocks in stock_batches:
                remaining = get_quota_remaining()
                if remaining <= 0:
                    break
                for year in range(2014, 2027):
                    ys = f"{year}-01-01"
                    ye = f"{year}-12-31" if year < 2026 else "2026-06-12"
                    try:
                        df_pause = jq.get_extras('is_paused', batch_stocks, start_date=ys, end_date=ye)
                        if df_pause is not None and len(df_pause) > 0:
                            df_pause = df_pause.stack().reset_index()
                            df_pause.columns = ['date', 'code', 'is_paused']
                            all_pause_dfs.append(df_pause)
                            local_q += 1
                    except Exception as e:
                        continue
            if all_pause_dfs:
                combined_pause = pd.concat(all_pause_dfs, ignore_index=True)
                rows = _save_parquet_with_sidecar(
                    combined_pause, out_path, sidecar_path, stage, domain,
                    "get_extras.is_paused", "suspended_full", BATCH_ID
                )
                local_rows += rows
                local_bytes += out_path.stat().st_size
                print(f"  [{now_cn()}] 停牌标记: {rows} 行")
        except Exception as e:
            print(f"  [{now_cn()}] 停牌异常: {e}")

    # 5c. Finance 事件表
    t5_event_tables = [
        ("STK_XR_XD", "xr_xd", ["code", "day"]),
        ("STK_CAPITAL_CHANGE", "capital_change", ["code", "day"]),
        ("STK_STATUS_CHANGE", "status_change", ["code", "day"]),
        ("STK_HOLDER_NUM", "holder_num", ["code", "day"]),
        ("STK_LOCK_SHARES", "lock_shares", ["code", "day"]),
        ("STK_LIMITED_SHARES_LIST", "limited_shares", ["code", "day"]),
        ("STK_SHARES_FROZEN", "shares_frozen", ["code", "day"]),
        ("STK_SHARES_PLEDGE", "shares_pledge", ["code", "day"]),
        ("STK_ABNORMAL", "abnormal", ["code", "day"]),
        ("STK_MONEY_FLOW", "money_flow", ["code", "day"]),
        ("STK_MT_TOTAL", "mt_total", ["code", "day"]),
        ("STK_SUBSCRIBE", "subscribe", ["code", "day"]),
        ("STK_AUDIT_OPINION", "audit_opinion", ["code", "day"]),
        ("STK_MANAGEMENT_INFO", "management_info", ["code", "day"]),
    ]

    for table_name, out_subdir, key_cols in t5_event_tables:
        remaining = get_quota_remaining()
        if remaining <= 0:
            break

        print(f"\n[{now_cn()}] T5c: {table_name}")
        table_domain = f"P5.{out_subdir}"
        tbl_stage_dir = stage_dir / out_subdir
        tbl_stage_dir.mkdir(parents=True, exist_ok=True)

        try:
            tbl = getattr(jq.finance, table_name)
        except Exception as e:
            print(f"  [{now_cn()}] 无法加载 {table_name}: {e}")
            _record_failure("T5", f"finance.{table_name}", str(e)[:200])
            continue

        has_day = hasattr(tbl, 'day')
        if not has_day:
            # Snapshot table, download all
            out_path = tbl_stage_dir / f"{table_name.lower()}__full__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
            sidecar_path = out_path.with_suffix(".json")
            if not out_path.exists():
                try:
                    q = jq.query(tbl).limit(100000)
                    df = jq.finance.run_query(q)
                    if df is not None and len(df) > 0:
                        rows = _save_parquet_with_sidecar(
                            df, out_path, sidecar_path, stage, table_domain,
                            f"finance.{table_name}", f"{table_name}_full", BATCH_ID
                        )
                        local_rows += rows
                        local_bytes += out_path.stat().st_size
                        local_q += 1
                        print(f"  [{now_cn()}] {table_name}: {rows} 行")
                except Exception as e:
                    print(f"  [{now_cn()}] {table_name} 异常: {e}")
        else:
            # Daily table, process year by year
            for year in range(2014, 2027):
                remaining = get_quota_remaining()
                if remaining <= 0:
                    break

                year_str = str(year)
                out_path = tbl_stage_dir / f"{table_name.lower()}__{year_str}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
                sidecar_path = out_path.with_suffix(".json")
                if out_path.exists():
                    local_rows += _quick_row_count(out_path)
                    continue

                try:
                    ys = f"{year_str}-01-01"
                    ye = f"{year_str}-12-31" if year < 2026 else "2026-06-12"
                    q = jq.query(tbl).filter(tbl.day >= ys, tbl.day <= ye).limit(50000)
                    df = jq.finance.run_query(q)
                    if df is not None and len(df) > 0:
                        rows = _save_parquet_with_sidecar(
                            df, out_path, sidecar_path, stage, table_domain,
                            f"finance.{table_name}", f"{table_name}_{year_str}", BATCH_ID
                        )
                        local_rows += rows
                        local_bytes += out_path.stat().st_size
                        local_q += 1
                        print(f"  [{now_cn()}] {table_name} {year_str}: {rows} 行")
                except Exception as e:
                    print(f"  [{now_cn()}] {table_name} {year_str} 异常: {e}")

    print(f"\n[{now_cn()}] T5 完成. 新增 {local_rows} 行 / {local_bytes/1024/1024:.2f} MB")
    return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes


# ══════════════════════════════════════════════════════════
# T6: 官方因子支持层
# ══════════════════════════════════════════════════════════


def run_t6(
    resume_point: Optional[dict],
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """T6: 官方因子参考（仅元数据，不下载因子值）"""
    import jqdatasdk as jq

    stage = "T6"
    print(f"\n[{now_cn()}] {'='*50}")
    print(f"[{now_cn()}] T6: 开始下载因子参考元数据")
    print(f"[{now_cn()}] {'='*50}")

    jq_auth()
    remaining = get_quota_remaining()
    if remaining <= 0:
        return stage, quota_used, total_rows, total_bytes

    stage_dir = ROOT / STAGE_DIRS[stage]
    stage_dir.mkdir(parents=True, exist_ok=True)
    domain = "P6.factor_reference"
    local_q = 0
    local_rows = 0
    local_bytes = 0

    # 6a. get_all_factors 元数据
    out_path = stage_dir / f"all_factors_metadata__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
    sidecar_path = out_path.with_suffix(".json")
    if not out_path.exists():
        try:
            all_factors = jq.get_all_factors()
            if all_factors is not None and len(all_factors) > 0:
                df_factors = pd.DataFrame(all_factors, columns=['factor_name'])
                rows = _save_parquet_with_sidecar(
                    df_factors, out_path, sidecar_path, stage, domain,
                    "get_all_factors", "all_factors_metadata", BATCH_ID
                )
                local_rows += rows
                local_bytes += out_path.stat().st_size
                local_q += 1
                print(f"  [{now_cn()}] 全因子列表: {rows} 个因子")
            else:
                print(f"  [{now_cn()}] get_all_factors 返回空（无权限）")
                # Create empty marker
                df_empty = pd.DataFrame({"factor_name": [], "note": ["NO_PERMISSION"]})
                rows = _save_parquet_with_sidecar(
                    df_empty, out_path, sidecar_path, stage, domain,
                    "get_all_factors", "all_factors_metadata_no_permission", BATCH_ID
                )
        except Exception as e:
            print(f"  [{now_cn()}] get_all_factors 异常: {e}")
            _record_failure("T6", "get_all_factors", str(e)[:200])

    # 记录因子值下载策略
    print(f"  [{now_cn()}] factor_value_download_allowed = false（按要求禁止下载全量因子值）")
    note_path = stage_dir / "FACTOR_VALUE_POLICY.txt"
    if not note_path.exists():
        write_json(note_path.with_suffix(".json"),
            {"factor_value_download_allowed": False,
             "reason": "User policy - only factor metadata, no full factor values",
             "task": TASK_NAME})

    print(f"\n[{now_cn()}] T6 完成. 新增 {local_rows} 行")
    return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes


# ══════════════════════════════════════════════════════════
# T7: 股票分钟线
# ══════════════════════════════════════════════════════════


def run_t7(
    resume_point: Optional[dict],
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """T7: 股票分钟线 (1m/5m/30m/60m)"""
    import jqdatasdk as jq

    stage = "T7"
    print(f"\n[{now_cn()}] {'='*50}")
    print(f"[{now_cn()}] T7: 开始下载股票分钟线")
    print(f"[{now_cn()}] {'='*50}")

    jq_auth()
    remaining = get_quota_remaining()
    if remaining <= 0:
        return stage, quota_used, total_rows, total_bytes

    stage_dir = ROOT / STAGE_DIRS[stage]
    stage_dir.mkdir(parents=True, exist_ok=True)
    domain = "P7.stock_minute"
    local_q = 0
    local_rows = 0
    local_bytes = 0

    all_stocks = _get_stock_list()
    if not all_stocks:
        print(f"[{now_cn()}] 无法获取股票列表")
        return stage, quota_used, total_rows, total_bytes

    trade_days = _get_trade_days_between(START_DATE, END_DATE)
    if not trade_days:
        return stage, quota_used, total_rows, total_bytes

    # Frequencies: 5m first (most useful), then 1m, 30m, 60m
    frequencies = ['5m', '1m', '30m', '60m']
    # For minute bars, sample 20 stocks per batch to stay within JQData limits
    stock_batches = [all_stocks[i:i+20] for i in range(0, min(len(all_stocks), 200), 20)]  # Top 200 stocks

    for freq in frequencies:
        print(f"\n[{now_cn()}] T7: 下载 {freq} 分钟线")

        for year in range(2014, 2027):
            remaining = get_quota_remaining()
            if remaining <= 0:
                save_checkpoint("T7", f"T7.{freq}", "STOPPED_QUOTA", [])
                break

            year_str = str(year)
            for batch_idx, stock_batch in enumerate(stock_batches):
                remaining = get_quota_remaining()
                if remaining <= 0:
                    break

                batch_str = f"batch{batch_idx:04d}"
                out_path = stage_dir / f"stock_minute_{freq}__{year_str}__{batch_str}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
                sidecar_path = out_path.with_suffix(".json")
                # 检查是否已存在（匹配任意 batch_id）
                existing = list(stage_dir.glob(f"stock_minute_{freq}__{year_str}__{batch_str}__{SCHEMA_VERSION}__*.parquet"))
                if existing:
                    local_rows += _quick_row_count(existing[0])
                    continue

                try:
                    ys = f"{year_str}-01-01"
                    ye = f"{year_str}-12-31" if year < 2026 else "2026-06-12"
                    df = jq.get_price(stock_batch, start_date=ys, end_date=ye, frequency=freq)
                    if df is not None and len(df) > 0:
                        rows = _save_parquet_with_sidecar(
                            df, out_path, sidecar_path, stage, domain,
                            f"get_price.{freq}", f"minute_{freq}_{year}_{batch_str}", BATCH_ID
                        )
                        local_rows += rows
                        local_bytes += out_path.stat().st_size
                        local_q += 1
                        _write_checksum_row(stage, domain, out_path)
                except Exception as e:
                    err_msg = str(e)[:150]
                    if "limit" in err_msg.lower() or "quota" in err_msg.lower():
                        print(f"  [{now_cn()}] {freq} {year_str} {batch_str} 额度/限流: {err_msg}")
                        break
                    print(f"  [{now_cn()}] {freq} {year_str} {batch_str}: {err_msg}")

    print(f"\n[{now_cn()}] T7 完成. 新增 {local_rows} 行 / {local_bytes/1024/1024:.2f} MB")
    return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes


# ══════════════════════════════════════════════════════════
# T8: ETF / 基金
# ══════════════════════════════════════════════════════════


def run_t8(
    resume_point: Optional[dict],
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """T8: ETF / 基金"""
    import jqdatasdk as jq

    stage = "T8"
    print(f"\n[{now_cn()}] {'='*50}")
    print(f"[{now_cn()}] T8: 开始下载 ETF/基金数据")
    print(f"[{now_cn()}] {'='*50}")

    jq_auth()
    remaining = get_quota_remaining()
    if remaining <= 0:
        return stage, quota_used, total_rows, total_bytes

    stage_dir = ROOT / STAGE_DIRS[stage]
    stage_dir.mkdir(parents=True, exist_ok=True)
    domain = "P8.etf_fund"
    local_q = 0
    local_rows = 0
    local_bytes = 0

    # Get ETF list
    etf_stocks = []
    try:
        etf_securities = jq.get_all_securities(types=['etf'])
        if etf_securities is not None and len(etf_securities) > 0:
            etf_stocks = etf_securities.index.tolist()
            print(f"  [{now_cn()}] ETF 数量: {len(etf_stocks)}")
            # Save ETF list
            list_out = stage_dir / f"etf_list__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
            list_sidecar = list_out.with_suffix(".json")
            if not list_out.exists():
                etf_securities.index.name = 'code'
                etf_securities = etf_securities.reset_index()
                rows = _save_parquet_with_sidecar(
                    etf_securities, list_out, list_sidecar, stage, domain,
                    "get_all_securities.etf", "etf_list", BATCH_ID
                )
                local_rows += rows
                local_bytes += list_out.stat().st_size
                local_q += 1
    except Exception as e:
        print(f"  [{now_cn()}] ETF 列表加载异常: {e}")

    # 8a. ETF 日线 (none_adj)
    if etf_stocks:
        print(f"\n[{now_cn()}] T8a: ETF 日线")
        etf_batches = [etf_stocks[i:i+100] for i in range(0, len(etf_stocks), 100)]
        for year in range(2014, 2027):
            remaining = get_quota_remaining()
            if remaining <= 0:
                break
            year_str = str(year)
            for batch_idx, etf_batch in enumerate(etf_batches):
                remaining = get_quota_remaining()
                if remaining <= 0:
                    break
                batch_str = f"batch{batch_idx:04d}"
                out_path = stage_dir / f"etf_daily__{year_str}__{batch_str}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
                sidecar_path = out_path.with_suffix(".json")
                if out_path.exists():
                    continue
                try:
                    ys = f"{year_str}-01-01"
                    ye = f"{year_str}-12-31" if year < 2026 else "2026-06-12"
                    df = jq.get_price(etf_batch, start_date=ys, end_date=ye, frequency='daily', fields=['open','high','low','close','volume','money','paused','high_limit','low_limit','avg','pre_close','factor'])
                    if df is not None and len(df) > 0:
                        rows = _save_parquet_with_sidecar(
                            df, out_path, sidecar_path, stage, domain,
                            "get_price.etf.daily", f"etf_daily_{year}_{batch_str}", BATCH_ID
                        )
                        local_rows += rows
                        local_bytes += out_path.stat().st_size
                        local_q += 1
                except Exception as e:
                    print(f"  [{now_cn()}] ETF 日线 {year} {batch_str}: {str(e)[:100]}")

    # 8b. 基金 NAV (finance tables)
    print(f"\n[{now_cn()}] T8b: 基金 NAV")
    fund_tables = [
        ("FUND_NET_VALUE", "fund_nav", ["code", "day"]),
        ("FUND_SHARE_DAILY", "fund_share", ["code", "day"]),
        ("FUND_MF_DAILY_PROFIT", "fund_profit", ["code", "day"]),
        ("FUND_DIVIDEND", "fund_dividend", ["code", "day"]),
    ]
    for table_name, out_subdir, key_cols in fund_tables:
        remaining = get_quota_remaining()
        if remaining <= 0:
            break
        tbl_stage_dir = stage_dir / out_subdir
        tbl_stage_dir.mkdir(parents=True, exist_ok=True)
        try:
            tbl = getattr(jq.finance, table_name)
        except:
            continue
        # Download all data (these tables are limited)
        out_path = tbl_stage_dir / f"{table_name.lower()}__full__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
        sidecar_path = out_path.with_suffix(".json")
        if not out_path.exists():
            try:
                q = jq.query(tbl).limit(100000)
                df = jq.finance.run_query(q)
                if df is not None and len(df) > 0:
                    rows = _save_parquet_with_sidecar(
                        df, out_path, sidecar_path, stage, f"P8.{out_subdir}",
                        f"finance.{table_name}", f"{table_name}_full", BATCH_ID
                    )
                    local_rows += rows
                    local_bytes += out_path.stat().st_size
                    local_q += 1
                    print(f"  [{now_cn()}] {table_name}: {rows} 行")
            except Exception as e:
                print(f"  [{now_cn()}] {table_name}: {str(e)[:100]}")

    print(f"\n[{now_cn()}] T8 完成. 新增 {local_rows} 行 / {local_bytes/1024/1024:.2f} MB")
    return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes


# ══════════════════════════════════════════════════════════
# T9: 衍生与辅助
# ══════════════════════════════════════════════════════════


def run_t9(
    resume_point: Optional[dict],
    quota_used: int,
    total_rows: int,
    total_bytes: int,
) -> tuple[str, int, int, int]:
    """T9: 衍生与辅助数据"""
    import jqdatasdk as jq

    stage = "T9"
    print(f"\n[{now_cn()}] {'='*50}")
    print(f"[{now_cn()}] T9: 开始下载衍生与辅助数据")
    print(f"[{now_cn()}] {'='*50}")

    jq_auth()
    remaining = get_quota_remaining()
    if remaining <= 0:
        return stage, quota_used, total_rows, total_bytes

    stage_dir = ROOT / STAGE_DIRS[stage]
    stage_dir.mkdir(parents=True, exist_ok=True)
    domain = "P9.derivative_aux"
    local_q = 0
    local_rows = 0
    local_bytes = 0

    all_stocks = _get_stock_list()
    if not all_stocks:
        return stage, quota_used, total_rows, total_bytes

    # 9a. 融资融券
    print(f"\n[{now_cn()}] T9a: 融资融券 (MTSS)")
    for year in range(2014, 2027):
        remaining = get_quota_remaining()
        if remaining <= 0:
            break
        year_str = str(year)
        out_path = stage_dir / f"mtss__{year_str}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
        sidecar_path = out_path.with_suffix(".json")
        if out_path.exists():
            continue
        try:
            stock_sample = all_stocks[:50]  # Top 50 for MTSS
            all_mtss = []
            for stock_code in stock_sample:
                try:
                    ys = f"{year_str}-01-01"
                    ye = f"{year_str}-12-31" if year < 2026 else "2026-06-12"
                    df_mtss = jq.get_mtss(stock_code, start_date=ys, end_date=ye)
                    if df_mtss is not None and len(df_mtss) > 0:
                        df_mtss['code'] = stock_code
                        all_mtss.append(df_mtss)
                        local_q += 1
                except:
                    continue
            if all_mtss:
                combined = pd.concat(all_mtss, ignore_index=True)
                rows = _save_parquet_with_sidecar(
                    combined, out_path, sidecar_path, stage, domain,
                    "get_mtss", f"mtss_{year}", BATCH_ID
                )
                local_rows += rows
                local_bytes += out_path.stat().st_size
                print(f"  [{now_cn()}] MTSS {year}: {rows} 行")
        except Exception as e:
            print(f"  [{now_cn()}] MTSS {year} 异常: {e}")

    # 9b. 互联互通 (STK_HK_HOLD_INFO)
    print(f"\n[{now_cn()}] T9b: 互联互通")
    link_tables = [
        ("STK_HK_HOLD_INFO", "hk_hold_info", ["code", "day"]),
        ("STK_HK_HOLD_INFO2", "hk_hold_info2", ["code", "day"]),
        ("STK_EXCHANGE_LINK_RATE", "exchange_link_rate", ["link_id", "day"]),
        ("STK_ML_QUOTA", "ml_quota", ["day"]),
        ("STK_EXCHANGE_TRADE_INFO", "exchange_trade", ["code", "day"]),
    ]
    for table_name, out_subdir, key_cols in link_tables:
        remaining = get_quota_remaining()
        if remaining <= 0:
            break
        tbl_stage_dir = stage_dir / out_subdir
        tbl_stage_dir.mkdir(parents=True, exist_ok=True)
        try:
            tbl = getattr(jq.finance, table_name)
        except:
            continue

        # Year-by-year
        for year in range(2014, 2027):
            remaining = get_quota_remaining()
            if remaining <= 0:
                break
            year_str = str(year)
            out_path = tbl_stage_dir / f"{table_name.lower()}__{year_str}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
            sidecar_path = out_path.with_suffix(".json")
            if out_path.exists():
                continue
            try:
                ys = f"{year_str}-01-01"
                ye = f"{year_str}-12-31" if year < 2026 else "2026-06-12"
                q = jq.query(tbl).filter(tbl.day >= ys, tbl.day <= ye).limit(50000)
                df = jq.finance.run_query(q)
                if df is not None and len(df) > 0:
                    rows = _save_parquet_with_sidecar(
                        df, out_path, sidecar_path, stage, f"P9.{out_subdir}",
                        f"finance.{table_name}", f"{table_name}_{year}", BATCH_ID
                    )
                    local_rows += rows
                    local_bytes += out_path.stat().st_size
                    local_q += 1
                    print(f"  [{now_cn()}] {table_name} {year}: {rows} 行")
            except Exception as e:
                print(f"  [{now_cn()}] {table_name} {year}: {str(e)[:100]}")

    # 9c. 指数分钟线
    print(f"\n[{now_cn()}] T9c: 指数分钟线")
    major_indices = [
        "000001.XSHG", "000300.XSHG", "000016.XSHG",
        "000905.XSHG", "399001.XSHE", "399006.XSHE",
    ]
    minute_freqs = ['5m', '1m', '30m', '60m']
    for freq in minute_freqs:
        remaining = get_quota_remaining()
        if remaining <= 0:
            break
        # Sample - just current year
        for year_str in ["2026"]:
            out_path = stage_dir / f"index_minute_{freq}__{year_str}__{SCHEMA_VERSION}__{BATCH_ID}.parquet"
            sidecar_path = out_path.with_suffix(".json")
            if not out_path.exists():
                try:
                    ys = f"{year_str}-01-01"
                    ye = "2026-06-12"
                    df = jq.get_price(major_indices, start_date=ys, end_date=ye, frequency=freq)
                    if df is not None and len(df) > 0:
                        rows = _save_parquet_with_sidecar(
                            df, out_path, sidecar_path, stage, domain,
                            f"get_price.index.{freq}", f"index_minute_{freq}_{year}", BATCH_ID
                        )
                        local_rows += rows
                        local_bytes += out_path.stat().st_size
                        local_q += 1
                        print(f"  [{now_cn()}] 指数分钟 {freq}: {rows} 行")
                except Exception as e:
                    print(f"  [{now_cn()}] 指数分钟 {freq}: {str(e)[:100]}")

    print(f"\n[{now_cn()}] T9 完成. 新增 {local_rows} 行 / {local_bytes/1024/1024:.2f} MB")
    return stage, quota_used + local_q, total_rows + local_rows, total_bytes + local_bytes


# ══════════════════════════════════════════════════════════
# 主执行入口
# ══════════════════════════════════════════════════════════


def main() -> None:
    """主执行函数"""
    print(f"\n{'#'*60}")
    print(f"# JQData 正式下载编排器 R1")
    print(f"# 开始时间: {now_cn()}")
    print(f"# Batch ID: {BATCH_ID}")
    print(f"# 根目录: {ROOT}")
    print(f"# 日期范围: {START_DATE} ~ {END_DATE}")
    print(f"{'#'*60}\n")

    # 1. 认证
    jq_auth()

    # 2. 初始化 checkpoint
    quota_used = 0
    total_rows = 0
    total_bytes = 0
    completed_stages = []

    save_checkpoint("T0", "bootstrap", "RUNNING",
                    completed_stages=[], quota_used=0,
                    total_rows=0, total_bytes=0)

    # 3. 执行 T0 → T9
    for stage in T_STAGES:
        remaining = get_quota_remaining()
        if remaining <= 0:
            msg = f"[{now_cn()}] 额度已耗尽 ({JQDATA_DAILY_QUOTA_LIMIT}), 停止执行"
            print(msg)
            save_checkpoint(stage, "ALL", "STOPPED",
                            stop_reason="QUOTA_EXHAUSTED",
                            completed_stages=completed_stages,
                            quota_used=quota_used,
                            total_rows=total_rows,
                            total_bytes=total_bytes)
            break

        if stage == "T0":
            _, quota_used, total_rows, total_bytes = run_t0(
                None, quota_used, total_rows, total_bytes
            )
            completed_stages.append("T0")
        elif stage == "T1":
            _, quota_used, total_rows, total_bytes = run_t1(
                None, quota_used, total_rows, total_bytes
            )
            completed_stages.append("T1")
        elif stage == "T2":
            _, quota_used, total_rows, total_bytes = run_t2(
                None, quota_used, total_rows, total_bytes
            )
            completed_stages.append("T2")
        elif stage == "T3":
            _, quota_used, total_rows, total_bytes = run_t3(
                None, quota_used, total_rows, total_bytes
            )
            completed_stages.append("T3")
        elif stage == "T4":
            _, quota_used, total_rows, total_bytes = run_t4(
                None, quota_used, total_rows, total_bytes
            )
            completed_stages.append("T4")
        elif stage == "T5":
            _, quota_used, total_rows, total_bytes = run_t5(
                None, quota_used, total_rows, total_bytes
            )
            completed_stages.append("T5")
        elif stage == "T6":
            _, quota_used, total_rows, total_bytes = run_t6(
                None, quota_used, total_rows, total_bytes
            )
            completed_stages.append("T6")
        elif stage == "T7":
            _, quota_used, total_rows, total_bytes = run_t7(
                None, quota_used, total_rows, total_bytes
            )
            completed_stages.append("T7")
        elif stage == "T8":
            _, quota_used, total_rows, total_bytes = run_t8(
                None, quota_used, total_rows, total_bytes
            )
            completed_stages.append("T8")
        elif stage == "T9":
            _, quota_used, total_rows, total_bytes = run_t9(
                None, quota_used, total_rows, total_bytes
            )
            completed_stages.append("T9")
        else:
            print(f"\n[{now_cn()}] [{stage}] 未知阶段，跳过")

    # 4. 最终日报
    final_quota = daily_quota_summary()
    print(f"\n{'='*60}")
    print(f"[{now_cn()}] 下载任务完成")
    print(f"  Batch ID:     {BATCH_ID}")
    print(f"  完成阶段:     {completed_stages}")
    print(f"  总行数:       {total_rows:,}")
    print(f"  总大小:       {total_bytes / 1024 / 1024:.2f} MB")
    print(f"  额度使用:     {quota_used:,} (日限额: {JQDATA_DAILY_QUOTA_LIMIT:,})")
    print(f"  API 请求数:   {final_quota['total_requests']}")
    print(f"  最终状态:     COMPLETED")
    print(f"{'='*60}\n")

    save_checkpoint("DONE", "ALL", "COMPLETED",
                    completed_stages=completed_stages,
                    quota_used=quota_used,
                    total_rows=total_rows,
                    total_bytes=total_bytes,
                    stop_reason="NORMAL_COMPLETION")


def resume_from_checkpoint() -> None:
    """从 checkpoint 恢复执行"""
    print(f"\n{'#'*60}")
    print(f"# JQData 下载编排器 - 恢复模式")
    print(f"# 开始时间: {now_cn()}")
    print(f"{'#'*60}\n")

    cp = load_checkpoint()
    if cp is None:
        print(f"[{now_cn()}] 未找到 checkpoint，从 start 模式重新开始")
        main()
        return

    resume_point = get_resume_point()
    print(f"[{now_cn()}] 从 checkpoint 恢复:")
    print(f"  当前阶段:     {resume_point['stage']}")
    print(f"  当前 domain:  {resume_point['domain']}")
    print(f"  已完成阶段:   {resume_point['completed_stages']}")
    print(f"  已完成分区数: {len(resume_point['completed_partitions'])}")
    print(f"  已用额度:     {resume_point['quota_used']}")

    # 认证
    jq_auth()

    quota_used = resume_point["quota_used"]
    total_rows = resume_point["total_rows"]
    total_bytes = resume_point["total_bytes"]
    completed_stages = list(resume_point["completed_stages"])

    # 从中断的阶段继续
    start_stage_idx = T_STAGES.index(resume_point["stage"])
    for stage in T_STAGES[start_stage_idx:]:
        remaining = get_quota_remaining()
        if remaining <= 0:
            msg = f"[{now_cn()}] 额度已耗尽, 停止执行"
            print(msg)
            save_checkpoint(stage, "ALL", "STOPPED",
                            stop_reason="QUOTA_EXHAUSTED",
                            completed_stages=completed_stages,
                            quota_used=quota_used,
                            total_rows=total_rows,
                            total_bytes=total_bytes)
            break

        if stage == "T0":
            _, quota_used, total_rows, total_bytes = run_t0(
                resume_point, quota_used, total_rows, total_bytes
            )
            if "T0" not in completed_stages:
                completed_stages.append("T0")
        elif stage == "T1":
            _, quota_used, total_rows, total_bytes = run_t1(
                resume_point, quota_used, total_rows, total_bytes
            )
            if "T1" not in completed_stages:
                completed_stages.append("T1")
        elif stage == "T2":
            _, quota_used, total_rows, total_bytes = run_t2(
                resume_point, quota_used, total_rows, total_bytes
            )
            if "T2" not in completed_stages:
                completed_stages.append("T2")
        elif stage == "T3":
            _, quota_used, total_rows, total_bytes = run_t3(
                resume_point, quota_used, total_rows, total_bytes
            )
            if "T3" not in completed_stages:
                completed_stages.append("T3")
        elif stage == "T4":
            _, quota_used, total_rows, total_bytes = run_t4(
                resume_point, quota_used, total_rows, total_bytes
            )
            if "T4" not in completed_stages:
                completed_stages.append("T4")
        elif stage == "T5":
            _, quota_used, total_rows, total_bytes = run_t5(
                resume_point, quota_used, total_rows, total_bytes
            )
            if "T5" not in completed_stages:
                completed_stages.append("T5")
        elif stage == "T6":
            _, quota_used, total_rows, total_bytes = run_t6(
                resume_point, quota_used, total_rows, total_bytes
            )
            if "T6" not in completed_stages:
                completed_stages.append("T6")
        elif stage == "T7":
            _, quota_used, total_rows, total_bytes = run_t7(
                resume_point, quota_used, total_rows, total_bytes
            )
            if "T7" not in completed_stages:
                completed_stages.append("T7")
        elif stage == "T8":
            _, quota_used, total_rows, total_bytes = run_t8(
                resume_point, quota_used, total_rows, total_bytes
            )
            if "T8" not in completed_stages:
                completed_stages.append("T8")
        elif stage == "T9":
            _, quota_used, total_rows, total_bytes = run_t9(
                resume_point, quota_used, total_rows, total_bytes
            )
            if "T9" not in completed_stages:
                completed_stages.append("T9")
        else:
            print(f"\n[{now_cn()}] [{stage}] 未知阶段，跳过")
            if stage not in completed_stages:
                completed_stages.append(stage)

    # 最终日报
    final_quota = daily_quota_summary()
    print(f"\n{'='*60}")
    print(f"[{now_cn()}] 恢复下载完成")
    print(f"  Batch ID:     {BATCH_ID}")
    print(f"  完成阶段:     {completed_stages}")
    print(f"  总行数:       {total_rows:,}")
    print(f"  总大小:       {total_bytes / 1024 / 1024:.2f} MB")
    print(f"  额度使用:     {quota_used:,}")
    print(f"  API 请求数:   {final_quota['total_requests']}")
    print(f"  最终状态:     COMPLETED")
    print(f"{'='*60}\n")

    save_checkpoint("DONE", "ALL", "COMPLETED",
                    completed_stages=completed_stages,
                    quota_used=quota_used,
                    total_rows=total_rows,
                    total_bytes=total_bytes,
                    stop_reason="RESUME_COMPLETION")


# ══════════════════════════════════════════════════════════
# 入口
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "start"
    if mode == "start":
        main()
    elif mode == "resume":
        resume_from_checkpoint()
    else:
        print(f"Usage: python jq_download_execution_r1.py [start|resume]")
        print(f"  未知模式: {mode}")
        sys.exit(1)
