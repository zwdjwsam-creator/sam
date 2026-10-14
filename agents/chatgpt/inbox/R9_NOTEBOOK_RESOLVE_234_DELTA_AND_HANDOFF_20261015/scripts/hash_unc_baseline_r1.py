import hashlib, os, time
unc = r"\\192.168.100.1\R9_SOURCE_BASELINE_20261014\SOURCE_BASELINE.sqlite"
expect = "94e6b7a7ec54fe91a5530fa3965926dc6ddcfd5e2861870f5ee370e4db7e98ba"
log = r"C:\LAN_SHARE_REPORT\R9_LOCAL_SOURCE_RECONCILE_20261014\logs\unc_sha.log"
h = hashlib.sha256()
n = 0
t0 = time.time()
size = os.path.getsize(unc)
with open(unc, "rb") as f, open(log, "w", encoding="utf-8") as lf:
    lf.write(f"size={size}\n")
    lf.flush()
    while True:
        b = f.read(8 << 20)
        if not b:
            break
        h.update(b)
        n += len(b)
        if n % (256 << 20) < (8 << 20):
            msg = f"{time.strftime('%H:%M:%S')} {n}/{size} {n/max(time.time()-t0,0.1)/1e6:.1f}MB/s"
            print(msg, flush=True)
            lf.write(msg + "\n")
            lf.flush()
got = h.hexdigest()
print("UNC_SHA", got, flush=True)
print("UNC_MATCH", got == expect, flush=True)
with open(log, "a", encoding="utf-8") as lf:
    lf.write(f"UNC_SHA={got}\nUNC_MATCH={got==expect}\n")
