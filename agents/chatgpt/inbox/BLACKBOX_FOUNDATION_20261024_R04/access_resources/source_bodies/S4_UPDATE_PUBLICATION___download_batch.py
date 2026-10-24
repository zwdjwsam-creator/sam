"""下载单批数据（子进程调用），用于带超时的主进程"""
import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import pandas as pd
import jqdatasdk as jq

# 参数：stock_codes_json start_date end_date frequency out_path
stock_codes = json.loads(sys.argv[1])
start_date = sys.argv[2]
end_date = sys.argv[3]
frequency = sys.argv[4]
out_path = sys.argv[5]
batch_id = sys.argv[6]
schema_version = sys.argv[7]

# 认证：支持「账号：/密码：」或两行明文
cred_file = r"E:/BLACKBOX/配置/secrets/已验证/聚宽账号.txt"
lines = [ln.strip() for ln in open(cred_file, encoding="utf-8").read().strip().split("\n") if ln.strip()]
username = password = None
plain = []
for line in lines:
    if "：" in line or ":" in line:
        k, v = (line.split("：", 1) if "：" in line else line.split(":", 1))
        k, v = k.strip(), v.strip()
        if "账号" in k or "user" in k.lower():
            username = v
        if "密码" in k or "pass" in k.lower():
            password = v
    else:
        plain.append(line)
if (not username or not password) and len(plain) >= 2:
    username, password = plain[0], plain[1]
if not username or not password:
    print(json.dumps({"status": "error", "error": "JQ_CREDENTIALS_MISSING"}))
    sys.exit(2)

jq.auth(username, password)

# 下载 — fq 必须显式传入（禁止默认复权）
t0 = time.time()
extra_kwargs = {}
if len(sys.argv) > 8:
    extra_kwargs = json.loads(sys.argv[8])
if "fq" not in extra_kwargs:
    print(json.dumps({"status": "error", "error": "FQ_EXPLICIT_REQUIRED", "hint": "pass fq=None for RAW_NONE"}))
    sys.exit(2)
df = jq.get_price(
    stock_codes,
    start_date=start_date,
    end_date=end_date,
    frequency=frequency,
    **extra_kwargs,
)
elapsed = time.time() - t0

if df is not None and len(df) > 0:
    df.to_parquet(out_path, index=False)
    meta = {
        "file": os.path.basename(out_path),
        "domain": "P7.stock_minute",
        "source_api": "get_price",
        "batch_id": batch_id,
        "schema_version": schema_version,
        "rows": len(df),
        "columns": list(df.columns),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(out_path.replace(".parquet", ".json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

# 输出结果给父进程解析
result = {
    "status": "ok",
    "rows": len(df) if df is not None else 0,
    "elapsed": round(elapsed, 1),
    "file": out_path if (df is not None and len(df) > 0) else None,
}
print(json.dumps(result))
